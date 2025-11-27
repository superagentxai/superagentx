import pytest
from superagentx.task_engine import TaskEngine
from superagentx.handler.task.general.dummy_handler import DummyHandler

'''
 pytest tests/task/test_safe_code_exec.py -q
'''


@pytest.mark.asyncio
async def test_safe_code_exec():
    engine = TaskEngine(
        handler=DummyHandler(),
        code="x = 5\ny = x * 2"
    )
    result = await engine.start("test")

    locals_dict = result[0]["code"]["locals"]
    assert locals_dict["x"] == 5
    assert locals_dict["y"] == 10
