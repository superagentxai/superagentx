from typing import Any

from opensearchpy import AsyncOpenSearch

from superagentx.llm import LLMClient
from superagentx.vector_stores import DEFAULT_EMBED_MODEL, DEFAULT_EMBED_TYPE
from superagentx.vector_stores.base import BaseVectorStore


class Opensearch(BaseVectorStore):
    """
        A class for interacting with an OpenSearch instance as a vector store.

        This class provides methods for storing, retrieving, and managing vector data
        in an OpenSearch database, enabling efficient search and retrieval capabilities.

    """

    def __init__(
            self,
            *,
            host: str | None = None,
            port: int | None = None,
            username: str | None = None,
            password: str | None = None,
            embed_cli: dict | None = None,
            **kwargs
    ):
        """
        Initialize the Opensearch.

        Args:
            client(opensearch): Existing Opensearch instance. defaults to None.
            host(str): Host address for Opensearch server. Default to None.
            port(int): Port for Opensearch server. Default to none.
            username(str): Username. Default to none.
            password(str): Password. Default to none.
            embed_cli (dict): Agentx embedding configuration. Defaults to None.
            **kwargs: Additional keyword arguments for further customization.
        """

        self.embed_cli = embed_cli
        if not self.embed_cli:
            embed_config = {
                "model": DEFAULT_EMBED_MODEL,
                "embed_type": DEFAULT_EMBED_TYPE
            }
            self.embed_cli = LLMClient(llm_config=embed_config)

        auth = (username, password)

        self.client = AsyncOpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=False,
            **kwargs
        )

    async def create(
            self,
            index_name: str,
            index_body: list[dict]
    ):
        """
            Creates a new collection (index) in the OpenSearch database.

            This method initializes a collection with the specified name and body configuration,
            allowing for structured data storage and retrieval.

            Parameters:
                index_name (str): The name of the index to be created. Must be unique within the OpenSearch instance.
                index_body (list[dict]): A list of dictionaries defining the index's mapping and settings.

            Returns:
                bool: True if the collection was successfully created, False otherwise.

        """

        return await self.client.indices.create(
            index=index_name,
            body=index_body
        )

    async def insert(
            self,
            index_name: str,
            document: dict,
            **kwargs
    ):
        """
              Inserts a document into the specified index in the OpenSearch database.

              This method adds a new document or updates an existing document in the specified index,
              allowing for efficient data storage and retrieval.

              Parameters:
                  index_name (str): The name of the index where the document will be inserted.
                  document (dict): The document to be inserted, represented as a dictionary.
                  **kwargs: Additional optional parameters for insertion, such as document ID or refresh options.

              Returns:
                   dict: A response from the OpenSearch server containing the result of the insertion.
        """
        return await self.client.index(
            index=index_name,
            body=document,
            **kwargs
        )

    async def search(
            self,
            query: Any,
            index_name: str,
            **kwargs
    ):
        """
            Searches for a specified query in the given index.

             Parameters:
                query (Any): The search definition using the Query DSL
                index_name (str): The name of the index where the search will be performed.

            Returns:
                list: A list of results matching the search query from the specified index.
        """

        return await self.client.search(
            body=query,
            index=index_name
        )

    async def exists(
            self,
            index_name: str
    ):
        """
            Checks if the specified index exists.

            Parameters:
                index_name (str): The name of the index to check for existence.

            Returns:
                bool: True if the index exists, False otherwise.

        """
        return await self.client.indices.exists(
            index=index_name
        )

    async def update(
            self,
            index_name: str,
            vector_id: str,
            body: dict,
            **kwargs
    ):
        """
            Updates a document in the specified index with the given ID based on the query provided.

            Parameters:
                index_name (str): The name of the index where the document is stored.
                vector_id (str): The unique identifier of the document to be updated.
                body (dict): The body string specifying the update operation to be applied.
                **kwargs: Additional optional parameters for the update operation.

            Returns:
                None

        """
        response = await self.client.update(
            index=index_name,
            id=vector_id,
            body=body,
            **kwargs
        )
        return response

    async def delete_collection(
            self,
            index_name: str
    ):
        """
            Deletes the entire collection (index) specified by the index name.

            Parameters:
                index_name (str): The name of the index (collection) to be deleted.

            Returns:
                bool: True if the collection was successfully deleted, False otherwise.
        """

        return await self.client.indices.delete(
            index=index_name
        )

    async def delete_by_conversation_id(self, **kwargs):
        raise NotImplementedError
