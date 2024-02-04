from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AgurApiClient, AgurApiConnectionError, AgurApiUnauthorizedError
from .const import SCAN_INTERVAL_IN_MINUTES, DOMAIN, LOGGER, CONF_CONTRACT_NUMBER


class EauAgurDataUpdateCoordinator(DataUpdateCoordinator):
    """Data returned by the coordinator."""

    def __init__(self, hass: HomeAssistant, api_client: AgurApiClient, entry: ConfigEntry):
        """Initialize the coordinator."""

        self._api_client = api_client
        self._email = entry.data.get(CONF_EMAIL)
        self._password = entry.data.get(CONF_PASSWORD)
        self._password = entry.data.get(CONF_PASSWORD)
        self._contract_number = entry.data.get(CONF_CONTRACT_NUMBER)

        super().__init__(
            hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=SCAN_INTERVAL_IN_MINUTES),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""

        try:
            LOGGER.debug("Updating data from API")

            # Refresh the token and login if needed
            await self._api_client.generate_temporary_token()
            await self._api_client.login(self._email, self._password)

            # Get the consumption data
            result = {
                "consumption": await self.async_get_consumption(),
                "last_invoice": await self.async_get_last_invoice(),
            }

            return result

        except AgurApiUnauthorizedError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err

    async def async_get_consumption(self) -> float | None:
        """Return the consumption data."""
        try:
            return await self._api_client.get_consumption(self._contract_number)
        except AgurApiConnectionError as err:
            LOGGER.error(f"Error communicating with API: {err}")
            return None

    async def async_get_last_invoice(self) -> dict[str, Any] | None:
        """Return the last invoice data."""
        try:
            return await self._api_client.get_last_invoice(self._contract_number)
        except AgurApiConnectionError as err:
            LOGGER.error(f"Error communicating with API: {err}")
            return None
