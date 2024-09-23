import os
from typing import Optional

from pydantic import BaseModel, Field

from agentx.memory.setup import mem_dir


class MemoryConfig(BaseModel):

    db_path: str = Field(
        description="Path to the database",
        default=os.path.join(mem_dir, "history.db"),
    )

    version: str = Field(
        description="The version of the API",
        default="v1.0",
    )
    custom_prompt: Optional[str] = Field(
        description="Custom prompt for the memory",
        default=None,
    )
