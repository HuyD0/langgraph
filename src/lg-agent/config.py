"""
Configuration for LangGraph MCP Agent

Update these settings to customize your agent's behavior and MCP server connections.
"""

from databricks.sdk import WorkspaceClient

###############################################################################
## LLM Configuration
###############################################################################

# TODO: Replace with your model serving endpoint
LLM_ENDPOINT_NAME = "databricks-claude-3-7-sonnet"

# TODO: Update with your system prompt
SYSTEM_PROMPT = "You are a helpful assistant that can run Python code."


###############################################################################
## MCP Server Configuration
##
## This section sets up server connections so your agent can retrieve data or take actions.
##
## There are three connection types:
## 1. Managed MCP servers — fully managed by Databricks (no setup required)
## 2. External MCP servers — hosted outside Databricks but proxied through a
##    Managed MCP server proxy (some setup required)
## 3. Custom MCP servers — MCP servers hosted as Databricks Apps (OAuth setup required)
##
## Note: External MCP servers get added to the "managed" URL list
## because their proxy endpoints are managed by Databricks.
###############################################################################

# Initialize workspace client
workspace_client = WorkspaceClient()
host = workspace_client.config.host

# ---------------------------------------------------------------------------
# Managed MCP Server — simplest setup
# ---------------------------------------------------------------------------
# Databricks manages this connection automatically using your workspace settings
# and Personal Access Token (PAT) authentication.

# Managed MCP Servers URLS (includes both fully managed and proxied external MCP)
# - If you're using an external MCP server, create a UC connection and flag it
#   as an MCP connection. This reveals a proxy endpoint.
# - Add that proxy endpoint URL to this list.

MANAGED_MCP_SERVER_URLS = [
    f"{host}/api/2.0/mcp/functions/system/ai",  # Default managed MCP endpoint
    # Example for external MCP:
    # "https://<workspace-hostname>/api/2.0/mcp/external/{connection_name}"
]

# ---------------------------------------------------------------------------
# Custom MCP Server — hosted as a Databricks App
# ---------------------------------------------------------------------------
# Use this if you're running your own MCP server in Databricks.
# These require OAuth with a service principal for machine-to-machine (M2M) auth.
#
# Uncomment and fill in the settings below to use a custom MCP server.
#
# import os
# workspace_client = WorkspaceClient(
#     host="<DATABRICKS_WORKSPACE_URL>",
#     client_id=os.getenv("DATABRICKS_CLIENT_ID"),
#     client_secret=os.getenv("DATABRICKS_CLIENT_SECRET"),
#     auth_type="oauth-m2m",  # Enables service principal authentication
# )

# Custom MCP Servers — add URLs below (not managed or proxied by Databricks)
CUSTOM_MCP_SERVER_URLS = [
    # Example: "https://<custom-mcp-app-url>/mcp"
]


###############################################################################
## OAuth Configuration (for Custom MCP Servers)
###############################################################################
# TODO: ONLY UNCOMMENT AND EDIT THIS SECTION IF YOU ARE USING OAUTH/SERVICE
#       PRINCIPAL FOR CUSTOM MCP SERVERS.
#       For managed MCP (the default), LEAVE THIS SECTION COMMENTED OUT.

# import os
# 
# # Set your Databricks client ID and client secret for service principal authentication.
# DATABRICKS_CLIENT_ID = "<YOUR_CLIENT_ID>"
# client_secret_scope_name = "<YOUR_SECRET_SCOPE>"
# client_secret_key_name = "<YOUR_SECRET_KEY_NAME>"
# 
# # Load your service principal credentials into environment variables
# os.environ["DATABRICKS_CLIENT_ID"] = DATABRICKS_CLIENT_ID
# # For local testing:
# # os.environ["DATABRICKS_CLIENT_SECRET"] = "<your_secret>"
# # For production (using Databricks secrets):
# from dbutils import dbutils
# os.environ["DATABRICKS_CLIENT_SECRET"] = dbutils.secrets.get(
#     scope=client_secret_scope_name, 
#     key=client_secret_key_name
# )
