import os

from agentx.vector_stores.base import BaseVectorStore
from neo4j import GraphDatabase, AsyncGraphDatabase

from agentx.vector_stores.exceptions import InvalidUrl


class Neo4jVector(BaseVectorStore):

    def __init__(
            self,
            *,
            url: str | None = None,
            username: str | None = None,
            password: str | None = None,
            **kwargs
    ):
        if not url:
            raise InvalidUrl(f"{url} is not valid url")

        self.url = url if url else os.getenv("NEO4J_URI")
        self.username = username if username else os.getenv("NEO4J_USERNAME")
        self.password = password if password else os.getenv("NEO4J_PASSWORD")

        self._driver = GraphDatabase.driver(
            url,
            auth=(username, password)
        )
        super().__init__()

    def create(self, collection_name: str):
        pass

    def insert(self, collection_name: str):
        pass

    def search(self, collection_name:str, query: str, top: int = 4):
        pass

    def delete(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass

    def exists(self, *args, **kwargs):
        pass
