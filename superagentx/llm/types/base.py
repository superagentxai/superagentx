import logging

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from superagentx.utils.llm_config import LLMType, OPENAI_MODELS, BEDROCK_MODELS

logger = logging.getLogger(__name__)


class LLMModelConfig(BaseModel):
    model: str | None = Field(
        description='LLM model name, supported models openai, azure-openai, mistral, llama 3.1',
        default=None
    )

    api_key: str | None = Field(
        description='Model API Key either as parameter or from environment',
        default=None
    )

    llm_type: str | None = Field(
        description=f'LLM llm_type should in anyone of '
                    f'{", ".join(map(lambda member: member.value, LLMType))}',
        default=None
    )

    base_url: str | None = Field(
        description='Model API base URL',
        default=None
    )

    api_version: str | None = Field(
        description='API version required for Azure OpenAI llm_type',
        default=None
    )

    async_mode: bool | None = Field(
        description='Asynchronous mode of OpenAI or Azure OpenAI client',
        default=True
    )

    embed_model: str | None = Field(
        description='Embedding model name, supported models openai, azure-openai, mistral, llama 3.1',
        default=None
    )
