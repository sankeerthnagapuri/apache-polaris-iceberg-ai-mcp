"""Namespace tools — list, inspect, and check existence of Iceberg namespaces."""

from typing import Literal
from client import polaris_client, encode


async def list_namespaces(
    catalog_name: str,
    parent: str | None = None,
    page_token: str | None = None,
    page_size: int | None = None,
) -> dict:
    """
    List namespaces in a catalog, optionally under a parent namespace.

    If parent is not provided, lists all top-level namespaces.
    For nested namespaces, provide the parent (e.g. "accounting" to list
    children like "accounting.tax").

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        parent: Optional parent namespace to list children of
        page_token: Optional pagination token from a previous response
        page_size: Optional maximum number of results to return
    """
    params = []
    if parent:
        params.append(f"parent={parent}")
    if page_token:
        params.append(f"pageToken={page_token}")
    if page_size:
        params.append(f"pageSize={page_size}")

    query = f"?{'&'.join(params)}" if params else ""
    path = f"/v1/{encode(catalog_name)}/namespaces{query}"
    result = await polaris_client.catalog_get(path)
    return result or {"namespaces": []}


async def get_namespace(catalog_name: str, namespace: str) -> dict:
    """
    Load the metadata properties for a namespace.

    Returns all stored metadata properties including location, owner, and
    any custom properties set on the namespace.

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        namespace: The namespace identifier (use %1F separator for multi-part, e.g. "db1%1Fschema1")
    """
    path = f"/v1/{encode(catalog_name)}/namespaces/{namespace}"
    result = await polaris_client.catalog_get(path)
    return result or {}


async def check_namespace_exists(catalog_name: str, namespace: str) -> dict:
    """
    Check if a namespace exists in a catalog.

    Returns a simple exists/not-exists status without loading full metadata.

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        namespace: The namespace identifier
    """
    path = f"/v1/{encode(catalog_name)}/namespaces/{namespace}"
    exists = await polaris_client.catalog_head(path)
    return {"namespace": namespace, "exists": exists}


async def namespace_request(
    catalog_name: str,
    operation: Literal["list", "get", "exists"],
    namespace: str | None = None,
    parent: str | None = None,
    page_token: str | None = None,
    page_size: int | None = None,
) -> dict:
    """
    Perform namespace operations in a catalog (list namespaces, get details, or check existence).

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        operation: 'list' to list namespaces, 'get' to load details, 'exists' to check existence.
        namespace: The namespace identifier (use %1F separator for multi-part, e.g. "db1%1Fschema1") (required for 'get' and 'exists').
        parent: Optional parent namespace to list children of (only for 'list').
        page_token: Optional pagination token from a previous response (only for 'list').
        page_size: Optional maximum number of results to return (only for 'list').
    """
    if operation == "list":
        return await list_namespaces(
            catalog_name=catalog_name,
            parent=parent,
            page_token=page_token,
            page_size=page_size,
        )
    elif operation == "get":
        if not namespace:
            raise ValueError("namespace is required for 'get' operation")
        return await get_namespace(catalog_name, namespace)
    elif operation == "exists":
        if not namespace:
            raise ValueError("namespace is required for 'exists' operation")
        return await check_namespace_exists(catalog_name, namespace)
    else:
        raise ValueError(f"Unsupported operation: {operation}")
