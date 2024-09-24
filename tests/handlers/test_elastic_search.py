from cgitb import handler

import pytest

from agentx.handler.elastic_search import ElasticsearchHandler

'''
 Run Pytest:  
 
   1.pytest --log-cli-level=INFO tests/handlers/test_elastic_search.py::TestElasticsearch::test_elasticsearch_search
   2.pytest --log-cli-level=INFO tests/handlers/test_elastic_search.py::TestElasticsearch::test_elasticsearch_create

'''


@pytest.fixture
def elasticsearch_client_init() -> ElasticsearchHandler:
    elasticsearch_handler = ElasticsearchHandler(
        hosts="http://localhost:9200",
        username="elastic",
        password="df_123456789"
    )
    return elasticsearch_handler


class TestElasticsearch:

    # Test async elasticsearch handler - search method
    async def test_elasticsearch_search(self, elasticsearch_client_init: ElasticsearchHandler):
        elasticsearch = await elasticsearch_client_init.handle(action="search",
                                                               index_name="index_name",
                                                               )
        assert isinstance(elasticsearch, object)

    # Test async elasticsearch handler - create method
    async def test_elasticsearch_create(self, elasticsearch_client_init: ElasticsearchHandler):
        elasticsearch = await elasticsearch_client_init.handle(action="create",
                                                               index_name="python_test1",
                                                               document_id="python1",
                                                               document={
                                                                   "@timestamp": "2099-11-15T13:12:00",
                                                                   "message": "GET /search HTTP/1.1 200 1070000",
                                                               },

                                                               )
        assert isinstance(elasticsearch, object)
