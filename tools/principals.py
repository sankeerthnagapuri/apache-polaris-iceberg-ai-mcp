"""Principal management tools — list, inspect principals and their role assignments."""

from typing import Literal
from client import polaris_client, encode


async def list_principals() -> dict:
    """
    List all principals in the Polaris service.

    Returns the names, properties, and metadata for every principal
    the authenticated user can see.
    """
    result = await polaris_client.management_get("/principals")
    return result or {"principals": []}


async def get_principal(principal_name: str) -> dict:
    """
    Get detailed information about a specific principal.

    Returns the principal's name, properties, entity version, and timestamps.

    Args:
        principal_name: The name of the principal to inspect
    """
    result = await polaris_client.management_get(
        f"/principals/{encode(principal_name)}"
    )
    return result or {}


async def list_principal_roles_assigned(principal_name: str) -> dict:
    """
    List the principal roles assigned to a specific principal.

    Use this to understand what roles a user/service principal has been granted.

    Args:
        principal_name: The name of the principal whose role assignments to list
    """
    result = await polaris_client.management_get(
        f"/principals/{encode(principal_name)}/principal-roles"
    )
    return result or {"roles": []}


async def principal_request(
    operation: Literal["list", "get", "roles_assigned"],
    principal_name: str | None = None,
) -> dict:
    """
    Perform principal management operations (list all principals, get details, or list role assignments).

    Args:
        operation: 'list' to list all principals, 'get' to get details, 'roles_assigned' to list role assignments.
        principal_name: The name of the principal (required for 'get' and 'roles_assigned').
    """
    if operation == "list":
        return await list_principals()
    elif operation in ("get", "roles_assigned"):
        if not principal_name:
            raise ValueError(f"principal_name is required for '{operation}' operation")
        if operation == "get":
            return await get_principal(principal_name)
        else:
            return await list_principal_roles_assigned(principal_name)
    else:
        raise ValueError(f"Unsupported operation: {operation}")
