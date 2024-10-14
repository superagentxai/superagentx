import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


def _db_path():
    _db_dir = os.environ.get('AGENTX_MEMORY_DIR')
    if not _db_dir:
        _db_dir = Path().home()
    else:
        _db_dir = Path(_db_dir)
    return _db_dir / 'history.db'


class MemoryConfig(BaseModel):

    db_path: Path = Field(
        description="Path to the database",
        default_factory=_db_path
        # default=os.path.join(mem_dir, "history.db"),
    )

    version: str = Field(
        description="The version of the API",
        default="v1.0",
    )
    custom_prompt: Optional[str] = Field(
        description="Custom prompt for the memory",
        default=None,
    )
