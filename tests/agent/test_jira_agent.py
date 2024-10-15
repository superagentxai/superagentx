import logging
import os

import pytest

from agentx.agent.agent import Agent
from agentx.agent.engine import Engine
from agentx.constants import SEQUENCE
from agentx.handler.jira import JiraHandler
from agentx.llm import LLMClient
from agentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_jira_agent.py::TestJiraAgent::test_jira_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestJiraAgent:

    async def test_jira_agent(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')
        jira_handler = JiraHandler(
            email=os.getenv('JIRA_EMAIL'),
            token=os.getenv('JIRA_TOKEN'),
            organization=os.getenv('JIRA_ORGANIZATION'),
        )
        prompt_template = PromptTemplate()
        jira_engine = Engine(
            handler=jira_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )
        jira_agent = Agent(
            goal="Get a proper answer for asking a question in Jira.",
            role="You are the JIRA admin",
            llm=llm_client,
            prompt_template=prompt_template
        )
        await jira_agent.add(
            jira_engine,
            execute_type=SEQUENCE

        )
        result = await jira_agent.execute(
            query_instruction="Get the issue list assigned to Arul on Board 1"
        )
        assert result
