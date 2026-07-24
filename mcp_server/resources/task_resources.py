import json
from mcp_server.api_client import get_client

def register_task_resources(mcp):
    @mcp.resource("pmtool://tasks/{task_id}")
    async def get_task_resource(task_id: str) -> str:
        """Resource providing details for a specific task."""
        client = get_client()
        try:
            task = await client.get_task(task_id)
            return json.dumps(task, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("pmtool://projects/{project_id}/tasks")
    async def get_project_tasks_resource(project_id: str) -> str:
        """Resource providing all tasks for a specific project."""
        client = get_client()
        try:
            tasks = await client.get_tasks(project_id)
            return json.dumps(tasks, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
