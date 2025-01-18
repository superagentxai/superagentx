import logging

import pytest

from superagentx.handler.openapi import OpenAPIHandler

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/handlers/test_openapi_spec_handler.py::TestOpenAPIHandler::test_openapi_handler

'''


@pytest.fixture
def openapi_handler_init() -> OpenAPIHandler:
    openapi_handler = OpenAPIHandler(base_url='https://petstore.swagger.io/v2/', spec_url_path='swagger.json')
    return openapi_handler


class TestOpenAPIHandler:

    async def test_openapi_handler(self, openapi_handler_init: OpenAPIHandler):
        response = await openapi_handler_init.call_endpoint(
            endpoint="/pet/findByStatus",
            method="GET",
            params={"query": {'status': 'sold'}})
        logger.info(f"Response {response}")

