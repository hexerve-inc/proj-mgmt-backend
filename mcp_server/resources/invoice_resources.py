import json
from mcp_server.api_client import get_client

def register_invoice_resources(mcp):
    @mcp.resource("pmtool://invoices")
    async def get_invoices_resource() -> str:
        """Resource providing a list of all invoices."""
        client = get_client()
        try:
            invoices = await client.get_invoices()
            return json.dumps(invoices, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("pmtool://invoices/{invoice_id}")
    async def get_invoice_resource(invoice_id: str) -> str:
        """Resource providing details for a specific invoice."""
        client = get_client()
        try:
            invoice = await client.get_invoice(invoice_id)
            return json.dumps(invoice, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
