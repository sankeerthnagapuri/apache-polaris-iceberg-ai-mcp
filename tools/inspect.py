import os
from typing import Literal
from pyiceberg.catalog import load_catalog
from client import polaris_client

def _get_pyiceberg_catalog(
    catalog_name: str,
    s3_endpoint: str | None = None,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
):
    """Instantiate a PyIceberg Catalog using the active connection token and configuration."""
    if not polaris_client.is_connected:
        raise ConnectionError("Not connected to Polaris. Use 'connect' first.")
    
    properties = {
        "type": "rest",
        "uri": polaris_client.catalog_url,
        "token": polaris_client._token,
        "warehouse": catalog_name,
        "header.X-Iceberg-Access-Delegation": "none",
    }

    
    # Resolve S3 Endpoint
    endpoint = s3_endpoint or os.getenv("S3_ENDPOINT") or "http://localhost:9000"
    properties["s3.endpoint"] = endpoint
    
    # Resolve AWS Credentials
    key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID") or "admin"
    secret_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY") or "password"

    properties["s3.access-key-id"] = key_id
    properties["s3.secret-access-key"] = secret_key
    
    # Ensure path style access is enabled for MinIO/local setups
    properties["s3.path-style-access"] = "true"
    
    return load_catalog(catalog_name, **properties)


def _make_json_serializable(obj):
    """Recursively convert PyArrow/binary/bytes/datetime objects to JSON-serializable types."""
    if obj is None:
        return None
        
    # Check if bytes-like
    if isinstance(obj, (bytes, bytearray, memoryview)):
        try:
            return obj.decode("utf-8")
        except Exception:
            return f"hex:{obj.hex() if hasattr(obj, 'hex') else bytes(obj).hex()}"
            
    # Check for lists, tuples, sets
    if isinstance(obj, (list, tuple, set)):
        return [_make_json_serializable(x) for x in obj]
        
    # Check for dicts/maps
    if isinstance(obj, dict):
        return {str(k): _make_json_serializable(v) for k, v in obj.items()}
        
    # Check for datetime/date
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
        
    # Check if it's a numeric or string primitive
    if isinstance(obj, (int, float, str, bool)):
        return obj
        
    # Check if it's a PyArrow scalar or any other custom type
    name = type(obj).__name__
    if "Scalar" in name:
        try:
            return _make_json_serializable(obj.as_py())
        except Exception:
            pass
        
    # As a last resort, if we cannot serialize it, stringify it
    try:
        import json
        json.dumps(obj)
        return obj
    except Exception:
        try:
            return f"hex:{bytes(obj).hex()}"
        except Exception:
            return str(obj)



