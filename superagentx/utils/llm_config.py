from enum import Enum


class LLMType(str, Enum):
    OPENAI_CLIENT = 'openai'
    AZURE_OPENAI_CLIENT = 'azure-openai'
    LLAMA_CLIENT = 'llama'
    GEMINI_CLIENT = 'gemini'
    MISTRAL_CLIENT = 'mistral'
    BEDROCK_CLIENT = 'bedrock'
    TOGETHER_CLIENT = 'together'
    GROQ_CLIENT = 'groq'
    ANTHROPIC_CLIENT = 'anthropic'

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
    "gpt-4o",
    "gpt-4o-2024-05-13",
    "gpt-4o-2024-08-06",
    "gpt-4-turbo-2024-04-09",
    "gpt-4",
    "gpt-4o-mini-2024-07-18",
    "gpt-4o-mini",
    "gpt-3.5-turbo",
    "text-embedding-ada-002",
    "text-embedding-3-small",
    "text-embedding-3-large"
]

# Azure Open AI Version - Default
DEFAULT_AZURE_API_VERSION = "2024-02-01"
