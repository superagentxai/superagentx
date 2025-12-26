import logging

import pytest

from superagentx.agent import Agent
from superagentx.engine import Engine
from superagentx.handler.send_email import EmailHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=DEBUG tests/agent/test_email_agent.py::TestEmailAgent::test_email
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-5-mini', 'llm_type': 'azure-openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'azure-openai'}
    return response

class TestEmailAgent:

    @pytest.mark.asyncio
    async def test_email(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')
        email_handler = EmailHandler(
            host="smtp.gmail.com",
            port=465,
            username="<USERNAME>",  # DO NOT hardcode passwords
            password="<PASSWORD>",  # Use environment variables
            ssl=True
        )

        prompt_template = PromptTemplate()
        email_engine = Engine(
            handler=email_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )

        goal = """
                Send a message to the given Email id
               """
        email_agent = Agent(
            goal=goal,
            role="You are the email sender",
            llm=llm_client,
            prompt_template=prompt_template
        )

        await email_agent.add(
            email_engine
        )

        result = await email_agent.execute(query_instruction='send a mail to example123@gmail.com "hi" message')
        logger.info(f'Result ==> {result}')
        assert result
