import asyncio
import logging
import uuid
from typing import Literal, Any

import yaml

from superagentx.agent import Agent
from superagentx.config import is_verbose_enabled
from superagentx.constants import SEQUENCE, PARALLEL
from superagentx.exceptions import StopSuperAgentX
from superagentx.result import GoalResult
from superagentx.utils.helper import iter_to_aiter

is_verbose_enabled()

logger = logging.getLogger(__name__)


class AgentXPipe:

    def __init__(
            self,
            *,
            pipe_id: str | None = None,
            name: str | None = None,
            description: str | None = None,
            agents: list[Agent | list[Agent]] | None = None,
            memory: Any | None = None,
            stop_if_goal_not_satisfied: bool = False
    ):
        """
        Initializes a new instance of the class with specified parameters.

        This constructor sets up an object that can manage a collection of agents,
        define a goal and role, and utilize a prompt for processing. Each instance
        can be uniquely identified by the `pipe_id`, which defaults to a newly
        generated UUID if not provided. This structure is particularly useful for
        organizing and executing workflows that involve multiple agents working
        toward a common goal.

        Args:
            pipe_id: A unique identifier for the agentxpipe. If not provided, a new UUID
                will be generated by default. Useful for tracking or referencing
                the agentxpipe in multi-engine environments.
            name: An optional name for the agentxpipe, providing a more friendly reference for display or
                logging purposes.
            description: An optional description that provides additional context or details about the agentxpipe's
                purpose and capabilities.
            agents: A list of Agent instances (or lists of Agent instances) that are part of this structure.
                These agents can perform tasks and contribute to achieving the defined goal.
            memory: An optional memory instance that allows the engine to retain information across interactions.
                This can enhance the pipe's contextual awareness and improve its performance over time.
            stop_if_goal_not_satisfied: A flag indicating whether to stop processing if the goal is not satisfied.
                When set to True, the agentxpipe operation will halt if the defined goal is not met,
                preventing any further actions. Defaults to False, allowing the process to continue regardless
                of goal satisfaction.
        """
        self.pipe_id = pipe_id or uuid.uuid4().hex
        self.name = name or f'{self.__str__()}-{self.pipe_id}'
        self.description = description
        self.agents: list[Agent | list[Agent]] = agents or []
        self.memory = memory
        if self.memory:
            self.memory_id = uuid.uuid4().hex
        self.stop_if_goal_not_satisfied = stop_if_goal_not_satisfied

        logger.debug(
            f'Initiating AgentXPipe...\n'
            f'Id : {self.pipe_id}\n'
            f'Name : {self.name}\n'
            f'Description : {self.description}\n'
            f'Agents Associated : {",".join([str(_agent) for _agent in self.agents])}\n'
            f'Memory Configured : {self.memory}\n'
            f'Stop if goal not satisfied configured : {self.stop_if_goal_not_satisfied}\n'
        )

    def __str__(self):
        return "AgentXPipe"

    def __repr__(self):
        return f"<{self.__str__()}>"

    async def add(
            self,
            *agents: Agent,
            execute_type: Literal['SEQUENCE', 'PARALLEL'] = 'SEQUENCE'
    ) -> None:
        """
        Adds one or more Agent instances to the current context for processing.

        This method allows the user to include multiple agents that will be used
        for execution based on the specified execution type. The `execute_type`
        parameter determines how the engines will be run: either in a sequence,
        where each engine runs one after the other, or in parallel, where all
        specified agents run concurrently.

        Args:
            agents: One or more Agent instances to be added to the context.
                This allows for flexibility in processing and task execution based on different capabilities
                or configurations.
            execute_type: The method of execution for the added engines.
                - 'SEQUENCE': Agents are executed one after another,
                  waiting for each to complete before starting the next.
                - 'PARALLEL': All agents are executed concurrently, allowing for
                  simultaneous processing.
                Default is 'SEQUENCE'.

        Returns:
            None
        """
        if execute_type == SEQUENCE:
            self.agents += agents
            logger.debug(f'Agent(s) added as {SEQUENCE} : {",".join([str(_agent) for _agent in agents])}')
        else:
            self.agents.append(list(agents))
            logger.debug(f'Agents added as {PARALLEL} : {",".join([str(_agent) for _agent in agents])}')

    @staticmethod
    async def _pre_result(
            results: list[GoalResult] | None = None
    ) -> list[str]:
        if not results:
            return []
        return [
            (f'Reason: {result.reason}\n'
             f'Result: \n{yaml.dump(result.result)}\n'
             f'Is Goal Satisfied: {result.is_goal_satisfied}\n\n')
            async for result in iter_to_aiter(results)
        ]

    async def add_memory(
            self,
            prompt_instruction: list[dict],
            conversation_id: str | None = None
    ) -> None:
        """
        Adds a list of prompt instructions to the memory of the engine.

        This method is designed to enhance the engine's contextual awareness by storing
        relevant prompt instructions in its memory. The stored instructions can be
        referenced in future interactions, allowing the engine to recall important
        information and improve its responses over time.

        Args:
            prompt_instruction: A list of dictionaries containing prompt instructions to be added to the engine's memory.
                Each dictionary should contain structured data relevant to the prompts, which may include keys such as
                'text', 'context', or any other relevant attributes that define the prompt instructions.
            conversation_id: A string representing the unique identifier of the conversation.

        Returns:
            None
        """
        logger.debug(f'Add prompt instruction to the memory : {prompt_instruction}')
        async for prompt in iter_to_aiter(prompt_instruction):
            await self.memory.add(
                memory_id=self.memory_id,
                conversation_id=conversation_id,
                message_id=uuid.uuid4().hex,
                role=prompt.get("role"),
                data=prompt.get("content"),
                reason=prompt.get("reason")
            )

    async def retrieve_memory(
            self,
            query_instruction: str,
            conversation_id: str | None = None
    ) -> list[dict]:
        """
        Retrieves a list of prompt instructions from the engine's memory based on the provided query instruction.

        This method allows the engine to search its memory for stored prompt instructions
        that match or are relevant to the given query. The retrieved instructions can be
        used to inform responses, provide context, or assist in decision-making during
        future interactions.

        Args:
            query_instruction: A string representing the query used to search the engine's memory.
                This instruction should be formulated in a way that allows the engine to identify relevant stored
                prompts.
            conversation_id: A string representing the unique identifier of the conversation.

        Returns:
            list[dict]
                A list of dictionaries containing the retrieved prompt instructions that match the query.
                Each dictionary represents an instruction and may contain keys such as 'text', 'context',
                and other relevant attributes that describe the prompt.
        """
        logger.debug(f'Retrieving memory by query : {query_instruction}')
        return await self.memory.search(
            query=query_instruction,
            memory_id=self.memory_id,
            limit=10,
            conversation_id=conversation_id
        )

    async def _flow(
            self,
            query_instruction: str,
            verify_goal: bool = True,
            conversation_id: str | None = None
    ):
        trigger_break = False
        results = []
        old_memory = None
        async for _agents in iter_to_aiter(self.agents):
            pre_result = await self._pre_result(results=results)
            logger.debug(f'Updated with previous results.\nPrevious Result : {pre_result}')
            if self.memory:
                old_memory = await self.retrieve_memory(query_instruction, conversation_id=conversation_id)
                logger.debug(f"Updated with old memory.\n{old_memory}")
            try:
                if isinstance(_agents, list):
                    logger.debug(f'Agent(s) are executing : {",".join([str(_agent) for _agent in _agents])}')
                    _res = await asyncio.gather(
                        *[
                            _agent.execute(
                                query_instruction=query_instruction,
                                pre_result=pre_result,
                                old_memory=old_memory,
                                verify_goal=verify_goal,
                                stop_if_goal_not_satisfied=self.stop_if_goal_not_satisfied,
                                conversation_id=conversation_id
                            )
                            async for _agent in iter_to_aiter(_agents)
                        ]
                    )
                    logger.debug(f'Agent(s) results : {_res}')
                else:
                    logger.debug(f'Agent is executing : {_agents}')
                    _res = await _agents.execute(
                        query_instruction=query_instruction,
                        pre_result=pre_result,
                        old_memory=old_memory,
                        verify_goal=verify_goal,
                        stop_if_goal_not_satisfied=self.stop_if_goal_not_satisfied,
                        conversation_id=conversation_id
                    )
                    logger.debug(f'Agent result : {_res}')
                if self.memory:
                    if _res.result and _res.reason:
                        assistant = {
                            "role": "assistant",
                            "content": f"{yaml.dump(_res.result)}",
                            "reason": _res.reason
                        }
                        await self.add_memory(
                            [assistant],
                            conversation_id=conversation_id
                        )
            except StopSuperAgentX as ex:
                trigger_break = True
                logger.warning(ex)
                _res = ex.goal_result

            if _res:
                results.append(_res)
            if trigger_break:
                break
        return results

    async def flow(
            self,
            query_instruction: str,
            verify_goal: bool = True,
            conversation_id: str | None = None
    ) -> list[GoalResult]:
        """
        Processes the specified query instruction and executes a flow of operations.

        This method interprets the `query_instruction` and coordinates a series of
        actions aimed at achieving the associated goals. It can involve multiple agents
        and may utilize previously defined workflows to effectively generate results.
        The method returns a list of GoalResult instances that indicate the outcomes of
        the executed operations.

        Args:
            query_instruction: A string representing the instruction or query that defines the goal to be achieved.
                This should be a clear and actionable statement that the method can execute.
            verify_goal: Option to enable or disable goal verification after agent execution. Default `True`
            conversation_id: A string representing the unique identifier of the conversation. Default `None`

        Returns:
            list[GoalResult]
                A list of GoalResult instances representing the outcomes of the operations executed in response to
                the query instruction. Each GoalResult provides details about the success or failure of the
                corresponding operation and may include additional context or data.
        """
        logger.info(f"Pipe {self.name} starting...")
        return await self._flow(
            query_instruction=query_instruction,
            verify_goal=verify_goal,
            conversation_id=conversation_id
        )
