import json
from mcp_server.api_client import get_client

def register_client_resources(mcp):
    @mcp.resource("pmtool://clients")
    async def get_clients_resource() -> str:
        """Resource providing a list of all clients."""
        client = get_client()
        try:
            clients = await client.get_clients()
            return json.dumps(clients, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("pmtool://clients/{client_id}")
    async def get_client_resource(client_id: str) -> str:
        """Resource providing details for a specific client."""
        client = get_client()
        try:
            client_data = await client.get_client(client_id)
            return json.dumps(client_data, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
