import datetime
from datetime import timedelta
import logging
from enum import Enum
from typing import Any, final

from pydantic import ValidationError

from superagentx.llm import LLMClient
from superagentx.memory.base import MemoryBase, MemoryItem
from superagentx.memory.config import MemoryConfig
from superagentx.memory.storage import SQLiteManager
from superagentx.utils.helper import iter_to_aiter
from superagentx.vector_stores import ChromaDB
from superagentx.vector_stores.base import BaseVectorStore
from superagentx.constants import DATE_TIME_FORMAT

logger = logging.getLogger(__name__)

COLLECTION_NAME = "agent"


class Memory(MemoryBase):

    def __init__(
            self,
            memory_config: dict
    ):
        self.memory_config = MemoryConfig(**memory_config)
        self.db = SQLiteManager(self.memory_config.db_path)
        self.vector_db: BaseVectorStore = self.memory_config.vector_store
        llm_client: LLMClient = self.memory_config.llm_client
        if not self.vector_db:
            self.vector_db: BaseVectorStore = ChromaDB(
                collection_name=COLLECTION_NAME,
                embed_cli=llm_client
            )

    @staticmethod
    def _from_config(config_dict: dict[str, Any]):
        try:
            _config = MemoryConfig(**config_dict)
        except ValidationError as e:
            logger.error(f"Configuration validation error: {e}")
            raise
        return _config

    @final
    async def add(self, *args, **kwargs):
        async with self.db as db:
            await db.add_history(*args, **kwargs)
        await self._add_to_vector_store(*args, **kwargs)

    @final
    async def get(self, *args, **kwargs):
        async with self.db as db:
            return await db.get_history(*args, **kwargs)

    @final
    async def update(self, memory_id, data):
        pass

    @final
    async def delete(self, *args, **kwargs):
        async with self.db as db:
            await db.reset()
        await self.vector_db.delete_collection()

    @staticmethod
    async def _get_history(memory_id: str, data) -> list[dict]:
        messages = []
        async for _data in iter_to_aiter(data):
            if memory_id == _data.get("memory_id"):
                message_construct = f"Reason: {_data.get('reason')}\nResult: {_data.get('memory')}"
                message = {
                    "role": _data.get("role"),
                    "content": message_construct
                }
                messages.append(message)
        return messages

    @staticmethod
    async def _epoch_to_timestamp(epoch_time):
        # Convert to datetime (UTC)
        dt_object = datetime.datetime.fromtimestamp(epoch_time)
        return dt_object.strftime(DATE_TIME_FORMAT)

    async def search(
            self,
            query: str,
            memory_id: str,
            limit: int = 10,
            filters: dict | None = None,
            conversation_id: str | None = None
    ) -> list[dict]:
        if not conversation_id:
            conversation_id = ""
        if not filters:
            filters = await self._filter(
                conversation_id=conversation_id,
                memory_id=memory_id
            )
        result = await self._search_vector_store(
            query=query,
            filters=filters,
            limit=limit
        )
        return await self._get_history(
            memory_id=memory_id,
            data=result
        )

    async def _search_vector_store(
            self,
            query: str,
            filters: dict,
            limit: int
    ):
        memories = await self.vector_db.search(
            query=query,
            limit=limit,
            filters=filters
        )
        excluded_keys = {
            "memory_id",
            "conversation_id",
            "role",
            "message_id",
            "data",
            "reason",
            "created_at",
            "updated_at",
        }

        original_memories = [
            {
                **MemoryItem(
                    id=mem.id,
                    memory=mem.payload["data"],
                    reason=mem.payload["reason"],
                    role=mem.payload["role"],
                    created_at=await self._epoch_to_timestamp(mem.payload.get("created_at")),
                    updated_at=await self._epoch_to_timestamp(mem.payload.get("updated_at")),
                    score=mem.score,
                ).model_dump(),
                **{key: mem.payload[key] for key in ["memory_id", "conversation_id", "message_id"] if
                   key in mem.payload},
                **(
                    {"metadata": {k: v for k, v in mem.payload.items() if k not in excluded_keys}}
                    if any(k for k in mem.payload if k not in excluded_keys)
                    else {}
                ),
            }
            async for mem in iter_to_aiter(memories)
        ]
        return original_memories

    async def _add_to_vector_store(
            self,
            *,
            memory_id: str,
            conversation_id: str,
            message_id: str,
            role: str | Enum,
            data: str,
            reason: str,
            created_at: datetime.datetime | None = None,
            updated_at: datetime.datetime | None = None,
            is_deleted: bool = False,
    ):
        metadata = {}
        if not created_at:
            created_at = datetime.datetime.now()
        if not updated_at:
            updated_at = datetime.datetime.now()
        if not conversation_id:
            conversation_id = ""
        if isinstance(created_at, datetime.datetime):
            created_at = created_at.timestamp()

        if isinstance(updated_at, datetime.datetime):
            updated_at = updated_at.timestamp()

        metadata["memory_id"] = memory_id
        metadata["data"] = data
        metadata["reason"] = reason
        metadata["conversation_id"] = conversation_id
        metadata["message_id"] = message_id
        metadata["role"] = role
        metadata["created_at"] = created_at
        metadata["updated_at"] = updated_at
        metadata["is_deleted"] = is_deleted
        await self.vector_db.insert(
            texts=[data],
            payloads=metadata,
            ids=[message_id]
        )

    async def delete_by_conversation_id(self, **kwargs):
        await self.vector_db.delete_by_conversation_id(**kwargs)

    @staticmethod
    async def _filter(conversation_id: str, memory_id: str):
        now = datetime.datetime.now()
        # Calculate time ranges
        now_epoch = now.timestamp()

        # Calculate past time ranges
        five_seconds_ago = (now - timedelta(seconds=5)).timestamp()
        five_minutes_ago = (now - timedelta(minutes=5)).timestamp()
        five_hours_ago = (now - timedelta(hours=5)).timestamp()

        filters = {"$and": [
            {"conversation_id": {"$eq": conversation_id}},
            {"memory_id": {"$eq": memory_id}},  # Direct condition
            {
                "$or": [
                    {
                        "$and": [
                            {"created_at": {"$gte": five_seconds_ago}},
                            {"created_at": {"$lte": now_epoch}}
                        ]
                    },
                    {
                        "$and": [
                            {"created_at": {"$gte": five_minutes_ago}},
                            {"created_at": {"$lte": now_epoch}}
                        ]
                    },
                    {
                        "$and": [
                            {"created_at": {"$gte": five_hours_ago}},
                            {"created_at": {"$lte": now_epoch}}
                        ]
                    }
                ]
            }
        ]}
        return filters
