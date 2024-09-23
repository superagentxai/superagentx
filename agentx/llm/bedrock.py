import boto3
from openai.types.chat import ChatCompletion

from agentx.llm.client import Client
from agentx.llm.models import ChatCompletionParams


class BedrockClient(Client):

    def __init__(self, client: boto3.client):
        self.client = client
        super().__init__()

    def chat_completion(self,
                        *,
                        chat_completion_params: ChatCompletionParams):
        pass

    async def achat_completion(self,
                               *,
                               chat_completion_params: ChatCompletionParams) -> ChatCompletion:
        if chat_completion_params:
            tools = chat_completion_params.tools

            if tools:
                messages = chat_completion_params.messages
                messages = [
                    {
                        "role": "user",
                        "content": [{"text": message["content"]} for message in messages],
                    }
                ]

        pass
