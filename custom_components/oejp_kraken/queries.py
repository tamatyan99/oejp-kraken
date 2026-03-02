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
VIEWER_ACCOUNTS_QUERY = """
query ViewerAccounts {
    viewer {
        accounts {
            number
        }
    }
}
"""

HALF_HOURLY_READINGS_QUERY = """
query HalfHourlyReadings($accountNumber: String!, $fromDatetime: DateTime, $toDatetime: DateTime) {
    account(accountNumber: $accountNumber) {
        properties {
            electricitySupplyPoints {
                halfHourlyReadings(fromDatetime: $fromDatetime, toDatetime: $toDatetime) {
                    startAt
                    endAt
                    version
                    value
                }
            }
        }
    }
}
"""

# Future queries can be added here:
# CONSUMPTION_QUERY = "..."
# RATE_QUERY = "..."
