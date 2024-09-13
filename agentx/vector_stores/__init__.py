import logging
from enum import Enum

from agentx.vector_stores.neo4j import Neo4jVector
from agentx.vector_stores.chroma import ChromaDB
from agentx.exceptions import InvalidType

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
            password: str | None = None
    ):
        self.vector_type = vector_database_type.lower()
        self.embed_config = embed_config
        self.url = url
        self.host = host or "localhost"
        self.port = port
        self.username = username
        self.password = password

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
                "api_type": "openai",
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

    def delete(
            self,
            *args,
            **kwargs
    ):
        return self.cli.delete(*args, **kwargs)

    def get(
            self,
            *args,
            **kwargs
    ):
        return self.cli.get(*args, **kwargs)

    def update(
            self,
            *args,
            **kwargs
    ):
        return self.cli.update(*args, **kwargs)
