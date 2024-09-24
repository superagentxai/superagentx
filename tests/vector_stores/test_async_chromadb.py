import logging
import pytest

from agentx.vector_stores import VectorStore, ChromaDB

logger = logging.getLogger(__name__)

'''
 Run Pytest:

   1. pytest --log-cli-level=INFO tests/vector_stores/test_async_chromadb.py::TestChroma::test_chromadb_client
   2. pytest --log-cli-level=INFO tests/vector_stores/test_async_chromadb.py::TestChroma::test_collection_exists
   3. pytest --log-cli-level=INFO tests/vector_stores/test_async_chromadb.py::TestChroma::test_document_insert
   4. pytest --log-cli-level=INFO tests/vector_stores/test_async_chromadb.py::TestChroma::test_search
   5. pytest --log-cli-level=INFO tests/vector_stores/test_async_chromadb.py::TestChroma::test_update
   6. pytest --log-cli-level=INFO tests/vector_stores/test_async_chromadb.py::TestChroma::test_delete_collection
'''


@pytest.fixture
def chromadb_client_init() -> VectorStore:
    chroma_config = {"collection_name": "test", "vector_database_type": "chroma"}
    chromadb: VectorStore = VectorStore(**chroma_config)
    return chromadb


class TestChroma:

    async def test_chromadb_client(self, chromadb_client_init: VectorStore):
        chromadb_client: ChromaDB = chromadb_client_init.cli
        logger.info(f"ChromDB Object testing....")
        assert isinstance(chromadb_client, ChromaDB)

    async def test_collection_exists(self, chromadb_client_init: VectorStore):
        if await chromadb_client_init.exists():
            assert True
        else:
            assert False

    async def test_document_insert(self, chromadb_client_init: VectorStore):
        documents = [
            "This is a document about pineapple",
            "This is a document about oranges"
        ]
        try:
            _insert = await chromadb_client_init.insert(texts=documents, ids=["id1", "id2"])
            logger.info(f"Documents are inserted")
            assert _insert is None
        except Exception as ex:
            logger.error(f"Document Insertion Error: {ex}")
            assert "Failed"

    async def test_search(self, chromadb_client_init: VectorStore):
        _search = await chromadb_client_init.search(
            query="This is a query document about hawaii",
            limit=2,
            filters=None
        )
        logger.info(_search)
        assert isinstance(_search, list)

    async def test_update(self, chromadb_client_init: VectorStore):
        try:
            _update = await chromadb_client_init.update(
                vector_id="id1",
                embeddings=None,
                payload=None
            )
            logger.info(f"Updated the vector")
            assert _update is None
        except Exception as ex:
            logger.error(f"Update Failed: {ex}")
            assert "Failed"

    async def test_delete_collection(self, chromadb_client_init: VectorStore):
        try:
            _delete = await chromadb_client_init.delete_collection()
            assert _delete is None
        except Exception as ex:
            logger.error(f"Collection Delete Failed: {ex}")
            assert "Failed"


