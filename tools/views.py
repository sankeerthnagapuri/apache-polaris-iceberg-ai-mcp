"""Iceberg view tools — list, load metadata, and check existence of views."""

from typing import Literal
from client import polaris_client, encode


async def list_views(
    catalog_name: str,
    namespace: str,
    page_token: str | None = None,
    page_size: int | None = None,
) -> dict:
    """
    List all view identifiers in a namespace.

    Returns view names under the given namespace in the specified catalog.

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        namespace: The namespace containing the views (use %1F separator for multi-part)
        page_token: Optional pagination token from a previous response
        page_size: Optional maximum number of results to return
    """
    params = []
    if page_token:
        params.append(f"pageToken={page_token}")
    if page_size:
        params.append(f"pageSize={page_size}")

    query = f"?{'&'.join(params)}" if params else ""
    path = f"/v1/{encode(catalog_name)}/namespaces/{namespace}/views{query}"
    result = await polaris_client.catalog_get(path)
    return result or {"identifiers": []}


async def load_view(catalog_name: str, namespace: str, view: str) -> dict:
    """
    Load full metadata for an Iceberg view.

    Returns comprehensive view information including schema, SQL representation,
    version history, and properties.

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        namespace: The namespace containing the view
        view: The view name
    """
    path = f"/v1/{encode(catalog_name)}/namespaces/{namespace}/views/{encode(view)}"
    result = await polaris_client.catalog_get(path)
    return result or {}


async def check_view_exists(
    catalog_name: str, namespace: str, view: str
) -> dict:
    """
    Check if a view exists in a namespace.

    Returns a simple exists/not-exists status without loading full metadata.

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        namespace: The namespace containing the view
        view: The view name to check
    """
    path = f"/v1/{encode(catalog_name)}/namespaces/{namespace}/views/{encode(view)}"
    exists = await polaris_client.catalog_head(path)
    return {"view": f"{namespace}.{view}", "exists": exists}


async def view_request(
    catalog_name: str,
    namespace: str,
    operation: Literal["list", "get", "exists"],
    view: str | None = None,
    page_token: str | None = None,
    page_size: int | None = None,
) -> dict:
    """
    Perform view operations under a namespace in a catalog (list views, get details, or check existence).

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        namespace: The namespace containing the view (use %1F separator for multi-part)
        operation: 'list' to list views, 'get' to load metadata, 'exists' to check existence.
        view: The view name (required for 'get' and 'exists').
        page_token: Optional pagination token from a previous response (only for 'list').
        page_size: Optional maximum number of results to return (only for 'list').
    """
    if operation == "list":
        return await list_views(
            catalog_name=catalog_name,
            namespace=namespace,
            page_token=page_token,
            page_size=page_size,
        )
    elif operation == "get":
        if not view:
            raise ValueError("view is required for 'get' operation")
        return await load_view(
            catalog_name=catalog_name,
            namespace=namespace,
            view=view,
        )
    elif operation == "exists":
        if not view:
            raise ValueError("view is required for 'exists' operation")
        return await check_view_exists(
            catalog_name=catalog_name,
            namespace=namespace,
            view=view,
        )
    else:
        raise ValueError(f"Unsupported operation: {operation}")
