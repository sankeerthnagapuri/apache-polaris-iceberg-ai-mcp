"""Polaris policy tools — list, load, and query applicable policies."""

from typing import Literal
from client import polaris_client, encode


async def list_policies(
    catalog_name: str,
    namespace: str,
    policy_type: str | None = None,
    page_token: str | None = None,
    page_size: int | None = None,
) -> dict:
    """
    List all policies in a namespace, optionally filtered by type.

    Policies define rules governing data compaction, access controls, and
    operational consistency. Common types include system.data_compaction.

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        namespace: The namespace containing the policies
        policy_type: Optional filter by policy type (e.g. "system.data-compaction")
        page_token: Optional pagination token from a previous response
        page_size: Optional maximum number of results to return
    """
    params = []
    if policy_type:
        params.append(f"policyType={policy_type}")
    if page_token:
        params.append(f"pageToken={page_token}")
    if page_size:
        params.append(f"pageSize={page_size}")

    query = f"?{'&'.join(params)}" if params else ""
    path = f"/polaris/v1/{encode(catalog_name)}/namespaces/{namespace}/policies{query}"
    result = await polaris_client.catalog_get(path)
    return result or {"identifiers": []}


async def load_policy(
    catalog_name: str, namespace: str, policy_name: str
) -> dict:
    """
    Load a specific policy's details and content.

    Returns the policy name, type, description, content (rules), version,
    and timestamps.

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        namespace: The namespace containing the policy
        policy_name: The name of the policy to load
    """
    path = f"/polaris/v1/{encode(catalog_name)}/namespaces/{namespace}/policies/{encode(policy_name)}"
    result = await polaris_client.catalog_get(path)
    return result or {}


async def get_applicable_policies(
    catalog_name: str,
    namespace: str | None = None,
    target_name: str | None = None,
    policy_type: str | None = None,
    page_token: str | None = None,
    page_size: int | None = None,
) -> dict:
    """
    Get all applicable policies for a catalog, namespace, table, or view.

    Includes inherited policies from parent entities. The inheritance rule is:
    - Table-level policies override namespace and catalog policies
    - Namespace-level policies override upper-level namespace or catalog policies

    To query by entity level:
    - Catalog level: omit both namespace and target_name
    - Namespace level: provide namespace, omit target_name
    - Table/View level: provide both namespace and target_name

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        namespace: Optional namespace identifier
        target_name: Optional table or view name (requires namespace)
        policy_type: Optional filter by policy type
        page_token: Optional pagination token
        page_size: Optional maximum number of results
    """
    params = []
    if namespace:
        params.append(f"namespace={namespace}")
    if target_name:
        params.append(f"target-name={target_name}")
    if policy_type:
        params.append(f"policyType={policy_type}")
    if page_token:
        params.append(f"pageToken={page_token}")
    if page_size:
        params.append(f"pageSize={page_size}")

    query = f"?{'&'.join(params)}" if params else ""
    path = f"/polaris/v1/{encode(catalog_name)}/applicable-policies{query}"
    result = await polaris_client.catalog_get(path)
    return result or {"policies": []}


async def policy_request(
    catalog_name: str,
    operation: Literal["list", "get", "get_applicable"],
    namespace: str | None = None,
    policy_name: str | None = None,
    target_name: str | None = None,
    policy_type: str | None = None,
    page_token: str | None = None,
    page_size: int | None = None,
) -> dict:
    """
    Perform policy-related operations in a catalog (list policies under a namespace, get details of a policy, or get all applicable policies).

    Args:
        catalog_name: The catalog name (used as the REST prefix)
        operation: 'list' to list policies under a namespace, 'get' to load a policy, 'get_applicable' to load applicable policies.
        namespace: Namespace containing the policy or target (required for 'list', 'get', and target-specific 'get_applicable').
        policy_name: Name of the policy (required for 'get').
        target_name: Optional table or view name (only for 'get_applicable').
        policy_type: Optional filter by policy type (for 'list' and 'get_applicable').
        page_token: Optional pagination token from a previous response (for 'list' and 'get_applicable').
        page_size: Optional maximum number of results to return (for 'list' and 'get_applicable').
    """
    if operation == "list":
        if not namespace:
            raise ValueError("namespace is required for 'list' operation")
        return await list_policies(
            catalog_name=catalog_name,
            namespace=namespace,
            policy_type=policy_type,
            page_token=page_token,
            page_size=page_size,
        )
    elif operation == "get":
        if not namespace or not policy_name:
            raise ValueError("namespace and policy_name are required for 'get' operation")
        return await load_policy(
            catalog_name=catalog_name,
            namespace=namespace,
            policy_name=policy_name,
        )
    elif operation == "get_applicable":
        return await get_applicable_policies(
            catalog_name=catalog_name,
            namespace=namespace,
            target_name=target_name,
            policy_type=policy_type,
            page_token=page_token,
            page_size=page_size,
        )
    else:
        raise ValueError(f"Unsupported operation: {operation}")
