import logging

import pytest

from superagentx.handler import FakeFlipkartHandler
from superagentx.llm import LLMClient

logger = logging.getLogger(__name__)

'''
 Run Pytest:

   1. pytest --log-cli-level=INFO tests/handlers/test_fake_product.py::TestFakeProducts::test_search

'''

@pytest.fixture
def fake_flipkarts_client_init() -> FakeFlipkartHandler:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    fake_flipkart_handler: FakeFlipkartHandler = FakeFlipkartHandler(
        llm_client=llm_client,
        product_models=[]  #  Needs to give sample products in the desired formats
    )
    return fake_flipkart_handler


class TestFakeProducts:

    async def test_search(self, fake_flipkarts_client_init: FakeFlipkartHandler):
        res = await fake_flipkarts_client_init.product_search(
            query="Get me the top 3 smart watches under 5k"
        )
        logger.info(res)
