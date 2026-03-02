"""GraphQL client for OEJP Kraken API.

This module provides an async GraphQL client for communicating with
the Octopus Energy Japan Kraken API, including authentication,
token management, and query execution.
"""

from __future__ import annotations

import logging
from types import TracebackType
from typing import TYPE_CHECKING, Any, Self

import aiohttp

from .const import API_BASE_URL

if TYPE_CHECKING:
    pass

_LOGGER = logging.getLogger(__name__)

# Type alias for GraphQL response
GraphQLResponse = dict[str, Any]


class KrakenError(Exception):
    """Base exception for Kraken API errors.

    This is the base class for all errors raised by the Kraken GraphQL client.

    Attributes:
        message: Human-readable error message.
        code: Error code from the API (if available).
        details: Additional error details from the API.

    """

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize KrakenError.

        Args:
            message: Human-readable error message.
            code: Error code from the API (optional).
            details: Additional error details (optional).

        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation of the error.

        Returns:
            Formatted error string with code prefix if available.

        """
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message

    def __repr__(self) -> str:
        """Return detailed representation of the error.

        Returns:
            Detailed string representation.

        """
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"code={self.code!r}, "
            f"details={self.details!r})"
        )


class KrakenAuthenticationError(KrakenError):
    """Exception raised for authentication-related errors.

    This exception is raised when:
    - Authentication credentials are invalid
    - Token has expired and cannot be refreshed
    - Authentication request fails

    """

    pass


class KrakenRateLimitError(KrakenError):
    """Exception raised when API rate limit is exceeded.

    This exception includes retry-after information when available.

    Attributes:
        retry_after: Seconds to wait before retrying (if available).

    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: int | None = None,
    ) -> None:
        """Initialize KrakenRateLimitError.

        Args:
            message: Error message.
            retry_after: Seconds to wait before retrying.

        """
        super().__init__(message, code="RATE_LIMIT")
        self.retry_after = retry_after


