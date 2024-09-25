import os

from agentx.handler.exa_search import ExaHandler
from exa_py.api import SearchResponse
import pytest

'''
 Run Pytest:  

   pytest --log-cli-level=INFO tests/handlers/test_exa_handler.py::TestExasearch::test_exa_handler

'''


@pytest.fixture
def exasearch_client_init() -> ExaHandler:
    # Set the exa api key in environment variable as EXA_API_KEY
    exa_handler = ExaHandler(api_key=os.getenv("EXA_API_KEY"))
    return exa_handler


class TestExasearch:

    # Test async exa handler - search_contents method
    async def test_exa_handler(self, exasearch_client_init: ExaHandler):
        exa = await exasearch_client_init.search_contents(
            query="Topics in AI",
            search_type="auto",
            use_autoprompt=True,
            num_results=5,
         )
        assert isinstance(exa, SearchResponse)
