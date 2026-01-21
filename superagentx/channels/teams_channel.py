from abc import ABC
from typing import Any

from superagentx.channels.base import HumanApprovalChannel


class TeamsApprovalChannel(HumanApprovalChannel, ABC):

    async def request_approval(self, *, agent_id: str, agent_name: str, query: str, pre_result: Any,
                               pipe_id: str | None = None, conversation_id: str | None = None) -> bool:
        pass