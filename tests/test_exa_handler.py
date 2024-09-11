from agentx.handler.exa_search import ExaHandler

exa_handler = ExaHandler()

def test_exa_handler():
    exa = exa_handler.handle(action="search_contents",
                             query="Topics in AI",
                             type="auto",
                             use_autoprompt=True,
                             num_results=5,
                             )
    print(exa)


async def test_aexa_handler():
    exa = await exa_handler.ahandle(action="search_contents",
                             query="Topics in AI",
                             type="auto",
                             use_autoprompt=True,
                             num_results=5,
                             )
    print(exa)

