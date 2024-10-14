import datetime
import logging
import uuid
from enum import Enum
from typing import Any, final

from pydantic import ValidationError

from agentx.memory.base import MemoryBase, MemoryItem
from agentx.memory.config import MemoryConfig
from agentx.memory.storage import SQLiteManager
from agentx.utils.helper import iter_to_aiter
from agentx.vector_stores import ChromaDB
from agentx.vector_stores.base import BaseVectorStore

logger = logging.getLogger(__name__)


class Memory(MemoryBase):

    def __init__(
            self,
            memory_config: MemoryConfig = MemoryConfig()
    ):
        self.memory_config = memory_config
        self.db = SQLiteManager(self.memory_config.db_path)
        self.vector_db: BaseVectorStore = self.memory_config.vector_store
        if not self.vector_db:
            self.vector_db: BaseVectorStore = ChromaDB(collection_name="test")

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
        # async with self.db as db:
        #     await db.add_history(*args, **kwargs)
        await self._add_to_vector_store(*args, **kwargs)

    @final
    async def get(self, *args, **kwargs):
        async with self.db as db:
            await db.get_history(*args, **kwargs)
        return self.vector_db.search(*args, **kwargs)

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
        async for data in iter_to_aiter(data):
            if memory_id == data.get("memory_id"):
                message = {
                    "role": data.get("role"),
                    "content": data.get("memory")
                }
                messages.append(message)
        return messages

    async def search(
            self,
            query,
            memory_id: str,
            chat_id: str,
            limit: int = 10,
            filters: dict | None = None
    ) -> list[dict]:
        filters = filters or {}
        if memory_id:
            filters["memory_id"] = memory_id
        # if chat_id:
        #     filters["chat_id"] = chat_id
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
            "chat_id",
            "role",
            "message_id",
            "message",
            "created_at",
            "updated_at",
        }

        original_memories = [
            {
                **MemoryItem(
                    id=mem.id,
                    memory=mem.payload["message"],
                    role=mem.payload["role"],
                    created_at=mem.payload.get("created_at"),
                    updated_at=mem.payload.get("updated_at"),
                    score=mem.score,
                ).model_dump(),
                **{key: mem.payload[key] for key in ["memory_id", "chat_id", "message_id"] if key in mem.payload},
                **(
                    {"metadata": {k: v for k, v in mem.payload.items() if k not in excluded_keys}}
                    if any(k for k in mem.payload if k not in excluded_keys)
                    else {}
                ),
            }
            for mem in memories
        ]

        return original_memories

    async def _add_to_vector_store(
            self,
            *,
            memory_id: str,
            chat_id: str,
            message_id: str,
            role: str | Enum,
            message: str,
            created_at: datetime.datetime | None = None,
            updated_at: datetime.datetime | None = None,
            is_deleted: bool = False,
    ):
        metadata = {}
        if not created_at:
            created_at = str(datetime.datetime.now())
        if not updated_at:
            updated_at = str(datetime.datetime.now())
        metadata["memory_id"] = memory_id
        metadata["message"] = message
        metadata["chat_id"] = chat_id
        metadata["message_id"] = message_id
        metadata["role"] = role
        metadata["created_at"] = str(created_at)
        metadata["updated_at"] = str(updated_at)
        metadata["is_deleted"] = is_deleted
        await self.vector_db.insert(
            texts=[message],
            payloads=metadata,
            ids=[message_id]
        )
