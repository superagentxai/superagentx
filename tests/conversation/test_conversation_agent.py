import datetime
import logging
import uuid
from enum import Enum

import pytest

from agentx.io import IOConsole
from agentx.llm import LLMClient, ChatCompletionParams
from agentx.memory import Memory
from agentx.utils.console_color import ConsoleColorType
from agentx.utils.helper import iter_to_aiter

logger = logging.getLogger(__name__)


class RoleEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


'''PyTest

    1. pytest -s --log-cli-level=INFO tests/conversation/test_conversation_agent.py::TestConversationAgent::test_conversation_agent
'''


@pytest.fixture
def clients_init() -> dict:
    io_console = IOConsole()
    llm_config = {
        "model": "gpt-4o",
        "llm_type": "openai",
        "async_mode": True
    }
    llm_client = LLMClient(llm_config=llm_config)
    memory_client: Memory = Memory()
    response = {"io_console": io_console, "llm_client": llm_client, "memory_client": memory_client}
    return response


class TestConversationAgent:

    @staticmethod
    async def _llm_response(messages: list, llm_client: LLMClient):
        system = [{
            "role": "system",
            "content": "You are a helpful assistant."
        }]
        message = system + messages
        logger.info(f"Message: {message}")

        chat_completion_params = ChatCompletionParams(
            messages=message
        )
        response = await llm_client.achat_completion(chat_completion_params=chat_completion_params)
        result = response.choices[0].message.content
        return result

    @staticmethod
    async def _get_history(user_id: str, chat_id: str, memory_client: Memory) -> list[dict]:
        messages = []
        response = await memory_client.get(
            user_id=user_id,
            chat_id=chat_id
        )

        async for data in iter_to_aiter(response):
            if (user_id == data.get("user_id")) and (chat_id == data.get("chat_id")):
                message = {
                    "role": data.get("role"),
                    "content": data.get("message")
                }
                messages.append(message)
        return messages

    async def test_conversation_agent(self, clients_init: dict):
        io_console: IOConsole = clients_init.get("io_console")
        llm_client: LLMClient = clients_init.get("llm_client")
        memory_client: Memory = clients_init.get("memory_client")

        exit_conditions = (":q", "quit", "exit")

        logging.info(f"IO Console Print & Input Test.")

        await io_console.write(ConsoleColorType.CYELLOW2.value, end="")
        await io_console.write("Hello, Super AgentX World!", flush=True)

        user_id = "55e497f4010d4eda909691272eaf31fb"
        chat_id = "915ec91bc2654f8da3af800c0bf6eca9"

        while True:
            # Getting input from the console
            await io_console.write(ConsoleColorType.CYELLOW2.value, end="")
            data = await io_console.read("User: ")
            await memory_client.add(
                user_id=user_id,
                chat_id=chat_id,
                message_id=str(uuid.uuid4().hex),
                event="ADD",
                role=RoleEnum.USER,
                message=data,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
                is_deleted=False
            )
            get_message = await self._get_history(user_id, chat_id, memory_client)
            llm_res = await self._llm_response(get_message, llm_client)
            await memory_client.add(
                user_id=user_id,
                chat_id=chat_id,
                message_id=str(uuid.uuid4().hex),
                event="ADD",
                role=RoleEnum.ASSISTANT,
                message=llm_res,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
                is_deleted=False
            )
            if data in exit_conditions:
                break
            else:
                await io_console.write(ConsoleColorType.CGREEN2.value, end="")
                await io_console.write(f"Assistant: {llm_res}", flush=True)
