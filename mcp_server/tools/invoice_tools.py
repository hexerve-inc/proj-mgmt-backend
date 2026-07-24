import json
from typing import Optional
from mcp_server.api_client import get_client

def register_invoice_tools(mcp):
    @mcp.tool()
    async def list_invoices() -> str:
        """List all invoices.
        
        Returns:
            JSON string containing a list of invoices.
        """
        client = get_client()
        try:
            invoices = await client.get_invoices()
            return json.dumps(invoices, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_invoice(invoice_id: str) -> str:
        """Get full details of a specific invoice.
        
        Args:
            invoice_id: The UUID of the invoice.
            
        Returns:
            JSON string with invoice details.
        """
        client = get_client()
        try:
            invoice = await client.get_invoice(invoice_id)
            return json.dumps(invoice, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def create_invoice(client_id: str, amount: float, description: str, due_date: Optional[str] = None) -> str:
        """Create a new invoice.
        
        Args:
            client_id: The UUID of the client.
            amount: The invoice amount.
            description: Description of the invoice.
            due_date: Optional due date (ISO 8601 string).
            
        Returns:
            JSON string with created invoice details.
        """
        client = get_client()
        try:
            data = {
                "client_id": client_id,
                "amount": amount,
                "description": description
            }
            if due_date: data["due_date"] = due_date
            
            invoice = await client.create_invoice(data)
            return json.dumps(invoice, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
