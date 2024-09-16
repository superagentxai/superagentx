import logging
from enum import Enum

from agentx.vector_stores.neo4j import Neo4jVector
from agentx.vector_stores.chroma import ChromaDB

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
        self.embed_config = embed_config
        self.url = url
        self.host = host or "localhost"
        self.port = port
        self.username = username
        self.password = password
        self.collection_name = collection_name

        vector_enum_list = VectorDatabaseType.list()
        if self.vector_type not in vector_enum_list:
            _msg = (
                f'Invalid Vector data type - '
                f'{self.vector_type}. It should be one of the following {", ".join(vector_enum_list)}'
            )
            logger.error(_msg)
            raise ValueError(_msg)

        if self.embed_config is None:
            self.embed_config = {
                "model": "text-embedding-ada-002",
                "embed_type": "openai",
            }

        _params = self.__dict__

        match self.vector_type:
            case VectorDatabaseType.NEO4J:
                self.cli = Neo4jVector(**_params)
            case VectorDatabaseType.CHROMA:
                self.cli = ChromaDB(**_params)

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

    def exists(self):
        return self.cli.exists()

    def delete_collection(self):
        return self.cli.delete_collection()

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

    async def aexists(self):
        return await self.cli.aexists()

    async def adelete_collection(self):
        return await self.cli.adelete_collection()
