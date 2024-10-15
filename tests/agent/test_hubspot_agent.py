import logging
import os

import pytest

from agentx.agent.agent import Agent
from agentx.agent.engine import Engine
from agentx.constants import SEQUENCE
from agentx.handler.hubspot import HubSpotHandler
from agentx.handler.jira import JiraHandler
from agentx.llm import LLMClient
from agentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_hubspot_agent.py::TestHubSpotAgent::test_hubspot_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestHubSpotAgent:

    async def test_hubspot_agent(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')
        hubspot_handler = HubSpotHandler(
            token=os.getenv('HUBSPOT_TOKEN'),
        )
        prompt_template = PromptTemplate()
        hubspot_engine = Engine(
            handler=hubspot_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )
        hubspot_agent = Agent(
            goal="Get a proper answer for asking a question in HubSpot.",
            role="You are the Hubspot admin",
            llm=llm_client,
            prompt_template=prompt_template
        )
        await hubspot_agent.add(
            hubspot_engine,
            execute_type=SEQUENCE

        )
        result = await hubspot_agent.execute(
            query_instruction="Get the list of tickets from hubspot"
        )
        logger.info(f'Result ==> {result}')
        assert result
