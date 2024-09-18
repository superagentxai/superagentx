from agentx.handler.wikipedia import WikipediaHandler
import pytest

'''
 Run Pytest:  

   1.pytest --log-cli-level=INFO tests/handlers/test_wikipedia.py::TestWikipedia::test_search

'''
@pytest.fixture
def wikipedia_client_init() -> WikipediaHandler:
    search = WikipediaHandler()
    return search


class TestWikipedia:
    async def test_search(self, wikipedia_client_init:WikipediaHandler):
        res = await wikipedia_client_init.ahandle(
            action="summary",
            query="story about titanic movie",
            sentences=20
        )
        assert "Titanic" in res
