import json
from typing import Optional
from mcp_server.api_client import get_client
from mcp_server.tools.utils import resolve_project_id

def register_task_tools(mcp):
    @mcp.tool()
    async def list_tasks(project_id: Optional[str] = None) -> str:
        """List tasks, optionally filtered by project.
        
        Use this tool to view the backlog or current tasks.
        
        Args:
            project_id: Optional UUID of a project to filter tasks by. If you only know the project name, you MUST call list_projects first to find its UUID. Do NOT pass a project name here.
            
        Returns:
            JSON string containing a list of tasks.
        """
        client = get_client()
        try:
            if project_id:
                project_id = await resolve_project_id(client, project_id)
            tasks = await client.get_tasks(project_id=project_id)
            return json.dumps(tasks, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_task(task_id: str) -> str:
        """Get full details of a specific task.
        
        Use this tool when you need comprehensive details about a single task,
        including its description, assignee, status, and watchers.
        
        Args:
            task_id: The UUID of the task.
            
        Returns:
            JSON string with task details.
        """
        client = get_client()
        try:
            task = await client.get_task(task_id)
            return json.dumps(task, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def create_task(project_id: str, title: str, description: Optional[str] = None, priority: Optional[str] = None, assignee_id: Optional[str] = None) -> str:
        """Create a new task.
        
        Args:
            project_id: The UUID of the project. If you only know the project name, you MUST call list_projects first to find its UUID. Do NOT pass a project name here.
            title: Task title.
            description: Optional task description.
            priority: Optional priority (LOW, MEDIUM, HIGH, URGENT).
            assignee_id: Optional user UUID.
            
        Returns:
            JSON string with created task details.
        """
        client = get_client()
        try:
            project_id = await resolve_project_id(client, project_id)
            data = {"project_id": project_id, "title": title}
            if description: data["description"] = description
            if priority: data["priority"] = priority
            if assignee_id: data["assignee_id"] = assignee_id
            
            task = await client.create_task(data)
            return json.dumps(task, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def update_task(task_id: str, title: Optional[str] = None, description: Optional[str] = None, priority: Optional[str] = None) -> str:
        """Update a task's details.
        
        Args:
            task_id: The UUID of the task.
            title: Optional new title.
            description: Optional new description.
            priority: Optional new priority.
            
        Returns:
            JSON string with updated task details.
        """
        client = get_client()
        try:
            data = {}
            if title: data["title"] = title
            if description: data["description"] = description
            if priority: data["priority"] = priority
            
            task = await client.update_task(task_id, data)
            return json.dumps(task, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def delete_task(task_id: str) -> str:
        """Delete a task (soft delete).
        
        Args:
            task_id: The UUID of the task.
            
        Returns:
            JSON string with success message.
        """
        client = get_client()
        try:
            result = await client.delete_task(task_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def change_task_status(task_id: str, status_id: str) -> str:
        """Change a task's workflow status.
        
        Args:
            task_id: The UUID of the task.
            status_id: The UUID of the new workflow status.
            
        Returns:
            JSON string with updated task details.
        """
        client = get_client()
        try:
            task = await client.change_task_status(task_id, status_id)
            return json.dumps(task, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def assign_task(task_id: str, assignee_id: str) -> str:
        """Assign a task to a user.
        
        Args:
            task_id: The UUID of the task.
            assignee_id: The UUID of the user.
            
        Returns:
            JSON string with updated task details.
        """
        client = get_client()
        try:
            task = await client.assign_task(task_id, assignee_id)
            return json.dumps(task, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
