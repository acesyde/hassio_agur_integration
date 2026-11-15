"""Configuration sessions live only for one authentication attempt."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from custom_components.eau_agur import async_reload_entry, config_flow
from custom_components.eau_agur.api import AgurApiConnectionError, AgurApiUnauthorizedError


@pytest.mark.asyncio
async def test_user_form_provides_documentation_placeholder():
    """The help link is supplied by the flow rather than embedded in translations."""
    result = await config_flow.EauAgurFlowHandler().async_step_user()
    assert result["description_placeholders"] == {
        "documentation_url": "https://github.com/acesyde/hassio_agur_integration"
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("step", ["user", "reconfigure"])
@pytest.mark.parametrize(
    "failure",
    [
        None,
        AgurApiUnauthorizedError("invalid credentials"),
        AgurApiConnectionError("timeout"),
        asyncio.CancelledError(),
    ],
)
async def test_authentication_attempt_detaches_session(step, failure):
    """Success, handled failure and cancellation release an attempt's private session."""
    session = Mock()
    api_client = Mock(
        generate_temporary_token=AsyncMock(),
        login=AsyncMock(side_effect=failure),
        get_default_contract=AsyncMock(return_value="12345"),
        get_contracts=AsyncMock(return_value={"12345": "12345"}),
    )
    entry = Mock(data={"email": "test@example.com", "password": "old", "provider": "agur"})
    flow = config_flow.EauAgurFlowHandler()
    flow.hass = SimpleNamespace(config_entries=Mock(async_get_entry=Mock(return_value=entry)))
    flow.context = {"entry_id": "entry"}
    flow._async_current_entries = Mock(return_value=[])
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = Mock()
    flow.async_create_entry = Mock(return_value={"type": "create_entry"})
    flow.async_update_and_abort = Mock(return_value={"type": "abort"})
    flow.async_show_form = Mock(return_value={"type": "form"})
    user_input = {"email": "test@example.com", "password": "new", "provider": "agur"}

    with (
        patch.object(config_flow, "async_create_clientsession", return_value=session) as create_session,
        patch.object(config_flow, "AgurApiClient", return_value=api_client),
    ):
        if isinstance(failure, asyncio.CancelledError):
            with pytest.raises(asyncio.CancelledError):
                await getattr(flow, f"async_step_{step}")(user_input)
        else:
            result = await getattr(flow, f"async_step_{step}")(user_input)
            assert result["type"] == ("form" if failure else "create_entry" if step == "user" else "abort")

    assert create_session.call_args.kwargs["auto_cleanup"] is False
    session.detach.assert_called_once_with()
    session.close.assert_not_called()


@pytest.mark.asyncio
async def test_duplicate_contract_detaches_session():
    """A configured-contract abort also cleans up the completed authentication."""
    session = Mock()
    flow = config_flow.EauAgurFlowHandler()
    flow.hass = Mock()
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = Mock(side_effect=RuntimeError("duplicate"))
    api_client = Mock(
        generate_temporary_token=AsyncMock(),
        login=AsyncMock(),
        get_default_contract=AsyncMock(return_value="12345"),
        get_contracts=AsyncMock(return_value={"12345": "12345"}),
    )
    with (
        patch.object(config_flow, "async_create_clientsession", return_value=session),
        patch.object(config_flow, "AgurApiClient", return_value=api_client),
        pytest.raises(RuntimeError, match="duplicate"),
    ):
        await flow.async_step_user({"email": "test@example.com", "password": "password", "provider": "agur"})
    session.detach.assert_called_once_with()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "password,failure,reloads",
    [("new", None, 1), ("old", None, 0), ("new", AgurApiUnauthorizedError("invalid credentials"), 0)],
)
async def test_reconfigure_uses_update_listener_without_deprecation(tmp_path, password, failure, reloads):
    hass = HomeAssistant(str(tmp_path))
    hass.config_entries = config_entries.ConfigEntries(hass, {})
    entry = config_entries.ConfigEntry(
        domain="eau_agur",
        version=1,
        minor_version=1,
        source="user",
        title="EAU par Agur",
        unique_id="001",
        data={"email": "test@example.com", "password": "old", "provider": "agur", "contract_number": "001"},
        options={},
        discovery_keys={},
        subentries_data=None,
    )
    hass.config_entries._entries[entry.entry_id] = entry
    entry.add_update_listener(async_reload_entry)
    flow = config_flow.EauAgurFlowHandler()
    flow.hass = hass
    flow.handler = "eau_agur"
    flow.context = {"source": "reconfigure", "entry_id": entry.entry_id}
    session = Mock()
    client = Mock(generate_temporary_token=AsyncMock(), login=AsyncMock(side_effect=failure))
    with (
        patch.object(config_flow, "async_create_clientsession", return_value=session),
        patch.object(config_flow, "AgurApiClient", return_value=client),
        patch.object(config_entries, "report_usage") as report,
        patch.object(hass.config_entries, "_async_schedule_save"),
        patch.object(hass.config_entries, "async_schedule_reload") as schedule,
    ):
        result = await flow.async_step_reconfigure({"password": password})
        await hass.async_block_till_done()
        report.assert_not_called()
        assert schedule.call_count == reloads
        if reloads:
            schedule.assert_called_once_with(entry.entry_id)
    if failure:
        assert result["errors"] == {"base": "auth"}
    else:
        assert result["reason"] == "reconfigure_successful"
    assert entry.data == {
        "email": "test@example.com",
        "password": "old" if failure else password,
        "provider": "agur",
        "contract_number": "001",
    }
    assert entry.unique_id == "001"
    session.detach.assert_called_once()
