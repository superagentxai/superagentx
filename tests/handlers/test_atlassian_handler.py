import logging
import os

import pytest

from agentx.handler.atlassian.confluence import ConfluenceHandler

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/handlers/test_atlassian_handler.py::TestAtlassian::test_get_all_groups


'''


@pytest.fixture
def confluence_client_init() -> ConfluenceHandler:
    confluence_handler = ConfluenceHandler(
        token=os.getenv('CONFLUENCE_TOKEN'),
        organization=os.getenv('CONFLUENCE_ORGANIZATION')
    )
    return confluence_handler


class TestAtlassian:

    async def test_get_all_groups(self, confluence_client_init: ConfluenceHandler):
        res = await confluence_client_init.get_all_groups()
        logger.info(f"Groups: {res}")
        assert isinstance(res, list)
        assert len(res) > 0
