import os

import pytest
import logging

from superagentx.handler.ecommerce.walmart import WalmartHandler

logger = logging.getLogger(__name__)

'''
Run Pytest:

    1. pytest --log-cli-level=INFO tests/handlers/test_walmart_handler.py::TestWalmart::test_search_product

'''


@pytest.fixture
def walmart_client_init() -> WalmartHandler:
    walmart = WalmartHandler(
        api_key= os.getenv("WALMART_API_KEY")
    )
    return walmart


class TestWalmart:

    async def test_search_product(
            self,
            walmart_client_init: WalmartHandler
    ):
        res = await walmart_client_init.product_search(
            query="best one blender provide 5 ratings"
        )
        logger.info(f"Projects: {res}")

