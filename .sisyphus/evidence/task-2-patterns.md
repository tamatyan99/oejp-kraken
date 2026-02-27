# Home Assistant Energy Integration Patterns Analysis

**Task**: Wave 1, Task 2 - OEJP Integration Pattern Research  
**Source**: BottlecapDave/HomeAssistant-OctopusEnergy (Custom Component)  
**Date**: 2026-02-27

---

## 1. File Structure

Based on analysis of the Octopus Energy custom component:

```
custom_components/octopus_energy/
├── __init__.py              # Entry point, setup coordinators
├── manifest.json            # Integration metadata
├── config_flow.py           # UI configuration flow
├── const.py                 # Constants and configuration keys
├── sensor.py                # Sensor platform setup
├── binary_sensor.py         # Binary sensor platform
├── coordinators/            # DataUpdateCoordinator implementations
│   ├── __init__.py          # Base classes and utilities
│   ├── account.py           # Account data coordinator
│   ├── current_consumption.py
│   ├── electricity_rates.py
│   ├── gas_rates.py
│   └── ...
├── electricity/             # Electricity sensor entities
│   ├── base.py              # Base electricity sensor class
│   ├── current_rate.py
│   ├── previous_accumulative_consumption.py
│   └── ...
├── gas/                     # Gas sensor entities
│   ├── base.py              # Base gas sensor class
│   ├── current_rate.py
│   └── ...
├── api_client/              # API client for external service
├── utils/                   # Utility functions
├── storage/                 # Persistent storage helpers
└── translations/            # Localization files
```

---

## 2. DataUpdateCoordinator Pattern

### 2.1 Base Coordinator Result Class

```python
# coordinators/__init__.py
from homeassistant.helpers.update_coordinator import CoordinatorEntity

class BaseCoordinatorResult:
    """Base class for coordinator results with retry logic."""
    last_evaluated: datetime
    last_retrieved: datetime
    next_refresh: datetime
    request_attempts: int
    refresh_rate_in_minutes: float
    last_error: Exception | None

    def __init__(
        self, 
        last_evaluated: datetime, 
        request_attempts: int, 
        refresh_rate_in_minutes: float, 
        last_retrieved: datetime | None = None, 
        last_error: Exception | None = None
    ):
        self.last_evaluated = last_evaluated
        self.last_retrieved = last_retrieved if last_retrieved is not None else last_evaluated
        self.request_attempts = request_attempts
        self.next_refresh = calculate_next_refresh(
            last_evaluated, request_attempts, refresh_rate_in_minutes
        )
        self.last_error = last_error
```

### 2.2 Coordinator Factory Pattern

```python
# coordinators/current_consumption.py
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

class CurrentConsumptionCoordinatorResult(BaseCoordinatorResult):
    data: list

    def __init__(
        self, 
        last_evaluated: datetime, 
        request_attempts: int, 
        refresh_rate_in_minutes: float, 
        data: list, 
        last_error: Exception | None = None
    ):
        super().__init__(last_evaluated, request_attempts, refresh_rate_in_minutes, None, last_error)
        self.data = data


async def async_create_current_consumption_coordinator(
    hass, 
    account_id: str, 
    client: OctopusEnergyApiClient, 
    device_id: str, 
    refresh_rate_in_minutes: float
):
    """Create current consumption coordinator"""
    key = DATA_CURRENT_CONSUMPTION_KEY.format(device_id)
    hass.data[DOMAIN][account_id][key] = None

    async def async_update_data():
        """Fetch data from API endpoint."""
        current: datetime = now()
        previous_consumption = hass.data[DOMAIN][account_id].get(key)
        hass.data[DOMAIN][account_id][key] = await async_get_live_consumption(
            current,
            client,
            device_id,
            previous_consumption,
            refresh_rate_in_minutes
        )
        return hass.data[DOMAIN][account_id][key]

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"current_consumption_{device_id}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=COORDINATOR_REFRESH_IN_SECONDS),
        always_update=True  # Key: always update even if data unchanged
    )

    return coordinator
```

### 2.3 Multi-Coordinator Entity Pattern

For entities that need data from multiple coordinators:

