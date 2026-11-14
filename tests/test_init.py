"""Session ownership and setup lifecycle regression tests."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest
from yarl import URL

from custom_components import eau_agur
from custom_components.eau_agur.const import COORDINATOR, DOMAIN


@pytest.mark.asyncio
async def test_setup_isolates_entry_sessions():
    """Setting up another account never changes a shared or existing cookie jar."""
    entries = [Mock(entry_id=entry_id, data={"provider": "agur"}) for entry_id in ("first", "second")]
    hass = SimpleNamespace(data={}, config_entries=Mock(async_forward_entry_setups=AsyncMock()))
    coordinator = Mock(async_config_entry_first_refresh=AsyncMock())
    sessions = []

    def create_session(_hass, **kwargs):
        session = aiohttp.ClientSession(cookie_jar=kwargs["cookie_jar"])
        sessions.append(session)
        return session

    async with aiohttp.ClientSession() as shared:
        jar = shared.cookie_jar
        shared.cookie_jar.update_cookies({"affinity": "shared"}, URL("https://ael.agur.fr"))
        try:
            with (
                patch.object(eau_agur, "async_get_clientsession", return_value=shared, create=True),
                patch.object(eau_agur, "async_create_clientsession", side_effect=create_session, create=True),
                patch.object(eau_agur, "AgurApiClient") as client,
                patch.object(eau_agur, "EauAgurDataUpdateCoordinator", return_value=coordinator),
            ):
                assert await eau_agur.async_setup_entry(hass, entries[0])
                first = client.call_args.kwargs["session"]
                first.cookie_jar.update_cookies({"affinity": "first"}, URL("https://ael.agur.fr"))
                assert await eau_agur.async_setup_entry(hass, entries[1])
                second = client.call_args.kwargs["session"]

            assert first is not second and first is not shared and second is not shared
            assert shared.cookie_jar is jar
            assert shared.cookie_jar.filter_cookies(URL("https://ael.agur.fr"))["affinity"].value == "shared"
            assert first.cookie_jar.filter_cookies(URL("https://ael.agur.fr"))["affinity"].value == "first"
            assert not second.cookie_jar.filter_cookies(URL("https://ael.agur.fr"))
        finally:
            for session in sessions:
                await session.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [RuntimeError("refresh failed"), asyncio.CancelledError()])
async def test_failed_setup_detaches_session(failure):
    """A failed or cancelled first refresh leaves neither a session nor entry data."""
    session = Mock()
    entry = Mock(entry_id="entry", data={"provider": "agur"})
    other_data = {COORDINATOR: Mock()}
    hass = SimpleNamespace(data={DOMAIN: {"other": other_data}}, config_entries=Mock())
    coordinator = Mock(async_config_entry_first_refresh=AsyncMock(side_effect=failure))
    with (
        patch.object(eau_agur, "async_get_clientsession", return_value=session, create=True),
        patch.object(eau_agur, "async_create_clientsession", return_value=session, create=True),
        patch.object(eau_agur, "EauAgurDataUpdateCoordinator", return_value=coordinator),
        pytest.raises(type(failure)),
    ):
        await eau_agur.async_setup_entry(hass, entry)

    session.detach.assert_called_once_with()
    session.close.assert_not_called()
    assert hass.data[DOMAIN] == {"other": other_data}


@pytest.mark.asyncio
async def test_reload_uses_home_assistant_lifecycle():
    """The integration lets Home Assistant coordinate unload and setup."""
    hass = SimpleNamespace(config_entries=Mock())
    entry = Mock(entry_id="entry")
    with patch.object(eau_agur, "async_setup_entry") as setup, patch.object(eau_agur, "async_unload_entry") as unload:
        await eau_agur.async_reload_entry(hass, entry)
    hass.config_entries.async_schedule_reload.assert_called_once_with("entry")
    setup.assert_not_called()
    unload.assert_not_called()


@pytest.mark.asyncio
async def test_refused_unload_keeps_entry_data():
    """A refused unload does not discard another active entry's data."""
    data = {COORDINATOR: Mock()}
    hass = SimpleNamespace(
        data={DOMAIN: {"entry": data}},
        config_entries=Mock(async_unload_platforms=AsyncMock(return_value=False)),
    )
    assert not await eau_agur.async_unload_entry(hass, Mock(entry_id="entry"))
    assert hass.data[DOMAIN]["entry"] is data
