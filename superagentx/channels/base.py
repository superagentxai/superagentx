# superagentx/human_approval/base.py

from abc import ABC, abstractmethod
from typing import Any

class HumanApprovalChannel(ABC):

    @abstractmethod
    async def request_approval(
        self,
        *,
        agent_id: str,
        agent_name: str,
        query: str,
        pre_result: Any,
        pipe_id: str | None = None,
        conversation_id: str | None = None
    ) -> bool:
        """Return True if approved, False if rejected"""
        pass
