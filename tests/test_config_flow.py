"""Configuration sessions live only for one authentication attempt."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.eau_agur import config_flow
from custom_components.eau_agur.api import AgurApiConnectionError, AgurApiUnauthorizedError


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
    )
    entry = Mock(data={"email": "test@example.com", "password": "old", "provider": "agur"})
    flow = config_flow.EauAgurFlowHandler()
    flow.hass = SimpleNamespace(config_entries=Mock(async_get_entry=Mock(return_value=entry)))
    flow.context = {"entry_id": "entry"}
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = Mock()
    flow.async_create_entry = Mock(return_value={"type": "create_entry"})
    flow.async_update_reload_and_abort = Mock(return_value={"type": "abort"})
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
    )
    with (
        patch.object(config_flow, "async_create_clientsession", return_value=session),
        patch.object(config_flow, "AgurApiClient", return_value=api_client),
        pytest.raises(RuntimeError, match="duplicate"),
    ):
        await flow.async_step_user({"email": "test@example.com", "password": "password", "provider": "agur"})
    session.detach.assert_called_once_with()
