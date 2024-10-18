import logging
import os

import pytest

from superagentx.agent.agent import Agent
from superagentx.agent.engine import Engine
from superagentx.constants import SEQUENCE
from superagentx.handler.ecommerce.target import TargetHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_target_agent.py::TestTargetAgent::test_target_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestTargetAgent:

    async def test_target_agent(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')
        target_handler = TargetHandler(
            api_key=os.getenv('RAPID_API_KEY')
        )
        prompt_template = PromptTemplate()
        target_engine = Engine(
            handler=target_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )
        target_agent = Agent(
            goal="Get a proper answer for asking a question in Target.",
            role="You are the product searcher",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[target_engine]
        )
        result = await target_agent.execute(
            query_instruction="Get me the best product of blender with 4.5 ratings"
        )
        logger.info(f"Result=>   {result}")
        assert result
