import pytest

from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.task_engine import TaskEngine
from superagentx.handler.task.general.dummy_handler import DummyHandler

'''
 pytest tests/task/test_sequential_execution.py -q
'''


@pytest.mark.asyncio
async def test_sequence_execution():
    engine_1 = TaskEngine(
        handler=DummyHandler(),
        instructions=[
            {"get_name": {}},
        ]
    )

    engine_2 = TaskEngine(
        handler=DummyHandler(),
        instructions=[
            {"get_age": {}},
        ]
    )

    engine_3 = TaskEngine(
        handler=DummyHandler(),
        instructions=[
            {"greet": {'name':'$prev_result.get_name.name'}},
        ]
    )

    task_agent1 = Agent(
        llm=None,
        engines=[engine_1],
        goal=None,
        tool=None,
        role=None,
        agent_id='task-1780567471277',
        name='Task Agent1',
        capabilities=[],
        description='',
        human_approval=False,
        output_format='json',
        max_retry=1
    )

    task_agent2 = Agent(
        engines=[engine_2],
        agent_id='task-1780548717837',
        name='Task Agent2',
        capabilities=[],
        description='',
        human_approval=False,
        output_format='json',
        max_retry=1
    )

    task_agent3 = Agent(
        engines=[engine_3],
        agent_id='task-1780548717838',
        name='Task Agent3',
        capabilities=[],
        description='',
        human_approval=False,
        output_format='json',
        max_retry=1
    )

    # Pipe
    pipe_1 = AgentXPipe(
        agents=[[task_agent1, task_agent2],task_agent3],
        memory=[],
        pipe_id=None,
        name='superagentx pipe',
        description='',
        router=None,
        stop_if_goal_not_satisfied=False
    )

    result = await pipe_1._flow(query_instruction="greet")
    print(result)
