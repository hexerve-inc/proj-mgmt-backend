import json
from mcp_server.api_client import get_client

def register_portfolio_tools(mcp):
    @mcp.tool()
    async def list_portfolios() -> str:
        """List all portfolios.
        
        Returns:
            JSON string containing a list of portfolios.
        """
        client = get_client()
        try:
            portfolios = await client.get_portfolios()
            return json.dumps(portfolios, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_portfolio_details(portfolio_id: str) -> str:
        """Get details of a specific portfolio.
        
        Args:
            portfolio_id: The UUID of the portfolio.
            
        Returns:
            JSON string with portfolio details.
        """
        client = get_client()
        try:
            portfolio = await client.get_portfolio(portfolio_id)
            return json.dumps(portfolio, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
