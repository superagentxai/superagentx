import logging
import os

import pytest

from superagentx.agent.agent import Agent
from superagentx.agent.engine import Engine
from superagentx.constants import SEQUENCE
from superagentx.handler.ecommerce.walmart import WalmartHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_walmart_agent.py::TestWalmartAgent::test_walmart_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestWalmartAgent:

    async def test_walmart_agent(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')
        walmart_handler = WalmartHandler(
            api_key=os.getenv('WALMART_API_KEY')
        )
        prompt_template = PromptTemplate()
        walmart_engine = Engine(
            handler=walmart_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )
        walmart_agent = Agent(
            goal="Get a proper answer for asking a question in Walmart.",
            role="You are the product searcher",
            llm=llm_client,
            prompt_template=prompt_template
        )
        await walmart_agent.add(
            walmart_engine,
            execute_type=SEQUENCE

        )
        result = await walmart_agent.execute(
            query_instruction="Get me the best product of blender with 4.5 ratings"
        )
        logger.info(f"Result=>   {result}")
        assert result
