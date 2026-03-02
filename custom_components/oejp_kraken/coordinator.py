"""Data update coordinator for OEJP Kraken integration.

This module provides the coordinator class that manages periodic data
updates from the OEJP Kraken API, including token refresh, error handling,
and exponential backoff.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Final

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN
from .graphql_client import KrakenAuthenticationError, KrakenError, KrakenRateLimitError

if TYPE_CHECKING:
    from .graphql_client import KrakenGraphQLClient

_LOGGER = logging.getLogger(__name__)

# Token refresh threshold (refresh 5 minutes before expiry)
TOKEN_REFRESH_THRESHOLD: Final[timedelta] = timedelta(minutes=5)

# Token expiry duration (assumed 60 minutes based on typical JWT)
TOKEN_EXPIRY_DURATION: Final[timedelta] = timedelta(minutes=60)

# Exponential backoff configuration
BACKOFF_BASE_SECONDS: Final[int] = 60  # 1 minute
BACKOFF_MAX_SECONDS: Final[int] = 900  # 15 minutes (max backoff)
BACKOFF_MULTIPLIER: Final[int] = 2

# Import queries
from .queries import VIEWER_ACCOUNTS_QUERY, HALF_HOURLY_READINGS_QUERY


class OEJPDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage data updates from OEJP Kraken API.

    This coordinator handles:
    - Periodic data fetching from the API
    - Automatic token refresh before expiry
    - Exponential backoff on consecutive errors
    - Rate limiting awareness

    Attributes:
        graphql_client: The GraphQL client for API communication.

    Example:
        coordinator = OEJPDataUpdateCoordinator(hass, client, update_interval=300)
        await coordinator.async_config_entry_first_refresh()

    """

    def __init__(
        self,
        hass: HomeAssistant,
        graphql_client: KrakenGraphQLClient,
        *,
        update_interval: int = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            graphql_client: GraphQL client for API communication.
            update_interval: Update interval in seconds (default: 300 = 5 minutes).

        """
        self.graphql_client = graphql_client
        self._token_issued_at: datetime | None = None
        self._consecutive_errors: int = 0
        self._current_backoff: int = 0

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(seconds=update_interval),
            always_update=True,  # Always update to capture latest data
        )

    @property
    def token_needs_refresh(self) -> bool:
        """Check if token needs to be refreshed.

        Returns True if token is close to expiry (within threshold)
        or if no token has been issued yet.

        Returns:
            True if token refresh is needed.

        """
        if self._token_issued_at is None:
            return True

        now = dt_util.utcnow()
        elapsed = now - self._token_issued_at
        return elapsed >= (TOKEN_EXPIRY_DURATION - TOKEN_REFRESH_THRESHOLD)

    @property
    def current_backoff_seconds(self) -> int:
        """Get current backoff duration in seconds.

        Returns:
            Current backoff duration, or 0 if not in backoff mode.

        """
        return self._current_backoff

    @property
    def is_in_backoff(self) -> bool:
        """Check if coordinator is in backoff mode.

        Returns:
            True if currently in exponential backoff mode.

        """
        return self._current_backoff > 0

    @property
    def consecutive_error_count(self) -> int:
        """Get the number of consecutive errors.

        Returns:
            Number of consecutive failed update attempts.

        """
        return self._consecutive_errors

    def _calculate_backoff(self) -> int:
        """Calculate exponential backoff duration.

        Pattern: 1m -> 2m -> 4m -> 8m -> 15m (max)

        Returns:
            Backoff duration in seconds.

        """
        backoff = BACKOFF_BASE_SECONDS * (BACKOFF_MULTIPLIER**self._consecutive_errors)
        return min(backoff, BACKOFF_MAX_SECONDS)

    def _reset_backoff(self) -> None:
        """Reset backoff counter after successful update."""
        self._consecutive_errors = 0
        self._current_backoff = 0

    def _increment_backoff(self) -> None:
        """Increment backoff after failed update."""
        self._consecutive_errors += 1
        self._current_backoff = self._calculate_backoff()
        _LOGGER.warning(
            "Consecutive errors: %d, next backoff: %d seconds",
            self._consecutive_errors,
            self._current_backoff,
        )

    async def _async_refresh_token(self) -> bool:
        """Refresh the authentication token.

        Returns:
            True if token was refreshed successfully.

        Raises:
            UpdateFailed: If token refresh fails.

        """
        _LOGGER.debug("Refreshing authentication token")
        try:
            result = await self.graphql_client.refresh_token()
            if result and result.get("token"):
                self._token_issued_at = dt_util.utcnow()
                _LOGGER.debug("Token refreshed successfully")
                return True
            raise UpdateFailed("Token refresh returned no token")
        except UpdateFailed:
            # Re-raise UpdateFailed as-is
            raise
        except KrakenAuthenticationError as err:
            _LOGGER.error("Authentication error during token refresh: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except KrakenError as err:
            _LOGGER.error("API error during token refresh: %s", err)
            raise UpdateFailed(f"API error: {err}") from err

    async def _async_ensure_valid_token(self) -> None:
        """Ensure we have a valid token, refreshing if necessary.

        Raises:
            UpdateFailed: If token cannot be obtained.

        """
        if self.token_needs_refresh:
            _LOGGER.info("Token needs refresh (issued at: %s)", self._token_issued_at)
            await self._async_refresh_token()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from OEJP Kraken API.

        This method:
        1. Checks and refreshes token if needed
        2. Fetches account number and electricity usage data
        3. Handles errors with exponential backoff
        4. Returns formatted data for sensors

        Returns:
            Dictionary containing electricity usage data.

        Raises:
            UpdateFailed: If data cannot be retrieved.

        """
        try:
            # Step 1: Ensure valid token
            await self._async_ensure_valid_token()

            # Step 2a: Fetch account number
            _LOGGER.debug("Fetching account number")
            accounts_data = await self.graphql_client.execute_query(
                VIEWER_ACCOUNTS_QUERY
            )
            
            accounts = accounts_data.get("viewer", {}).get("accounts", [])
            if not accounts:
                raise UpdateFailed("No accounts found")
            
            account_number = accounts[0].get("number")
            if not account_number:
                raise UpdateFailed("Account number not found")
            
            _LOGGER.debug("Found account number: %s", account_number)

            # Step 2b: Fetch half-hourly readings
            _LOGGER.debug("Fetching electricity usage data")
            from_datetime = (dt_util.utcnow() - timedelta(hours=1)).isoformat()
            to_datetime = dt_util.utcnow().isoformat()
            
            usage_data = await self.graphql_client.execute_query(
                HALF_HOURLY_READINGS_QUERY,
                variables={
                    "accountNumber": account_number,
                    "fromDatetime": from_datetime,
                    "toDatetime": to_datetime,
                }
            )

            # Step 3: Process and format data for sensors
            formatted_data = self._format_usage_data(usage_data, account_number)

            # Step 4: Reset backoff on success
            self._reset_backoff()

            _LOGGER.debug("Successfully updated data")
            return formatted_data


        except UpdateFailed:
            # Re-raise UpdateFailed as-is
            self._increment_backoff()
            raise

        except KrakenRateLimitError as err:
            # Handle rate limiting specially
            self._increment_backoff()
            retry_after = err.retry_after or self._current_backoff
            _LOGGER.warning("Rate limited, retry after %d seconds", retry_after)
            raise UpdateFailed(f"Rate limited: {err}") from err
        except KrakenAuthenticationError as err:
            # Auth errors need re-authentication
            self._increment_backoff()
            _LOGGER.error("Authentication error: %s", err)
            raise UpdateFailed(f"Authentication required: {err}") from err
        except KrakenError as err:
            # Other API errors
            self._increment_backoff()
            _LOGGER.error("API error: %s", err)
            raise UpdateFailed(f"API error: {err}") from err

    def _format_usage_data(self, raw_data: dict[str, Any], account_number: str) -> dict[str, Any]:
        """Format raw API data for sensor consumption.

        Args:
            raw_data: Raw data from GraphQL API.
            account_number: The account number.

        Returns:
            Formatted dictionary for sensors.

        """
        if not raw_data:
            return self._create_empty_response()

        formatted: dict[str, Any] = {
            "last_updated": dt_util.utcnow().isoformat(),
            "account_number": account_number,
            "raw_data": raw_data,  # Keep raw data for debugging
        }

        try:
            account = raw_data.get("account", {})
            properties = account.get("properties", [])
            if properties:
                property_data = properties[0]
                supply_points = property_data.get("electricitySupplyPoints", [])
                if supply_points:
                    readings = supply_points[0].get("halfHourlyReadings", [])
                    if readings:
                        # Get the most recent reading
                        latest_reading = readings[-1]
                        formatted["current_usage"] = float(latest_reading.get("value", 0))
                        formatted["last_reading_time"] = latest_reading.get("endAt")
                        
                        # Calculate total consumption from all readings
                        total = sum(float(r.get("value", 0)) for r in readings)
                        formatted["total_consumption"] = total
        except (KeyError, IndexError, TypeError, ValueError) as err:
            _LOGGER.debug("Could not extract usage data: %s", err)

        return formatted
    def _create_empty_response(self) -> dict[str, Any]:
        """Create an empty response with default values.

        Returns:
            Dictionary with None values and last_updated timestamp.

        """
        return {
            "current_usage": None,
            "total_consumption": None,
            "last_updated": dt_util.utcnow().isoformat(),
        }

    async def async_config_entry_first_refresh(self) -> None:
        """Handle first refresh with token initialization.

        Overrides parent to ensure token is initialized before first data fetch.

        """
        # Initialize token timestamp if client already has a valid token
        if self.graphql_client.is_authenticated:
            self._token_issued_at = dt_util.utcnow()

        await super().async_config_entry_first_refresh()

    def get_next_update_interval(self) -> timedelta:
        """Get the next update interval, accounting for backoff.

        If we're in backoff mode, return the backoff duration instead of
        the regular update interval.

        Returns:
            Time until next update.

        """
        if self._current_backoff > 0:
            _LOGGER.info(
                "Using backoff interval: %d seconds (normal: %d)",
                self._current_backoff,
                self.update_interval.total_seconds(),
            )
            return timedelta(seconds=self._current_backoff)
        return self.update_interval
