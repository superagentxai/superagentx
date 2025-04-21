from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel


@dataclass
class StepInfo:
    step_number: int
    max_steps: int

    def is_last_step(self) -> bool:
        """Check if this is the last step"""
        return self.step_number >= self.max_steps - 1


class ToolResult(BaseModel):
    """Result of executing an action"""

    is_done: Optional[bool] = False
    success: Optional[bool] = None
    extracted_content: Optional[str] = None
    error: Optional[str] = None
    include_in_memory: bool = False  # whether to include in past messages as context or not
