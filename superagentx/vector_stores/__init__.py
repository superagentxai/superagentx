import logging
from enum import Enum

from superagentx.vector_stores.chroma import ChromaDB
from superagentx.llm import LLMClient
from superagentx.vector_stores.constants import DEFAULT_EMBED_TYPE, DEFAULT_EMBED_MODEL, EmbedTypeEnum
from superagentx.vector_stores.opensearch import Opensearch

logger = logging.getLogger(__name__)


class VectorDatabaseType(Enum):
    CHROMA = "chroma"
    NEO4J = "neo4j"
    ELASTICSEARCH = "elasticsearch"
    OPENSEARCH = "opensearch"
    QDRANT = "qdrant"


class VectorStore:

    def __init__(
            self,
            *,
            vector_database_type: str,
            embed_config: dict | None = None,
            url: str | None = None,
            host: str | None = None,
            port: int | None = None,
            username: str | None = None,
            password: str | None = None,
            collection_name: str | None = None
    ):
        self.vector_type = vector_database_type.lower()
        self.url = url
        self.host = host or "localhost"
        self.port = port
        self.username = username
        self.password = password
        self.collection_name = collection_name

        if not embed_config:
            embed_config = {
                "model": DEFAULT_EMBED_MODEL,
                "embed_type": DEFAULT_EMBED_TYPE,
            }

        match embed_config.get("embed_type"):
            case EmbedTypeEnum.OPENAI:
                embed_config["llm_type"] = embed_config.get("embed_type")
                embed_config.pop("embed_type")
                self.embed_cli = LLMClient(llm_config=embed_config)
            case _:
                raise ValueError(f"Invalid type: {embed_config.get('embed_type')}")

        _params = self.__dict__

        match self.vector_type:
            case VectorDatabaseType.CHROMA:
                self.cli = ChromaDB(**_params)
            case VectorDatabaseType.OPENSEARCH:
                self.cli = Opensearch(**_params)
            case _:
                _msg = (
                    f'Invalid Vector data type - '
                    f'{self.vector_type}. It should be one of the following '
                    f'{", ".join(list(map(lambda c: c.value, VectorDatabaseType)))}'
                )
                logger.error(_msg)
                raise ValueError(_msg)

    async def create(
            self,
            *args,
            **kwargs
    ):
        return await self.cli.create(
            *args,
            **kwargs
        )

    async def search(
            self,
            *args,
            **kwargs
    ):
        return await self.cli.search(
            *args,
            **kwargs
        )

    async def insert(
            self,
            *args,
            **kwargs
    ):
        return await self.cli.insert(
            *args,
            **kwargs
        )

    async def update(
            self,
            *args,
            **kwargs
    ):
        return await self.cli.update(
            *args,
            **kwargs
        )

    async def exists(
            self,
            *args,
            **kwargs
    ):
        return await self.cli.exists(
            *args,
            **kwargs
        )

    async def delete(
            self,
            *args,
            **kwargs
    ):
        return await self.cli.delete_collection(
            *args,
            **kwargs
        )
