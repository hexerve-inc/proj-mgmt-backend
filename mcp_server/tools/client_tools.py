from typing import Optional, List, Dict, Any
import json
from mcp_server.api_client import get_client

def register_client_tools(mcp):
    @mcp.tool()
    async def list_clients() -> str:
        """List all clients.
        
        Use this tool to view the list of clients and their details.
        
        Returns:
            JSON string containing a list of clients.
        """
        client = get_client()
        try:
            clients = await client.get_clients()
            return json.dumps(clients, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_client_details(client_id: str) -> str:
        """Get full details of a specific client.
        
        Args:
            client_id: The UUID of the client.
            
        Returns:
            JSON string with client details.
        """
        client = get_client()
        try:
            client_data = await client.get_client(client_id)
            return json.dumps(client_data, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def create_client(name: str, email: Optional[str] = None, phone: Optional[str] = None, company: Optional[str] = None) -> str:
        """Create a new client.
        
        Args:
            name: Name of the client.
            email: Optional email address.
            phone: Optional phone number.
            company: Optional company name.
            
        Returns:
            JSON string with created client details.
        """
        client = get_client()
        try:
            data = {"name": name}
            if email: data["email"] = email
            if phone: data["phone"] = phone
            if company: data["company"] = company
            
            client_data = await client.create_client(data)
            return json.dumps(client_data, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def update_client(client_id: str, name: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None, company: Optional[str] = None) -> str:
        """Update an existing client.
        
        Args:
            client_id: The UUID of the client.
            name: Optional new name.
            email: Optional new email address.
            phone: Optional new phone number.
            company: Optional new company name.
            
        Returns:
            JSON string with updated client details.
        """
        client = get_client()
        try:
            data = {}
            if name: data["name"] = name
            if email: data["email"] = email
            if phone: data["phone"] = phone
            if company: data["company"] = company
            
            client_data = await client.update_client(client_id, data)
            return json.dumps(client_data, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def delete_client(client_id: str) -> str:
        """Delete a client (soft delete).
        
        Args:
            client_id: The UUID of the client.
            
        Returns:
            JSON string with success message.
        """
        client = get_client()
        try:
            result = await client.delete_client(client_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
