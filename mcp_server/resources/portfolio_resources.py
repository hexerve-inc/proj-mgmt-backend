import json
from mcp_server.api_client import get_client

def register_portfolio_resources(mcp):
    @mcp.resource("pmtool://portfolios")
    async def get_portfolios_resource() -> str:
        """Resource providing a list of all portfolios."""
        client = get_client()
        try:
            portfolios = await client.get_portfolios()
            return json.dumps(portfolios, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("pmtool://portfolios/{portfolio_id}")
    async def get_portfolio_resource(portfolio_id: str) -> str:
        """Resource providing details for a specific portfolio."""
        client = get_client()
        try:
            portfolio = await client.get_portfolio(portfolio_id)
            return json.dumps(portfolio, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
