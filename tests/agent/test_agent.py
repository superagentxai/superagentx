import logging

import pytest

from agentx.agent import Engine, Agent
from agentx.constants import PARALLEL
from agentx.handler.ecommerce.amazon import AmazonHandler
from agentx.handler.ecommerce.flipkart import FlipkartHandler
from agentx.llm import LLMClient
from agentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_agent.py::TestEcommerceAgent::test_ecommerce_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestEcommerceAgent:

    async def test_ecommerce_agent(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')
        amazon_ecom_handler = AmazonHandler(
            api_key="",
            country="IN"
            # llm_client=llm_client,
            # product_models=mobile_phones
        )
        flipkart_ecom_handler = FlipkartHandler(
            api_key=""
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
        ecom_agent = Agent(
            goal="Get me a best and cheap blender",
            role="You are the best product searcher",
            llm=llm_client,
            prompt_template=prompt_template
        )
        await ecom_agent.add(
            amazon_engine,
            flipkart_engine,
            execute_type=PARALLEL
        )
        await ecom_agent.add(
            amazon_engine,
            flipkart_engine
        )
        result = await ecom_agent.execute()
        assert result