class KrakenGraphQLClient:
    """Async GraphQL client for OEJP Kraken API.

    This client handles:
    - Authentication with email/password
    - Token refresh management
    - GraphQL query and mutation execution
    - Error handling and retry logic

    Example:
        async with KrakenGraphQLClient(email, password) as client:
            await client.authenticate()
            result = await client.execute_query("{ viewer { id } }")

    Attributes:
        OBTAIN_TOKEN_MUTATION: GraphQL mutation for obtaining tokens.
        REFRESH_TOKEN_MUTATION: GraphQL mutation for refreshing tokens.

    """

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
        *,
        session: aiohttp.ClientSession | None = None,
        endpoint: str = API_BASE_URL,
        timeout: int = 30,
    ) -> None:
        """Initialize the GraphQL client.

        Args:
            email: OEJP Kraken account email.
            password: OEJP Kraken account password.
            session: Optional aiohttp ClientSession (creates one if not provided).
            endpoint: API endpoint URL (defaults to API_BASE_URL).
            timeout: Request timeout in seconds (default: 30).

        """
        self._email = email
        self._password = password
        self._session = session
        self._owns_session = session is None
        self._endpoint = endpoint
        self._timeout = timeout
        self._access_token: str | None = None
        self._refresh_token: str | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session.

        Creates a new session if one doesn't exist or if the existing
        session has been closed.

        Returns:
            The aiohttp ClientSession.

        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session if we own it.

        This method should be called when the client is no longer needed
        to properly release resources.

        """
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()
            _LOGGER.debug("Closed aiohttp session")

    @property
    def is_authenticated(self) -> bool:
        """Check if client has valid authentication tokens.

        Returns:
            True if an access token is available.

        """
        return self._access_token is not None

    @property
    def endpoint(self) -> str:
        """Get the API endpoint URL.

        Returns:
            The API endpoint URL.

        """
        return self._endpoint

    def set_tokens(self, access_token: str, refresh_token: str) -> None:
        """Set authentication tokens manually.

        Use this method to restore authentication state from stored tokens.

        Args:
            access_token: JWT access token.
            refresh_token: JWT refresh token.

        """
        self._access_token = access_token
        self._refresh_token = refresh_token

    def get_tokens(self) -> tuple[str | None, str | None]:
        """Get current authentication tokens.

        Returns:
            Tuple of (access_token, refresh_token).

        """
        return self._access_token, self._refresh_token

    async def authenticate(self) -> GraphQLResponse:
        """Authenticate with the Kraken API.

        Sends an authentication request using the configured email and password,
        and stores the received tokens.

        Returns:
            Dict containing 'token' and 'refreshToken'.

        Raises:
            KrakenAuthenticationError: If authentication fails.

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
        except aiohttp.ClientError as err:
            raise KrakenAuthenticationError(
                f"Network error during authentication: {err}",
                code="NETWORK_ERROR",
            ) from err
        except TimeoutError as err:
            raise KrakenAuthenticationError(
                f"Timeout during authentication: {err}",
                code="TIMEOUT",
            ) from err
        except OSError as err:
            raise KrakenAuthenticationError(
                f"OS error during authentication: {err}",
                code="OS_ERROR",
            ) from err

    async def refresh_token(self) -> GraphQLResponse:
        """Refresh the authentication token.

        Uses the stored refresh token to obtain a new access token.

        Returns:
            Dict containing new 'token' and 'refreshToken'.

        Raises:
            KrakenAuthenticationError: If refresh fails or no refresh token available.

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
        except aiohttp.ClientError as err:
            raise KrakenAuthenticationError(
                f"Network error during token refresh: {err}",
                code="NETWORK_ERROR",
            ) from err
        except TimeoutError as err:
            raise KrakenAuthenticationError(
                f"Timeout during token refresh: {err}",
                code="TIMEOUT",
            ) from err
        except OSError as err:
            raise KrakenAuthenticationError(
                f"OS error during token refresh: {err}",
                code="OS_ERROR",
            ) from err

    async def execute_query(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> GraphQLResponse:
        """Execute a GraphQL query.

        Args:
            query: GraphQL query string.
            variables: Optional query variables.

        Returns:
            Query result data.

        Raises:
            KrakenError: If query execution fails.
            KrakenAuthenticationError: If not authenticated.

        """
        if not self.is_authenticated:
            raise KrakenAuthenticationError(
                "Not authenticated. Call authenticate() first.",
            )

        return await self._execute_request(query, variables, require_auth=True)

    async def _execute_request(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        *,
        require_auth: bool = True,
    ) -> GraphQLResponse:
        """Execute a GraphQL request.

        Args:
            query: GraphQL query/mutation string.
            variables: Optional query variables.
            require_auth: Whether to include auth header.

        Returns:
            Query result data.

        Raises:
            KrakenError: If request fails.
            KrakenAuthenticationError: If authentication error (401).
            KrakenRateLimitError: If rate limit exceeded (429).

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
                timeout=aiohttp.ClientTimeout(total=self._timeout),
            ) as response:
                return await self._handle_response(response)

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

    async def _handle_response(
        self, response: aiohttp.ClientResponse
    ) -> GraphQLResponse:
        """Handle HTTP response and extract data or raise errors.

        Args:
            response: The aiohttp response object.

        Returns:
            The GraphQL response data.

        Raises:
            KrakenAuthenticationError: For 401 responses.
            KrakenRateLimitError: For 429 responses.
            KrakenError: For other error responses.

        """
        # Handle specific HTTP status codes
        if response.status == 401:
            raise KrakenAuthenticationError(
                "Authentication expired or invalid",
                code="UNAUTHORIZED",
            )

        if response.status == 429:
            retry_after = response.headers.get("Retry-After")
            raise KrakenRateLimitError(
                retry_after=int(retry_after) if retry_after else None,
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

        # Parse JSON response
        result = await response.json()

        # Check for GraphQL errors
        errors = result.get("errors", [])
        if errors:
            error = errors[0]
            message = error.get("message", "Unknown GraphQL error")
            extensions = error.get("extensions", {})
            code = extensions.get("code")
            details = extensions

            raise KrakenError(
                message,
                code=code,
                details=details,
            )

        return result.get("data", {})

    async def __aenter__(self) -> Self:
        """Async context manager entry.

        Returns:
            The client instance.

        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit.

        Args:
            exc_type: Exception type if an error occurred.
            exc_val: Exception value if an error occurred.
            exc_tb: Exception traceback if an error occurred.

        """
        await self.close()
