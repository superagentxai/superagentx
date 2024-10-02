import pytest
import logging
from examples.ecommerce_data_generator.fake_products import generate_data_products
from examples.ecommerce_data_generator import mobile_phones

logger = logging.getLogger(__name__)

'''
 Run Pytest:

   1. pytest --log-cli-level=INFO tests/ecommerce_data_generator/test_fake_products.py::TestFakeMobileProducts::test_generate_mobile_data

'''


@pytest.fixture
def fake_products_client_init() -> list:
    return mobile_phones


class TestFakeMobileProducts:

    async def test_generate_mobile_data(self, fake_products_client_init: list):
        data = await generate_data_products(fake_products_client_init, total=5, provider='Flipkart')
        logger.info(f'Phone Product List - {data}')
