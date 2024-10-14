import pytest
import logging

from agentx.handler.ecommerce.amazon import AmazonHandler

logger = logging.getLogger(__name__)

'''
 Run Pytest:

   1. pytest --log-cli-level=INFO tests/handlers/test_amazon.py::TestAmazon::test_search_product
   2.pytest --log-cli-level=INFO tests/handlers/test_amazon.py::TestAmazon::test_product_reviews

'''


@pytest.fixture
def amazon_client_init() -> AmazonHandler:
    amazon = AmazonHandler(
        api_key="<API_KEY>",
        country="IN"
    )
    return amazon


class TestAmazon:

    async def test_search_product(self, amazon_client_init: AmazonHandler):
        logger.info(await amazon_client_init.product_search(query="Oneplus"))

    async def test_product_reviews(self, amazon_client_init: AmazonHandler):
        res = await amazon_client_init.product_reviews(asin='B093YSSN6T')
        logger.info(res)
