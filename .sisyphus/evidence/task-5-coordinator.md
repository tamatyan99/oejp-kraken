# Task 5: DataUpdateCoordinator Implementation

**Task**: Wave 2, Task 5 - OEJP Data Update Coordinator  
**Date**: 2026-02-27  
**Status**: ✅ Complete

---

## 1. Implementation Summary

Created `custom_components/oejp_kraken/coordinator.py` with the following components:

### 1.1 OEJPDataUpdateCoordinator Class

Extends `DataUpdateCoordinator` from Home Assistant core.

```python
class OEJPDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage data updates from OEJP Kraken API."""
```

**Constructor Parameters:**
- `hass`: Home Assistant instance
- `graphql_client`: GraphQL client for API communication (from Task 4)
- `update_interval`: Update interval in seconds (default: 300 = 5 minutes)

**Features:**
- `always_update=True`: Always update to capture latest data
- Automatic name generation: `{DOMAIN}_coordinator`

### 1.2 Token Management

**Configuration:**
```python
TOKEN_EXPIRY_DURATION = timedelta(minutes=60)  # Token valid for 60 minutes
TOKEN_REFRESH_THRESHOLD = timedelta(minutes=5)  # Refresh 5 min before expiry
```

**Implementation:**
- `token_needs_refresh` property: Checks if token is within threshold
- `_async_refresh_token()`: Calls graphql_client.async_refresh_token()
- `_async_ensure_valid_token()`: Ensures valid token before API calls
- Token timestamp tracked in `_token_issued_at`

**Refresh Flow:**
```
1. Check token_needs_refresh property
2. If true, call _async_refresh_token()
3. Update _token_issued_at timestamp
4. Continue with data fetch
```

### 1.3 Exponential Backoff Strategy

**Configuration:**
```python
BACKOFF_BASE_SECONDS = 60      # 1 minute initial backoff
BACKOFF_MAX_SECONDS = 900      # 15 minutes maximum backoff
BACKOFF_MULTIPLIER = 2         # Double each time
```

**Pattern:** 1m → 2m → 4m → 8m → 15m (capped at max)

**Implementation:**
- `_consecutive_errors`: Counter for consecutive failures
- `_current_backoff`: Current backoff duration
- `_calculate_backoff()`: Calculates exponential backoff
- `_reset_backoff()`: Resets counter on success
- `_increment_backoff()`: Increments after failure
- `get_next_update_interval()`: Returns backoff-adjusted interval

### 1.4 Data Update Flow

```python
async def _async_update_data(self) -> dict[str, Any]:
    """Fetch data from OEJP Kraken API."""
    # 1. Ensure valid token
    await self._async_ensure_valid_token()
    
    # 2. Fetch electricity usage data via GraphQL query
    usage_data = await self.graphql_client.execute_query(
        ELECTRICITY_USAGE_QUERY
    )
    
    # 3. Process and format data
    formatted_data = self._format_usage_data(usage_data)
    
    # 4. Reset backoff on success
    self._reset_backoff()
    
    return formatted_data
```

### 1.5 Data Formatting

`_format_usage_data()` extracts and structures:
- `current_usage`: Real-time demand (kW)
- `total_consumption`: Cumulative consumption (kWh)
- `daily_consumption`: Daily breakdown
- `monthly_consumption`: Monthly breakdown
- `current_rate`: Current electricity rate
- `account`: Account information
- `raw_data`: Original API response (for debugging)

### 1.6 OEJPCoordinatorResult Helper

Container class for coordinator data with metadata:
- `data`: The fetched data
- `last_retrieved`: Timestamp of last successful fetch
- `request_attempts`: Failed attempt counter
- `last_error`: Last exception encountered
- `next_refresh`: Calculated next refresh time
- `is_stale` property: Whether data needs refresh
- `has_data` property: Whether data is valid

---

## 2. Rate Limiting Awareness

The coordinator is designed to work with the rate limit of 50,000 points/hour:

1. Default update interval of 5 minutes = 12 updates/hour
2. Each update is designed to be efficient (single GraphQL query)
3. Backoff mechanism reduces API calls during failures
4. `always_update=True` ensures we don't miss data while minimizing redundant calls

---

## 3. Error Handling

### 3.1 Exception Wrapping

All exceptions are wrapped in `UpdateFailed`:
```python
except Exception as err:
    self._increment_backoff()
    raise UpdateFailed(f"Error fetching data: {err}") from err
```

### 3.2 Logging

- Debug: Token refresh, data fetch operations
- Info: Token refresh needed, backoff usage
- Warning: Consecutive errors count, backoff duration
- Error: Token refresh failures, data fetch errors

### 3.3 Graceful Degradation

- Previous data remains available during failures
- Sensors can check `coordinator.last_update_success`
- Backoff prevents API spam during outages

---

## 4. Integration Points

The coordinator uses the `KrakenGraphQLClient` from Task 4:
```python
class KrakenGraphQLClient:
    async def refresh_token(self) -> dict[str, str]: ...  # Returns {"token": ..., "refreshToken": ...}
    async def execute_query(self, query: str, variables: dict = None) -> dict: ...
    
    @property
    def is_authenticated(self) -> bool: ...
```

```python
from .coordinator import OEJPDataUpdateCoordinator
from .graphql_client import KrakenGraphQLClient

async def async_setup_entry(hass, entry):
    client = KrakenGraphQLClient(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD]
    )
    await client.authenticate()
    coordinator = OEJPDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator
```

### 4.3 Usage in Sensors

```python
from homeassistant.helpers.update_coordinator import CoordinatorEntity

class OEJPElectricitySensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
    
    @property
    def native_value(self):
        return self.coordinator.data.get("current_usage")
```

---

## 5. File Statistics

- **File**: `custom_components/oejp_kraken/coordinator.py`
- **Lines**: 345
- **Classes**: 2 (`OEJPDataUpdateCoordinator`, `OEJPCoordinatorResult`)
- **Dependencies**: 
  - `homeassistant.helpers.update_coordinator`
  - `homeassistant.util.dt`
  - `.const` (DOMAIN, DEFAULT_UPDATE_INTERVAL)
  - `.graphql_client` (TYPE_CHECKING only)

---

## 6. Checklist Verification

- [x] `coordinator.py` file created
- [x] `OEJPDataUpdateCoordinator` class implemented
- [x] `_async_update_data()` method implemented
- [x] Token auto-refresh functionality (60-minute expiry with 5-minute threshold)
- [x] Rate limiting awareness (50,000 points/hour)
- [x] Error backoff strategy (exponential: 1m→2m→4m→8m→15m max)
- [x] Evidence file created

---

## 7. Next Steps

Task 6 will implement:
- Sensor entities using this coordinator
- Energy Dashboard integration
- Device registry setup
