import pytest

from agentx.handler.wikipedia import WikipediaHandler


'''
 Run Pytest:  

   1.pytest --log-cli-level=INFO tests/handlers/test_wikipedia.py::TestWikipedia::test_search
   
'''


@pytest.fixture
def wikipedia_client_init() -> WikipediaHandler:
    search = WikipediaHandler()
    return search

class TestWikipedia:
    def test_search(self, wikipedia_client_init:WikipediaHandler):
        res = wikipedia_client_init.handle(
            action="summary",
            query="story about titanic movie",
            sentences=20
        )
        assert "Titanic" in res

    # search.handle(
    #     action="search",
    #     query="good",
    #     results=10,
    #     language="hi"
    # )
