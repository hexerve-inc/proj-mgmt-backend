import json
from mcp_server.api_client import get_client

def register_sprint_resources(mcp):
    @mcp.resource("pmtool://sprints")
    async def get_sprints_resource() -> str:
        """Resource providing a list of all sprints."""
        client = get_client()
        try:
            sprints = await client.get_sprints()
            return json.dumps(sprints, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("pmtool://sprints/{sprint_id}")
    async def get_sprint_resource(sprint_id: str) -> str:
        """Resource providing details for a specific sprint."""
        client = get_client()
        try:
            sprint = await client.get_sprint(sprint_id)
            return json.dumps(sprint, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
