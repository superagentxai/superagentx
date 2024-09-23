import pytest
import logging

from agentx.vector_stores import VectorStore

logger = logging.getLogger(__name__)

'''
 Run Pytest:

   1. pytest --log-cli-level=INFO tests/vector_stores/test_opensearch.py::TestOpensearch::test_create_collection
   2. pytest --log-cli-level=INFO tests/vector_stores/test_opensearch.py::TestOpensearch::test_insert
   3. pytest --log-cli-level=INFO tests/vector_stores/test_opensearch.py::TestOpensearch::test_search
   4. pytest --log-cli-level=INFO tests/vector_stores/test_opensearch.py::TestOpensearch::test_update
   5. pytest --log-cli-level=INFO tests/vector_stores/test_opensearch.py::TestOpensearch::test_exists
   6. pytest --log-cli-level=INFO tests/vector_stores/test_opensearch.py::TestOpensearch::test_delete_collection

'''

@pytest.fixture
def opensearch_client_init() -> VectorStore:
    opensearch = {
        "vector_database_type": "opensearch",
        "port": 9200,
        "host": "localhost",
        "username": "admin",
        "password": "admin"
    }
    search: VectorStore = VectorStore(**opensearch)
    return search

class TestOpensearch:

    def test_create_collection(self, opensearch_client_init: VectorStore):
        res = opensearch_client_init.create(
            index_name="python-test4",
            index_body={
              'settings': {
                'index': {
                  'number_of_shards': 4
                }
              }
            }
        )
        logger.info(f"Result: {res}")

    def test_insert(self, opensearch_client_init: VectorStore):
        res = opensearch_client_init.insert(
            index_name="python-test4",
            id="1",
            document= {
                'title': 'Moneyball',
                'director': 'Bennett Miller',
                'year': '2011'
            }
        )
        print(res)

    def test_search(self, opensearch_client_init: VectorStore):
        q = 'miller'
        res = opensearch_client_init.search(
            query=q,
            index_name= "python-test4"
        )
        print(res)

    def test_update(self, opensearch_client_init: VectorStore):
        res = opensearch_client_init.update(
            index_name= "python-test4",
            id= "1",
            body={
                  "doc": {
                    'title': 'Miller',
                    'director': 'Bennett Miller',
                    'year': '2011'
                    }
            }
        )
        print(res)

    def test_exists(self, opensearch_client_init: VectorStore):
        res = opensearch_client_init.exists(
            index="python-test4"
        )
        print(res)

    def test_delete_collection(self, opensearch_client_init: VectorStore):
        res = opensearch_client_init.delete_collection(
            index_name=""
        )
        print(res)
