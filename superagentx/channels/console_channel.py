# superagentx/human_approval/console.py

import asyncio
import logging
from typing import Callable

from superagentx.channels.base import HumanApprovalChannel

logger = logging.getLogger(__name__)

class ConsoleApprovalChannel(HumanApprovalChannel):

    async def request_approval(
        self,
        *,
        agent_id: str,
        agent_name: str,
        query: str,
        pre_result,
        pipe_id=None,
        conversation_id=None
    ) -> bool:
        loop = asyncio.get_running_loop()

        logger.info("\n" + "=" * 60)
        logger.info(" HUMAN APPROVAL REQUIRED")
        logger.info(f"Agent : {agent_name} ({agent_id})")
        logger.info(f"Query : {query}")
        logger.info(f"Result: {pre_result}")
        logger.info("=" * 60)

        # Explicitly type the blocking callable
        ask: Callable[[], str] = lambda: input("Approve this execution? (y/n): ").strip().lower()

        answer = await asyncio.wait_for(loop.run_in_executor(None, ask), timeout=60.0)
        return answer == "y"