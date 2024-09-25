import logging
from typing import Any, final

from pydantic import ValidationError

from agentx.memory.base import MemoryBase
from agentx.memory.config import MemoryConfig
from agentx.memory.storage import SQLiteManager

logger = logging.getLogger(__name__)


class Memory(MemoryBase):

    def __init__(
            self,
            memory_config: MemoryConfig = MemoryConfig()
    ):
        self.memory_config = memory_config
        self.db = SQLiteManager(self.memory_config.db_path)

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
            return await db.add_history(*args, **kwargs)

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
            return await db.reset()
