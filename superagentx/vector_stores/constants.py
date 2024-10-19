from enum import Enum

DEFAULT_EMBED_MODEL = "text-embedding-ada-002"
DEFAULT_EMBED_TYPE = "openai"


class EmbedTypeEnum(str, Enum):
    OPENAI = "openai"
