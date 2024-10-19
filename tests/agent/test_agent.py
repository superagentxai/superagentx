import logging
import os

import pytest

from superagentx.agent.agent import Agent
from superagentx.agent.engine import Engine
from superagentx.handler.ecommerce.amazon import AmazonHandler
from superagentx.handler.ecommerce.flipkart import FlipkartHandler
from superagentx.io import IOConsole
from superagentx.llm import LLMClient
from superagentx.memory import Memory
from superagentx.prompt import PromptTemplate
from superagentx.utils.console_color import ConsoleColorType

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_agent.py::TestEcommerceAgent::test_ecommerce_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    # llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}
    llm_config = {'model': 'anthropic.claude-3-5-sonnet-20240620-v1:0', 'llm_type': 'bedrock', 'async_mode': True}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client}
    return response


class TestEcommerceAgent:

    async def test_ecommerce_agent(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')
        amazon_ecom_handler = AmazonHandler(
            api_key=os.getenv('RAPID_API_KEY'),
            country="IN"
        )
        flipkart_ecom_handler = FlipkartHandler(
            api_key=os.getenv('RAPID_API_KEY'),
        )
        prompt_template = PromptTemplate()
        amazon_engine = Engine(
            handler=amazon_ecom_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )
        flipkart_engine = Engine(
            handler=flipkart_ecom_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )
        memory = Memory()
        ecom_agent = Agent(
            goal="Get me the best search results",
            role="You are the best product searcher",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[amazon_engine, flipkart_engine],
        )
        io_console = IOConsole()
        while True:
            await io_console.write(ConsoleColorType.CYELLOW2.value, end="")
            query_instruction = await io_console.read("User: ")
            # "Get me a mobile phone which has rating 4 out of 5 and camera minimum 30 MP compare the"
            # " prices with photo link"
            result = await ecom_agent.execute(
                query_instruction=query_instruction
            )
            await io_console.write(ConsoleColorType.CGREEN2.value, end="")
            await io_console.write(f"Assistant: {result}", flush=True)
            assert result
