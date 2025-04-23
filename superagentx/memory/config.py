import os
from pathlib import Path

from pydantic import BaseModel, Field
from superagentx.vector_stores.base import BaseVectorStore
from superagentx.llm import LLMClient


def _db_path():
    _db_dir = os.environ.get('AGENTX_MEMORY_DIR')
    if not _db_dir:
        return ":memory:"
    else:
        _db_dir = Path(_db_dir)
        return _db_dir / 'history.db'


class MemoryConfig(BaseModel):
    vector_store: BaseVectorStore | None = Field(
        description="Configuration for the vector store",
        default=None,
    )

    db_path: str | None = Field(
        description="Path to the history database",
        default=_db_path(),
    )

    llm_client: LLMClient | None = Field(
        description="Configuration for the LLM",
        default=None,
    )

    class Config:
        arbitrary_types_allowed = True
