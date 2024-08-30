from agentx.handler.wikipedia import Wikipedia

search = Wikipedia(
    action="",
    query="",
    sentences=5
)


def test_search():
    result = search.handle(
        action="summary",
        query="story about mangatha movie",
        sentences=10,
        **{}
    )
    assert result
