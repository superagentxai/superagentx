from agentx.handler.wikipedia import WikipediaHandler

search = WikipediaHandler(
    action="",
    query="",
    sentences=5
)


async def test_search():
    await search.ahandle(
        action="summary",
        query="story about titanic movie",
        sentences=20
    )
