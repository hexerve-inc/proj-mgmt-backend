import json
from mcp_server.api_client import get_client

def register_task_attachment_tools(mcp):
    @mcp.tool()
    async def upload_attachment(task_id: str, file_path: str) -> str:
        """Upload a file as an attachment to a task.
        
        Args:
            task_id: The UUID of the task.
            file_path: The absolute path to the local file to upload.
            
        Returns:
            JSON string containing the attachment details (including URL).
        """
        client = get_client()
        try:
            attachment = await client.upload_task_attachment(task_id, file_path)
            return json.dumps(attachment, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def delete_attachment(task_id: str, attachment_id: str) -> str:
        """Delete an attachment from a task.
        
        Args:
            task_id: The UUID of the task.
            attachment_id: The UUID of the attachment.
            
        Returns:
            JSON string with success message.
        """
        client = get_client()
        try:
            result = await client.delete_task_attachment(task_id, attachment_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
