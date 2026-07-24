import json
from mcp_server.api_client import get_client

def register_team_resources(mcp):
    @mcp.resource("pmtool://teams")
    async def get_teams_resource() -> str:
        """Resource providing a list of all teams."""
        client = get_client()
        try:
            teams = await client.get_teams()
            return json.dumps(teams, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("pmtool://teams/{team_id}")
    async def get_team_resource(team_id: str) -> str:
        """Resource providing details for a specific team."""
        client = get_client()
        try:
            team = await client.get_team(team_id)
            return json.dumps(team, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
