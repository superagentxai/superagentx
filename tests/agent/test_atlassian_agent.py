import logging
import os

import pytest

from superagentx.agent.agent import Agent
from superagentx.agent.engine import Engine
from superagentx.handler.atlassian.jira import JiraHandler
from superagentx.handler.atlassian.confluence import ConfluenceHandler
from superagentx.llm import LLMClient
from superagentx.memory import Memory
from superagentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_atlassian_agent.py::TestAtlassianAgent::test_atlassian_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestAtlassianAgent:

    async def test_atlassian_agent(
            self,
            agent_client_init: dict
    ):
        llm_client: LLMClient = agent_client_init.get('llm')
        jira_handler = JiraHandler(
            email=os.getenv('ATLASSIAN_EMAIL'),
            token=os.getenv('ATLASSIAN_TOKEN'),
            organization=os.getenv('ATLASSIAN_ORGANIZATION')
        )

        confluence_handler = ConfluenceHandler(
            email=os.getenv('ATLASSIAN_EMAIL'),
            token=os.getenv('ATLASSIAN_TOKEN'),
            organization=os.getenv('ATLASSIAN_ORGANIZATION'),
        )
        prompt_template = PromptTemplate()
        jira_engine = Engine(
            handler=jira_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )

        confluence_engine = Engine(
            handler=confluence_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )
        memory = Memory()
        atlassian_agent = Agent(
            goal="Get a proper answer for asking a question in atlassian.",
            role="You are the Atlassian admin",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[jira_engine, confluence_engine],
            memory=memory
        )

        result = await atlassian_agent.execute(
            query_instruction="Give me all the spaces in confluence"
        )
        logger.info(f"Result => {result}")

        assert result