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

    async def async_step_user(self, user_input=None) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors: dict[str, str] = {}
        if user_input is not None:
            session = None
            try:
                config_provider = PROVIDERS.get(user_input[CONF_PROVIDER], None)
                if config_provider is None:
                    raise AgurApiError("Provider not found")

                session = async_create_clientsession(
                    self.hass,
                    auto_cleanup=False,
                    cookie_jar=aiohttp.CookieJar(unsafe=False, quote_cookie=False),
                )
                api_client = AgurApiClient(
                    host=config_provider["base_url"],
                    base_path=config_provider.get("base_path", None),
                    timeout=config_provider.get("default_timeout", None),
                    client_id=config_provider["client_id"],
                    access_key=config_provider["access_key"],
                    session=session,
                )

                await api_client.generate_temporary_token()

                await api_client.login(
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                )

                contracts = await api_client.get_contracts()
                default_contract_id = await api_client.get_default_contract() if contracts else None

                self._contract_data = {
                    CONF_EMAIL: user_input[CONF_EMAIL],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_PROVIDER: user_input[CONF_PROVIDER],
                }

                self._contracts = contracts
                self._default_contract = default_contract_id

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
                if not contracts:
                    return self.async_abort(reason="no_contracts")
                if len(contracts) == 1:
                    return await self.async_step_contract({CONF_CONTRACT_NUMBER: next(iter(contracts))})
                return await self.async_step_contract()
            finally:
                if session is not None:
                    session.detach()

        return self.async_show_form(
            step_id="user",
            description_placeholders={"documentation_url": "https://github.com/acesyde/hassio_agur_integration"},
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

    async def async_step_contract(self, user_input=None) -> config_entries.ConfigFlowResult:
        """Choose one of the contracts returned by the authenticated account."""
        errors = {}
        if user_input is not None:
            number = user_input.get(CONF_CONTRACT_NUMBER)
            if not isinstance(number, str) or number not in self._contracts:
                errors["base"] = "invalid_contract"
            else:
                provider = self._contract_data[CONF_PROVIDER]
                await self.async_set_unique_id(f"{provider}:{number}")
                self._abort_if_unique_id_configured()
                # Legacy entries identify themselves by contract alone; keep them intact.
                if any(
                    entry.data.get(CONF_PROVIDER) == provider and entry.data.get(CONF_CONTRACT_NUMBER) == number
                    for entry in self._async_current_entries()
                ):
                    return self.async_abort(reason="already_configured")
                return self.async_create_entry(
                    title=f"{PROVIDERS[provider]['display_name']} — {number}",
                    data={**self._contract_data, CONF_CONTRACT_NUMBER: number},
                )
        default = self._default_contract
        return self.async_show_form(
            step_id="contract",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONTRACT_NUMBER, **({"default": default} if default in self._contracts else {})
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=number, label=label)
                                for number, label in self._contracts.items()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        entry_id = self.context.get("entry_id")
        if entry_id is None:
            return self.async_abort(reason="reconfigure_failed")

        entry = self.hass.config_entries.async_get_entry(entry_id)
        if entry is None:
            return self.async_abort(reason="reconfigure_failed")

        _errors: dict[str, str] = {}

        if user_input is not None:
            session = None
            try:
                # Get provider and email from existing entry (not from user input)
                provider = entry.data.get(CONF_PROVIDER)
                email = entry.data.get(CONF_EMAIL)
                password = user_input[CONF_PASSWORD]

                config_provider = PROVIDERS.get(provider, None)
                if config_provider is None:
                    raise AgurApiError("Provider not found")

                # Validate new credentials
                session = async_create_clientsession(
                    self.hass,
                    auto_cleanup=False,
                    cookie_jar=aiohttp.CookieJar(unsafe=False, quote_cookie=False),
                )
                api_client = AgurApiClient(
                    host=config_provider["base_url"],
                    base_path=config_provider.get("base_path", None),
                    timeout=config_provider.get("default_timeout", None),
                    client_id=config_provider["client_id"],
                    access_key=config_provider["access_key"],
                    session=session,
                )

                await api_client.generate_temporary_token()

                await api_client.login(email, password)

                # Update entry data - only password is updated
                updated_data = {**entry.data, CONF_PASSWORD: password}

                return self.async_update_and_abort(entry, data=updated_data)

            except AgurApiUnauthorizedError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"

            except AgurApiConnectionError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"

            except AgurApiError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            finally:
                if session is not None:
                    session.detach()

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
