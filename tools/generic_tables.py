"""Generic table tools — list and load non-Iceberg tables (Delta, CSV, etc.)."""

from typing import Literal
from client import polaris_client, encode


async def list_generic_tables(
    catalog_name: str,
    namespace: str,
    page_token: str | None = None,
    page_size: int | None = None,
) -> dict:
    """
    List all generic table identifiers in a namespace.

    Generic tables represent non-Iceberg table formats registered in Polaris,
    such as Delta Lake, CSV, Parquet, etc.

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        namespace: The namespace containing the generic tables
        page_token: Optional pagination token from a previous response
        page_size: Optional maximum number of results to return
    """
    params = []
    if page_token:
        params.append(f"pageToken={page_token}")
    if page_size:
        params.append(f"pageSize={page_size}")

    query = f"?{'&'.join(params)}" if params else ""
    path = f"/polaris/v1/{encode(catalog_name)}/namespaces/{namespace}/generic-tables{query}"
    result = await polaris_client.catalog_get(path)
    return result or {"identifiers": []}


async def load_generic_table(
    catalog_name: str, namespace: str, generic_table: str
) -> dict:
    """
    Load detailed information about a generic table.

    Returns the table name, format (e.g. "delta", "csv"), base location,
    description, properties, and optional storage access configurations.

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        namespace: The namespace containing the generic table
        generic_table: The name of the generic table to load
    """
    path = f"/polaris/v1/{encode(catalog_name)}/namespaces/{namespace}/generic-tables/{encode(generic_table)}"
    result = await polaris_client.catalog_get(path)
    return result or {}


async def generic_table_request(
    catalog_name: str,
    namespace: str,
    operation: Literal["list", "get"],
    generic_table: str | None = None,
    page_token: str | None = None,
    page_size: int | None = None,
) -> dict:
    """
    Perform operations on non-Iceberg generic tables (Delta, CSV, Parquet, etc.) under a namespace.

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        namespace: The namespace containing the generic tables
        operation: 'list' to list all generic tables, 'get' to load details of a specific generic table.
        generic_table: The generic table name (required for 'get').
        page_token: Optional pagination token from a previous response (only for 'list').
        page_size: Optional maximum number of results to return (only for 'list').
    """
    if operation == "list":
        return await list_generic_tables(
            catalog_name=catalog_name,
            namespace=namespace,
            page_token=page_token,
            page_size=page_size,
        )
    elif operation == "get":
        if not generic_table:
            raise ValueError("generic_table is required for 'get' operation")
        return await load_generic_table(
            catalog_name=catalog_name,
            namespace=namespace,
            generic_table=generic_table,
        )
    else:
        raise ValueError(f"Unsupported operation: {operation}")
