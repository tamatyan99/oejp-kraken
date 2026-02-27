"""Sensor platform for OEJP Kraken integration.

This module provides sensor entities for monitoring electricity usage,
consumption, and rates from the OEJP Kraken API.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OEJPDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OEJP Kraken sensors from a config entry.

    Creates sensor entities for:
    - Current power consumption (W)
    - Today's electricity consumption (kWh)
    - Current electricity rate (JPY/kWh)

    Args:
        hass: The Home Assistant instance.
        entry: The config entry being set up.
        async_add_entities: Callback to register entities.

    """
    coordinator: OEJPDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    # Get account info for device identification
    account_info = hass.data[DOMAIN][entry.entry_id].get("account_info", {})

    entities = [
        OEJPCurrentPowerSensor(coordinator, entry, account_info),
        OEJPTodayConsumptionSensor(coordinator, entry, account_info),
        OEJPCurrentRateSensor(coordinator, entry, account_info),
    ]

    async_add_entities(entities)
    _LOGGER.debug("Added %d OEJP Kraken sensors", len(entities))


class OEJPBaseSensor(CoordinatorEntity[OEJPDataUpdateCoordinator], SensorEntity):
    """Base class for OEJP Kraken sensors.

    Provides common functionality for all OEJP sensors:
    - Device info linking for grouping in UI
    - Coordinator update handling
    - Unique ID generation
    - Availability status

    Attributes:
        _attr_has_entity_name: Enable entity naming from translation.

    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OEJPDataUpdateCoordinator,
        entry: ConfigEntry,
        account_info: dict[str, Any],
        sensor_type: str,
    ) -> None:
        """Initialize the base sensor.

        Args:
            coordinator: Data update coordinator for fetching data.
            entry: Config entry for this sensor.
            account_info: Account information for device details.
            sensor_type: Type identifier for this sensor (e.g., 'current_power').

        """
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_type = sensor_type

        # Extract account details for device info
        self._account_id = account_info.get("account_id", entry.entry_id)
        self._mpan = account_info.get("mpan", "unknown")
        self._serial_number = account_info.get("serial_number", "unknown")

        # Set unique ID
        self._attr_unique_id = f"{DOMAIN}_{self._account_id}_{sensor_type}"

        # Set device info for grouping entities
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"electricity_{self._serial_number}_{self._mpan}")},
            name="OEJP Electricity Meter",
            manufacturer="OEJP Kraken",
            model="Smart Meter",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available.

        Returns False if coordinator has no data or the last update failed.

        Returns:
            True if the sensor has valid data available.

        """
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )

    def _get_coordinator_value(self, key: str, default: Any = None) -> Any:
        """Get a value from coordinator data safely.

        Args:
            key: The key to look up in coordinator data.
            default: Default value if key not found or data is None.

        Returns:
            The value from coordinator data, or the default.

        """
        if self.coordinator.data is None:
            return default
        return self.coordinator.data.get(key, default)


