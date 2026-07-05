---
name: connect_polaris_catalog
description: Guides the agent to ask the user for their preferred authentication mode and credentials when they request to connect to the Polaris catalog, rather than using default credentials.
---

# Connect to Polaris Catalog

When the user asks to connect to the Polaris catalog, you MUST NOT use the default authentication credentials automatically. Instead, follow these steps:

1. **Ask for Authentication Mode**: Use the `ask_question` tool to ask the user which authentication mode they want to use:
   - **Client Credentials (default)**: Requires Client ID, Client Secret, and Polaris URI.
   - **Bearer Token**: Requires a pre-existing OIDC/JWT Token and Polaris URI.
   - **OIDC Password Credentials**: Requires Token URL, Client ID, Client Secret, Username, Password, and Polaris URI.
2. **Collect Credentials (One by One)**: Once the user chooses their authentication mode, collect the required connection details **one value at a time** to avoid overwhelming them.
   - For each parameter, ask a single question or present a single input request, providing a reasonable default if available, and wait for the user's response before asking for the next value.
   - **Do NOT ask for all values in a single response.**
   - Parameters to collect:
     - For **Client Credentials**: `uri` (default: "http://localhost:8181"), then `client_id` (default: "admin"), then `client_secret` (default: "password").
     - For **Bearer Token**: `uri` (default: "http://localhost:8181"), then `token`.
     - For **OIDC Password Credentials**:
       - `uri` (default: "http://localhost:8181")
       - `oauth_token_url` (default: "http://localhost:8080/realms/polaris-realm/protocol/openid-connect/token")
       - `client_id` (default: "polaris-client")
       - `client_secret` (default: "sBbUvTG7qWGbmgwgxKmnEuzqpuE3uGAu")
       - `username` (default: "sankeerth")
       - `password` (type: "sensitive")
3. **Connect via MCP Tool**: Use the `polaris-catalog` MCP server's `connect` tool to execute the connection. Do not attempt to run python scripts or write code to connect; always use the MCP server tools for catalog operations.


