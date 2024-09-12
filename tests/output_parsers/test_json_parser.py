from openai.types.chat.chat_completion import ChatCompletion, ChatCompletionMessage
from agentx.llm import LLMClient
from agentx.llm.openai import ChatCompletionParams

import json

llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

llm_client: LLMClient = LLMClient(llm_config=llm_config)

messages = [{"content": "Return ONLY JSON object"
                        "Input: List top five billionaires"

             }]

params = ChatCompletionParams(
    messages=messages,
).model_dump(exclude_none=True)

response: ChatCompletion = llm_client.chat_completion(params=params)
for choice in response.choices:
    message: ChatCompletionMessage = choice.message
    print(message.content)
