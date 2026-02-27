# OEJP GraphQL API Queries for Home Assistant Integration

## API Endpoint
- **Base URL**: `https://api.oejp-kraken.energy/v1/graphql/`
- **Auth Header**: `Authorization: Bearer <JWT_TOKEN>`

---

## 1. Authentication Query

### Obtain JWT Token (API Key Method)
```graphql
mutation ObtainToken($apiKey: String!) {
  obtainKrakenToken(input: { APIKey: $apiKey }) {
    token
    refreshToken
    payload
  }
}
```

### Refresh Token
```graphql
mutation RefreshToken($refreshToken: String!) {
  obtainKrakenToken(input: { refreshToken: $refreshToken }) {
    token
    refreshToken
  }
}
```

---

## 2. Account Data Access

### Get Viewer (Current User) with Accounts
```graphql
query GetViewerAccounts {
  viewer {
    id
    number
    email
    givenName
    familyName
    accounts {
      edges {
        node {
          id
          number
          status
          balance
          billingEmail
          billingAddress
        }
      }
    }
  }
}
```

### Get Account Details
```graphql
query GetAccount($accountNumber: String!) {
  account(accountNumber: $accountNumber) {
    id
    number
    status
    balance
    overdueBalance
    billingName
    billingEmail
    billingAddress
    billingAddressPostcode
    hasActiveAgreement
    properties {
      id
      address
      postcode
      electricitySupplyPoints {
        id
        spin
        status
      }
    }
    marketSupplyAgreements(active: true) {
      edges {
        node {
          id
          validFrom
          validTo
          product {
            code
            displayName
          }
        }
      }
    }
  }
}
```

---

## 3. Electricity Consumption Data

### Get Half-Hourly Readings
```graphql
query GetHalfHourlyReadings($supplyPointId: ID!, $from: DateTime!, $to: DateTime!) {
  supplyPoint(id: $supplyPointId) {
    ... on ElectricitySupplyPoint {
      id
      spin
      halfHourlyReadings(from: $from, to: $to) {
        edges {
          node {
            value
            units
            intervalStart
            intervalEnd
            source
            quality
          }
        }
      }
    }
  }
}
```

### Get Import Readings (Consumption)
```graphql
query GetImportReadings($supplyPointId: ID!, $first: Int) {
  supplyPoint(id: $supplyPointId) {
    readings {
      importReadings(first: $first) {
        edges {
          node {
            value
            units
            intervalStart
            intervalEnd
            source
            quality
          }
        }
        totalCount
      }
    }
  }
}
```

### Get Export Readings (Solar/Generation)
```graphql
query GetExportReadings($supplyPointId: ID!, $first: Int) {
  supplyPoint(id: $supplyPointId) {
    readings {
      exportReadings(first: $first) {
        edges {
          node {
            value
            units
            intervalStart
            intervalEnd
            source
            quality
          }
        }
        totalCount
      }
    }
  }
}
```

---

## 4. Pricing/Tariff Data

### Get Tariff Summary
```graphql
query GetTariffSummary($gridOperatorCode: String!) {
  tariffSummary(gridOperatorCode: $gridOperatorCode) {
    code
    displayName
    gridOperatorCode
    tiers {
      edges {
        node {
          tier
          price
          unitPrice
        }
      }
    }
  }
}
```

### Get Agreement with Product Rates
```graphql
query GetAgreementRates($agreementId: Int!) {
  agreement(id: $agreementId) {
    id
    validFrom
    validTo
    product {
      code
      displayName
      description
    }
    addonRates {
      edges {
        node {
          productRate {
            gridOperatorCode
            unitType
            pricePerUnit
            validFrom
            validTo
          }
        }
      }
    }
  }
}
```

---

## 5. Rate Limiting

### Check Rate Limit Status
```graphql
query GetRateLimitInfo {
  rateLimitInfo {
    pointsAllowanceRateLimit {
      limit
      remainingPoints
      usedPoints
      ttl
      isBlocked
    }
  }
}
```

