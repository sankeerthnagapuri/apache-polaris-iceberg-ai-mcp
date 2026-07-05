# Polaris Catalog & Iceberg Governance MCP Server

A [FastMCP](https://github.com/jlowin/fastmcp) server that gives AI assistants (and data engineers) conversational access to **Apache Polaris** catalog management, **Iceberg REST Catalog** APIs, and **PyIceberg** table storage/health inspection tools. 

It is designed to enable AI agents (like Cursor, Windsurf, or Claude Desktop) to audit data governance, check access control roles, query namespaces, and inspect Iceberg metadata.

---

## What it does

**12 tools** across 10 categories:

| Category | Tool Name | Operations | What you can ask |
|----------|-----------|------------|-----------------|
| **Connection** | `connect` | N/A | "Connect to Polaris" |
| | `disconnect` | N/A | "Disconnect from the Polaris server" |
| | `get_server_config` | N/A | "What endpoints does the server support?" |
| **Catalogs** | `catalog_request` | `list`, `get` | "What catalogs exist?", "Show me the storage config for catalog X" |
| **Namespaces** | `namespace_request` | `list`, `get`, `exists` | "List all namespaces in catalog X", "Does namespace Y exist?" |
| **Tables** | `table_request` | `list`, `get`, `exists` | "List tables in prod.analytics", "Show me the schema and snapshots for table Z" |
| **Views** | `view_request` | `list`, `get`, `exists` | "List views", "Load the revenue_daily view metadata" |
| **Principals** | `principal_request` | `list`, `get`, `roles_assigned` | "Who has access?", "What roles does Alice have?" |
| **Roles & Grants** | `role_request` | `list_principal_roles`, `get_principal_role`, `list_principals_for_role`, `list_catalog_roles`, `get_catalog_role`, `list_catalog_roles_for_principal_role`, `list_principal_roles_for_catalog_role`, `list_grants_for_catalog_role` | "What roles exist?", "Which catalog roles map to service_admin?", "What privileges does the analyst role have?" |
| **Policies** | `policy_request` | `list`, `get`, `get_applicable` | "What policies apply to this table?", "Show the compaction policy" |
| **Generic Tables** | `generic_table_request` | `list`, `get` | "What Delta/CSV tables are registered?" |
| **Metadata Inspection** | `inspect_request` | `snapshots`, `files`, `manifests`, `partitions`, `health` | "Check snapshot history", "List raw Parquet data/delete files", "Show partition health/delete file overhead" |

---

## Quick Start

### Install

```bash
cd apache-polaris-iceberg-ai-mcp
pip install -e .
```

### Run the server

```bash
# Via FastMCP CLI
fastmcp run server.py

# Or directly
python -m server
```

### Configure in Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "polaris-catalog": {
      "command": "fastmcp",
      "args": ["run", "/path/to/apache-polaris-iceberg-ai-mcp/server.py"]
    }
  }
}
```

### Configure in VS Code (Copilot / Cline / etc.)

Add to your `.vscode/mcp.json` or MCP settings:

```json
{
  "servers": {
    "polaris-catalog": {
      "command": "fastmcp",
      "args": ["run", "/path/to/apache-polaris-iceberg-ai-mcp/server.py"]
    }
  }
}
```

---

## Authentication

The server supports three authentication modes via the `connect` tool:

### 1. Client Credentials (default)
```
connect(uri="http://localhost:8181", client_id="admin", client_secret="password")
```

### 2. Bearer Token
```
connect(uri="http://localhost:8181", token="eyJhbGciOiJSUzI1NiIs...")
```

### 3. Keycloak / OIDC Password Credentials
Use this to exchange username/password credentials for a token from Keycloak or another OIDC provider first, and then authenticate to Polaris with that token:
```
connect(
  uri="http://localhost:8181",
  oauth_token_url="http://localhost:8080/realms/polaris-realm/protocol/openid-connect/token",
  client_id="polaris-client",
  client_secret="sBbUvTG7qWGbmgwgxKmnEuzqpuE3uGAu",
  username="sankeerth",
  password="nagapuri"
)
```

---

## Storage & Inspection Configuration

Since the `inspect_request` tool reads the underlying Avro metadata and Parquet data/delete files directly from your object storage, you should configure your S3/MinIO environment variables or pass options dynamically.

### S3 / MinIO Environment Variables
By default, the inspection tools look for these environment variables or fallback to local MinIO dev defaults (`admin` / `password` / `http://localhost:9000`):
*   `S3_ENDPOINT`: S3 endpoint URL (e.g., `http://localhost:9000` or `https://s3.amazonaws.com`)
*   `AWS_ACCESS_KEY_ID`: Your AWS or MinIO access key
*   `AWS_SECRET_ACCESS_KEY`: Your AWS or MinIO secret key

### Override parameters
The `inspect_request` tool also accepts optional overrides:
*   `s3_endpoint`
*   `aws_access_key_id`
*   `aws_secret_access_key`

---

## Architecture

```
apache-polaris-iceberg-ai-mcp/
├── server.py              # FastMCP server — registers consolidated tools
├── client.py              # Async HTTP client (httpx) with OAuth2 + password grant auth
├── requirements.txt       # Dependencies (fastmcp, httpx, pydantic, pyiceberg, pyarrow, s3fs)
└── tools/                 # Tool implementations by domain
    ├── connection.py      # connect, disconnect, get_server_config
    ├── catalogs.py        # catalog_request (list, get)
    ├── principals.py      # principal_request (list, get, roles_assigned)
    ├── roles.py           # role_request (principal/catalog roles, mapping, grants)
    ├── namespaces.py      # namespace_request (list, get, exists)
    ├── tables.py          # table_request (list, get, exists)
    ├── views.py           # view_request (list, get, exists)
    ├── policies.py        # policy_request (list, get, get_applicable)
    ├── generic_tables.py  # generic_table_request (list, get)
    └── inspect.py         # inspect_request (snapshots, files, manifests, partitions, health)
```

---

## License

MIT License
