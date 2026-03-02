"""Config flow for OEJP Kraken integration.

This module provides the UI-based configuration flow for setting up
the OEJP Kraken integration in Home Assistant.
"""

from __future__ import annotations

import logging
import re
import aiohttp

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Schema for user input
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional("update_interval", default=DEFAULT_UPDATE_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=60, max=3600)
        ),
    }
)


class OEJPConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OEJP Kraken.

    This class manages the UI-based setup flow for the integration,
    including credential validation and initial configuration.

    Attributes:
        version: The config flow version (1).

    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step of the config flow.

        This method displays a form for the user to enter their OEJP
        credentials and validates them by attempting authentication.

        Args:
            user_input: User input from the form, or None if this is
                the initial display.

        Returns:
            Either a form to display or a config entry creation result.

        """
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input.get(CONF_EMAIL, "")
            password = user_input.get(CONF_PASSWORD, "")
            update_interval = user_input.get("update_interval", DEFAULT_UPDATE_INTERVAL)

            # Validate email format
            if not self._validate_email(email):
                errors[CONF_EMAIL] = "invalid_email"
            elif not password:
                errors[CONF_PASSWORD] = "invalid_input"
            else:
                # Attempt authentication
                auth_result = await self._async_authenticate(email, password)
                if auth_result is True:
                    # Check for existing entry with same email
                    await self.async_set_unique_id(email.lower())
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title="OEJP Kraken",
                        data={
                            CONF_EMAIL: email,
                            CONF_PASSWORD: password,
                            "update_interval": update_interval,
                        },
                    )
                errors["base"] = auth_result

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_import(self, import_config: dict[str, Any]) -> FlowResult:
        """Handle import from YAML configuration.

        This method is called when the integration is configured via YAML.
        Currently, YAML configuration is not supported.

        Args:
            import_config: The YAML configuration dictionary.

        Returns:
            An abort result indicating YAML is not supported.

        """
        # YAML import is not supported, use UI config
        return self.async_abort(reason="yaml_not_supported")

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle re-authentication flow.

        This method is called when authentication fails and the user
        needs to re-enter their credentials.

        Args:
            entry_data: Existing entry data.

        Returns:
            The reauth confirm form.

        """
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle re-authentication confirmation.

        Args:
            user_input: User input from the form.

        Returns:
            Either a form to display or a config entry update result.

        """
        errors: dict[str, str] = {}

        if user_input is not None:
            entry = await self.async_set_unique_id(
                user_input.get(CONF_EMAIL, "").lower()
            )
            if entry:
                password = user_input.get(CONF_PASSWORD, "")
                if (
                    await self._async_authenticate(user_input[CONF_EMAIL], password)
                    is True
                ):
                    self.hass.config_entries.async_update_entry(
                        entry,
                        data={
                            **entry.data,
                            CONF_PASSWORD: password,
                        },
                    )
                    await self.hass.config_entries.async_reload(entry.entry_id)
                    return self.async_abort(reason="reauth_successful")
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler.

        Args:
            config_entry: The config entry to get options for.

        Returns:
            The options flow handler.

        """
        return OEJPOptionsFlowHandler(config_entry)

    def _validate_email(self, email: str) -> bool:
        """Validate email format.

        Args:
            email: The email address to validate.

        Returns:
            True if the email format is valid.

        """
        if not email or not isinstance(email, str):
            return False
        # Basic email format validation
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email.strip()))

    async def _async_authenticate(self, email: str, password: str) -> bool | str:
        """Attempt to authenticate with the OEJP Kraken API.

        Args:
            email: The email address for authentication.
            password: The password for authentication.

        Returns:
            True if authentication succeeded, or an error code string.

        """
        from .graphql_client import (
            KrakenAuthenticationError,
            KrakenError,
            KrakenGraphQLClient,
        )

        try:
            client = KrakenGraphQLClient(email, password)
            await client.authenticate()
            await client.close()
            return True
        except KrakenAuthenticationError:
            return "invalid_auth"
        except KrakenError:
            return "cannot_connect"
        except aiohttp.ClientError as err:


            _LOGGER.warning("Network error during authentication: %s", err)
            return "cannot_connect"
        except TimeoutError as err:
            _LOGGER.warning("Timeout during authentication: %s", err)
            return "timeout_connect"
        except OSError as err:  # pragma: no cover - unexpected errors
            _LOGGER.exception("OS error during authentication: %s", err)
            return "unknown"
class OEJPOptionsFlowHandler(OptionsFlow):
    """Handle options flow for OEJP Kraken.

    This class manages the options configuration UI for the integration.

    Attributes:
        config_entry: The config entry being configured.

    """

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the options flow handler.

        Args:
            config_entry: The config entry to configure options for.

        """
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options flow initialization.

        This method displays the options form and handles user input.

        Args:
            user_input: User input from the form, or None if this is
                the initial display.

        Returns:
            Either a form to display or a config entry update result.

        """
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        update_interval = options.get("update_interval", DEFAULT_UPDATE_INTERVAL)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "update_interval",
                        default=update_interval,
                    ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
                }
            ),
        )
