import logging

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from agentx.utils.embed_config import EmbedType, OPENAI_MODELS

logger = logging.getLogger(__name__)


class EmbeddingConfig(BaseModel):
    model: str = Field(
        description='Embedding model to use',
        default=None
    )

    embedding_dims: int = Field(
        description='The number of dimensions in the embedding',
        default=None
    )

    api_key: str | None = Field(
        description='Model API Key either as parameter or from environment',
        default=None
    )

    embed_type: str = Field(
            description=f'Embed embed_type should in anyone of '
                        f'{", ".join(map(lambda member: member.value, EmbedType))}'
    )

    base_url: str | None = Field(
        description='Model API base URL',
        default=None
    )

    api_version: str | None = Field(
        description='API version required for Azure OpenAI embed_type',
        default=None
    )

    async_mode: bool | None = Field(
        description='Asynchronous mode of OpenAI or Azure OpenAI client',
        default=None
    )

    @model_validator(mode="after")
    def __validate_variables__(self) -> Self:
        if not EmbedType.has_member_value(self.llm_type):
            _msg = (
                f'Embed embed_type is should be one of the following '
                f'{", ".join(map(lambda member: member.value, EmbedType))}'
            )
            logger.error(_msg)
            raise ValueError(_msg)

        elif EmbedType.AZURE_OPENAI_CLIENT.value == self.llm_type and not self.api_version:
            raise ValueError('API Version should not be empty for Azure OpenAI')
        return self

    @model_validator(mode="after")
    def __validate_model_name__(self) -> Self:
        # Validate for Open AI. Azure OpenAI deployment model can be custom name. Hence validation not required!!!
        if self.llm_type == EmbedType.OPENAI_CLIENT.value:
            if not self.model:
                self.model = 'gpt-4o'
            elif self.model not in OPENAI_MODELS:
                _msg = (
                    f'Invalid Open AI or Azure Open AI Model - '
                    f'{self.model}. It should be one of the following {", ".join(OPENAI_MODELS)}'
                )
                logger.error(_msg)
                raise ValueError(_msg)
        return self
