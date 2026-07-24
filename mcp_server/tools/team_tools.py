from typing import Optional, List, Dict, Any
import json
from mcp_server.api_client import get_client

def register_team_tools(mcp):
    @mcp.tool()
    async def list_teams() -> str:
        """List all teams.
        
        Use this tool to view all teams across the organization.
        
        Returns:
            JSON string containing a list of teams.
        """
        client = get_client()
        try:
            teams = await client.get_teams()
            return json.dumps(teams, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_team(team_id: str) -> str:
        """Get full details of a specific team, including its members.
        
        Args:
            team_id: The UUID of the team.
            
        Returns:
            JSON string with team details.
        """
        client = get_client()
        try:
            team = await client.get_team(team_id)
            return json.dumps(team, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def create_team(name: str, description: Optional[str] = None) -> str:
        """Create a new team.
        
        Args:
            name: Name of the team.
            description: Optional team description.
            
        Returns:
            JSON string with created team details.
        """
        client = get_client()
        try:
            data = {"name": name}
            if description: data["description"] = description
            
            team = await client.create_team(data)
            return json.dumps(team, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def update_team(team_id: str, name: Optional[str] = None, description: Optional[str] = None) -> str:
        """Update a team's details.
        
        Args:
            team_id: The UUID of the team.
            name: Optional new name.
            description: Optional new description.
            
        Returns:
            JSON string with updated team details.
        """
        client = get_client()
        try:
            data = {}
            if name: data["name"] = name
            if description: data["description"] = description
            
            team = await client.update_team(team_id, data)
            return json.dumps(team, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def add_team_member(team_id: str, user_id: str) -> str:
        """Add a user to a team.
        
        Args:
            team_id: The UUID of the team.
            user_id: The UUID of the user to add.
            
        Returns:
            JSON string with success message or updated team.
        """
        client = get_client()
        try:
            result = await client.add_team_member(team_id, user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def remove_team_member(team_id: str, user_id: str) -> str:
        """Remove a user from a team.
        
        Args:
            team_id: The UUID of the team.
            user_id: The UUID of the user to remove.
            
        Returns:
            JSON string with success message.
        """
        client = get_client()
        try:
            result = await client.remove_team_member(team_id, user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
