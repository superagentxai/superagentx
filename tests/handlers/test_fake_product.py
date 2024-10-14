import logging

import pytest

from agentx.handler.ecommerce.fake_product import FakeProductHandler
from agentx.llm import LLMClient
from examples.ecommerce_data_generator import mobile_phones

logger = logging.getLogger(__name__)

'''
 Run Pytest:

   1. pytest --log-cli-level=INFO tests/handlers/test_fake_product.py::TestFakeProducts::test_search

'''

@pytest.fixture
def fake_products_client_init() -> FakeProductHandler:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    fake_product_handler: FakeProductHandler = FakeProductHandler(
        llm_client=llm_client,
        product_models=mobile_phones
    )
    return fake_product_handler


class TestFakeProducts:

    async def test_search(self, fake_products_client_init: FakeProductHandler):
        res = await fake_products_client_init.product_search(
            provider='Amazon'
        )
        logger.info(res)
