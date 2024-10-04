import logging

import pytest

from agentx.agent import Engine, Agent
from agentx.handler.ecommerce.fake_flipkart import FakeFlipkartHandler
from agentx.llm import LLMClient
from agentx.prompt import PromptTemplate
from examples.ecommerce_data_generator import mobile_phones

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
        amazon_ecom_handler = FakeFlipkartHandler(
            llm_client=llm_client,
            product_models=mobile_phones
        )
        ecom_engine = Engine(
            handler=amazon_ecom_handler,
            llm=llm_client,
            prompt_template=PromptTemplate()
        )
        ecom_agent = Agent(
            goal="Get me a best and cheap mobile",
            role="You are the best product searcher",
            llm=llm_client,
            prompt_template=PromptTemplate()
        )
        await ecom_agent.add(ecom_engine)
        result = await ecom_agent.execute()
        logger.info(f"Result => \n{result}")
        assert result
