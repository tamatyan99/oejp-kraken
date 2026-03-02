"""GraphQL queries and mutations for OEJP Kraken API.

This module centralizes all GraphQL operations for easier
maintenance and reuse.
"""

from __future__ import annotations

# Authentication mutations
OBTAIN_TOKEN_MUTATION = """
mutation ObtainKrakenToken($input: ObtainJSONWebTokenInput!) {
    obtainKrakenToken(input: $input) {
        token
        refreshToken
    }
}
"""

REFRESH_TOKEN_MUTATION = """
mutation RefreshToken($input: RefreshInput!) {
    refreshToken(input: $input) {
        token
        refreshToken
    }
}
"""

# Data queries
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

# Future queries can be added here:
# CONSUMPTION_QUERY = "..."
# RATE_QUERY = "..."
