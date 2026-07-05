"""Role management tools — principal roles, catalog roles, and cross-mappings."""

from typing import Literal
from client import polaris_client, encode


# ---------------------------------------------------------------------------
# Principal Roles
# ---------------------------------------------------------------------------


async def list_principal_roles() -> dict:
    """
    List all principal roles in the Polaris service.

    Principal roles are the top-level RBAC roles that can be assigned to principals
    and then mapped to catalog-specific roles.
    """
    result = await polaris_client.management_get("/principal-roles")
    return result or {"roles": []}


async def get_principal_role(principal_role_name: str) -> dict:
    """
    Get detailed information about a specific principal role.

    Returns the role name, properties, entity version, and timestamps.

    Args:
        principal_role_name: The name of the principal role to inspect
    """
    result = await polaris_client.management_get(
        f"/principal-roles/{encode(principal_role_name)}"
    )
    return result or {}


async def list_principals_for_role(principal_role_name: str) -> dict:
    """
    List all principals that have been assigned a specific principal role.

    Use this to answer "who has this role?" questions.

    Args:
        principal_role_name: The name of the principal role
    """
    result = await polaris_client.management_get(
        f"/principal-roles/{encode(principal_role_name)}/principals"
    )
    return result or {"principals": []}


# ---------------------------------------------------------------------------
# Catalog Roles
# ---------------------------------------------------------------------------


async def list_catalog_roles(catalog_name: str) -> dict:
    """
    List all catalog roles defined within a specific catalog.

    Catalog roles hold the actual privileges (grants) on catalog resources
    like namespaces, tables, and views.

    Args:
        catalog_name: The name of the catalog whose roles to list
    """
    result = await polaris_client.management_get(
        f"/catalogs/{encode(catalog_name)}/catalog-roles"
    )
    return result or {"roles": []}


async def get_catalog_role(catalog_name: str, catalog_role_name: str) -> dict:
    """
    Get detailed information about a specific catalog role.

    Returns the role name, properties, entity version, and timestamps.

    Args:
        catalog_name: The name of the catalog containing the role
        catalog_role_name: The name of the catalog role to inspect
    """
    result = await polaris_client.management_get(
        f"/catalogs/{encode(catalog_name)}/catalog-roles/{encode(catalog_role_name)}"
    )
    return result or {}


# ---------------------------------------------------------------------------
# Cross-mappings: Principal Role <-> Catalog Role
# ---------------------------------------------------------------------------


async def list_catalog_roles_for_principal_role(
    principal_role_name: str, catalog_name: str
) -> dict:
    """
    List the catalog roles mapped to a principal role within a specific catalog.

    This shows what catalog-level permissions a principal role inherits.

    Args:
        principal_role_name: The name of the principal role
        catalog_name: The catalog to check mappings in
    """
    result = await polaris_client.management_get(
        f"/principal-roles/{encode(principal_role_name)}/catalog-roles/{encode(catalog_name)}"
    )
    return result or {"roles": []}


async def list_principal_roles_for_catalog_role(
    catalog_name: str, catalog_role_name: str
) -> dict:
    """
    List the principal roles that have been assigned a specific catalog role.

    Use this to answer "which principal roles have access via this catalog role?"

    Args:
        catalog_name: The name of the catalog containing the role
        catalog_role_name: The name of the catalog role
    """
    result = await polaris_client.management_get(
        f"/catalogs/{encode(catalog_name)}/catalog-roles/{encode(catalog_role_name)}/principal-roles"
    )
    return result or {"roles": []}


# ---------------------------------------------------------------------------
# Grant Inspection
# ---------------------------------------------------------------------------


async def list_grants_for_catalog_role(
    catalog_name: str, catalog_role_name: str
) -> dict:
    """
    List all grants (privileges) held by a catalog role.

    Returns the list of privilege grants including the grant type
    (TABLE_READ_DATA, NAMESPACE_LIST, CATALOG_MANAGE_CONTENT, etc.),
    the resource type, and the resource path (namespace/table).

    Args:
        catalog_name: The name of the catalog containing the role
        catalog_role_name: The name of the catalog role whose grants to list
    """
    result = await polaris_client.management_get(
        f"/catalogs/{encode(catalog_name)}/catalog-roles/{encode(catalog_role_name)}/grants"
    )
    return result or {"grants": []}


async def role_request(
    operation: Literal[
        "list_principal_roles",
        "get_principal_role",
        "list_principals_for_role",
        "list_catalog_roles",
        "get_catalog_role",
        "list_catalog_roles_for_principal_role",
        "list_principal_roles_for_catalog_role",
        "list_grants_for_catalog_role",
    ],
    principal_role_name: str | None = None,
    catalog_name: str | None = None,
    catalog_role_name: str | None = None,
) -> dict:
    """
    Perform role-related and grant inspection operations.

    Args:
        operation: The role/grant operation to execute.
        principal_role_name: Name of the principal role (required for get_principal_role, list_principals_for_role, list_catalog_roles_for_principal_role).
        catalog_name: Catalog name (required for catalog role operations and grants).
        catalog_role_name: Catalog role name (required for get_catalog_role, list_principal_roles_for_catalog_role, list_grants_for_catalog_role).
    """
    if operation == "list_principal_roles":
        return await list_principal_roles()
    
    elif operation == "get_principal_role":
        if not principal_role_name:
            raise ValueError("principal_role_name is required for 'get_principal_role' operation")
        return await get_principal_role(principal_role_name)
        
    elif operation == "list_principals_for_role":
        if not principal_role_name:
            raise ValueError("principal_role_name is required for 'list_principals_for_role' operation")
        return await list_principals_for_role(principal_role_name)
        
    elif operation == "list_catalog_roles":
        if not catalog_name:
            raise ValueError("catalog_name is required for 'list_catalog_roles' operation")
        return await list_catalog_roles(catalog_name)
        
    elif operation == "get_catalog_role":
        if not catalog_name or not catalog_role_name:
            raise ValueError("catalog_name and catalog_role_name are required for 'get_catalog_role' operation")
        return await get_catalog_role(catalog_name, catalog_role_name)
        
    elif operation == "list_catalog_roles_for_principal_role":
        if not principal_role_name or not catalog_name:
            raise ValueError("principal_role_name and catalog_name are required for 'list_catalog_roles_for_principal_role' operation")
        return await list_catalog_roles_for_principal_role(principal_role_name, catalog_name)
        
    elif operation == "list_principal_roles_for_catalog_role":
        if not catalog_name or not catalog_role_name:
            raise ValueError("catalog_name and catalog_role_name are required for 'list_principal_roles_for_catalog_role' operation")
        return await list_principal_roles_for_catalog_role(catalog_name, catalog_role_name)
        
    elif operation == "list_grants_for_catalog_role":
        if not catalog_name or not catalog_role_name:
            raise ValueError("catalog_name and catalog_role_name are required for 'list_grants_for_catalog_role' operation")
        return await list_grants_for_catalog_role(catalog_name, catalog_role_name)
        
    else:
        raise ValueError(f"Unsupported operation: {operation}")
