"""Adds config flow for EAU par Agur."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    AgurApiClient,
    AgurApiConnectionError,
    AgurApiError,
    AgurApiUnauthorizedError,
)
from .const import CONF_CONTRACT_NUMBER, CONF_PROVIDER, DOMAIN, LOGGER, PROVIDERS


class EauAgurFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for  EAU par Agur."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors: dict[str, str] = {}
        if user_input is not None:
            try:
                config_provider = PROVIDERS.get(user_input[CONF_PROVIDER], None)
                if config_provider is None:
                    raise AgurApiError("Provider not found")

                api_client = AgurApiClient(
                    host=config_provider["base_url"],
                    base_path=config_provider.get("base_path", None),
                    timeout=config_provider.get("default_timeout", None),
                    client_id=config_provider["client_id"],
                    access_key=config_provider["access_key"],
                    session=async_create_clientsession(
                        self.hass, cookie_jar=aiohttp.CookieJar(unsafe=False, quote_cookie=False)
                    ),
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
                    CONF_PROVIDER: user_input[CONF_PROVIDER],
                    CONF_CONTRACT_NUMBER: default_contract_id,
                }

                await self.async_set_unique_id(default_contract_id)

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
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_EMAIL,
                        default=(user_input or {}).get(CONF_EMAIL),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.EMAIL),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD),
                    ),
                    vol.Required(CONF_PROVIDER): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=key, label=PROVIDERS[key]["display_name"])
                                for key in PROVIDERS
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                }
            ),
            errors=_errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        entry_id = self.context.get("entry_id")
        if entry_id is None:
            return self.async_abort(reason="reconfigure_failed")
        
        entry = self.hass.config_entries.async_get_entry(entry_id)
        if entry is None:
            return self.async_abort(reason="reconfigure_failed")
        
        _errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                # Get provider and email from existing entry (not from user input)
                provider = entry.data.get(CONF_PROVIDER)
                email = entry.data.get(CONF_EMAIL)
                password = user_input[CONF_PASSWORD]

                config_provider = PROVIDERS.get(provider, None)
                if config_provider is None:
                    raise AgurApiError("Provider not found")

                # Validate new credentials
                api_client = AgurApiClient(
                    host=config_provider["base_url"],
                    base_path=config_provider.get("base_path", None),
                    timeout=config_provider.get("default_timeout", None),
                    client_id=config_provider["client_id"],
                    access_key=config_provider["access_key"],
                    session=async_create_clientsession(
                        self.hass, cookie_jar=aiohttp.CookieJar(unsafe=False, quote_cookie=False)
                    ),
                )

                await api_client.generate_temporary_token()

                await api_client.login(email, password)

                # Update entry data - only password is updated
                updated_data = {
                    **entry.data,
                    CONF_PASSWORD: password
                }

                return self.async_update_reload_and_abort(entry, data=updated_data)

            except AgurApiUnauthorizedError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"

            except AgurApiConnectionError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"

            except AgurApiError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"

        # Show form with only password field
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD),
                    ),
                }
            ),
            errors=_errors,
        )
