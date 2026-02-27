"""GraphQL client for OEJP Kraken API."""

import logging
from typing import Any, Optional

import aiohttp

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


class KrakenError(Exception):
    """Exception raised for Kraken API errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        """Initialize KrakenError.

        Args:
            message: Error message
            code: Error code from API
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation of error."""
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class KrakenAuthenticationError(KrakenError):
    """Exception raised for authentication errors."""


class KrakenGraphQLClient:
    """Async GraphQL client for OEJP Kraken API."""

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

    def __init__(
        self,
        email: str,
        password: str,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        """Initialize the GraphQL client.

        Args:
            email: OEJP Kraken account email
            password: OEJP Kraken account password
            session: Optional aiohttp ClientSession (will create one if not provided)
        """
        self._email = email
        self._password = password
        self._session = session
        self._owns_session = session is None
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._endpoint = API_BASE_URL

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session.

        Returns:
            aiohttp ClientSession
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session if we own it."""
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    @property
    def is_authenticated(self) -> bool:
        """Check if client has valid authentication tokens.

        Returns:
            True if access token is available
        """
        return self._access_token is not None

    def set_tokens(self, access_token: str, refresh_token: str) -> None:
        """Set authentication tokens manually.

        Args:
            access_token: JWT access token
            refresh_token: JWT refresh token
        """
        self._access_token = access_token
        self._refresh_token = refresh_token

    def get_tokens(self) -> tuple[Optional[str], Optional[str]]:
        """Get current authentication tokens.

        Returns:
            Tuple of (access_token, refresh_token)
        """
        return self._access_token, self._refresh_token

    async def authenticate(self) -> dict[str, str]:
        """Authenticate with the Kraken API.

        Returns:
            Dict containing token and refreshToken

        Raises:
            KrakenAuthenticationError: If authentication fails
        """
        variables = {
            "input": {
                "email": self._email,
                "password": self._password,
            }
        }

        try:
            result = await self._execute_request(
                self.OBTAIN_TOKEN_MUTATION,
                variables,
                require_auth=False,
            )

            data = result.get("obtainKrakenToken", {})
            token = data.get("token")
            refresh = data.get("refreshToken")

            if not token:
                raise KrakenAuthenticationError(
                    "Authentication failed: no token received",
                    details=result,
                )

            self._access_token = token
            self._refresh_token = refresh

            _LOGGER.info("Successfully authenticated with Kraken API")

            return {
                "token": token,
                "refreshToken": refresh,
            }

        except KrakenError:
            raise
        except Exception as err:
            raise KrakenAuthenticationError(
                f"Authentication request failed: {err}",
            ) from err

    async def refresh_token(self) -> dict[str, str]:
        """Refresh the authentication token.

        Returns:
            Dict containing new token and refreshToken

        Raises:
            KrakenAuthenticationError: If refresh fails
        """
        if not self._refresh_token:
            raise KrakenAuthenticationError(
                "Cannot refresh token: no refresh token available",
            )

        variables = {
            "input": {
                "refreshToken": self._refresh_token,
            }
        }

        try:
            result = await self._execute_request(
                self.REFRESH_TOKEN_MUTATION,
                variables,
                require_auth=False,
            )

            data = result.get("refreshToken", {})
            token = data.get("token")
            refresh = data.get("refreshToken")

            if not token:
                raise KrakenAuthenticationError(
                    "Token refresh failed: no token received",
                    details=result,
                )

            self._access_token = token
            self._refresh_token = refresh

            _LOGGER.info("Successfully refreshed Kraken API token")

            return {
                "token": token,
                "refreshToken": refresh,
            }

        except KrakenError:
            raise
        except Exception as err:
            raise KrakenAuthenticationError(
                f"Token refresh request failed: {err}",
            ) from err

    async def execute_query(
        self,
        query: str,
        variables: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query.

        Args:
            query: GraphQL query string
            variables: Optional query variables

        Returns:
            Query result data

        Raises:
            KrakenError: If query execution fails
            KrakenAuthenticationError: If not authenticated
        """
        if not self.is_authenticated:
            raise KrakenAuthenticationError(
                "Not authenticated. Call authenticate() first.",
            )

        return await self._execute_request(query, variables, require_auth=True)

    async def _execute_request(
        self,
        query: str,
        variables: Optional[dict[str, Any]] = None,
        require_auth: bool = True,
    ) -> dict[str, Any]:
        """Execute a GraphQL request.

        Args:
            query: GraphQL query/mutation string
            variables: Optional query variables
            require_auth: Whether to include auth header

        Returns:
            Query result data

        Raises:
            KrakenError: If request fails
        """
        session = await self._get_session()

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if require_auth and self._access_token:
            headers["Authorization"] = f"JWT {self._access_token}"

        payload = {
            "query": query,
            "variables": variables or {},
        }

        try:
            async with session.post(
                self._endpoint,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status == 401:
                    raise KrakenAuthenticationError(
                        "Authentication expired or invalid",
                        code="UNAUTHORIZED",
                    )

                if response.status == 429:
                    raise KrakenError(
                        "Rate limit exceeded",
                        code="RATE_LIMIT",
                    )

                if response.status >= 500:
                    raise KrakenError(
                        f"Server error: HTTP {response.status}",
                        code="SERVER_ERROR",
                    )

                if response.status >= 400:
                    text = await response.text()
                    raise KrakenError(
                        f"Request failed: HTTP {response.status} - {text}",
                        code="HTTP_ERROR",
                    )

                result = await response.json()

        except aiohttp.ClientError as err:
            raise KrakenError(
                f"Network error: {err}",
                code="NETWORK_ERROR",
            ) from err
        except TimeoutError as err:
            raise KrakenError(
                "Request timeout",
                code="TIMEOUT",
            ) from err

        # Check for GraphQL errors
        errors = result.get("errors", [])
        if errors:
            error = errors[0]
            message = error.get("message", "Unknown GraphQL error")
            code = error.get("extensions", {}).get("code")
            details = error.get("extensions", {})

            raise KrakenError(
                message,
                code=code,
                details=details,
            )

        return result.get("data", {})

    async def __aenter__(self) -> "KrakenGraphQLClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