class OEJPCurrentPowerSensor(OEJPBaseSensor):
    """Sensor for current power consumption in watts.

    Displays real-time power demand from the electricity meter.
    The value is updated every 5 minutes (configurable) via the coordinator.

    Attributes:
        _attr_device_class: Power device class.
        _attr_state_class: Measurement state class.
        _attr_native_unit_of_measurement: Watts.
        _attr_translation_key: Translation key for UI.
        _attr_icon: Material Design icon.

    """

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_translation_key = "current_power"
    _attr_icon = "mdi:flash"

    def __init__(
        self,
        coordinator: OEJPDataUpdateCoordinator,
        entry: ConfigEntry,
        account_info: dict[str, Any],
    ) -> None:
        """Initialize the current power sensor.

        Args:
            coordinator: Data update coordinator.
            entry: Config entry.
            account_info: Account information.

        """
        super().__init__(coordinator, entry, account_info, "current_power")

    @property
    def native_value(self) -> float | None:
        """Return the current power consumption in watts.

        The API may return power in kW, which is converted to W.

        Returns:
            Current power in W, or None if unavailable.

        """
        current_usage = self._get_coordinator_value("current_usage")
        if current_usage is not None and isinstance(current_usage, (int, float)):
            # Convert kW to W if needed (API typically returns kW)
            return round(current_usage * 1000, 2)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes.

        Returns:
            Dictionary containing last_update time.

        """
        return self._build_attributes(["last_updated"])

    def _build_attributes(self, keys: list[str]) -> dict[str, Any]:
        """Build attributes dict from coordinator data.

        Args:
            keys: List of keys to include in attributes.

        Returns:
            Dictionary of non-None attributes.

        """
        attrs: dict[str, Any] = {}
        for key in keys:
            value = self._get_coordinator_value(key)
            if value is not None:
                attrs[key] = value
        return attrs


class OEJPTodayConsumptionSensor(OEJPBaseSensor):
    """Sensor for today's electricity consumption in kWh.

    Displays cumulative consumption for the current day.
    Uses TOTAL_INCREASING state class for Energy Dashboard compatibility.

    Attributes:
        _attr_device_class: Energy device class.
        _attr_state_class: Total increasing state class.
        _attr_native_unit_of_measurement: Kilowatt-hours.
        _attr_translation_key: Translation key for UI.
        _attr_icon: Material Design icon.

    """

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_translation_key = "today_consumption"
    _attr_icon = "mdi:lightning-bolt"

    def __init__(
        self,
        coordinator: OEJPDataUpdateCoordinator,
        entry: ConfigEntry,
        account_info: dict[str, Any],
    ) -> None:
        """Initialize the today consumption sensor.

        Args:
            coordinator: Data update coordinator.
            entry: Config entry.
            account_info: Account information.

        """
        super().__init__(coordinator, entry, account_info, "today_consumption")

    @property
    def native_value(self) -> float | None:
        """Return today's cumulative consumption in kWh.

        First checks daily_consumption, then falls back to total_consumption.

        Returns:
            Today's consumption in kWh, or None if unavailable.

        """
        # Try daily consumption first
        daily_consumption = self._get_coordinator_value("daily_consumption", {})
        if daily_consumption:
            today_value = daily_consumption.get("consumption")
            if today_value is not None and isinstance(today_value, (int, float)):
                return round(today_value, 3)

        # Fallback to total_consumption
        total_consumption = self._get_coordinator_value("total_consumption")
        if total_consumption is not None and isinstance(
            total_consumption, (int, float)
        ):
            return round(total_consumption, 3)

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes.

        Includes daily consumption breakdown if available.

        Returns:
            Dictionary containing consumption details.

        """
        attrs: dict[str, Any] = {}

        # Add last update time
        if last_updated := self._get_coordinator_value("last_updated"):
            attrs["last_updated"] = last_updated

        # Add daily consumption details
        daily_consumption = self._get_coordinator_value("daily_consumption", {})
        if daily_consumption:
            for key in ["date", "peak_consumption", "off_peak_consumption"]:
                if key in daily_consumption:
                    attrs[key] = daily_consumption[key]

        return attrs


class OEJPCurrentRateSensor(OEJPBaseSensor):
    """Sensor for current electricity rate in JPY/kWh.

    Displays the current rate per kilowatt-hour.
    Uses monetary device class for currency formatting.

    Attributes:
        _attr_device_class: Monetary device class.
        _attr_state_class: Measurement state class.
        _attr_native_unit_of_measurement: JPY/kWh.
        _attr_translation_key: Translation key for UI.
        _attr_icon: Material Design icon.

    """

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "JPY/kWh"
    _attr_translation_key = "current_rate"
    _attr_icon = "mdi:currency-jpy"

    def __init__(
        self,
        coordinator: OEJPDataUpdateCoordinator,
        entry: ConfigEntry,
        account_info: dict[str, Any],
    ) -> None:
        """Initialize the current rate sensor.

        Args:
            coordinator: Data update coordinator.
            entry: Config entry.
            account_info: Account information.

        """
        super().__init__(coordinator, entry, account_info, "current_rate")

    @property
    def native_value(self) -> float | None:
        """Return the current electricity rate in JPY/kWh.

        Returns:
            Current rate in JPY/kWh, or None if unavailable.

        """
        current_rate = self._get_coordinator_value("current_rate")
        if current_rate is not None and isinstance(current_rate, (int, float)):
            return round(current_rate, 4)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes.

        Includes rate period information if available.

        Returns:
            Dictionary containing rate details.

        """
        attrs: dict[str, Any] = {}

        # Add last update time
        if last_updated := self._get_coordinator_value("last_updated"):
            attrs["last_updated"] = last_updated

        # Add rate details
        rate_info = self._get_coordinator_value("rate_info", {})
        if rate_info:
            for key in ["tariff_name", "rate_period", "peak_rate", "off_peak_rate"]:
                if key in rate_info:
                    attrs[key] = rate_info[key]

        return attrs
