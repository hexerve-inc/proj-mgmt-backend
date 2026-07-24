import json
from typing import Optional
from mcp_server.api_client import get_client

def register_time_entry_tools(mcp):
    @mcp.tool()
    async def list_time_entries(task_id: Optional[str] = None) -> str:
        """List time entries, optionally filtered by task.
        
        Use this tool to view logged time across tasks or for a specific task.
        
        Args:
            task_id: Optional UUID of a task to filter by.
            
        Returns:
            JSON string containing a list of time entries.
        """
        client = get_client()
        try:
            entries = await client.get_time_entries(task_id=task_id)
            return json.dumps(entries, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def start_timer(task_id: str, description: Optional[str] = None) -> str:
        """Start a time tracking timer on a task.
        
        Args:
            task_id: The UUID of the task.
            description: Optional description of the work being done.
            
        Returns:
            JSON string with the running time entry.
        """
        client = get_client()
        try:
            data = {"task_id": task_id}
            if description: data["description"] = description
            
            entry = await client.start_timer(data)
            return json.dumps(entry, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def stop_timer(description: Optional[str] = None) -> str:
        """Stop the currently running timer.
        
        Args:
            description: Optional updated description of the work done.
            
        Returns:
            JSON string with the stopped time entry and computed duration.
        """
        client = get_client()
        try:
            data = {}
            if description: data["description"] = description
            
            entry = await client.stop_timer(data)
            return json.dumps(entry, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def log_time(task_id: str, duration: int, description: Optional[str] = None) -> str:
        """Manually log time spent on a task.
        
        Args:
            task_id: The UUID of the task.
            duration: Duration in minutes.
            description: Optional description of the work done.
            
        Returns:
            JSON string with the created time entry.
        """
        client = get_client()
        try:
            data = {"task_id": task_id, "duration": duration}
            if description: data["description"] = description
            
            entry = await client.log_time(data)
            return json.dumps(entry, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
