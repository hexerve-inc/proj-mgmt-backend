from typing import Optional, List, Dict, Any
import json
from mcp_server.api_client import get_client
from mcp_server.tools.utils import resolve_project_id

def register_project_tools(mcp):
    @mcp.tool()
    async def list_projects() -> str:
        """List all projects in the PM Tool.
        
        Use this tool to view the overall project portfolio, including status and progress.
        
        Returns:
            JSON string containing a list of projects.
        """
        client = get_client()
        try:
            projects = await client.get_projects()
            return json.dumps(projects, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_project(project_id: str) -> str:
        """Get detailed information for a specific project.
        
        Use this tool when you need full details about a single project.
        
        Args:
            project_id: The UUID of the project. If you only know the project name, you MUST call list_projects first to find its UUID.
            
        Returns:
            JSON string with project details.
        """
        client = get_client()
        try:
            project_id = await resolve_project_id(client, project_id)
            project = await client.get_project(project_id)
            return json.dumps(project, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def create_project(name: str, project_key: str, description: Optional[str] = None, client_id: Optional[str] = None) -> str:
        """Create a new project.
        
        Args:
            name: Name of the project.
            project_key: Short key for the project (e.g., PROJ).
            description: Optional description.
            client_id: Optional UUID of a client.
            
        Returns:
            JSON string with created project details.
        """
        client = get_client()
        try:
            data = {"name": name, "project_key": project_key}
            if description: data["description"] = description
            if client_id: data["client_id"] = client_id
            
            project = await client.create_project(data)
            return json.dumps(project, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def update_project(project_id: str, name: Optional[str] = None, description: Optional[str] = None, status: Optional[str] = None, progress: Optional[int] = None) -> str:
        """Update an existing project.
        
        Args:
            project_id: The UUID of the project. If you only know the project name, you MUST call list_projects first to find its UUID.
            name: Optional new name.
            description: Optional new description.
            status: Optional new status (e.g. ACTIVE, COMPLETED).
            progress: Optional new progress percentage (0-100).
            
        Returns:
            JSON string with updated project details.
        """
        client = get_client()
        try:
            project_id = await resolve_project_id(client, project_id)
            data = {}
            if name: data["name"] = name
            if description: data["description"] = description
            if status: data["status"] = status
            if progress is not None: data["progress"] = progress
            
            project = await client.update_project(project_id, data)
            return json.dumps(project, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def delete_project(project_id: str) -> str:
        """Delete a project (soft delete).
        
        Args:
            project_id: The UUID of the project. If you only know the project name, you MUST call list_projects first to find its UUID.
            
        Returns:
            JSON string with success message.
        """
        client = get_client()
        try:
            project_id = await resolve_project_id(client, project_id)
            result = await client.delete_project(project_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
