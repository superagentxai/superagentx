import pytest
import logging

from agentx.handler.ecommerce.amazon import AmazonHandler

logger = logging.getLogger(__name__)

'''
 Run Pytest:

   1.pytest --log-cli-level=INFO tests/handlers/test_amazon.py::TestAmazon::test_search_product
   2.pytest --log-cli-level=INFO tests/handlers/test_amazon.py::TestAmazon::test_product_reviews


'''

@pytest.fixture
def amazon_client_init() -> AmazonHandler:
    amazon = AmazonHandler(
        api_key="af373c6babmshce07fb4b2aaf98fp1e8af3jsn78ccf48eca03",
        page=2,
        country="US",
        sort_by="RELEVANCE",
        product_condition="ALL",
        is_prime="false",
        deals_and_discounts="NONE"

    )
    return amazon

class TestAmazon:

    async def test_search_product(self, amazon_client_init: AmazonHandler):
        async for item in await amazon_client_init.search_product(query="Oneplus"):
            logger.info(item)

    async def test_product_reviews(self, amazon_client_init: AmazonHandler):
        res = await amazon_client_init.product_reviews(asin='B093YSSN6T')
        logger.info(res)