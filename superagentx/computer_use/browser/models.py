from __future__ import annotations

from pydantic import BaseModel


class StepInfo(BaseModel):
    step_number: int
    max_steps: int

    def is_last_step(self) -> bool:
        """Check if this is the last step"""
        return self.step_number >= self.max_steps - 1


class ToolResult(BaseModel):
    """Result of executing an action"""

    is_done: bool = False
    success: bool | None = None
    extracted_content: str | None = None
    error: str | None = None
    include_in_memory: bool = False  # whether to include in past messages as context or not


class InputTextParams(BaseModel):
    index: int
    text: str
    has_sensitive: bool


class GoToUrl(BaseModel):
    url: str


class ToastConfig(BaseModel):
    font_size: int = 22
    background: str = 'linear-gradient(45deg, #ff6ec4, #7873f5)'
    color: str = 'white'
