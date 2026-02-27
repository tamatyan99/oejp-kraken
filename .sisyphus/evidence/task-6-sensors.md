# Task 6: MVP Sensors Implementation

**Task**: Wave 3, Task 6 - OEJP MVP Sensors  
**Date**: 2026-02-27  
**Status**: COMPLETED

---

## 1. Implementation Summary

Created `custom_components/oejp_kraken/sensor.py` with 3 MVP sensors:

| Sensor | Class | device_class | state_class | Unit | Energy Dashboard |
|--------|-------|--------------|-------------|------|------------------|
| Current Power | OEJPCurrentPowerSensor | power | measurement | W | No |
| Today Consumption | OEJPTodayConsumptionSensor | energy | total_increasing | kWh | Yes |
| Current Rate | OEJPCurrentRateSensor | monetary | measurement | JPY/kWh | No |

---

## 2. Code Structure

### 2.1 Entry Point

```python
async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    account_info = hass.data[DOMAIN][entry.entry_id].get("account_info", {})
    
    entities = [
        OEJPCurrentPowerSensor(coordinator, entry, account_info),
        OEJPTodayConsumptionSensor(coordinator, entry, account_info),
        OEJPCurrentRateSensor(coordinator, entry, account_info),
    ]
    async_add_entities(entities)
```

### 2.2 Base Sensor Class

- `OEJPBaseSensor(CoordinatorEntity, SensorEntity)`
- Provides device info linking via `DeviceInfo`
- Common unique ID generation pattern: `{DOMAIN}_{account_id}_{sensor_type}`
- Shared availability checking

### 2.3 Sensor Implementations

#### OEJPCurrentPowerSensor
- Displays real-time power demand (W)
- Converts kW to W if needed (`* 1000`)
- Icon: `mdi:flash`

#### OEJPTodayConsumptionSensor
- Displays daily cumulative consumption (kWh)
- `TOTAL_INCREASING` state class for Energy Dashboard
- Fallback to total_consumption if daily unavailable
- Icon: `mdi:lightning-bolt`

#### OEJPCurrentRateSensor
- Displays current electricity rate (JPY/kWh)
- Monetary device class for currency formatting
- Includes rate period info in attributes
- Icon: `mdi:currency-jpy`

---

## 3. Key Design Decisions

### 3.1 State Class Selection

| Use Case | State Class | Rationale |
|----------|-------------|-----------|
| Real-time power | MEASUREMENT | Instantaneous reading |
| Daily consumption | TOTAL_INCREASING | Cumulative, only increases |
| Rate | MEASUREMENT | Current rate at point in time |

### 3.2 Device Info Pattern

```python
self._attr_device_info = DeviceInfo(
    identifiers={(DOMAIN, f"electricity_{serial_number}_{mpan}")},
    name="OEJP Electricity Meter",
    manufacturer="OEJP Kraken",
    model="Smart Meter",
)
```

Groups all sensors under single device in HA UI.

### 3.3 Data Access Pattern

Sensors access coordinator data via:
- `self.coordinator.data.get("current_usage")` - Power
- `self.coordinator.data.get("daily_consumption")` - Consumption
- `self.coordinator.data.get("current_rate")` - Rate

---

## 4. Verification

### 4.1 Syntax Check
```bash
python3 -m py_compile sensor.py
# Result: Syntax OK
```

### 4.2 Import Check
All imports are from standard Home Assistant packages:
- `homeassistant.components.sensor` - SensorEntity, SensorDeviceClass, SensorStateClass
- `homeassistant.const` - UnitOfPower, UnitOfEnergy
- `homeassistant.helpers.update_coordinator` - CoordinatorEntity

---

## 5. Energy Dashboard Integration

The `OEJPTodayConsumptionSensor` is configured for Energy Dashboard:

- `device_class = SensorDeviceClass.ENERGY`
- `state_class = SensorStateClass.TOTAL_INCREASING`
- `native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR`

No `last_reset` property needed for `TOTAL_INCREASING` state class.

---

## 6. Files Modified/Created

| File | Action | Lines |
|------|--------|-------|
| `custom_components/oejp_kraken/sensor.py` | Created | 353 |

---

## 7. Next Steps

1. Update `__init__.py` to properly initialize coordinator and account_info
2. Add translations to `translations/ja.json` for sensor names
3. Test with mock coordinator data
4. Implement remaining 12 sensors in future waves

---

*Evidence generated for Task 6 completion*
