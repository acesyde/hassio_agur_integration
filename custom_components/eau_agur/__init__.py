from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AgurApiClient
from .const import CONF_PROVIDER, DOMAIN, PLATFORMS, COORDINATOR, PROVIDERS
from .coordinator import EauAgurDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EAU par Agur from a config entry."""
    session = async_get_clientsession(hass)

    config_provider = PROVIDERS.get(entry.data[CONF_PROVIDER], None)
    if config_provider is None:
        raise Exception("Provider not found")

    client = AgurApiClient(
        host=config_provider["base_url"],
        base_path=config_provider.get("base_path", None),
        timeout=config_provider.get("default_timeout", None),
        conversation_id=config_provider["conversation_id"],
        client_id=config_provider["client_id"],
        access_key=config_provider["access_key"],
        session=session,
    )

    local_coordinator = EauAgurDataUpdateCoordinator(hass=hass, api_client=client, entry=entry)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {COORDINATOR: local_coordinator}

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await local_coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
