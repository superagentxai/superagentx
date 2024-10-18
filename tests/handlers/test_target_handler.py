import os

import pytest
import logging

from superagentx.handler.ecommerce.target import TargetHandler

logger = logging.getLogger(__name__)

'''
Run Pytest:

    1. pytest --log-cli-level=INFO tests/handlers/test_target_handler.py::TestTarget::test_search_product

'''


@pytest.fixture
def target_client_init() -> TargetHandler:
    target = TargetHandler(
        api_key= os.getenv("TARGET_API_KEY")
    )
    return target


class TestTarget:

    async def test_search_product(
            self,
            target_client_init: TargetHandler
    ):
        res = await target_client_init.product_search(
            query="best one blender provide 5 ratings"
        )
        logger.info(f"Projects: {res}")