```python
# coordinators/__init__.py
class MultiCoordinatorEntity(CoordinatorEntity):
    """Entity that depends on multiple coordinators."""
    
    def __init__(self, primary_coordinator, secondary_coordinators):
        CoordinatorEntity.__init__(self, primary_coordinator)
        self._secondary_coordinators = secondary_coordinators

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        for secondary_coordinator in self._secondary_coordinators:
            self.async_on_remove(
                secondary_coordinator.async_add_listener(
                    self._handle_coordinator_update, 
                    self.coordinator_context
                )
            )
```

---

## 3. Sensor Entity Pattern

### 3.1 Base Sensor Class with Device Info

```python
# electricity/base.py
from homeassistant.helpers.entity import DeviceInfo

class OctopusEnergyElectricitySensor:
    """Base class for electricity sensors."""
    
    _unrecorded_attributes = frozenset({"data_last_retrieved"})

    def __init__(self, hass: HomeAssistant, meter, point, entity_domain="sensor"):
        self._point = point
        self._meter = meter
        self._hass = hass

        self._mpan = point["mpan"]
        self._serial_number = meter["serial_number"]
        self._is_export = meter["is_export"]
        self._is_smart_meter = meter["is_smart_meter"]

        self._attributes = {
            "mpan": self._mpan,
            "serial_number": self._serial_number,
            "is_export": self._is_export,
            "is_smart_meter": self._is_smart_meter
        }

        self.entity_id = generate_entity_id(
            entity_domain + ".{}", 
            self.unique_id, 
            hass=hass
        )

        export_name_suffix = " Export" if self._is_export else ""
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"electricity_{self._serial_number}_{self._mpan}")},
            name=f"Electricity Meter{export_name_suffix}",
            connections=set(),
            manufacturer=self._meter["manufacturer"],
            model=self._meter["model"],
            sw_version=self._meter["firmware"]
        )
```

### 3.2 Energy Consumption Sensor (TOTAL state_class)

```python
# electricity/previous_accumulative_consumption.py
from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy

class OctopusEnergyPreviousAccumulativeElectricityConsumption(
    CoordinatorEntity, 
    OctopusEnergyElectricitySensor, 
    RestoreSensor
):
    """Sensor for displaying the previous days accumulative electricity reading."""

    def __init__(self, hass, client, coordinator, account_id, meter, point, peak_type=None):
        CoordinatorEntity.__init__(self, coordinator)
        self._state = None
        self._last_reset = None
        OctopusEnergyElectricitySensor.__init__(self, hass, meter, point)

    @property
    def device_class(self):
        """The type of sensor"""
        return SensorDeviceClass.ENERGY

    @property
    def state_class(self):
        """The state class of sensor"""
        return SensorStateClass.TOTAL  # For consumption with last_reset

    @property
    def native_unit_of_measurement(self):
        """The unit of measurement of sensor"""
        return UnitOfEnergy.KILO_WATT_HOUR

    @property
    def last_reset(self):
        """Return the time when the sensor was last reset, if any."""
        return self._last_reset

    @property
    def native_value(self):
        return self._state
```

### 3.3 Total Consumption Sensor (TOTAL_INCREASING state_class)

**For Energy Dashboard integration:**

```python
# gas/current_total_consumption_kwh.py
class OctopusEnergyCurrentTotalGasConsumptionKwh(
    CoordinatorEntity, 
    OctopusEnergyGasSensor, 
    RestoreSensor
):
    """Sensor for displaying the current total gas consumption in kwh."""

    @property
    def device_class(self):
        """The type of sensor"""
        return SensorDeviceClass.ENERGY

    @property
    def state_class(self):
        """The state class of sensor"""
        return SensorStateClass.TOTAL_INCREASING  # Key for Energy Dashboard!

    @property
    def native_unit_of_measurement(self):
        """The unit of measurement of sensor"""
        return UnitOfEnergy.KILO_WATT_HOUR

    @property
    def native_value(self):
        return self._state
```

### 3.4 State Class Selection Guide

| State Class | Use Case | Energy Dashboard |
|-------------|----------|------------------|
| `SensorStateClass.MEASUREMENT` | Real-time readings (current rate, demand) | No |
| `SensorStateClass.TOTAL` | Daily/period consumption with reset | Yes (with `last_reset`) |
| `SensorStateClass.TOTAL_INCREASING` | Cumulative total that only increases | Yes (no `last_reset` needed) |

