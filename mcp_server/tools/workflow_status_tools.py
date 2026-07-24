import json
from typing import Optional, List, Dict, Any
from mcp_server.api_client import get_client
from mcp_server.tools.utils import resolve_project_id

def register_workflow_status_tools(mcp):
    @mcp.tool()
    async def list_project_statuses(project_id: str) -> str:
        """List all workflow statuses for a project.
        
        Args:
            project_id: The UUID of the project. If you only know the project name, you MUST call list_projects first to find its UUID.
            
        Returns:
            JSON string containing a list of workflow statuses.
        """
        client = get_client()
        try:
            project_id = await resolve_project_id(client, project_id)
            statuses = await client.get_project_statuses(project_id)
            return json.dumps(statuses, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def create_status(project_id: str, name: str, color: Optional[str] = None, icon: Optional[str] = None, group: Optional[str] = "todo") -> str:
        """Create a new custom status within a project.
        
        Args:
            project_id: The UUID of the project.
            name: Status name.
            color: Optional color hex code.
            icon: Optional icon name.
            group: Group category ('todo', 'in_progress', 'done').
            
        Returns:
            JSON string with created status details.
        """
        client = get_client()
        try:
            project_id = await resolve_project_id(client, project_id)
            data = {"name": name, "group": group}
            if color: data["color"] = color
            if icon: data["icon"] = icon
            
            status = await client.create_project_status(project_id, data)
            return json.dumps(status, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def update_status(project_id: str, status_id: str, name: Optional[str] = None, color: Optional[str] = None, icon: Optional[str] = None, group: Optional[str] = None) -> str:
        """Update an existing workflow status.
        
        Args:
            project_id: The UUID of the project.
            status_id: The UUID of the status.
            name: Optional new name.
            color: Optional new color.
            icon: Optional new icon.
            group: Optional new group.
            
        Returns:
            JSON string with updated status details.
        """
        client = get_client()
        try:
            project_id = await resolve_project_id(client, project_id)
            data = {}
            if name: data["name"] = name
            if color: data["color"] = color
            if icon: data["icon"] = icon
            if group: data["group"] = group
            
            status = await client.update_project_status(project_id, status_id, data)
            return json.dumps(status, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def delete_status(project_id: str, status_id: str, move_to_status_id: Optional[str] = None) -> str:
        """Delete a workflow status.
        
        Args:
            project_id: The UUID of the project.
            status_id: The UUID of the status.
            move_to_status_id: Required if tasks exist in the deleted status.
            
        Returns:
            JSON string with success message.
        """
        client = get_client()
        try:
            project_id = await resolve_project_id(client, project_id)
            result = await client.delete_project_status(project_id, status_id, move_to_status_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
