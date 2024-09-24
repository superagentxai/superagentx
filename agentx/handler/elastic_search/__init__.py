import elasticsearch
import logging

from enum import Enum, StrEnum
from typing import Any, Union, Mapping, Sequence

from elastic_transport import NodeConfig
from elasticsearch import AsyncElasticsearch

from agentx.handler.base import BaseHandler
from agentx.handler.elastic_search.exceptions import InvalidElasticsearchAction

logger = logging.getLogger(__name__)

class ElasticsearchAction(StrEnum):
    SEARCH = "search"
    CREATE = "create"


class ElasticsearchHandler(BaseHandler):
    """
    A handler class for managing interactions with an Elasticsearch instance.
    This class extends the BaseHandler and provides methods to perform various operations
    on an Elasticsearch index, such as creating, searching, updating, and deleting documents.
    """

    def __init__(
            self,
            hosts: str | Sequence[Union[str, Mapping[str, Union[str, int]], NodeConfig]] | None = None,
            cloud_id: str | None = None,
            api_key: str | None = None,
            username: str | None = None,
            password: str | None = None,
            ca_certs: str | None = None
    ):
        self._conn = AsyncElasticsearch(
            hosts=hosts,
            cloud_id=cloud_id,
            api_key=api_key,
            basic_auth=(username, password),
            ca_certs=ca_certs
        )

    async def handle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:

        """
        Asynchronously processes the specified action, which can be a string or an Enum, along with any additional
        keyword arguments. This method executes the corresponding logic based on the provided action and parameters.

        parameters:
            action (str | Enum): The action to be performed. This can either be a string or an Enum value representing
            the action.
            **kwargs: Additional keyword arguments that may be passed to customize the behavior of the handler.

        Returns:
            Any: The result of handling the action. The return type may vary depending on the specific action handled.
        """

        if isinstance(action, str):
            action = action.lower()
        match action:
            case ElasticsearchAction.SEARCH:
                return await self.search(**kwargs)
            case ElasticsearchAction.CREATE:
                return await self.create(**kwargs)
            case _:
                raise InvalidElasticsearchAction(f"Invalid Elasticsearch Action '{action}'")

    async def search(
            self,
            index_name: str,
            query: dict | None = None,
            start_index: int = 0,
            size: int = 20
    ):
        """
         Asynchronously performs a search operation on the specified index.This function executes a query against
         the specified index and retrieves a set of results based on the query criteria.

        parameters:
            index_name(str):The name of the index to search in.
            query(dict or None, optional):The search query, formatted as a dictionary. If no query is provided,
            it defaults to None and performs a match-all search.
            start_index(int, optional):The starting index for the search results, used for pagination. Defaults to 0.
            size(int, optional):The number of results to retrieve. Defaults to 20.

        """
        result = await self._conn.search(
            index=index_name,
            filter_path=['hits'],
            from_=start_index,
            size=size,
            query=query
        )
        return result

    async def create(
            self,
            index_name: str,
            document: dict,
            document_id: str
    ):
        """
        Asynchronously creates a new document in the specified index.This method adds a document to the given
        index with a specified identifier. If a document with the same identifier already exists,
        it may be updated or replaced based on the implementation.

        parameter:
            index_name(str):The name of the index where the document should be created.
            document(dict):A dictionary representing the document to be indexed, containing the data to be stored.
            document_id(str):The unique identifier for the document. This ID is used to reference the document in future operations.

        """
        try:
            return await self._conn.create(
                index=index_name,
                document=document,
                id=document_id
            )
        except elasticsearch.BadRequestError as ex:
            logger.error('Elasticsearch error!', exc_info=ex)
        except elasticsearch.ConnectionTimeout as ex:
            logger.error(f"Elasticsearch error! {ex}")
        return {}

    def __dir__(self):
        return (
            'search',
            'create'
        )