---

## 4. Config Flow Pattern

### 4.1 Main Config Flow Class

```python
# config_flow.py
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.helpers import selector
from homeassistant.data_entry_flow import section

class OctopusEnergyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow."""
    VERSION = CONFIG_VERSION

    async def async_step_user(self, user_input):
        """Handle the initial step."""
        return await self.async_step_account(user_input)

    async def async_step_account(self, user_input):
        """Setup the initial account based on the provided user input"""
        errors = await async_validate_main_config(user_input) if user_input else {}

        if len(errors) < 1 and user_input is not None:
            user_input[CONFIG_KIND] = CONFIG_KIND_ACCOUNT
            return self.async_create_entry(
                title=user_input[CONFIG_ACCOUNT_ID],
                data=user_input
            )

        return self.async_show_form(
            step_id="account",
            data_schema=self.add_suggested_values_to_schema(
                self.__setup_account_schema__(),
                user_input or {}
            ),
            description_placeholders=description_placeholders,
            errors=errors
        )

    def __setup_account_schema__(self, include_account_id=True):
        """Define the account configuration schema."""
        schema = {
            vol.Required(CONFIG_ACCOUNT_ID): str,
            vol.Required(CONFIG_MAIN_API_KEY): str,
            vol.Required(CONFIG_MAIN_CALORIFIC_VALUE, default=DEFAULT_CALORIFIC_VALUE): cv.positive_float,
            # Nested sections using 'section'
            vol.Required(CONFIG_MAIN_HOME_MINI_SETTINGS): section(
                vol.Schema({
                    vol.Required(CONFIG_MAIN_SUPPORTS_LIVE_CONSUMPTION): bool,
                    vol.Required(CONFIG_MAIN_LIVE_ELECTRICITY_CONSUMPTION_REFRESH_IN_MINUTES, 
                                default=CONFIG_DEFAULT_LIVE_ELECTRICITY_CONSUMPTION_REFRESH_IN_MINUTES): cv.positive_int,
                }),
                {"collapsed": True},
            ),
        }
        return vol.Schema(schema)
```

### 4.2 Reconfigure Pattern

```python
async def async_step_reconfigure_account(self, user_input):
    """Handle reconfiguration."""
    config = dict(self._get_reconfigure_entry().data)
    
    if user_input is not None:
        config.update(user_input)
    
    errors = await async_validate_main_config(config, [])
    
    if len(errors) < 1 and user_input is not None:
        return self.async_update_reload_and_abort(
            self._get_reconfigure_entry(),
            data_updates=config,
        )
    
    return self.async_show_form(
        step_id="reconfigure_account",
        data_schema=self.add_suggested_values_to_schema(
            self.__setup_account_schema__(False),
            config
        ),
        errors=errors
    )
```

### 4.3 Discovery Pattern

```python
async def async_step_integration_discovery(self, discovery_info: DiscoveryInfoType):
    """Handle integration discovery."""
    if discovery_info[CONFIG_KIND] == CONFIG_KIND_COST_TRACKER:
        self._target_entity_id = discovery_info[CONFIG_COST_TRACKER_TARGET_ENTITY_ID]
        
        unique_id = f"octopus_energy_ct_{self._account_id}_{self._target_entity_id}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
        
        return await self.async_step_cost_tracker(None)
    
    return self.async_abort(reason="unexpected_discovery")
```

---

## 5. Entry Point Pattern (__init__.py)

### 5.1 Platform Setup

```python
# __init__.py
ACCOUNT_PLATFORMS = ["sensor", "binary_sensor", "number", "switch", "text", "time", "event", "select", "climate", "water_heater", "calendar"]

async def async_setup_entry(hass, entry):
    """This is called from the config flow."""
    hass.data.setdefault(DOMAIN, {})
    config = dict(entry.data)
    account_id = config[CONFIG_ACCOUNT_ID]
    hass.data[DOMAIN].setdefault(account_id, {})

    if config[CONFIG_KIND] == CONFIG_KIND_ACCOUNT:
        await async_setup_dependencies(hass, config)
        await hass.config_entries.async_forward_entry_setups(entry, ACCOUNT_PLATFORMS)
        
        # Cleanup on HA stop
        async def async_close_connection(_):
            await _async_close_client(hass, account_id)
        
        entry.async_on_unload(
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_close_connection)
        )
    
    entry.async_on_unload(entry.add_update_listener(options_update_listener))
    return True
```

