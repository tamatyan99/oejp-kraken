"""Data update coordinator for OEJP Kraken integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN

if TYPE_CHECKING:
    from .graphql_client import KrakenGraphQLClient

_LOGGER = logging.getLogger(__name__)

# Token refresh threshold (refresh 5 minutes before expiry)
TOKEN_REFRESH_THRESHOLD = timedelta(minutes=5)

# Token expiry duration
TOKEN_EXPIRY_DURATION = timedelta(minutes=60)

# Exponential backoff configuration
BACKOFF_BASE_SECONDS = 60  # 1 minute
BACKOFF_MAX_SECONDS = 900  # 15 minutes (max backoff)
BACKOFF_MULTIPLIER = 2

# GraphQL query for electricity usage
ELECTRICITY_USAGE_QUERY = """
query ElectricityUsage {
    viewer {
        accounts {
            electricityAgreements {
                validFrom
                validTo
                meterPoint {
                    mpan
                }
                meter {
                    serialNumber
                }
            }
        }
    }
}
"""


class OEJPDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage data updates from OEJP Kraken API.

    Handles:
    - Periodic data fetching
    - Automatic token refresh before expiry
    - Exponential backoff on errors
    - Rate limiting awareness
    """

    def __init__(
        self,
        hass: HomeAssistant,
        graphql_client: KrakenGraphQLClient,
        update_interval: int = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            graphql_client: GraphQL client for API communication
            update_interval: Update interval in seconds (default: 300 = 5 minutes)

        """
        self.graphql_client = graphql_client
        self._token_issued_at: datetime | None = None
        self._consecutive_errors = 0
        self._current_backoff = 0

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

        Returns True if token is close to expiry (within threshold).

        """
        if self._token_issued_at is None:
            return True

        now = dt_util.utcnow()
        elapsed = now - self._token_issued_at
        return elapsed >= (TOKEN_EXPIRY_DURATION - TOKEN_REFRESH_THRESHOLD)

    @property
    def current_backoff_seconds(self) -> int:
        """Get current backoff duration in seconds."""
        return self._current_backoff

    def _calculate_backoff(self) -> int:
        """Calculate exponential backoff duration.

        Pattern: 1m -> 2m -> 4m -> 8m -> 15m (max)

        Returns:
            Backoff duration in seconds

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
            True if token was refreshed successfully

        Raises:
            UpdateFailed: If token refresh fails

        """
        _LOGGER.debug("Refreshing authentication token")
        try:
            result = await self.graphql_client.refresh_token()
            if result and result.get("token"):
                self._token_issued_at = dt_util.utcnow()
                _LOGGER.debug("Token refreshed successfully")
                return True
            raise UpdateFailed("Token refresh returned no token")
        except Exception as err:
            _LOGGER.error("Failed to refresh token: %s", err)
            raise UpdateFailed(f"Token refresh failed: {err}") from err

    async def _async_ensure_valid_token(self) -> None:
        """Ensure we have a valid token, refreshing if necessary.

        Raises:
            UpdateFailed: If token cannot be obtained

        """
        if self.token_needs_refresh:
            _LOGGER.info("Token needs refresh (issued at: %s)", self._token_issued_at)
            await self._async_refresh_token()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from OEJP Kraken API.

        This method:
        1. Checks and refreshes token if needed
        2. Fetches electricity usage data
        3. Handles errors with exponential backoff
        4. Returns formatted data for sensors

        Returns:
            Dictionary containing electricity usage data

        Raises:
            UpdateFailed: If data cannot be retrieved

        """
        try:
            # Step 1: Ensure valid token
            await self._async_ensure_valid_token()

            # Step 2: Fetch electricity usage data
            _LOGGER.debug("Fetching electricity usage data")

            usage_data = await self.graphql_client.execute_query(
                ELECTRICITY_USAGE_QUERY
            )

            # Step 3: Process and format data for sensors
            formatted_data = self._format_usage_data(usage_data)

            # Step 4: Reset backoff on success
            self._reset_backoff()

            _LOGGER.debug("Successfully updated data")
            return formatted_data

        except UpdateFailed:
            # Re-raise UpdateFailed as-is
            self._increment_backoff()
            raise

        except Exception as err:
            # Wrap other exceptions in UpdateFailed
            self._increment_backoff()
            _LOGGER.error("Error fetching data: %s", err)
            raise UpdateFailed(f"Error fetching data: {err}") from err

    def _format_usage_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Format raw API data for sensor consumption.

        Args:
            raw_data: Raw data from GraphQL API

        Returns:
            Formatted dictionary for sensors

        """
        if not raw_data:
            return {
                "current_usage": None,
                "total_consumption": None,
                "last_updated": dt_util.utcnow().isoformat(),
            }

        # Extract relevant fields from the API response
        # Structure depends on actual GraphQL schema
        formatted = {
            "last_updated": dt_util.utcnow().isoformat(),
            "raw_data": raw_data,  # Keep raw data for debugging
        }

        # Current usage (real-time demand in kW)
        if "current_usage" in raw_data:
            formatted["current_usage"] = raw_data["current_usage"]

        # Total consumption (cumulative kWh)
        if "total_consumption" in raw_data:
            formatted["total_consumption"] = raw_data["total_consumption"]

        # Daily consumption data
        if "daily_consumption" in raw_data:
            formatted["daily_consumption"] = raw_data["daily_consumption"]

        # Monthly consumption data
        if "monthly_consumption" in raw_data:
            formatted["monthly_consumption"] = raw_data["monthly_consumption"]

        # Rate information
        if "current_rate" in raw_data:
            formatted["current_rate"] = raw_data["current_rate"]

        # Account information
        if "account" in raw_data:
            formatted["account"] = raw_data["account"]

        return formatted

    async def async_config_entry_first_refresh(self) -> None:
        """Handle first refresh with token initialization.

        Overrides parent to ensure token is initialized before first data fetch.

        """
        # Initialize token timestamp if client already has a valid token
        if (
            hasattr(self.graphql_client, "is_authenticated")
            and self.graphql_client.is_authenticated
        ):
            self._token_issued_at = dt_util.utcnow()

        await super().async_config_entry_first_refresh()

    def get_next_update_interval(self) -> timedelta:
        """Get the next update interval, accounting for backoff.

        If we're in backoff mode, return the backoff duration instead of
        the regular update interval.

        Returns:
            Time until next update

        """
        if self._current_backoff > 0:
            _LOGGER.info(
                "Using backoff interval: %d seconds (normal: %d)",
                self._current_backoff,
                self.update_interval.total_seconds(),
            )
            return timedelta(seconds=self._current_backoff)
        return self.update_interval


class OEJPCoordinatorResult:
    """Container for coordinator data with metadata.

    Provides consistent structure for coordinator results including
    timing information and retry status.

    """

    def __init__(
        self,
        data: dict[str, Any],
        last_retrieved: datetime,
        request_attempts: int = 0,
        last_error: Exception | None = None,
    ) -> None:
        """Initialize coordinator result.

        Args:
            data: The fetched data
            last_retrieved: When data was last retrieved
            request_attempts: Number of failed attempts before success
            last_error: Last error encountered (if any)

        """
        self.data = data
        self.last_retrieved = last_retrieved
        self.request_attempts = request_attempts
        self.last_error = last_error
        self.next_refresh = self._calculate_next_refresh()

    def _calculate_next_refresh(self) -> datetime:
        """Calculate when the next refresh should occur."""
        # Base refresh interval with backoff consideration
        backoff = BACKOFF_BASE_SECONDS * (BACKOFF_MULTIPLIER**self.request_attempts)
        backoff = min(backoff, BACKOFF_MAX_SECONDS)
        return self.last_retrieved + timedelta(seconds=backoff)

    @property
    def is_stale(self) -> bool:
        """Check if data is stale and needs refresh."""
        return dt_util.utcnow() >= self.next_refresh

    @property
    def has_data(self) -> bool:
        """Check if result contains valid data."""
        return self.data is not None and len(self.data) > 0
