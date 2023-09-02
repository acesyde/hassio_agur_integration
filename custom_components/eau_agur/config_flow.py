"""Adds config flow for EAU par Agur."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers import selector

from .api import AgurApiClient, AgurApiError, AgurApiConnectionError, AgurApiUnauthorizedError
from .const import DOMAIN, LOGGER, CONF_CONTRACT_NUMBER


class EauAgurFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for  EAU par Agur."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                api_client = AgurApiClient(
                    session=async_create_clientsession(self.hass),
                )

                await api_client.generate_temporary_token()

                await api_client.login(
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                )

                default_contract_id = await api_client.get_default_contract()

                data = {
                    CONF_EMAIL: user_input[CONF_EMAIL],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_CONTRACT_NUMBER: default_contract_id,
                }

                await self.async_set_unique_id(
                    default_contract_id
                )

                self._abort_if_unique_id_configured()

            except AgurApiUnauthorizedError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"

            except AgurApiConnectionError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"

            except AgurApiError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"

            else:
                return self.async_create_entry(title="EAU par Agur", data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_EMAIL,
                    default=(user_input or {}).get(CONF_EMAIL),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.EMAIL
                    ),
                ),
                vol.Required(CONF_PASSWORD): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.PASSWORD
                    ),
                ),
            }))
