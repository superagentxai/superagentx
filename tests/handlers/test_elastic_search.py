from cgitb import handler

import pytest

from agentx.handler.elastic_search import ElasticsearchHandler

'''
 Run Pytest:  
 
   1.pytest --log-cli-level=INFO tests/handlers/test_elastic_search.py::TestElasticsearch::test_elasticsearch_search
   2.pytest --log-cli-level=INFO tests/handlers/test_elastic_search.py::TestElasticsearch::test_elasticsearch_asearch
   3.pytest --log-cli-level=INFO tests/handlers/test_elastic_search.py::TestElasticsearch::test_elasticsearch_create
   4.pytest --log-cli-level=INFO tests/handlers/test_elastic_search.py::TestElasticsearch::test_elasticsearch_acreate
'''


@pytest.fixture
def elasticsearch_client_init() -> ElasticsearchHandler:
    elasticsearch_handler = ElasticsearchHandler(
        addresses="<URL>",
        username="<USER_NAME>",
        password="<PASSWORD>"
    )
    return elasticsearch_handler


class TestElasticsearch:

    #Test sync elasticsearch handler - search method
    def test_elasticsearch_search(self, elasticsearch_client_init: ElasticsearchHandler):
        elasticsearch = elasticsearch_client_init.handle(action="search",
                                                         index_name="index_name",
                                                         )
        assert isinstance(elasticsearch, object)

    # Test async elasticsearch handler - search method
    async def test_elasticsearch_asearch(self, elasticsearch_client_init: ElasticsearchHandler):
        elasticsearch = await elasticsearch_client_init.ahandle(action="search",
                                                                index_name="index_name",
                                                                )
        assert isinstance(elasticsearch, object)

    # Test sync elasticsearch handler - create method
    def test_elasticsearch_create(self, elasticsearch_client_init: ElasticsearchHandler):
        elasticsearch = elasticsearch_client_init.handle(action="create",
                                                         index_name="index_name",
                                                         document={
                                                             "@timestamp": "2099-11-15T13:12:00",
                                                             "message": "GET /search HTTP/1.1 200 1070000",
                                                             "user": {
                                                                 "id": "kimchy"
                                                             }
                                                         },

                                                         )
        assert isinstance(elasticsearch, object)

    # Test async elasticsearch handler - create method
    async def test_elasticsearch_acreate(self, elasticsearch_client_init: ElasticsearchHandler):
        elasticsearch = await elasticsearch_client_init.ahandle(action="create",
                                                          index_name="index_name",
                                                          document={
                                                              "@timestamp": "2099-11-15T13:12:00",
                                                              "message": "GET /search HTTP/1.1 200 1070000",
                                                              "user": {
                                                                  "id": "kimchy"
                                                              }
                                                          },

                                                          )
        assert isinstance(elasticsearch, object)
