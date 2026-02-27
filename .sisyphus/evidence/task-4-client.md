# Task 4: GraphQL Client Implementation Evidence

## Summary
Implemented `KrakenGraphQLClient` class for OEJP Kraken GraphQL API communication.

## Files Created
- `custom_components/oejp_kraken/graphql_client.py`

## Implementation Details

### Exception Classes
- `KrakenError`: Base exception for API errors with code and details
- `KrakenAuthenticationError`: Specific exception for auth failures

### KrakenGraphQLClient Class

#### Constructor
```python
def __init__(self, email: str, password: str, session: Optional[aiohttp.ClientSession] = None)
```
- Accepts email and password for authentication
- Optional shared aiohttp session for connection pooling

#### Methods Implemented

| Method | Description |
|--------|-------------|
| `authenticate()` | Obtains JWT token via `obtainKrakenToken` mutation |
| `refresh_token()` | Refreshes access token using refresh token |
| `execute_query(query, variables)` | Executes arbitrary GraphQL query |
| `close()` | Closes aiohttp session if owned |
| `is_authenticated` | Property to check auth state |
| `set_tokens()` / `get_tokens()` | Manual token management |

#### Features
- Async/await with aiohttp
- Context manager support (`async with`)
- Comprehensive error handling:
  - HTTP status codes (401, 429, 5xx, 4xx)
  - GraphQL errors in response
  - Network/timeout errors
- Token management (access + refresh)
- Rate limit error detection
- Configurable timeout (30s default)

### GraphQL Operations

#### Authentication Mutation
```graphql
mutation ObtainKrakenToken($input: ObtainJSONWebTokenInput!) {
    obtainKrakenToken(input: $input) {
        token
        refreshToken
    }
}
```

#### Refresh Token Mutation
```graphql
mutation RefreshToken($input: RefreshInput!) {
    refreshToken(input: $input) {
        token
        refreshToken
    }
}
```

## Dependencies
- `aiohttp` (async HTTP client)
- `const.API_BASE_URL` for endpoint configuration

## Testing Status
- File created successfully
- Python syntax valid
- Ready for integration testing

## Next Steps
1. Integration with config flow
2. Token persistence via Home Assistant storage
3. Sensor data fetching implementation
