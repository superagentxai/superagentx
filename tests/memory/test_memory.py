import datetime

import pytest
import uuid
import logging
from superagentx.memory import Memory
from superagentx.llm import LLMClient
from superagentx.llm.models import ChatCompletionParams

logger = logging.getLogger(__name__)

"""
Run Pytest:  
    
   1. pytest --log-cli-level=INFO tests/memory/test_memory.py::TestMemory::test_add_history
   2. pytest --log-cli-level=INFO tests/memory/test_memory.py::TestMemory::test_get_history
   3. pytest --log-cli-level=INFO tests/memory/test_memory.py::TestMemory::test_reset
   4. pytest --log-cli-level=INFO tests/memory/test_memory.py::TestMemory::test_search
"""
llm_config = {
    "llm_type": "openai",
}

llm_client = LLMClient(llm_config=llm_config)


@pytest.fixture
def test_memory_init() -> dict:
    memory_client: Memory = Memory(memory_config={"llm_client": llm_client})
    datas = {
        "memory_id": "55e497f4010d4eda909691272eaf31fb",
        "chat_id": "915ec91bc2654f8da3af800c0bf6eca9"
    }
    response = {
        "data": datas,
        "client": memory_client
    }
    return response


class TestMemory:

    async def test_add_history(self, test_memory_init: dict):
        datas = test_memory_init.get("data")
        client: Memory = test_memory_init.get("client")
        user_input = "Tell me about a Agentic AI Framework"
        role = "user"
        logger.info(f"User Id: {datas.get('memory_id')}")
        logger.info(f"Chat Id: {datas.get('chat_id')}")
        await client.add(
            memory_id=datas.get("memory_id"),
            chat_id=datas.get("chat_id"),
            message_id=str(uuid.uuid4().hex),
            role=role,
            message=user_input,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            is_deleted=False
        )
        messages = [
            {
                "role": "assistant",
                "content": user_input
            }
        ]
        role = "assistant"
        chat_completion_params = ChatCompletionParams(
            messages=messages
        )
        response = await llm_client.achat_completion(chat_completion_params=chat_completion_params)
        result = response.choices[0].message.content
        await client.add(
            memory_id=datas.get("memory_id"),
            chat_id=datas.get("chat_id"),
            message_id=str(uuid.uuid4().hex),
            role=role,
            message=result
        )

    async def test_get_history(self, test_memory_init: dict):
        datas = test_memory_init.get("data")
        client: Memory = test_memory_init.get("client")
        response = await client.get(
            memory_id=datas.get('memory_id'),
            chat_id=datas.get('chat_id')
        )
        logger.info(f"Result History: {response}")

    async def test_reset(self, test_memory_init: dict):
        client: Memory = test_memory_init.get("client")
        await client.delete()

    async def test_search(self, test_memory_init: dict):
        datas = test_memory_init.get("data")
        client: Memory = test_memory_init.get("client")
        response = await client.search(
            query="agentic",
            memory_id=datas.get("memory_id")
        )
        logger.info(response)
        return response


