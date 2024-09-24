import logging
from typing import Dict, Any

from pydantic import ValidationError

from agentx.memory.base import MemoryBase
from agentx.memory.config import MemoryConfig
from agentx.memory.storage import SQLiteManager

logger = logging.getLogger(__name__)


class Memory(MemoryBase):

    def __init__(
            self,
            mem_config: MemoryConfig = MemoryConfig()
    ):
        self.config = mem_config
        self.db = SQLiteManager(self.config.db_path)

    @classmethod
    def from_config(cls, config_dict: Dict[str, Any]):
        try:
            _config = MemoryConfig(**config_dict)
        except ValidationError as e:
            logger.error(f"Configuration validation error: {e}")
            raise
        return cls(_config)

    async def add(self, *args, **kwargs):
        async with self.db as db:
            return await db.add_history(*args, **kwargs)

    async def get(self, *args, **kwargs):
        async with self.db as db:
            return await db.get_history(*args, **kwargs)

    async def update(self, memory_id, data):
        pass

    async def delete(self, *args, **kwargs):
        async with self.db as db:
            return await db.reset()
