from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from eau_agur.api import AgurApiClient, AgurApiConnectionError, AgurApiUnauthorizedError
from eau_agur.const import SCAN_INTERVAL_IN_MINUTES, DOMAIN, LOGGER


class EauAgurDataUpdateCoordinator(DataUpdateCoordinator):
    """Data returned by the coordinator."""

    def __init__(self, hass: HomeAssistant, api_client: AgurApiClient, entry: ConfigEntry):
        """Initialize the coordinator."""

        super().__init__(
            hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL_IN_MINUTES,
        )

        self._api_client = api_client
        self._email = entry.data.get(CONF_EMAIL)
        self._password = entry.data.get(CONF_PASSWORD)

    async def _async_update_data(self) -> float:
        """Update data via library."""

        try:
            # Refresh the token and login if needed
            await self._api_client.generate_temporary_token()
            await self._api_client.login(self._email, self._password)

            # Get the consumption data
            return await self._api_client.get_consumption()

        except AgurApiUnauthorizedError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        except AgurApiConnectionError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
