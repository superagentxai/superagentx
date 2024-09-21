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

    def add(self, *args, **kwargs):
        return self.db.add_history(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.db.get_history(*args, **kwargs)

    def get_all(self):
        pass

    def update(self, memory_id, data):
        pass

    def delete(self, *args, **kwargs):
        self.db.reset()
