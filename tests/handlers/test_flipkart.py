import pytest
import logging

from agentx.handler.ecommerce.flipkart import FlipkartHandler

logger = logging.getLogger(__name__)

'''
Run Pytest:
    
    1.pytest --log-cli-level=INFO tests/handlers/test_flipkart.py::TestFlipkart::test_search_product
    2.pytest --log-cli-level=INFO tests/handlers/test_flipkart.py::TestFlipkart::test_product_reviews
    
'''

@pytest.fixture
def flipkart_client_init() -> FlipkartHandler:
    flipkart = FlipkartHandler(
        api_key="<API_KEY>"
    )
    return flipkart

class TestFlipkart:

    async def test_search_product(self, flipkart_client_init: FlipkartHandler):
         logger.info(await flipkart_client_init.product_search(query="apple"))

    async def test_product_reviews(self, flipkart_client_init: FlipkartHandler):
        res = await flipkart_client_init.product_reviews(pid='MOBGTAGPTB3VS24W')
        logger.info(res)
