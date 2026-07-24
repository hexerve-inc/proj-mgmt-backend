import json
from typing import Optional
from mcp_server.api_client import get_client

def register_program_tools(mcp):
    @mcp.tool()
    async def list_programs() -> str:
        """List all programs.
        
        Returns:
            JSON string containing a list of programs.
        """
        client = get_client()
        try:
            programs = await client.get_programs()
            return json.dumps(programs, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_program(program_id: str) -> str:
        """Get full details of a specific program.
        
        Args:
            program_id: The UUID of the program.
            
        Returns:
            JSON string with program details.
        """
        client = get_client()
        try:
            program = await client.get_program(program_id)
            return json.dumps(program, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def create_program(name: str, description: Optional[str] = None) -> str:
        """Create a new program.
        
        Args:
            name: Program name.
            description: Optional program description.
            
        Returns:
            JSON string with created program details.
        """
        client = get_client()
        try:
            data = {"name": name}
            if description: data["description"] = description
            program = await client.create_program(data)
            return json.dumps(program, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
