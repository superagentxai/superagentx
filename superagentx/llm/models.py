import uuid
from typing import Any

from pydantic import BaseModel, Field, conlist, conint


class Message(BaseModel):
    role: str = Field(
        description='the role of the messenger (either system, user, assistant or tool)',
        default='system'
    )
    content: Any = Field(
        description='the content of the message (e.g., Write me a beautiful poem)'
    )
    name: str | None = Field(
        description='Messages can also contain an optional name field, which give the messenger a name',
        default=None
    )


class ChatCompletionParams(BaseModel):
    # Required parameters
    model: str | None = Field(
        description='the name of the model you want to use (e.g., gpt-3.5-turbo, gpt-4, gpt-3.5-turbo-16k-1106)',
        default=None
    )
    messages: conlist(Message, min_length=1) = Field(
        description='the content of the message (e.g., Write me a beautiful poem)'
    )
    # Optional parameters
    frequency_penalty: float | None = Field(
        description='Penalizes tokens based on their frequency, reducing repetition.',
        default=None
    )
    logit_bias: dict[str, float] | None = Field(
        description='Modifies likelihood of specified tokens with bias values.',
        default=None
    )
    logprobs: bool | None = Field(
        description='Returns log probabilities of output tokens if true.',
        default=False
    )
    top_logprobs: conint(ge=0) | None = Field(
        description='Specifies the number of most likely tokens to return at each position.',
        default=None
    )
    max_tokens: int | None = Field(
        description='Sets the maximum number of generated tokens in chat completion.',
        default=None
    )
    n: int | None = Field(
        description='Generates a specified number of chat completion choices for each input.',
        default=1
    )
    presence_penalty: float | None = Field(
        description='Penalizes new tokens based on their presence in the text.',
        default=0
    )
    response_format: Any | None = Field(
        description='Specifies the output format, e.g., JSON mode.',
        default=None
    )
    seed: int | None = Field(
        description='Ensures deterministic sampling with a specified seed.',
        default=None
    )
    service_tier: str | None = Field(
        description='Specifies the latency tier to use for processing the request. '
                    'This parameter is relevant for customers subscribed to the scale'
                    ' tier service:',
        default=None
    )
    stop: str | list[str] | None = Field(
        description='Specifies up to 4 sequences where the API should stop generating tokens.',
        default=None
    )
    stream: bool | None = Field(
        description='Sends partial message deltas as tokens become available.',
        default=False
    )
    temperature: float | None = Field(
        description='Sets the sampling temperature between 0 and 2.',
        default=None
    )
    top_p: float | None = Field(
        description='Uses nucleus sampling; considers tokens with top_p probability mass.',
        default=None
    )
    tools: list[dict] | None = Field(
        description='Lists functions the model may call.',
        default=None
    )
    tool_choice: str | None = Field(
        description='Controls the model function calls (none/auto/function).',
        default=None
    )
    user: str = Field(
        description="Unique identifier for end-user monitoring and abuse detection.",
        default=f'{uuid.uuid4()}'
    )
    performance_config: bool | None = Field(
        description="Latency-optimized inference for foundation models in Amazon Bedrock delivers faster response"
                    " times and improved responsiveness for AI applications",
        default=None
    )
