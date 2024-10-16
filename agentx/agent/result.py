from typing import Any

from pydantic import BaseModel

class GoalResult(BaseModel):
    name: str
    id: str
    reason: str
    result: Any
    is_goal_satisfied: bool
