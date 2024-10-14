from typing import Any

from pydantic import BaseModel

class GoalResult(BaseModel):
    reason: str
    result: Any
    is_goal_satisfied: bool
