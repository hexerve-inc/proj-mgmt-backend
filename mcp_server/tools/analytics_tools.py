import json
from typing import Optional
from mcp_server.api_client import get_client

def register_analytics_tools(mcp):
    @mcp.tool()
    async def get_analytics_summary() -> str:
        """Get high-level analytics summary.
        
        Use this tool to get an overview of system metrics (total users, projects, tasks, completion rates).
        
        Returns:
            JSON string containing the analytics summary.
        """
        client = get_client()
        try:
            summary = await client.get_analytics_summary()
            return json.dumps(summary, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_user_workload(project_id: Optional[str] = None) -> str:
        """Get active task count per user.
        
        Args:
            project_id: Optional project to filter workload by.
            
        Returns:
            JSON string containing workload details.
        """
        client = get_client()
        try:
            workload = await client.get_user_workload(project_id)
            return json.dumps(workload, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
