import logging

import pytest

from agentx.agent.agent import Agent
from agentx.agent.engine import Engine
from agentx.handler.wikipedia import WikipediaHandler
from agentx.llm import LLMClient
from agentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_wikipedia_agent.py::TestWikipediaAgent::test_movies_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestWikipediaAgent:

    async def test_movies_agent(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')
        wikipedia_handler = WikipediaHandler()
        prompt_template = PromptTemplate()

        wikipedia_engine = Engine(
            handler=wikipedia_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )

        goal = f""" List top 10 highest grossing indian films in the below format
        
                     Movie Name: Movie Title
                     Profit: Movie Profit
                     Language: Movie Language         
                    """
        movie_analyse_agent = Agent(
            goal=goal,
            role="You are the best story teller",
            llm=llm_client,
            prompt_template=prompt_template
        )

        await movie_analyse_agent.add(
            wikipedia_engine
        )

        result = await movie_analyse_agent.execute()
        assert result
