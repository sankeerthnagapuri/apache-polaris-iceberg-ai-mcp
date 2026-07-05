"""Iceberg table tools — list, load metadata, and check existence of tables."""

from typing import Literal
from client import polaris_client, encode


async def list_tables(
    catalog_name: str,
    namespace: str,
    page_token: str | None = None,
    page_size: int | None = None,
) -> dict:
    """
    List all table identifiers in a namespace.

    Returns table names under the given namespace in the specified catalog.

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        namespace: The namespace containing the tables (use %1F separator for multi-part)
        page_token: Optional pagination token from a previous response
        page_size: Optional maximum number of results to return
    """
    params = []
    if page_token:
        params.append(f"pageToken={page_token}")
    if page_size:
        params.append(f"pageSize={page_size}")

    query = f"?{'&'.join(params)}" if params else ""
    path = f"/v1/{encode(catalog_name)}/namespaces/{namespace}/tables{query}"
    result = await polaris_client.catalog_get(path)
    return result or {"identifiers": []}


async def load_table(
    catalog_name: str,
    namespace: str,
    table: str,
    snapshots: str | None = None,
) -> dict:
    """
    Load full metadata for an Iceberg table.

    Returns comprehensive table information including:
    - Schema (column names, types, field IDs)
    - Current snapshot and snapshot history
    - Partition spec
    - Sort order
    - Table properties
    - Table location

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        namespace: The namespace containing the table
        table: The table name
        snapshots: Optional snapshot filter — "all" (default) or "refs" (only branch/tag snapshots)
    """
    params = []
    if snapshots:
        params.append(f"snapshots={snapshots}")

    query = f"?{'&'.join(params)}" if params else ""
    path = f"/v1/{encode(catalog_name)}/namespaces/{namespace}/tables/{encode(table)}{query}"
    result = await polaris_client.catalog_get(path)
    return result or {}


async def check_table_exists(
    catalog_name: str, namespace: str, table: str
) -> dict:
    """
    Check if a table exists in a namespace.

    Returns a simple exists/not-exists status without loading full metadata.

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        namespace: The namespace containing the table
        table: The table name to check
    """
    path = f"/v1/{encode(catalog_name)}/namespaces/{namespace}/tables/{encode(table)}"
    exists = await polaris_client.catalog_head(path)
    return {"table": f"{namespace}.{table}", "exists": exists}


async def table_request(
    catalog_name: str,
    namespace: str,
    operation: Literal["list", "get", "exists"],
    table: str | None = None,
    page_token: str | None = None,
    page_size: int | None = None,
    snapshots: str | None = None,
) -> dict:
    """
    Perform table operations under a namespace in a catalog (list tables, get details, or check existence).

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        namespace: The namespace containing the table (use %1F separator for multi-part)
        operation: 'list' to list tables, 'get' to load metadata, 'exists' to check existence.
        table: The table name (required for 'get' and 'exists').
        page_token: Optional pagination token from a previous response (only for 'list').
        page_size: Optional maximum number of results to return (only for 'list').
        snapshots: Optional snapshot filter — "all" (default) or "refs" (only branch/tag snapshots) (only for 'get').
    """
    if operation == "list":
        return await list_tables(
            catalog_name=catalog_name,
            namespace=namespace,
            page_token=page_token,
            page_size=page_size,
        )
    elif operation == "get":
        if not table:
            raise ValueError("table is required for 'get' operation")
        return await load_table(
            catalog_name=catalog_name,
            namespace=namespace,
            table=table,
            snapshots=snapshots,
        )
    elif operation == "exists":
        if not table:
            raise ValueError("table is required for 'exists' operation")
        return await check_table_exists(
            catalog_name=catalog_name,
            namespace=namespace,
            table=table,
        )
    else:
        raise ValueError(f"Unsupported operation: {operation}")
