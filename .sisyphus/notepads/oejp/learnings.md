
## 2026-02-27: Task 2 - Energy Integration Pattern Research

### Key Patterns from Octopus Energy Integration

1. **Coordinator Pattern**
   - Use `DataUpdateCoordinator` with `always_update=True` for real-time data
   - Implement `BaseCoordinatorResult` class with retry logic and `next_refresh` calculation
   - Separate coordinators per data type (account, rates, consumption)
   - Use `MultiCoordinatorEntity` for entities needing multiple data sources

2. **Sensor Entity Patterns**
   - Base sensor class with `DeviceInfo` for device grouping
   - `SensorStateClass.TOTAL_INCREASING` for Energy Dashboard cumulative sensors
   - `SensorStateClass.TOTAL` with `last_reset` property for daily/period totals
   - `SensorStateClass.MEASUREMENT` for real-time readings (current rate, demand)

3. **Energy Dashboard Integration**
   - `SensorDeviceClass.ENERGY` with `UnitOfEnergy.KILO_WATT_HOUR`
   - `SensorDeviceClass.MONETARY` with currency unit for cost sensors
   - No `last_reset` needed for `TOTAL_INCREASING` state class

4. **Config Flow**
   - Use `section()` for collapsible nested configuration
   - Implement `async_step_reconfigure_*` for settings changes
   - Use `ConfigEntryNotReady` for setup failures
   - Use issue registry for user-facing errors

5. **Error Handling**
   - Graceful degradation with cached data on API failures
   - Retry logic with exponential backoff
   - Issue registry for persistent error notifications

### File Structure Reference
```
custom_components/octopus_energy/
├── __init__.py          # Entry point, setup
├── config_flow.py       # UI config
├── sensor.py            # Platform setup
├── coordinators/        # DataUpdateCoordinator implementations
├── electricity/         # Electricity sensor entities
├── gas/                 # Gas sensor entities
├── api_client/          # External API client
└── const.py             # Constants
```
