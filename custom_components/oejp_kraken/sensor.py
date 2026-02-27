"""Sensor platform for OEJP Kraken integration."""

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

    Args:
        hass: Home Assistant instance
        entry: Config entry being set up
        async_add_entities: Callback to add entities

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

    Provides common functionality:
    - Device info linking
    - Coordinator update handling
    - Unique ID generation

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
            coordinator: Data update coordinator
            entry: Config entry
            account_info: Account information for device details
            sensor_type: Type identifier for this sensor

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

        Returns False if coordinator has no data or data is None.

        """
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )


class OEJPCurrentPowerSensor(OEJPBaseSensor):
    """Sensor for current power consumption in watts.

    Displays real-time power demand from the electricity meter.
    Updates every 5 minutes via the coordinator.

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
            coordinator: Data update coordinator
            entry: Config entry
            account_info: Account information

        """
        super().__init__(coordinator, entry, account_info, "current_power")

    @property
    def native_value(self) -> float | None:
        """Return the current power consumption in watts.

        Returns:
            Current power in W, or None if unavailable

        """
        if self.coordinator.data is None:
            return None

        # Get current usage - API may return in kW, convert to W
        current_usage = self.coordinator.data.get("current_usage")
        if current_usage is not None:
            # If data is in kW, convert to W
            if isinstance(current_usage, (int, float)):
                # Assume API returns kW for power, convert to W
                return round(current_usage * 1000, 2)

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes.

        Returns:
            Dictionary of extra attributes

        """
        attrs = {
            "last_updated": self.coordinator.data.get("last_updated")
            if self.coordinator.data
            else None,
        }
        return {k: v for k, v in attrs.items() if v is not None}


class OEJPTodayConsumptionSensor(OEJPBaseSensor):
    """Sensor for today's electricity consumption in kWh.

    Displays cumulative consumption for the current day.
    Uses TOTAL_INCREASING state class for Energy Dashboard compatibility.

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
            coordinator: Data update coordinator
            entry: Config entry
            account_info: Account information

        """
        super().__init__(coordinator, entry, account_info, "today_consumption")

    @property
    def native_value(self) -> float | None:
        """Return today's cumulative consumption in kWh.

        Returns:
            Today's consumption in kWh, or None if unavailable

        """
        if self.coordinator.data is None:
            return None

        # Get daily consumption data
        daily_consumption = self.coordinator.data.get("daily_consumption", {})
        if daily_consumption:
            # Get today's consumption value
            today_value = daily_consumption.get("consumption")
            if today_value is not None and isinstance(today_value, (int, float)):
                return round(today_value, 3)

        # Fallback to total_consumption if daily not available
        total_consumption = self.coordinator.data.get("total_consumption")
        if total_consumption is not None and isinstance(
            total_consumption, (int, float)
        ):
            return round(total_consumption, 3)

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes.

        Returns:
            Dictionary of extra attributes including daily breakdown

        """
        attrs: dict[str, Any] = {}

        if self.coordinator.data is None:
            return attrs

        # Add last update time
        if last_updated := self.coordinator.data.get("last_updated"):
            attrs["last_updated"] = last_updated

        # Add daily consumption details if available
        daily_consumption = self.coordinator.data.get("daily_consumption", {})
        if daily_consumption:
            if "date" in daily_consumption:
                attrs["date"] = daily_consumption["date"]
            if "peak_consumption" in daily_consumption:
                attrs["peak_consumption"] = daily_consumption["peak_consumption"]
            if "off_peak_consumption" in daily_consumption:
                attrs["off_peak_consumption"] = daily_consumption[
                    "off_peak_consumption"
                ]

        return attrs


class OEJPCurrentRateSensor(OEJPBaseSensor):
    """Sensor for current electricity rate in JPY/kWh.

    Displays the current rate per kilowatt-hour.
    Uses monetary device class for currency formatting.

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
            coordinator: Data update coordinator
            entry: Config entry
            account_info: Account information

        """
        super().__init__(coordinator, entry, account_info, "current_rate")

    @property
    def native_value(self) -> float | None:
        """Return the current electricity rate in JPY/kWh.

        Returns:
            Current rate in JPY/kWh, or None if unavailable

        """
        if self.coordinator.data is None:
            return None

        # Get current rate
        current_rate = self.coordinator.data.get("current_rate")
        if current_rate is not None and isinstance(current_rate, (int, float)):
            return round(current_rate, 4)

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes.

        Returns:
            Dictionary of extra attributes including rate period info

        """
        attrs: dict[str, Any] = {}

        if self.coordinator.data is None:
            return attrs

        # Add last update time
        if last_updated := self.coordinator.data.get("last_updated"):
            attrs["last_updated"] = last_updated

        # Add rate details if available
        rate_info = self.coordinator.data.get("rate_info", {})
        if rate_info:
            if "tariff_name" in rate_info:
                attrs["tariff_name"] = rate_info["tariff_name"]
            if "rate_period" in rate_info:
                attrs["rate_period"] = rate_info["rate_period"]
            if "peak_rate" in rate_info:
                attrs["peak_rate"] = rate_info["peak_rate"]
            if "off_peak_rate" in rate_info:
                attrs["off_peak_rate"] = rate_info["off_peak_rate"]

        return attrs
