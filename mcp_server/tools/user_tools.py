import json
from mcp_server.api_client import get_client

def register_user_tools(mcp):
    @mcp.tool()
    async def list_users() -> str:
        """List all users.
        
        Use this tool to view all users in the system.
        
        Returns:
            JSON string containing a list of users.
        """
        client = get_client()
        try:
            users = await client.get_users()
            return json.dumps(users, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_user(user_id: str) -> str:
        """Get details for a specific user.
        
        Args:
            user_id: The UUID of the user.
            
        Returns:
            JSON string with user details.
        """
        client = get_client()
        try:
            user = await client.get_user(user_id)
            return json.dumps(user, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
