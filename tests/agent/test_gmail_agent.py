import logging
import os

import pytest

from superagentx.agent.agent import Agent
from superagentx.agent.engine import Engine
from superagentx.handler.google.gmail import GmailHandler
from superagentx.llm import LLMClient
from superagentx.memory import Memory
from superagentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_gmail_agent.py::TestGmailAgent::test_read_mail_agent
'''

@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4o', 'llm_type': 'openai'}
    # llm_config = {'model': 'anthropic.claude-3-5-sonnet-20240620-v1:0', 'llm_type': 'bedrock', 'async_mode': True}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client}
    return response


class TestGmailAgent:

    async def test_read_mail_agent(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')
        gmail_handler = GmailHandler(
            credentials="/home/elangovanr/Documents/Gmail_Creds/credentials.json"
        )
        prompt_template = PromptTemplate()
        gmail_engine = Engine(
            handler=gmail_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )

        memory = Memory()
        gmail_agent = Agent(
            goal="Get me the best search results",
            role="You are the best gmail reader",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[gmail_engine],
        )
        result = await gmail_agent.execute(
            query_instruction="Read mail and get today mail content and attachments"
        )
        logger.info(f"Result=>   {result}")