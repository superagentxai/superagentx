from typing import Any

from superagentx.agent import Agent
from superagentx.agentxdag import WorkflowContext


class AgentNode:
    """Wraps a SuperAgentX Agent to make it a callable Graph Node."""
    def __init__(self, agent: Agent, approval_required: bool = False):
        self.agent = agent
        self.name = agent.name
        self.approval_required = approval_required

    async def __call__(self, ctx: WorkflowContext) -> Any:
        """
        Makes the instance callable. Maps your workflow context to the
        exact execution signature expected by the SuperAgentX framework.
        """
        # Map parameters cleanly out of your state context layer
        return await self.agent.execute(
            query_instruction=ctx.global_ctx.get("query_instruction"),
            pipe_id=ctx.global_ctx.get("pipe_id"),
            conversation_id=ctx.global_ctx.get("conversation_id")
        )