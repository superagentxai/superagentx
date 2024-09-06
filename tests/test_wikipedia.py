from agentx.handler.wikipedia import WikipediaHandler

search = WikipediaHandler(
    action="",
    query="",
    sentences=5
)


def test_search():
    search.handle(
        action="summary",
        query="story about titanic movie",
        sentences=20
    )

    # search.handle(
    #     action="search",
    #     query="good",
    #     results=10,
    #     language="hi"
    # )
