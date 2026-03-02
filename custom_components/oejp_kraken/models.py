"""Data models for OEJP Kraken integration.

This module defines typed structures for API responses and
coordinator data to improve type safety and IDE support.
"""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class MeterInfo(TypedDict):
    """Meter identification information."""

    mpan: str | None
    serial_number: str | None


class DailyConsumption(TypedDict, total=False):
    """Daily consumption breakdown."""

    consumption: float
    date: str
    peak_consumption: NotRequired[float | None]
    off_peak_consumption: NotRequired[float | None]


class RateInfo(TypedDict, total=False):
    """Rate information for current period."""

    tariff_name: NotRequired[str | None]
    rate_period: NotRequired[str | None]
    peak_rate: NotRequired[float | None]
    off_peak_rate: NotRequired[float | None]


class AccountInfo(TypedDict):
    """Account information from API."""

    account_id: str


class OEJPCoordinatorData(TypedDict, total=False):
    """Typed structure for coordinator data.

    This defines the expected structure of data returned by
    the OEJP Kraken API and stored in the coordinator.
    """

    # Timestamps
    last_updated: str

    # Power and consumption
    current_usage: float | None  # Current power in kW
    total_consumption: float | None  # Total consumption in kWh
    daily_consumption: NotRequired[DailyConsumption | None]
    monthly_consumption: NotRequired[float | None]

    # Rate information
    current_rate: float | None  # Current rate in JPY/kWh
    rate_info: NotRequired[RateInfo | None]

    # Account information
    account: NotRequired[AccountInfo | None]
    mpan: NotRequired[str | None]
    serial_number: NotRequired[str | None]

    # Debug data (not exposed to sensors)
    raw_data: NotRequired[dict[str, Any]]
