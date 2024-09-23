import logging
from enum import Enum

from agentx.vector_stores.neo4j import Neo4jVector
from agentx.vector_stores.chroma import ChromaDB
from agentx.llm import LLMClient
from agentx.vector_stores.constants import DEFAULT_EMBED_TYPE, DEFAULT_EMBED_MODEL, EmbedTypeEnum
from agentx.vector_stores.opensearch import Opensearch

logger = logging.getLogger(__name__)


class VectorDatabaseType(str, Enum):
    CHROMA = "chroma"
    NEO4J = "neo4j"
    ELASTICSEARCH = "elasticsearch"
    OPENSEARCH = "opensearch"
    QDRANT = "qdrant"

    @staticmethod
    def list():
        return list(map(lambda c: c.value, VectorDatabaseType))


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

        if embed_config is None:
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
            case VectorDatabaseType.NEO4J:
                self.cli = Neo4jVector(**_params)
            case VectorDatabaseType.CHROMA:
                self.cli = ChromaDB(**_params)
            case VectorDatabaseType.OPENSEARCH:
                self.cli = Opensearch(**_params)
            case _:
                vector_enum_list = VectorDatabaseType.list()
                _msg = (
                    f'Invalid Vector data type - '
                    f'{self.vector_type}. It should be one of the following {", ".join(vector_enum_list)}'
                )
                logger.error(_msg)
                raise ValueError(_msg)

    def create(
            self,
            *args,
            **kwargs
    ):
        return self.cli.create_collection(*args, **kwargs)

    def search(
            self,
            *args,
            **kwargs
    ):
        return self.cli.search(*args, **kwargs)

    def insert(
            self,
            *args,
            **kwargs
    ):
        return self.cli.insert(*args, **kwargs)

    def update(
            self,
            *args,
            **kwargs
    ):
        return self.cli.update(*args, **kwargs)

    def exists(
            self,
            *args,
            **kwargs
    ):
        return self.cli.exists(*args, **kwargs)

    def delete_collection(
            self,
            *args,
            **kwargs
    ):
        return self.cli.delete_collection(*args, **kwargs)

    async def acreate(
            self,
            *args,
            **kwargs
    ):
        return await self.cli.acreate_collection(*args, **kwargs)

    async def asearch(
            self,
            *args,
            **kwargs
    ):
        return await self.cli.asearch(*args, **kwargs)

    async def ainsert(
            self,
            *args,
            **kwargs
    ):
        return await self.cli.ainsert(*args, **kwargs)

    async def aupdate(
            self,
            *args,
            **kwargs
    ):
        return await self.cli.aupdate(*args, **kwargs)

    async def aexists(
            self,
            *args,
            **kwargs
    ):
        return await self.cli.aexists(*args,**kwargs)

    async def adelete_collection(
            self,
            *args,
            **kwargs
    ):
        return await self.cli.adelete_collection(*args,**kwargs)
