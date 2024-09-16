from agentx.handler.exa_search import ExaHandler
from exa_py.api import SearchResponse
import pytest

'''
 Run Pytest:  

   pytest --log-cli-level=INFO tests/handlers/test_exa_handler.py::TestExasearch::test_exa_handler
   pytest --log-cli-level=INFO tests/handlers/test_exa_handler.py::TestExasearch::test_aexa_handler

'''


@pytest.fixture
def exasearch_client_init() -> ExaHandler:
    exa_handler = ExaHandler()
    return exa_handler

class TestExasearch:

    def test_exa_handler(self, exasearch_client_init: ExaHandler):
        exa = exasearch_client_init.handle(action="search_contents",
                                 query="Topics in AI",
                                 use_autoprompt=True,
                                 type="auto",
                                 num_results=5,
                                 )
        print(exa)


    async def test_aexa_handler(self, exasearch_client_init: ExaHandler):
        exa = await exasearch_client_init.ahandle(action="search_contents",
                                 query="Topics in AI",
                                 type="auto",
                                 use_autoprompt=True,
                                 num_results=5,
                                 )
        print(exa)

