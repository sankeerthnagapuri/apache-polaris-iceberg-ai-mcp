"""
Async HTTP client for Apache Polaris Management API and Iceberg REST Catalog API.

Handles OAuth2 client credentials authentication, bearer token injection,
and dual base URL routing (management vs catalog endpoints).
"""

import httpx
from urllib.parse import quote


class PolarisClient:
    """
    Async HTTP client that wraps both the Polaris Management API
    and the Iceberg REST Catalog API.

    Manages authentication state and provides low-level request methods
    for the MCP tool layer.
    """

    def __init__(self):
        self._http: httpx.AsyncClient | None = None
        self._management_url: str = ""
        self._catalog_url: str = ""
        self._token: str | None = None
        self._connected: bool = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self._token is not None

    @property
    def management_url(self) -> str:
        return self._management_url

    @property
    def catalog_url(self) -> str:
        return self._catalog_url

    async def connect_with_credentials(
        self,
        uri: str,
        client_id: str,
        client_secret: str,
        scope: str = "PRINCIPAL_ROLE:ALL",
    ) -> str:
        """Authenticate using OAuth2 client credentials flow."""
        clean_url = uri.rstrip("/")
        self._resolve_base_urls(clean_url)

        token_url = f"{self._catalog_url}/v1/oauth/tokens"

        self._http = httpx.AsyncClient(timeout=30.0)

        resp = await self._http.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": scope,
            },
        )

        if resp.status_code != 200:
            await self._http.aclose()
            self._http = None
            raise ConnectionError(
                f"Authentication failed (HTTP {resp.status_code}): {resp.text}"
            )

        self._token = resp.json().get("access_token")
        if not self._token:
            await self._http.aclose()
            self._http = None
            raise ConnectionError("No access_token in response")

        self._connected = True
        return "Connected successfully via client credentials"

    async def connect_with_token(self, uri: str, token: str) -> str:
        """Connect using a pre-existing bearer token (e.g. from Keycloak OIDC)."""
        clean_url = uri.rstrip("/")
        self._resolve_base_urls(clean_url)

        self._http = httpx.AsyncClient(timeout=30.0)
        self._token = token
        self._connected = True
        return "Connected successfully via bearer token"

    async def connect_with_password_credentials(
        self,
        uri: str,
        oauth_token_url: str,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
    ) -> str:
        """Authenticate against Keycloak/OIDC using Resource Owner Password Credentials flow, then connect to Polaris."""
        self._http = httpx.AsyncClient(timeout=30.0)

        # 1. Fetch token from Keycloak/OIDC provider
        resp = await self._http.post(
            oauth_token_url,
            data={
                "grant_type": "password",
                "client_id": client_id,
                "client_secret": client_secret,
                "username": username,
                "password": password,
            },
        )

        if resp.status_code != 200:
            await self._http.aclose()
            self._http = None
            raise ConnectionError(
                f"OIDC Password Grant authentication failed (HTTP {resp.status_code}): {resp.text}"
            )

        token = resp.json().get("access_token")
        if not token:
            await self._http.aclose()
            self._http = None
            raise ConnectionError("No access_token in OIDC response")

        # 2. Connect to Polaris using the fetched token
        clean_url = uri.rstrip("/")
        self._resolve_base_urls(clean_url)
        self._token = token
        self._connected = True
        return "Connected successfully via Keycloak/OIDC password credentials"


    async def disconnect(self) -> str:
        """Clear the current session."""
        if self._http:
            await self._http.aclose()
        self._http = None
        self._token = None
        self._connected = False
        return "Disconnected"

    def _resolve_base_urls(self, url: str) -> None:
        """Resolve management and catalog base URLs from any input URL format."""
        if "/api/management/v1" in url:
            self._management_url = url
            self._catalog_url = url.replace("/api/management/v1", "/api/catalog")
        elif "/api/catalog" in url:
            self._catalog_url = url
            self._management_url = url.replace("/api/catalog", "/api/management/v1")
        else:
            self._catalog_url = f"{url}/api/catalog"
            self._management_url = f"{url}/api/management/v1"

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _ensure_connected(self) -> None:
        if not self.is_connected or self._http is None:
            raise ConnectionError(
                "Not connected. Use the 'connect' tool first to authenticate."
            )

    # -------------------------------------------------------------------------
    # Management API requests (principals, roles, catalogs, grants)
    # -------------------------------------------------------------------------

    async def management_get(self, path: str) -> dict | list | None:
        """GET request against the Polaris Management API."""
        self._ensure_connected()
        assert self._http is not None
        url = f"{self._management_url}{path}"
        resp = await self._http.get(url, headers=self._headers)
        return self._handle_response(resp)

    # -------------------------------------------------------------------------
    # Catalog API requests (namespaces, tables, views, policies, generic tables)
    # -------------------------------------------------------------------------

    async def catalog_get(self, path: str) -> dict | list | None:
        """GET request against the Iceberg REST Catalog API."""
        self._ensure_connected()
        assert self._http is not None
        url = f"{self._catalog_url}{path}"
        resp = await self._http.get(url, headers=self._headers)
        return self._handle_response(resp)

    async def catalog_head(self, path: str) -> bool:
        """HEAD request against the Iceberg REST Catalog API. Returns True if 2xx."""
        self._ensure_connected()
        assert self._http is not None
        url = f"{self._catalog_url}{path}"
        resp = await self._http.head(url, headers=self._headers)
        return 200 <= resp.status_code < 300

    # -------------------------------------------------------------------------
    # Response handling
    # -------------------------------------------------------------------------

    @staticmethod
    def _handle_response(resp: httpx.Response) -> dict | list | None:
        """Parse response, raising descriptive errors for non-2xx."""
        if 200 <= resp.status_code < 300:
            if resp.status_code == 204 or not resp.text:
                return None
            return resp.json()

        # Build a clear error message
        try:
            error_body = resp.json()
            if "error" in error_body:
                err = error_body["error"]
                msg = err.get("message", resp.text)
                err_type = err.get("type", "")
                detail = f"{err_type}: {msg}" if err_type else msg
            else:
                detail = str(error_body)
        except Exception:
            detail = resp.text

        raise RuntimeError(f"API error (HTTP {resp.status_code}): {detail}")


def encode(value: str) -> str:
    """URL-encode a path parameter value."""
    return quote(value, safe="")


# Module-level client instance shared across all tools
polaris_client = PolarisClient()