### 5.2 Dependency Setup Pattern

```python
async def async_setup_dependencies(hass, config):
    """Setup the coordinator and api client which will be shared by various entities"""
    account_id = config[CONFIG_ACCOUNT_ID]
    
    # Create API client
    client = OctopusEnergyApiClient(config[CONFIG_MAIN_API_KEY])
    hass.data[DOMAIN][account_id][DATA_CLIENT] = client
    
    # Fetch account info with error handling
    try:
        account_info = await client.async_get_account(account_id)
        if account_info is None:
            raise ConfigEntryNotReady("Failed to retrieve account information")
    except AuthenticationException:
        ir.async_create_issue(
            hass,
            DOMAIN,
            safe_repair_key(REPAIR_INVALID_API_KEY, account_id),
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key="invalid_api_key",
        )
        raise ConfigEntryNotReady("Failed to retrieve account information")
    
    # Store account data
    hass.data[DOMAIN][account_id][DATA_ACCOUNT] = AccountCoordinatorResult(
        utcnow(), 1, account_info
    )
    
    # Setup coordinators for each meter
    for point in account_info["electricity_meter_points"]:
        electricity_tariff = get_active_tariff(now(), point["agreements"])
        if electricity_tariff is not None:
            for meter in point["meters"]:
                await async_setup_electricity_rates_coordinator(
                    hass, account_id, point["mpan"], meter["serial_number"], ...
                )
```

---

## 6. Manifest.json Pattern

```json
{
  "domain": "octopus_energy",
  "name": "Octopus Energy",
  "codeowners": ["@bottlecapdave"],
  "config_flow": true,
  "dependencies": ["repairs", "recorder"],
  "documentation": "https://bottlecapdave.github.io/HomeAssistant-OctopusEnergy",
  "iot_class": "cloud_polling",
  "issue_tracker": "https://github.com/BottlecapDave/HomeAssistant-OctopusEnergy/issues",
  "requirements": ["pydantic"],
  "version": "18.0.0"
}
```

---

## 7. Key Takeaways for OEJP Integration

### 7.1 Energy Dashboard Integration

For Energy Dashboard compatibility, use these patterns:

1. **Consumption sensors**: `SensorStateClass.TOTAL_INCREASING` with `SensorDeviceClass.ENERGY`
2. **Unit**: `UnitOfEnergy.KILO_WATT_HOUR`
3. **No `last_reset` property needed** for `TOTAL_INCREASING`

### 7.2 Coordinator Best Practices

1. Use `DataUpdateCoordinator` with `always_update=True` for real-time data
2. Implement retry logic with exponential backoff
3. Cache data during API failures with fallback to previous result
4. Use separate coordinators for different data types (rates, consumption, account)

### 7.3 Entity Organization

1. Create base sensor class with common device info
2. Use `CoordinatorEntity` mixin for coordinator-based updates
3. Use `RestoreSensor` for state persistence across restarts
4. Group entities by device using `DeviceInfo`

### 7.4 Error Handling

1. Use Home Assistant's issue registry (`ir.async_create_issue`) for user-facing errors
2. Raise `ConfigEntryNotReady` during setup failures
3. Implement graceful degradation with cached data

---

## 8. OEJP-Specific Recommendations

For the Octopus Energy Japan integration:

1. **API Client**: Create similar `api_client/` module for Tokyo Power API
2. **Coordinators**: 
   - `account_coordinator.py` - Account info
   - `usage_coordinator.py` - Daily/monthly usage
   - `rates_coordinator.py` - Rate information
3. **Sensors**:
   - Current usage (MEASUREMENT)
   - Cumulative consumption (TOTAL_INCREASING)
   - Current rate (MEASUREMENT)
   - Monthly cost (TOTAL_INCREASING with monetary device class)

---

*Document generated from analysis of BottlecapDave/HomeAssistant-OctopusEnergy repository*