### Check Query Complexity
```graphql
query GetQueryComplexity($query: String!) {
  queryComplexity(input: { query: $query }) {
    complexityValue
  }
}
```

---

## 6. Home Assistant Integration Queries

### Minimal Query for Sensor Updates (Low Complexity)
```graphql
query GetDailyConsumption($accountNumber: String!) {
  account(accountNumber: $accountNumber) {
    balance
    properties {
      electricitySupplyPoints {
        spin
        status
        readings {
          importReadings(first: 48) {
            edges {
              node {
                value
                intervalStart
                intervalEnd
              }
            }
          }
        }
      }
    }
  }
}
```

### Query for Real-Time Power (Single Reading)
```graphql
query GetCurrentPower($supplyPointId: ID!) {
  supplyPoint(id: $supplyPointId) {
    ... on ElectricitySupplyPoint {
      readings {
        importReadings(first: 1) {
          edges {
            node {
              value
              intervalStart
              intervalEnd
            }
          }
        }
      }
    }
  }
}
```

---

## Query Complexity Notes (Verified)

### Complexity Calculation Rules

Based on Kraken GraphQL documentation:

- **Maximum complexity per request**: 200
- **Maximum nodes per request**: 10,000
- Each GraphQL field has an assigned complexity value
- Complexity is calculated as sum of all field costs
- Nested connections multiply complexity
- Use `first`/`last` parameters (max 100) to limit result sets

### Field Type Costs

| Field Type | Cost |
|------------|------|
| Scalar | 0 |
| Enum | 0 |
| Object | 1 |
| Interface | 1 |
| Union | 1 |

### Estimated Complexity Values

| Query | Estimated Complexity | Notes |
|-------|----------------------|-------|
| GetViewerAccounts | ~10-20 | Basic user info |
| GetAccount (basic) | ~15-25 | Account + properties |
| GetHalfHourlyReadings (48 readings) | ~50-60 | 48 half-hour readings |
| GetImportReadings (first: 100) | ~100-120 | At pagination limit |
| GetDailyConsumption | ~80-100 | Balance + readings |

### Rate Limit Management

**Hourly Points Allowance:**
- Account users: 50,000 points/hour
- Organizations: 100,000 points/hour
- OAuth applications: 300,000 points/hour

**Dynamic Scaling:**
- Points allowance scales with number of supply points
- Commercial/Industrial customers get higher limits

**Recommendations:**
- Cache responses for 5-15 minutes
- Use pagination with `first: 100` or less
- Monitor rateLimitInfo query for remaining balance
- Implement exponential backoff on rate limit errors

---

## Error Codes

| Code | Description |
|------|-------------|
| KT-CT-1111 | Unauthorized |
| KT-CT-1112 | Authorization header not provided |
| KT-CT-1113 | Disabled GraphQL field requested |
| KT-CT-1134 | Invalid data (auth) |
| KT-CT-1135 | Invalid data (auth) |
| KT-CT-1188 | Query complexity limit exceeded |
| KT-CT-1189 | Query exceeds maximum node count |
| KT-CT-1199 | Rate limit exceeded |
| KT-CT-4177 | Unauthorized (account access) |

---

## Token Lifecycle

- **Token validity**: 60 minutes from issuance
- **Refresh token validity**: 7 days
- **Recommended flow**:
  1. Cache both token and refreshToken
  2. Use cached token for API requests
  3. Regenerate token using refreshToken when expired
  4. Re-authenticate with original method when refreshToken expires

---

## Next Steps for Integration

1. **Authentication**: Implement config flow with API key input
2. **Token Management**: Store token and refresh token in hass.data
3. **Coordinator**: Use DataUpdateCoordinator with 5-minute interval
4. **Sensors**: Create sensors for:
   - Current power consumption
   - Daily consumption total
   - Account balance
   - Current tariff rate
5. **Error Handling**: Handle auth failures with re-authentication flow
