import pytest
import logging

from elastic_transport import ApiResponse

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
        res = await opensearch_client_init.create(
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
        assert isinstance(res, ApiResponse)

    async def test_insert(self, opensearch_client_init: VectorStore):
        res = await opensearch_client_init.insert(
            index_name="python-test",
            id="1",
            document={
                'title': 'Moneyball',
                'director': 'Bennett Miller',
                'year': '2011'
            }
        )
        logger.info(f"Result: {res}")
        assert isinstance(res, dict)

    async def test_search(self, opensearch_client_init: VectorStore):
        q = 'miller'
        query = {
            'size': 5,
            'query': {
                'multi_match': {
                    'query': q,
                    'fields': ['title^2', 'director']
                }
            }
        }
        res = await opensearch_client_init.search(
            query=query,
            index_name="python-test6"
        )
        logger.info(f"Result: {res}")
        assert isinstance(res, dict)

    async def test_update(self, opensearch_client_init: VectorStore):
        res = await opensearch_client_init.update(
            index_name="python-test",
            vector_id="1",
            body={
                "doc": {
                    'title': 'Miller',
                    'director': 'Bennett Miller',
                    'year': '2011'
                }
            }

        )
        logger.info(f"Result: {res}")
        assert isinstance(res, dict)

    async def test_exists(self, opensearch_client_init: VectorStore):
        res = await opensearch_client_init.exists(
            index_name="python-test"
        )
        logger.info(f"Resul: {res}")
        assert isinstance(res, bool)

    async def test_delete_collection(self, opensearch_client_init: VectorStore):
        res = await opensearch_client_init.delete(
            index_name="python-test"
        )
        assert isinstance(res, dict)
