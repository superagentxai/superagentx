import pytest
from superagentx.task_engine import TaskEngine
from superagentx.handler.task.general.dummy_handler import DummyHandler

'''
 pytest tests/task/test_sequential_execution.py -q
'''


@pytest.mark.asyncio
async def test_sequence_execution():
    engine = TaskEngine(
        handler=DummyHandler(),
        instructions=[
            {"get_name": {}},
            {"greet": {"name": "$prev.name"}},
        ]
    )

    result = await engine.start("seq test")
    assert result[0]["get_name"]["success"] is True
    assert result[1]["greet"]["result"]["greeting"] == "Hello SuperAgentX!"
