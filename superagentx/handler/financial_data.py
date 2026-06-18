import os

import aiohttp

from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool


class FinancialHandler(BaseHandler):
    base_url: str = 'https://financialmodelingprep.com/api/v3'

    def __init__(
            self,
            symbol: str,
            api_key: str | None = None
    ):
        super().__init__()
        self.api_key = api_key or os.getenv("FINANCIAL_DATA_API_KEY")
        self.symbol = symbol

    async def _retrieve(
            self,
            endpoint: str
    ):
        """
        Asynchronously fetches data from the specified API endpoint.
        This method sends an asynchronous HTTP request to the given
        endpoint and returns the response data upon successful
        completion. It is designed to be used with `await` to ensure
        that the data is retrieved without blocking
        the main thread.

        parameter:
            endpoint(str): The API endpoint URL from which data  will be retrieved.
             This should be a string representing valid endpoint.
        """
        _url = f'{self.base_url}/{endpoint.strip("/")}'
        async with aiohttp.ClientSession() as session:
            async with session.get(_url) as resp:
                return await resp.json()

    @tool
    async def get_stock_price(self) -> list[dict]:
        """
            Asynchronously retrieves stock prices.

            This method fetches the current stock prices from a predefined
            source or API and returns a list of dictionaries, where each
            dictionary contains information about a specific stock, such as
            its symbol, price, and other relevant details.

            Returns:
                list[dict]: A list of dictionaries containing stock data.
                Each dictionary typically includes fields like 'symbol',
                'price', 'volume', and 'timestamp', but the exact structure
                depends on the data source.
        """

        _endpoint = f'quote-order/{self.symbol}?apikey={self.api_key}'
        return await self._retrieve(_endpoint)

    @tool
    async def get_company_financials(self) -> list[dict]:
        """
            Asynchronously retrieves financial data for a company or multiple companies.

            This method fetches financial information such as revenue, profit,
            expenses, and other key financial metrics from a predefined data source
            or API. The data is returned as a list of dictionaries, where each
            dictionary contains detailed financial information for a specific company.

            Returns:
                list[dict]: A list of dictionaries, where each dictionary contains
                financial data for a company. The fields may include 'company_name',
                'revenue', 'net_income', 'expenses', 'assets', 'liabilities',
                and other financial metrics, depending on the data source.

        """
        _endpoint = f"profit/{self.symbol}?apikey={self.api_key}"
        return await self._retrieve(_endpoint)

    @tool
    async def get_income_statement(self) -> list[dict]:
        """
            Asynchronously retrieves the income statement data for a company or multiple companies.

            This method fetches income statement details such as revenue, gross profit,
            operating expenses, net income, and other relevant financial metrics from
            a predefined data source or API. The data is returned as a list of dictionaries,
            with each dictionary containing income statement information for a specific company.

            Returns:
                list[dict]: A list of dictionaries, where each dictionary contains income
                statement data for a company. Typical fields include 'company_name', 'revenue',
                'gross_profit', 'operating_income', 'net_income', 'earnings_per_share', and
                other key financial figures.
        """

        _endpoint = f"income-statement/{self.symbol}?apikey={self.api_key}"
        return await self._retrieve(_endpoint)
