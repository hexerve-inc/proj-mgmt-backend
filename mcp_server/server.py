from fastmcp import FastMCP
from mcp_server.config import mcp_settings

# Initialize FastMCP with OAuth 2.1 PKCE configuration
mcp = FastMCP(
    name=mcp_settings.MCP_NAME,
    instructions=mcp_settings.MCP_INSTRUCTIONS,
)

# Phase 1 & 2: Register read-only tools
from mcp_server.tools.project_tools import register_project_tools
from mcp_server.tools.task_tools import register_task_tools
from mcp_server.tools.sprint_tools import register_sprint_tools
from mcp_server.tools.team_tools import register_team_tools
from mcp_server.tools.user_tools import register_user_tools
from mcp_server.tools.time_entry_tools import register_time_entry_tools
from mcp_server.tools.analytics_tools import register_analytics_tools
from mcp_server.tools.client_tools import register_client_tools
from mcp_server.tools.portfolio_tools import register_portfolio_tools
from mcp_server.tools.program_tools import register_program_tools
from mcp_server.tools.invoice_tools import register_invoice_tools
from mcp_server.tools.workflow_status_tools import register_workflow_status_tools
from mcp_server.tools.task_attachment_tools import register_task_attachment_tools

register_project_tools(mcp)
register_task_tools(mcp)
register_sprint_tools(mcp)
register_team_tools(mcp)
register_user_tools(mcp)
register_time_entry_tools(mcp)
register_analytics_tools(mcp)
register_client_tools(mcp)
register_portfolio_tools(mcp)
register_program_tools(mcp)
register_invoice_tools(mcp)
register_workflow_status_tools(mcp)
register_task_attachment_tools(mcp)

# Phase 1: Register read-only resources
from mcp_server.resources.project_resources import register_project_resources
from mcp_server.resources.task_resources import register_task_resources

register_project_resources(mcp)
register_task_resources(mcp)

# Health Check Route
from starlette.requests import Request
from starlette.responses import JSONResponse
from mcp_server.api_client import get_client

@mcp.custom_route("/", methods=["GET"])
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Verifies that the MCP server is running and can connect to the PM Tool backend."""
    client = get_client()
    try:
        # We ping the projects endpoint to ensure the API token and URL are valid
        await client.get_projects()
        return JSONResponse({
            "status": "online",
            "mcp_server": "running",
            "pmtool_backend_connection": "successful",
            "message": "PM Tool MCP Server is healthy and connected to the backend!"
        })
    except Exception as e:
        return JSONResponse({
            "status": "degraded",
            "mcp_server": "running",
            "pmtool_backend_connection": "failed",
            "error": str(e),
            "message": "MCP Server is running, but failed to connect to the PM Tool backend. Check PMTOOL_API_BASE_URL and PMTOOL_API_TOKEN."
        }, status_code=503)

if __name__ == "__main__":
    if mcp_settings.MCP_TRANSPORT in ["http", "sse"]:
        mcp.run(transport=mcp_settings.MCP_TRANSPORT, host=mcp_settings.MCP_HOST, port=mcp_settings.PORT)
    else:
        mcp.run(transport=mcp_settings.MCP_TRANSPORT)
