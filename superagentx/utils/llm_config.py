from enum import Enum


class LLMType(str, Enum):
    OPENAI_CLIENT = 'openai'
    AZURE_OPENAI_CLIENT = 'azure-openai'
    DEEPSEEK = 'deepseek'
    LLAMA_CLIENT = 'llama'
    GEMINI_CLIENT = 'gemini'
    MISTRAL_CLIENT = 'mistral'
    BEDROCK_CLIENT = 'bedrock'
    TOGETHER_CLIENT = 'together'
    GROQ_CLIENT = 'groq'
    ANTHROPIC_CLIENT = 'anthropic'
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
    "gpt-4.1",
    "gpt-4o",
    "gpt-4o-2024-05-13",
    "gpt-4o-2024-08-06",
    "gpt-4-turbo-2024-04-09",
    "gpt-4",
    "gpt-4o-mini-2024-07-18",
    "gpt-4o-mini",
    "text-embedding-ada-002",
    "text-embedding-3-small",
    "text-embedding-3-large"
]

BEDROCK_MODELS = [
    'anthropic.claude-3-5-sonnet-20241022-v2:0',
    'anthropic.claude-3-5-haiku-20241022-v1:0',
    'anthropic.claude-instant-v1:2:100k',
    'anthropic.claude-3-sonnet-20240229-v1:0',
    'anthropic.claude-3-haiku-20240307-v1:0',
    'anthropic.claude-3-opus-20240229-v1:0',
    'anthropic.claude-3-5-sonnet-20240620-v1:0',
    'cohere.command-r-v1:0',
    'cohere.command-r-plus-v1:0',
    'meta.llama3-1-8b-instruct-v1:0',
    'meta.llama3-1-70b-instruct-v1:0',
    'meta.llama3-1-405b-instruct-v1:0',
    'meta.llama3-2-11b-instruct-v1:0',
    'meta.llama3-2-90b-instruct-v1:0',
    'meta.llama3-2-1b-instruct-v1:0',
    'meta.llama3-2-3b-instruct-v1:0',
    'mistral.mistral-large-2402-v1:0',
    'mistral.mistral-large-2407-v1:0'
]

ANTHROPIC_MODELS = [
    'claude-3-5-sonnet-20241022',
    'claude-3-5-haiku-20241022',
    'claude-3-opus-20240229',
    'claude-3-sonnet-20240229',
    'claude-3-haiku-20240307'
]

DEEPSEEK_MODELS = [
    "deepseek-chat",
]

OLLAMA_MODELS = [
    "mistral:latest",
    "llama3.3:latest",
]

# Azure Open AI Version - Default
DEFAULT_AZURE_API_VERSION = "2024-02-01"
