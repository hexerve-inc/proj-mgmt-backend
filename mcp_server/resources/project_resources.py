import json
from mcp_server.api_client import get_client

def register_project_resources(mcp):
    @mcp.resource("pmtool://projects")
    async def get_projects_resource() -> str:
        """Resource providing a list of all projects."""
        client = get_client()
        try:
            projects = await client.get_projects()
            return json.dumps(projects, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("pmtool://projects/{project_id}")
    async def get_project_resource(project_id: str) -> str:
        """Resource providing details for a specific project."""
        client = get_client()
        try:
            project = await client.get_project(project_id)
            return json.dumps(project, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
