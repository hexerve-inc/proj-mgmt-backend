import json
from mcp_server.api_client import get_client

def register_program_resources(mcp):
    @mcp.resource("pmtool://programs")
    async def get_programs_resource() -> str:
        """Resource providing a list of all programs."""
        client = get_client()
        try:
            programs = await client.get_programs()
            return json.dumps(programs, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("pmtool://programs/{program_id}")
    async def get_program_resource(program_id: str) -> str:
        """Resource providing details for a specific program."""
        client = get_client()
        try:
            program = await client.get_program(program_id)
            return json.dumps(program, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
