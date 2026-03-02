"""OEJP Kraken integration for Home Assistant.

This integration connects to Octopus Energy Japan's Kraken API
to provide electricity usage monitoring and rate information.

For more details about this integration, please refer to
https://github.com/tamatyan99/oejp-kraken
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import aiohttp
from homeassistant.exceptions import ConfigEntryNotReady

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import OEJPDataUpdateCoordinator
from .graphql_client import KrakenGraphQLClient

if TYPE_CHECKING:
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

import logging
from typing import TYPE_CHECKING

import aiohttp
from homeassistant.exceptions import ConfigEntryNotReady
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import OEJPDataUpdateCoordinator
from .graphql_client import KrakenGraphQLClient

if TYPE_CHECKING:
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the OEJP Kraken integration from YAML configuration.

    This function is called when the integration is set up via YAML.
    Currently, only UI-based configuration is supported.

    Args:
        hass: The Home Assistant instance.
        config: The YAML configuration dictionary.

    Returns:
        True if setup was successful.

    """
    # Store an empty dict for the domain data
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OEJP Kraken from a config entry.

    This function is called when a config entry is added and sets up
    the integration by:
    1. Creating the GraphQL client
    2. Authenticating with the API
    3. Creating the data coordinator
    4. Setting up the sensor platform

    Args:
        hass: The Home Assistant instance.
        entry: The config entry being set up.

    Returns:
        True if setup was successful.

    Raises:
        ConfigEntryNotReady: If the API is not available.

    """
    from .const import CONF_EMAIL, CONF_PASSWORD

    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    update_interval = entry.data.get("update_interval", 300)

    # Create GraphQL client
    client = KrakenGraphQLClient(email, password)

    # Authenticate with the API
    from .graphql_client import KrakenAuthenticationError, KrakenError

    try:
        await client.authenticate()
        _LOGGER.info("Successfully authenticated with OEJP Kraken API")
    except KrakenAuthenticationError as err:
        _LOGGER.error("Authentication failed: %s", err)
        await client.close()
        raise ConfigEntryNotReady(f"Authentication failed: {err}") from err
    except KrakenError as err:
        _LOGGER.error("API error during setup: %s", err)
        await client.close()
        raise ConfigEntryNotReady(f"API error: {err}") from err
    except aiohttp.ClientError as err:
        _LOGGER.error("Network error during setup: %s", err)
        await client.close()
        raise ConfigEntryNotReady(f"Network error: {err}") from err

    # Create the coordinator
    coordinator = OEJPDataUpdateCoordinator(
        hass,
        client,
        update_interval=update_interval,
    )

    # Store the coordinator and client in hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
        "account_info": {
            "account_id": entry.entry_id,
        },
    }

    # Perform initial data refresh
    await coordinator.async_config_entry_first_refresh()

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    This function is called when a config entry is removed or disabled.
    It cleans up the coordinator and closes the API client.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry being unloaded.

    Returns:
        True if unload was successful.

    """
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Get stored data
        data = hass.data[DOMAIN].pop(entry.entry_id, {})

        # Close the GraphQL client
        client: KrakenGraphQLClient | None = data.get("client")
        if client:
            await client.close()
            _LOGGER.debug("Closed GraphQL client for entry %s", entry.entry_id)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry data to new version.

    This function is called when the config entry version changes.
    Currently, only version 1 is supported.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry to migrate.

    Returns:
        True if migration was successful.

    """
    _LOGGER.debug(
        "Migrating configuration from version %s.%s",
        entry.version,
        entry.minor_version,
    )

    # Version 1 is the current version, no migration needed
    if entry.version == 1:
        return True

    # Future migrations would go here
    # Example:
    # if entry.version == 1:
    #     new_data = {**entry.data}
    #     new_data["new_field"] = "default_value"
    #     hass.config_entries.async_update_entry(entry, data=new_data, version=2)

    _LOGGER.error(
        "Unknown configuration version %s.%s",
        entry.version,
        entry.minor_version,
    )
    return False
