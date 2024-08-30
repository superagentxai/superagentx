from agentx.handler.wikipedia import Wikipedia

search = Wikipedia(
    action="",
    query="",
    sentences=5
)


def test_search():
    search.handle(
        action="summary",
        query="story about mangatha movie",
        sentences=10,
        # language="hi"
    )
    #
    # search.handle(
    #     action="search",
    #     query="good",
    #     results=10,
    #     # language="hi"
    # )

    # search.handle(
    #     action="page",
    #     query="india"
    # )
