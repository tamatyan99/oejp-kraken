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
        except Exception as err:
            _LOGGER.error("Failed to refresh token: %s", err)
            raise UpdateFailed(f"Token refresh failed: {err}") from err

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
        2. Fetches electricity usage data
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
            raw_data: Raw data from GraphQL API.

        Returns:
            Formatted dictionary for sensors.

        """
        if not raw_data:
            return self._create_empty_response()

        # Extract relevant fields from the API response
        formatted: dict[str, Any] = {
            "last_updated": dt_util.utcnow().isoformat(),
            "raw_data": raw_data,  # Keep raw data for debugging
        }

        # Map raw data fields to formatted output
        # These fields depend on the actual GraphQL schema
        field_mappings = [
            ("current_usage", "current_usage"),
            ("total_consumption", "total_consumption"),
            ("daily_consumption", "daily_consumption"),
            ("monthly_consumption", "monthly_consumption"),
            ("current_rate", "current_rate"),
            ("account", "account"),
            ("rate_info", "rate_info"),
        ]

        for source_key, dest_key in field_mappings:
            if source_key in raw_data:
                formatted[dest_key] = raw_data[source_key]

        # Extract account info if available
        self._extract_account_info(raw_data, formatted)

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

    def _extract_account_info(
        self, raw_data: dict[str, Any], formatted: dict[str, Any]
    ) -> None:
        """Extract account information from raw data.

        Args:
            raw_data: Raw API response data.
            formatted: Formatted data dictionary to update.

        """
        try:
            viewer = raw_data.get("viewer", {})
            accounts = viewer.get("accounts", [])
            if accounts:
                account = accounts[0]
                agreements = account.get("electricityAgreements", [])
                if agreements:
                    agreement = agreements[0]
                    meter_point = agreement.get("meterPoint", {})
                    meter = agreement.get("meter", {})

                    formatted["mpan"] = meter_point.get("mpan")
                    formatted["serial_number"] = meter.get("serialNumber")
        except (KeyError, IndexError, TypeError):
            _LOGGER.debug("Could not extract account info from response")

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
