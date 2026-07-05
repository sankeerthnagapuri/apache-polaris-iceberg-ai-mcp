"""Catalog management tools — list and inspect Polaris catalogs."""

from typing import Literal
from client import polaris_client, encode


async def list_catalogs() -> dict:
    """
    List all catalogs in the Polaris service.

    Returns catalog names, types (INTERNAL/EXTERNAL), storage configurations,
    and properties for every catalog the authenticated principal can access.
    """
    result = await polaris_client.management_get("/catalogs")
    return result or {"catalogs": []}


async def get_catalog(catalog_name: str) -> dict:
    """
    Get detailed information about a specific catalog.

    Returns the catalog type (INTERNAL/EXTERNAL), storage configuration,
    default base location, connection config (for external catalogs),
    entity version, and timestamps.

    Args:
        catalog_name: The name of the catalog to inspect
    """
    result = await polaris_client.management_get(f"/catalogs/{encode(catalog_name)}")
    return result or {}


async def catalog_request(
    operation: Literal["list", "get"],
    catalog_name: str | None = None,
) -> dict:
    """
    Perform catalog operations (list all catalogs or load a specific catalog).

    Args:
        operation: 'list' to retrieve all catalogs, 'get' to inspect a specific catalog.
        catalog_name: The name of the catalog (required for 'get' operation).
    """
    if operation == "list":
        return await list_catalogs()
    elif operation == "get":
        if not catalog_name:
            raise ValueError("catalog_name is required for 'get' operation")
        return await get_catalog(catalog_name)
    else:
        raise ValueError(f"Unsupported operation: {operation}")
