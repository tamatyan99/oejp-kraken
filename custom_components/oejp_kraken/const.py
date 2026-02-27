"""Constants for OEJP Kraken integration."""

DOMAIN = "oejp_kraken"

# Configuration keys
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Defaults
DEFAULT_UPDATE_INTERVAL = 300  # 5 minutes

# API endpoints
API_BASE_URL = "https://api.oejp-kraken.energy/v1/graphql/"
AUTH_URL = "https://auth.oejp-kraken.energy"

# Rate limiting
MAX_QUERY_COMPLEXITY = 200
MAX_NODES_PER_REQUEST = 10000
RATE_LIMIT_POINTS_PER_HOUR = 50000
