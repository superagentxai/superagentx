import os

import pytest

from agentx.handler.financial_data import FinancialHandler

'''
 Run Pytest:

   1.pytest --log-cli-level=INFO tests/handlers/test_financial_data.py::TestFinancial::test_get_stock_price 
   2.pytest --log-cli-level=INFO tests/handlers/test_financial_data.py::TestFinancial::test_get_company_financials
   3.pytest --log-cli-level=INFO tests/handlers/test_financial_data.py::TestFinancial::test_get_income_statement

'''

@pytest.fixture
def financial_client_init() -> FinancialHandler:
    financial_handler = FinancialHandler(
        api_key=os.getenv("FINANCIAL_MODELING_PREP_API_KEY"),
        symbol='AA'
    )
    return financial_handler

class TestFinancial:

    async def test_get_stock_price(self, financial_client_init: FinancialHandler):
        res = await financial_client_init.get_stock_price()
        assert isinstance(res, list)
        assert len(res) > 0

    async def test_get_company_financials(self, financial_client_init: FinancialHandler):
        res = await financial_client_init.get_company_financials()
        assert isinstance(res, list)
        assert len(res) > 0

    async def test_get_income_statement(self, financial_client_init: FinancialHandler ):
         res = await financial_client_init.get_income_statement()
         assert isinstance(res, list)
         assert len(res) > 0
