import logging

import pytest

from agentx.handler.serper_dev import SerperDevToolHandler

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_serper_dev.py::TestSerperDev::test_serper_dev_search
'''


@pytest.fixture
def serper_dev_client_init() -> dict:
    return {}


class TestSerperDev:

    async def test_serper_dev_search(self):
        serper_dev_handler = SerperDevToolHandler()
        response = await serper_dev_handler.search(query='Select the best city based on weather, season, and prices')
        logger.info(f'Results ==> {response}')
