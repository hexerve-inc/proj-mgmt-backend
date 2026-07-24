import json
from typing import Optional
from mcp_server.api_client import get_client
from mcp_server.tools.utils import resolve_project_id

def register_sprint_tools(mcp):
    @mcp.tool()
    async def list_sprints(project_id: Optional[str] = None) -> str:
        """List sprints, optionally filtered by project.
        
        Use this tool to view the active, upcoming, or completed sprints.
        
        Args:
            project_id: Optional UUID of a project to filter sprints by. If you only know the project name, you MUST call list_projects first to find its UUID.
            
        Returns:
            JSON string containing a list of sprints.
        """
        client = get_client()
        try:
            if project_id:
                project_id = await resolve_project_id(client, project_id)
            sprints = await client.get_sprints(project_id=project_id)
            return json.dumps(sprints, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_sprint(sprint_id: str) -> str:
        """Get full details of a specific sprint.
        
        Args:
            sprint_id: The UUID of the sprint.
            
        Returns:
            JSON string with sprint details.
        """
        client = get_client()
        try:
            sprint = await client.get_sprint(sprint_id)
            return json.dumps(sprint, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def create_sprint(name: str, project_id: str, goal: Optional[str] = None) -> str:
        """Create a new sprint.
        
        Args:
            name: Sprint name.
            project_id: The UUID of the project. If you only know the project name, you MUST call list_projects first to find its UUID.
            goal: Optional sprint goal.
            
        Returns:
            JSON string with created sprint details.
        """
        client = get_client()
        try:
            project_id = await resolve_project_id(client, project_id)
            data = {"name": name, "project_id": project_id}
            if goal: data["goal"] = goal
            
            sprint = await client.create_sprint(data)
            return json.dumps(sprint, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def update_sprint(sprint_id: str, name: Optional[str] = None, goal: Optional[str] = None, status: Optional[str] = None) -> str:
        """Update a sprint's details.
        
        Args:
            sprint_id: The UUID of the sprint.
            name: Optional new name.
            goal: Optional new goal.
            status: Optional new status (PLANNED, ACTIVE, COMPLETED).
            
        Returns:
            JSON string with updated sprint details.
        """
        client = get_client()
        try:
            data = {}
            if name: data["name"] = name
            if goal: data["goal"] = goal
            if status: data["status"] = status
            
            sprint = await client.update_sprint(sprint_id, data)
            return json.dumps(sprint, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def delete_sprint(sprint_id: str) -> str:
        """Delete a sprint.
        
        Args:
            sprint_id: The UUID of the sprint.
            
        Returns:
            JSON string with success message.
        """
        client = get_client()
        try:
            result = await client.delete_sprint(sprint_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
