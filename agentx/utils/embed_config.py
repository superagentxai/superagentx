from enum import Enum


class EmbedType(str, Enum):
    OPENAI_CLIENT = 'openai'
    AZURE_OPENAI_CLIENT = 'azure-openai'
    HUGGINGFACE = 'huggingface'
    OLLAMA = 'ollama'

    @classmethod
    def has_member_key(cls, key):
        return key in cls.__members__

    @classmethod
    def has_member_value(cls, value) -> bool:
        try:
            if cls(value):
                return True
        except ValueError:
            return False


OPENAI_MODELS = [
    "text-embedding-ada-002",
    "text-embedding-3-small",
    "text-embedding-3-large"
]

# Azure Open AI Version - Default
DEFAULT_AZURE_API_VERSION = "2024-02-01"
