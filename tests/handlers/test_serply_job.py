import pytest
import logging

from agentx.handler.serply_api.serply_job_search import SerplyJobHandler

logger = logging.getLogger(__name__)

'''
 Run Pytest:

   1. pytest --log-cli-level=INFO tests/handlers/test_serply_job.py::TestSerplyJobHandler::test_search_product

'''


@pytest.fixture
def serply_job_client_init() -> SerplyJobHandler:
    seply_job_handler = SerplyJobHandler(location='US')
    return seply_job_handler


class TestSerplyJobHandler:

    async def test_search_product(self, serply_job_client_init: SerplyJobHandler):
        await serply_job_client_init.search('Java')
