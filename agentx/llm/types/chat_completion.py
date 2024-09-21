from pydantic import BaseModel
from typing import List, Optional


class ChatCompletionMessage(BaseModel):
    content: str
    refusal: Optional[str]
    role: str
    function_call: Optional[str]
    tool_calls: Optional[str]


class Choice(BaseModel):
    finish_reason: str
    index: int
    logprobs: Optional[str]
    message: ChatCompletionMessage


class CompletionUsage(BaseModel):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int


class ChatCompletion(BaseModel):
    id: str
    choices: List[Choice]
    created: int
    model: str
    object: str
    service_tier: Optional[str]
    system_fingerprint: str
    usage: CompletionUsage
