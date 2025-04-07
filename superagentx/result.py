from typing import Any

from pydantic import BaseModel


class GoalResult(BaseModel):
    name: str
    agent_id: str
    reason: str | None = None
    result: Any | None = None
    content: Any | None = None
    error: str | None = None
    verify_goal: bool = True
    is_goal_satisfied: bool | None = None
