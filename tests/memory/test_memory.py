import pytest
import uuid
import logging
from agentx.memory import Memory
from agentx.llm import LLMClient
from agentx.llm.models import ChatCompletionParams

logger = logging.getLogger(__name__)

"""
Run Pytest:  
    
   1. pytest --log-cli-level=INFO tests/memory/test_memory.py::TestMemory::test_add_history

"""
llm_config = {
    "model": "gpt-4o",
    "llm_type": "openai",
}

llm_client = LLMClient(llm_config=llm_config)


@pytest.fixture
def test_memory_init() -> dict:
    memory_client: Memory = Memory()
    datas = {
        "user_id": str(uuid.uuid4().hex),
        "chat_id": str(uuid.uuid4().hex)
    }
    response = {
        "data": datas,
        "client": memory_client
    }
    return response


class TestMemory:

    # def test_conversation(self):
    #     exit_conditions = (":q", "quit", "exit")
    #     while True:
    #         query = input("> ")
    #         role = "user"
    #         if query in exit_conditions:
    #             break
    #         else:
    #             messages = [
    #                 {
    #                     "role": "user"
    #                 }
    #             ]
    #             chat_completion_params = ChatCompletionParams(
    #                 messages=messages,
    #                 seed=34,
    #                 tools=tools,
    #             )
    #             llm_client.chat_completion()

    def test_add_history(self, test_memory_init: dict):
        datas = test_memory_init.get("data")
        client: Memory = test_memory_init.get("client")
        user_input = "Tell me about a Agentic AI Framework"
        role = "user"
        client.add(
            user_id=datas.get("user_id"),
            chat_id=datas.get("chat_id"),
            message_id=str(uuid.uuid4().hex)
        )



