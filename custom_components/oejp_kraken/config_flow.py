"""OEJP Kraken config flow for UI setup."""

from __future__ import annotations
import re

import voluptuous as vol
import logging

from homeassistant import config_entries
from homeassistant import config_entries
from .const import (
    DOMAIN,
    CONF_EMAIL as EMAIL_KEY,
    CONF_PASSWORD as PASSWORD_KEY,
    DEFAULT_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class OEJPConfigFlow(config_entries.ConfigFlow):
    domain = DOMAIN
    """Config flow for OEJP Kraken integration."""

    version = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            email = user_input.get(EMAIL_KEY)
            password = user_input.get(PASSWORD_KEY)
            update_interval = user_input.get("update_interval", DEFAULT_UPDATE_INTERVAL)

            # Normalize update interval
            try:
                update_interval = int(update_interval)
            except (TypeError, ValueError):
                update_interval = DEFAULT_UPDATE_INTERVAL

            # Validate basic fields
            if not email or not isinstance(email, str):
                errors[EMAIL_KEY] = "invalid_email"
            else:
                # Basic email format check
                if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
                    errors[EMAIL_KEY] = "invalid_email"
            if not password or not isinstance(password, str):
                errors[PASSWORD_KEY] = "invalid_input"

            if not errors:
                # Try authenticate via GraphQL client
                from .graphql_client import (
                    KrakenGraphQLClient,
                    KrakenAuthenticationError,
                    KrakenError,
                )

                try:
                    client = KrakenGraphQLClient(email, password)
                    await client.authenticate()

                    return self.async_create_entry(
                        title="OEJP Kraken",
                        data={
                            EMAIL_KEY: email,
                            PASSWORD_KEY: password,
                            "update_interval": update_interval,
                        },
                    )
                except KrakenAuthenticationError:
                    errors["base"] = "invalid_auth"
                except KrakenError:
                    errors["base"] = "cannot_connect"
                except Exception as err:  # pragma: no cover - unexpected errors
                    _LOGGER.exception("Unexpected error during authentication: %s", err)
                    errors["base"] = "unknown"

        # Show the config form
        data_schema = vol.Schema(
            {
                vol.Required(EMAIL_KEY): str,
                vol.Required(PASSWORD_KEY): str,
                vol.Optional("update_interval", default=DEFAULT_UPDATE_INTERVAL): int,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_import(
        self, import_config
    ):  # pragma: no cover - not used in tests
        return self.async_abort(reason="already_configured")
