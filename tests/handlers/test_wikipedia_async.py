import pytest
import logging
from agentx.handler.wikipedia import WikipediaHandler

logger = logging.getLogger(__name__)
'''
 Run Pytest:  

   1.pytest --log-cli-level=INFO tests/handlers/test_wikipedia_async.py::TestWikipedia::test_search

'''


@pytest.fixture
def wikipedia_client_init() -> WikipediaHandler:
    search = WikipediaHandler()
    return search


class TestWikipedia:

    async def test_summary(self, wikipedia_client_init: WikipediaHandler):
        res = await wikipedia_client_init.get_summary(
            query="story about titanic movie",
            sentences=20
        )
        logger.info(f"Wikipedia Result {res}")
        assert "Titanic" in res
