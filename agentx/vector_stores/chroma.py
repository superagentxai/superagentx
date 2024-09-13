import os
from typing import Optional

import chromadb
from chromadb.config import Settings

from agentx.vector_stores.base import BaseVectorStore
from agentx.embeddings import Embeddings
from agentx.vector_stores.exceptions import InvalidUrl


class ChromaDB(BaseVectorStore):

    def __init__(
            self,
            *,
            collection_name: str,
            client: Optional[chromadb.Client] = None,
            host: Optional[str] = None,
            port: Optional[int] = None,
            path: Optional[str] = None,
            embed_config: dict | None = None,
            **kwargs
    ):
        """
        Initialize the Chromadb vector store.

        Args:
            collection_name (str): Name of the collection.
            client (chromadb.Client, optional): Existing chromadb client instance. Defaults to None.
            host (str, optional): Host address for chromadb server. Defaults to None.
            port (int, optional): Port for chromadb server. Defaults to None.
            path (str, optional): Path for local chromadb database. Defaults to None.
            embed_config (dict): Agentx embedding configuration. Defaults to None.
        """

        if embed_config is None:
            embed_config = {
                "model": "text-embedding-ada-002",
                "api_type": "openai"
            }
        self.embeddings = Embeddings(embed_config=embed_config)

        if client:
            self.client = client
        else:
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
        # self.collection = self.create_collection(collection_name)

        super().__init__()

    def create_collection(self, *args, **kwargs):
        pass

    def insert(self, collection_name: str):
        pass

    def search(self, collection_name: str, query: str, top: int = 4):
        pass

    def delete(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass

    def exists(self, *args, **kwargs):
        pass

    def get(self, name, vector_id):
        pass

    def list_cols(self):
        pass

    def delete_col(self, name):
        pass

    def col_info(self, name):
        pass
