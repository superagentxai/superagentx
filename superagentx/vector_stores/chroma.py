import logging

from pydantic import BaseModel
from typing import List, Sequence, Dict

import chromadb
from chromadb.api.models import Collection
from chromadb.config import Settings

from superagentx.llm import LLMClient
from superagentx.vector_stores.base import BaseVectorStore
from superagentx.utils.helper import sync_to_async, iter_to_aiter
from superagentx.vector_stores.constants import DEFAULT_EMBED_TYPE, DEFAULT_EMBED_MODEL

logger = logging.getLogger(__name__)


class Documents(BaseModel):
    id: str  # memory id
    score: float  # distance
    payload: dict  # metadata


class ChromaDB(BaseVectorStore):

    def __init__(
            self,
            *,
            collection_name: str,
            host: str | None = None,
            port: int | None = None,
            path: str | None = None,
            embed_cli: LLMClient | None = None
    ):
        """
        Initialize the Chromadb vector store.

        Args:
            collection_name (str): Name of the collection.
            host (str, optional): Host address for chromadb server. Defaults to None.
            port (int, optional): Port for chromadb server. Defaults to None.
            path (str, optional): Path for local chromadb database. Defaults to None.
            embed_cli (dict): Agentx openai-client/huggingface client configuration. Defaults to None.
        """
        self.embed_cli = embed_cli
        if not self.embed_cli:
            embed_config = {
                "model": DEFAULT_EMBED_MODEL,
                "llm_type": DEFAULT_EMBED_TYPE
            }
            self.embed_cli = LLMClient(llm_config=embed_config)

        self.settings = Settings(anonymized_telemetry=False)

        if host and port:
            self.settings.chroma_server_host = host
            self.settings.chroma_server_http_port = port
            self.settings.chroma_api_impl = "chromadb.api.fastapi.FastAPI"
        else:
            if path is None:
                path = "db"

        self.settings.persist_directory = path
        self.settings.is_persistent = True

        self.client = chromadb.Client(self.settings)

        self.collection_name = collection_name

    async def _get_or_create_collection(
            self,
            name: str,
            **kwargs
    ):
        return await sync_to_async(
            self.client.get_or_create_collection,
            name=name,
            **kwargs
        )

    async def create(
            self,
            name: str,
            **kwargs
    ) -> Collection:
        """
        Create a new collection.

        Args:
            name (str): Name of the collection.

        Returns:
            chromadb.Collection: The created or retrieved collection.
        """
        # Skip creating collection if already exists
        return await self._get_or_create_collection(
            name=name,
            **kwargs
        )

    async def insert(
            self,
            texts: list[str],
            payloads: list[dict] | None = None,
            ids: list[str] | None = None
    ):
        """
        Insert vectors into a collection.

        Args:
            texts (List[str]): List of text to insert.
            payloads (Optional[List[Dict]], optional): List of payloads corresponding to vectors. Defaults to None.
            ids (Optional[List[str]], optional): List of IDs corresponding to vectors. Defaults to None.
        """
        vectors = [await self.embed_cli.aembed(text=text) async for text in iter_to_aiter(texts)]
        logger.info(f"Inserting {len(vectors)} vectors into collection {self.collection_name}")
        collection = await self._get_or_create_collection(name=self.collection_name)
        await sync_to_async(
            collection.add,
            ids=ids,
            embeddings=vectors,
            metadatas=payloads,
            documents=texts
        )

    async def search(
            self,
            query: str,
            limit: int = 5,
            filters: dict | None = None
    ) -> list[Documents]:
        """
        Search for similar vectors.

        Args:
            query (str): The query to embed.
            limit (int, optional): Number of results to return. Defaults to 5.
            filters (Optional[Dict], optional): Filters to apply to the search. Defaults to None.

        Returns:
            List[OutputData]: Search results.
        """
        query_vector = await self.embed_cli.aembed(text=query)
        collection = await self._get_or_create_collection(name=self.collection_name)
        results = await sync_to_async(
            collection.query,
            query_embeddings=query_vector,
            where=filters,
            n_results=limit,
            include=['embeddings', 'metadatas', "distances", "data"]
        )
        return await self._parse_output(results)

    async def update(
            self,
            vector_id: str,
            vector: list[float] | None = None,
            payload: dict | None = None
    ):
        """
        Update a vector and its payload.

        Args:
            vector_id (str): ID of the vector to update.
            vector (Optional[List[float]], optional): Updated vector. Defaults to None.
            payload (Optional[Dict], optional): Updated payload. Defaults to None.
        """
        collection = await self._get_or_create_collection(name=self.collection_name)
        await sync_to_async(
            collection.update,
            ids=vector_id,
            embeddings=vector,
            metadatas=payload
        )

    async def exists(self):
        try:
            await sync_to_async(
                self.client.get_collection,
                self.collection_name
            )
            return True
        except Exception as ex:
            return False

    async def list_cols(self) -> Sequence[chromadb.Collection]:
        """
        List all collections.

        Returns:
            List[chromadb.Collection]: List of collections.
        """
        return await sync_to_async(self.client.list_collections)

    async def delete_collection(self):
        """
        Delete a collection.
        """
        await sync_to_async(
            self.client.delete_collection,
            name=self.collection_name
        )

    @staticmethod
    async def _parse_output(data: dict) -> list[Documents]:
        """
        Parse the output data.

        Args:
            data (Dict): Output data.

        Returns:
            List[Documents]: Parsed output data.
        """
        keys = ["ids", "distances", "metadatas"]
        values = []

        async for key in iter_to_aiter(keys):
            value = data.get(key, [])
            if value and isinstance(value, list) and isinstance(value[0], list):
                value = value[0]
            values.append(value)

        ids, distances, metadatas = values
        max_length = max(
            len(v) for v in values if isinstance(v, list) and v is not None
        )

        result = []
        async for i in iter_to_aiter(range(max_length)):
            entry = Documents(
                id=ids[i] if isinstance(ids, list) and ids and i < len(ids) else None,
                score=(
                    distances[i]
                    if isinstance(distances, list) and distances and i < len(distances)
                    else None
                ),
                payload=(
                    metadatas[i]
                    if isinstance(metadatas, list) and metadatas and i < len(metadatas)
                    else None
                ),
            )
            result.append(entry)
        return await sync_to_async(
            sorted,
            result,
            key=lambda doc: doc.payload['created_at']
        )

    async def delete_by_conversation_id(self, conversation_id):
        collection = await self._get_or_create_collection(self.collection_name)
        await sync_to_async(
            collection.delete,
            where={"conversation_id": conversation_id}
        )
