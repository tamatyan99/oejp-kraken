"""Constants for OEJP Kraken integration.

This module defines all constants used throughout the OEJP Kraken
integration, including configuration keys, API endpoints, and
default values.
"""

from __future__ import annotations

from typing import Final

# Integration domain
DOMAIN: Final = "oejp_kraken"

# Configuration keys
CONF_EMAIL: Final = "email"
CONF_PASSWORD: Final = "password"
CONF_UPDATE_INTERVAL: Final = "update_interval"

# Default values
DEFAULT_UPDATE_INTERVAL: Final = 300  # 5 minutes
MIN_UPDATE_INTERVAL: Final = 60  # 1 minute
MAX_UPDATE_INTERVAL: Final = 3600  # 1 hour

# API endpoints
API_BASE_URL: Final = "https://api.oejp-kraken.energy/v1/graphql/"
AUTH_URL: Final = "https://auth.oejp-kraken.energy"

# Rate limiting (from Kraken API documentation)
MAX_QUERY_COMPLEXITY: Final = 200
MAX_NODES_PER_REQUEST: Final = 10000
RATE_LIMIT_POINTS_PER_HOUR: Final = 50000

# Sensor configuration
SENSOR_CURRENT_POWER = "current_power"
SENSOR_TODAY_CONSUMPTION = "today_consumption"
SENSOR_CURRENT_RATE = "current_rate"

# Device information
MANUFACTURER: Final = "OEJP Kraken"
DEVICE_MODEL: Final = "Smart Meter"
