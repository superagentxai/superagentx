import uuid

import elasticsearch
import logging

from enum import Enum
from typing import Any

from elasticsearch import Elasticsearch

from agentx.handler.base import BaseHandler
from agentx.handler.elastic_search.exceptions import InvalidElasticsearchAction
from agentx.utils.helper import sync_to_async

logger = logging.getLogger(__name__)

class ElasticsearchAction(str, Enum):
    SEARCH = "search"
    CREATE = "create"


class ElasticsearchHandler(BaseHandler):

    def __init__(
            self,
            addresses: str | None = None,
            cloud_id: str | None = None,
            api_key: str | None = None,
            username: str | None = None,
            password: str | None = None,
            cacert: str | None = None
    ):
        self._conn = Elasticsearch(
            hosts=addresses,
            cloud_id=cloud_id or None,
            api_key=api_key or None,
            basic_auth=(username, password),
            ca_certs=cacert or None
        )

    def handle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:

        """Perform a search with an Exa prompt-engineered query and retrieve a list of relevant results.
           params:
               action(str): Give an action what has given in the Enum.
        """

        if isinstance(action, str):
            action = action.lower()
        match action:
            case ElasticsearchAction.SEARCH:
                return self.search(**kwargs)
            case ElasticsearchAction.CREATE:
                return self.create(**kwargs)
            case _:
                raise InvalidElasticsearchAction(f"Invalid Elasticsearch Action '{action}'")

    async def ahandle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:

        """Perform a search with an Exa prompt-engineered query and retrieve a list of relevant results.
           params:
               action(str): Give an action what has given in the Enum.
        """

        if isinstance(action, str):
            action = action.lower()
        match action:
            case ElasticsearchAction.SEARCH:
                return await self.asearch(**kwargs)
            case ElasticsearchAction.CREATE:
                return await self.acreate(**kwargs)
            case _:
                raise InvalidElasticsearchAction(f"Invalid Elasticsearch Action '{action}'")

    def search(
            self,
            index_name: str,
            query: dict | None = None,
            start_index: int = 0,
            size: int = 20
    ):
        """Perform a search with an Exa prompt-engineered query and retrieve a list of relevant results.
                params:
                    query (dict): The query dict.
                    index_name(str): Given an index name.
                    start_index(int): Starting document offset.
                    size(int):  The number of hits to return.
         """

        result = self._conn.search(
            index=index_name,
            filter_path=['hits'],
            from_=start_index,
            size=size,
            query=query
        )
        return result

    async def asearch(
            self,
            index_name: str,
            query: dict | None = None,
            start_index: int = 0,
            size: int = 20
    ):
        """Perform a search with an Exa prompt-engineered query and retrieve a list of relevant results.
                params:
                    query (dict): The query dict.
                    index_name(str): Given an index name.
                    start_index(int): Starting document offset.
                    size(int):  The number of hits to return.
        """
        result = await sync_to_async(self._conn.search,
            index=index_name,
            filter_path=['hits'],
            from_=start_index,
            size=size,
            query=query
        )
        return result

    def create(
            self,
            index_name: str,
            document: dict
    ):
        """Perform a search with an Exa prompt-engineered query and retrieve a list of relevant results.
                params:
                    index_name(str): Given an index name.
                    document(str):An artificial document (a document not present in the index) for
                    which you want to retrieve term vectors.
        """
        try:
            return self._conn.create(
                index=index_name,
                document=document
            )
        except elasticsearch.BadRequestError as ex:
            logger.error('Elasticsearch error!', exc_info=ex)
            return {}
        except elasticsearch.ConnectionTimeout as ex:
            logger.error(f"Elasticsearch error! {ex}")
            return {}


    async def acreate(
            self,
            index_name: str,
            document: dict
    ):
        """Perform a search with an Exa prompt-engineered query and retrieve a list of relevant results.
            params:
                index_name(str): Given an index name.
                document(str):An artificial document (a document not present in the index) for
                which you want to retrieve term vectors.
        """
        try:
            return await self._conn.create(
                index=index_name,
                document=document
            )
        except elasticsearch.BadRequestError as ex:
            logger.error('Elasticsearch error!', exc_info=ex)
            return {}
        except elasticsearch.ConnectionTimeout as ex:
            logger.error(f"Elasticsearch error! {ex}")
            return {}
