"""Connection management tools — connect, disconnect, get server config."""

from client import polaris_client


async def connect(
    uri: str = "http://localhost:8181",
    client_id: str = "admin",
    client_secret: str = "password",
    token: str | None = None,
    scope: str = "PRINCIPAL_ROLE:ALL",
    oauth_token_url: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> str:
    """
    Connect to Apache Polaris.

    Supports three authentication modes:
    1. Client Credentials (default) — provide client_id and client_secret
    2. Bearer Token — provide a pre-existing OIDC/JWT token
    3. Keycloak / OIDC Password Credentials — provide oauth_token_url, client_id, client_secret, username, and password

    Args:
        uri: Polaris server URL (e.g. http://localhost:8181)
        client_id: OAuth2 client ID
        client_secret: OAuth2 client secret
        token: Pre-existing bearer token (if provided, other auth inputs are ignored)
        scope: OAuth2 scope for client credentials flow
        oauth_token_url: URL to exchange password credentials for a token (e.g. Keycloak token endpoint)
        username: Resource owner username
        password: Resource owner password
    """
    if polaris_client.is_connected:
        await polaris_client.disconnect()

    if token:
        result = await polaris_client.connect_with_token(uri, token)
    elif oauth_token_url and username and password:
        result = await polaris_client.connect_with_password_credentials(
            uri, oauth_token_url, client_id, client_secret, username, password
        )
    else:
        result = await polaris_client.connect_with_credentials(
            uri, client_id, client_secret, scope
        )

    return (
        f"✅ {result}\n"
        f"  Management API: {polaris_client.management_url}\n"
        f"  Catalog API:    {polaris_client.catalog_url}"
    )



async def disconnect() -> str:
    """Disconnect from Apache Polaris and clear the current session."""
    result = await polaris_client.disconnect()
    return f"✅ {result}"


async def get_server_config(warehouse: str | None = None) -> dict:
    """
    Get catalog configuration settings from the Polaris server.

    Returns default and override configuration properties, plus the list
    of supported API endpoints.

    Args:
        warehouse: Optional warehouse location or identifier
    """
    path = "/v1/config"
    if warehouse:
        path += f"?warehouse={warehouse}"
    result = await polaris_client.catalog_get(path)
    return result or {}
