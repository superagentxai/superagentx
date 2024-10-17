import logging

import pytest

from superagentx.handler.scrape import ScrapeHandler

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

    1.pytest --log-cli-level=INFO tests/handlers/test_scrap_handler.py::TestScrap::test_scrap_content    

'''

@pytest.fixture
def weather_client_init() -> ScrapeHandler:
    scrap_handler = ScrapeHandler(
        domain_url=""
    )
    return scrap_handler

class TestScrap:

    async def test_scrap_content(self):
        pass
