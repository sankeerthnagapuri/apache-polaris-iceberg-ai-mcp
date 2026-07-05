"""
Apache Polaris Catalog MCP Server

A read-only FastMCP server providing 28 tools for data engineers to interact
with Apache Polaris catalog management and Iceberg REST catalog APIs.

Covers:
- Polaris Management API: catalogs, principals, roles, grants
- Iceberg REST Catalog API: namespaces, tables, views
- Polaris-native APIs: policies, generic tables

Run with:
    fastmcp run server.py
"""

from fastmcp import FastMCP

# Import all tool functions
from tools.connection import (
    connect,
    disconnect,
    get_server_config,
)
from tools.catalogs import catalog_request
from tools.namespaces import namespace_request
from tools.tables import table_request
from tools.views import view_request
from tools.principals import principal_request
from tools.roles import role_request
from tools.policies import policy_request
from tools.generic_tables import generic_table_request
from tools.inspect import inspect_request



# ---------------------------------------------------------------------------
# Create the FastMCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="Polaris Catalog MCP",
    instructions="""
You are connected to an Apache Polaris catalog management server.

This server provides access to:
1. **Polaris Management API** — catalogs, principals, principal roles, catalog roles, grants
2. **Iceberg REST Catalog API** — namespaces, tables, views
3. **Polaris-native APIs** — policies, generic tables (Delta, CSV, etc.)
4. **Table Inspection** — metadata inspection (snapshots, partitions, manifests, health) using PyIceberg

**Getting started:**
- First call `connect` to authenticate with the Polaris server
- Then use any of the consolidated request tools to explore the catalog:
  - `catalog_request(operation="list")`
  - `namespace_request(catalog_name="...", operation="list")`
  - `table_request(catalog_name="...", namespace="...", operation="list")`
  - `view_request(catalog_name="...", namespace="...", operation="list")`
  - `principal_request(operation="list")`
  - `role_request(operation="list_principal_roles")`
  - `policy_request(catalog_name="...", operation="list", namespace="...")`
  - `generic_table_request(catalog_name="...", namespace="...", operation="list")`
  - `inspect_request(catalog_name="...", namespace="...", table="...", operation="health")`
""",
)


# ---------------------------------------------------------------------------
# Register all tools
# ---------------------------------------------------------------------------

# Connection
mcp.tool()(connect)
mcp.tool()(disconnect)
mcp.tool()(get_server_config)

# Consolidated requests
mcp.tool()(catalog_request)
mcp.tool()(namespace_request)
mcp.tool()(table_request)
mcp.tool()(view_request)
mcp.tool()(principal_request)
mcp.tool()(role_request)
mcp.tool()(policy_request)
mcp.tool()(generic_table_request)
mcp.tool()(inspect_request)



# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