async def inspect_snapshots(
    catalog_name: str,
    namespace: str,
    table: str,
    s3_endpoint: str | None = None,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> list[dict]:
    """
    Inspect the snapshot history of a table.
    
    Args:
        catalog_name: Name of the catalog
        namespace: Namespace containing the table
        table: Name of the table
        s3_endpoint: Optional S3/MinIO endpoint override (defaults to S3_ENDPOINT env var or http://localhost:9000)
        aws_access_key_id: Optional AWS access key override
        aws_secret_access_key: Optional AWS secret key override
    """
    catalog = _get_pyiceberg_catalog(
        catalog_name, s3_endpoint, aws_access_key_id, aws_secret_access_key
    )
    tbl = catalog.load_table(f"{namespace}.{table}")
    snapshots_table = tbl.inspect.snapshots()
    return _make_json_serializable(snapshots_table.to_pylist())

async def inspect_files(
    catalog_name: str,
    namespace: str,
    table: str,
    s3_endpoint: str | None = None,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> list[dict]:
    """
    Inspect all active data and delete files in a table.
    
    Args:
        catalog_name: Name of the catalog
        namespace: Namespace containing the table
        table: Name of the table
        s3_endpoint: Optional S3/MinIO endpoint override
        aws_access_key_id: Optional AWS access key override
        aws_secret_access_key: Optional AWS secret key override
    """
    catalog = _get_pyiceberg_catalog(
        catalog_name, s3_endpoint, aws_access_key_id, aws_secret_access_key
    )
    tbl = catalog.load_table(f"{namespace}.{table}")
    files_table = tbl.inspect.files()
    return _make_json_serializable(files_table.to_pylist())

async def inspect_manifests(
    catalog_name: str,
    namespace: str,
    table: str,
    s3_endpoint: str | None = None,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> list[dict]:
    """
    Inspect all manifest files of a table.
    
    Args:
        catalog_name: Name of the catalog
        namespace: Namespace containing the table
        table: Name of the table
        s3_endpoint: Optional S3/MinIO endpoint override
        aws_access_key_id: Optional AWS access key override
        aws_secret_access_key: Optional AWS secret key override
    """
    catalog = _get_pyiceberg_catalog(
        catalog_name, s3_endpoint, aws_access_key_id, aws_secret_access_key
    )
    tbl = catalog.load_table(f"{namespace}.{table}")
    manifests_table = tbl.inspect.manifests()
    return _make_json_serializable(manifests_table.to_pylist())

async def inspect_partitions(
    catalog_name: str,
    namespace: str,
    table: str,
    s3_endpoint: str | None = None,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> list[dict]:
    """
    Inspect the partitions of a table.
    
    Args:
        catalog_name: Name of the catalog
        namespace: Namespace containing the table
        table: Name of the table
        s3_endpoint: Optional S3/MinIO endpoint override
        aws_access_key_id: Optional AWS access key override
        aws_secret_access_key: Optional AWS secret key override
    """
    catalog = _get_pyiceberg_catalog(
        catalog_name, s3_endpoint, aws_access_key_id, aws_secret_access_key
    )
    tbl = catalog.load_table(f"{namespace}.{table}")
    partitions_table = tbl.inspect.partitions()
    return _make_json_serializable(partitions_table.to_pylist())


async def inspect_table_health(
    catalog_name: str,
    namespace: str,
    table: str,
    s3_endpoint: str | None = None,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> dict:
    """
    Perform a comprehensive health check on a table and return recommendations for maintenance.
    
    Args:
        catalog_name: Name of the catalog
        namespace: Namespace containing the table
        table: Name of the table
        s3_endpoint: Optional S3/MinIO endpoint override
        aws_access_key_id: Optional AWS access key override
        aws_secret_access_key: Optional AWS secret key override
    """
    catalog = _get_pyiceberg_catalog(
        catalog_name, s3_endpoint, aws_access_key_id, aws_secret_access_key
    )
    tbl = catalog.load_table(f"{namespace}.{table}")
    
    # 1. Analyze snapshots
    snapshots = tbl.metadata.snapshots or []
    num_snapshots = len(snapshots)
    
    # 2. Analyze manifests
    manifests_table = tbl.inspect.manifests()
    manifests = manifests_table.to_pylist()
    num_manifests = len(manifests)
    
    # 3. Analyze data & delete files
    files_table = tbl.inspect.files()
    files = files_table.to_pylist()
    
    data_files = [f for f in files if f.get("content") == 0]
    delete_files = [f for f in files if f.get("content") == 1]
    
    num_data_files = len(data_files)
    num_delete_files = len(delete_files)
    
    total_data_records = sum(f.get("record_count", 0) for f in data_files)
    total_delete_records = sum(f.get("record_count", 0) for f in delete_files)
    
    # Calculate average file size
    avg_data_file_size_mb = 0
    if num_data_files > 0:
        total_data_size = sum(f.get("file_size_in_bytes", 0) for f in data_files)
        avg_data_file_size_mb = total_data_size / (1024 * 1024) / num_data_files
        
    # Generate recommendations
    recommendations = []
    issues = []
    
    if num_snapshots > 10:
        issues.append(f"High snapshot count ({num_snapshots} snapshots)")
        recommendations.append(
            f"⚠️ Run snapshot expiration to prune historical metadata. Recommended threshold exceeded (current: {num_snapshots}, max recommended: 10)."
        )
        
    if num_delete_files > 0:
        ratio = num_delete_files / (num_data_files + num_delete_files) if (num_data_files + num_delete_files) > 0 else 0
        issues.append(f"Table contains active delete files ({num_delete_files} delete files)")
        recommendations.append(
            f"⚠️ Run data file compaction (rewrite_data_files) to merge the delete files (Merge-on-Read overhead: {ratio:.1%} of files are deletes; total deleted records: {total_delete_records})."
        )
        
    if num_data_files > 5 and avg_data_file_size_mb < 10:
        issues.append(f"Table consists of many small files (average size: {avg_data_file_size_mb:.2f} MB)")
        recommendations.append(
            f"⚠️ Run data file compaction to merge tiny Parquet files into larger, more optimal ones (target size is typically 128MB to 512MB)."
        )
        
    if num_manifests > 15:
        issues.append(f"High manifest count ({num_manifests} manifests)")
        recommendations.append(
            f"⚠️ Run manifest rewriting (rewrite_manifests) to consolidate manifest files and speed up planning."
        )
        
    if not recommendations:
        recommendations.append("✅ Table is in optimal health! No maintenance required.")
        
    report = {
        "table_name": f"{namespace}.{table}",
        "metadata_location": tbl.metadata_location,
        "format_version": tbl.metadata.format_version,
        "summary": {
            "num_snapshots": num_snapshots,
            "num_manifests": num_manifests,
            "num_data_files": num_data_files,
            "num_delete_files": num_delete_files,
            "total_data_records": total_data_records,
            "total_delete_records": total_delete_records,
            "avg_data_file_size_mb": round(avg_data_file_size_mb, 2),
        },
        "issues_detected": issues,
        "recommendations": recommendations,
    }
    
    return _make_json_serializable(report)


async def inspect_request(
    catalog_name: str,
    namespace: str,
    table: str,
    operation: Literal["snapshots", "files", "manifests", "partitions", "health"],
    s3_endpoint: str | None = None,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> list[dict] | dict:
    """
    Perform low-level PyIceberg inspections on a table (view snapshots, active files, manifests, partitions, or table health).

    Args:
        catalog_name: Name of the catalog
        namespace: Namespace containing the table
        table: Name of the table
        operation: 'snapshots' to view historical snapshots, 'files' to view active files, 'manifests' to view manifest files, 'partitions' to view partition layout, 'health' to perform a health check.
        s3_endpoint: Optional S3/MinIO endpoint override (defaults to S3_ENDPOINT env var or http://localhost:9000)
        aws_access_key_id: Optional AWS access key override
        aws_secret_access_key: Optional AWS secret key override
    """
    if operation == "snapshots":
        return await inspect_snapshots(
            catalog_name=catalog_name,
            namespace=namespace,
            table=table,
            s3_endpoint=s3_endpoint,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
    elif operation == "files":
        return await inspect_files(
            catalog_name=catalog_name,
            namespace=namespace,
            table=table,
            s3_endpoint=s3_endpoint,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
    elif operation == "manifests":
        return await inspect_manifests(
            catalog_name=catalog_name,
            namespace=namespace,
            table=table,
            s3_endpoint=s3_endpoint,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
    elif operation == "partitions":
        return await inspect_partitions(
            catalog_name=catalog_name,
            namespace=namespace,
            table=table,
            s3_endpoint=s3_endpoint,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
    elif operation == "health":
        return await inspect_table_health(
            catalog_name=catalog_name,
            namespace=namespace,
            table=table,
            s3_endpoint=s3_endpoint,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
    else:
        raise ValueError(f"Unsupported operation: {operation}")


