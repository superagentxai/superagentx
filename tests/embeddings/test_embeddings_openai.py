import pytest
import logging
from agentx.embeddings import Embeddings

from openai.types.create_embedding_response import CreateEmbeddingResponse

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/embeddings/test_embeddings_openai.py::TestOpenAIEmbedding::test_embed
   2. pytest --log-cli-level=INFO tests/embeddings/test_embeddings_openai.py::TestOpenAIEmbedding::test_aembed
'''


@pytest.fixture
def openai_client_init() -> dict:
    embed_config = {"model": "text-embedding-ada-002", "embed_type": "openai", "async_mode": False}

    embed_client: Embeddings = Embeddings(embed_config=embed_config)
    response = {'embed': embed_client, 'embed_type': 'openai'}
    return response


class TestOpenAIEmbedding:

    async def test_openai_client(self, openai_client_init: dict):
        embed_client: Embeddings = openai_client_init.get('embed')
        assert isinstance(embed_client, Embeddings)

    async def test_embed(self, openai_client_init: dict):
        embed_obj: Embeddings = openai_client_init.get("embed")
        result = embed_obj.embed(text="Hi, Tell me about Agentic Framework")
        assert isinstance(result, list)

    async def test_aembed(self, openai_client_init: dict):
        embed_obj: Embeddings = openai_client_init.get("embed")
        result = await embed_obj.aembed(text="Hi, Tell me about Agentic Framework")
        assert isinstance(result, list)
