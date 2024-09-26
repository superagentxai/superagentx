import logging
import json
import pytest

from agentx.llm import LLMClient, Message
from agentx.llm.models import ChatCompletionParams
from agentx.llm.bedrock import BedrockClient

logger = logging.getLogger(__name__)

# Start a conversation with the user message.
user_message = "What is the most famous song on ABCD?"

conversations = [
            {
                "role": "user",
                "content": user_message
            }
        ]

tools = [
    {
        "toolSpec": {
            "name": "top_song",
            "description": "Get the most popular song played on a radio station.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "sign": {
                            "type": "string",
                            "description": "The call sign for the radio station for which you want the most "
                                           "popular song. Example calls signs are WZPZ, ABCD and WKRP."
                        }
                    },
                    "required": [
                        "sign"
                    ]
                }
            }
        }
    }
]


@pytest.fixture
def aws_bedrock_client_init() -> dict:
    # llm_config = {'model': 'anthropic.claude-3-5-sonnet-20240620-v1:0', 'llm_type': 'bedrock', 'async_mode': True}
    llm_config = {'model': 'mistral.mistral-large-2402-v1:0', 'llm_type': 'bedrock', 'async_mode': True}
    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client}
    return response


class TestAWSBedrockClient:

    async def test_bedrock_client_init(self, aws_bedrock_client_init: dict):
        llm_client: LLMClient = aws_bedrock_client_init.get('llm').client
        assert isinstance(llm_client, BedrockClient)

    async def test_message_format(self):
        formatted_messages = []
        message = {}

        for conversation in conversations:

            if conversation.get('role') == 'user':
                message['role'] = 'user'
                message['content'] = [conversation.get('content')]
                formatted_messages.append(message)
            else:
                formatted_messages.append(conversation)

        logger.info(f'Messages {formatted_messages}')

    async def test_bedrock_aclient_converse(self, aws_bedrock_client_init: dict):
        llm_client: LLMClient = aws_bedrock_client_init.get('llm')

        chat_completion_params = ChatCompletionParams(
            messages=conversations,
            tools=tools
        )

        response = await llm_client.achat_completion(chat_completion_params=chat_completion_params)
        logger.info(response)

    async def test_bedrock_client_converse(self, aws_bedrock_client_init: dict):
        llm_client: LLMClient = aws_bedrock_client_init.get('llm')

        chat_completion_params = ChatCompletionParams(
            messages=conversations,
            tools=tools
        )

        response = llm_client.chat_completion(chat_completion_params=chat_completion_params)
        logger.info(response)

    async def test_bedrock_func_client_converse(self, aws_bedrock_client_init: dict):
        llm_client: LLMClient = aws_bedrock_client_init.get('llm')

        chat_completion_params = ChatCompletionParams(
            messages=conversations,
            tools=tools
        )

        result: [Message] = await llm_client.afunc_chat_completion(chat_completion_params=chat_completion_params)
        logger.info(f'Result {result}')
