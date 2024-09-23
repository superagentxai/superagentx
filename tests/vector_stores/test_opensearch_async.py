import pytest
import logging

from agentx.vector_stores import VectorStore

logger = logging.getLogger(__name__)

'''
 Run Pytest:
 
   1. pytest --log-cli-level=INFO tests/vector_stores/test_opensearch_async.py::TestOpensearch::test_create_collection
   2. pytest --log-cli-level=INFO tests/vector_stores/test_opensearch_async.py::TestOpensearch::test_insert
   3. pytest --log-cli-level=INFO tests/vector_stores/test_opensearch_async.py::TestOpensearch::test_search
   4. pytest --log-cli-level=INFO tests/vector_stores/test_opensearch_async.py::TestOpensearch::test_update
   5. pytest --log-cli-level=INFO tests/vector_stores/test_opensearch_async.py::TestOpensearch::test_exists
   6. pytest --log-cli-level=INFO tests/vector_stores/test_opensearch_async.py::TestOpensearch::test_delete_collection

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

    async def test_create_collection(self, opensearch_client_init: VectorStore):
        res = await opensearch_client_init.acreate(
            index_name="python-test6",
            index_body={
              'settings': {
                'index': {
                  'number_of_shards': 4
                }
              }
            }
        )
        logger.info(f"Result: {res}")

    async def test_insert(self, opensearch_client_init: VectorStore):
        res = await opensearch_client_init.ainsert(
            index_name="python-test6",
            document= {
                'title': 'Moneyball',
                'director': 'Bennett Miller',
                'year': '2011'
            }
        )
        print(res)

    async def test_search(self, opensearch_client_init: VectorStore):
        q = 'miller'
        res =await opensearch_client_init.asearch(
            query=q,
            index_name= "python-test6"
        )
        print(res)

    async def test_update(self, opensearch_client_init: VectorStore):
        res = await opensearch_client_init.aupdate(
            index_name= "python-test6",
            id= "1",
            query="miller"
        )
        print(res)

    async def test_exists(self, opensearch_client_init: VectorStore):
        res = await opensearch_client_init.aexists(
            index=""
        )
        print(res)

    async def test_delete_collection(self, opensearch_client_init: VectorStore):
        res = await opensearch_client_init.adelete_collection(
            index_name=""
        )
        print(res)
