import logging
import copy
from enum import Enum
from typing import Any

from superagentx.constants import DEFAULT
from superagentx.exceptions import InvalidType


class PromptTypeEnum(str, Enum):
    DEFAULT = "default"
    REACT = "react"


logger = logging.getLogger(__name__)


class PromptTemplate:

    """
    Prompt is the input to the model.

    Prompt is often constructed from multiple components and prompt values. Prompt classes and functions make
    constructing and working with prompts easy.
    """

    def __init__(
            self,
            *,
            prompt_type: str | Enum | None = None,
            system_message: str | None = None
    ):
        self.prompt_type = prompt_type
        self.system_message = system_message
        if self.prompt_type is None:
            self.prompt_type = "default"

    async def _get_prompt(self) -> list[dict]:
        match self.prompt_type:
            case PromptTypeEnum.DEFAULT:
                return copy.deepcopy(DEFAULT)
            case _:
                raise InvalidType(f"Invalid Prompt type: {self.prompt_type}")

    async def get_messages(
            self,
            *,
            input_prompt: str,
            old_memory: list[dict] | None = None,
            **kwargs: Any
    ) -> list[dict]:
        """
        To construct the message structure based on the user's prompt type

        Args:
            input_prompt (str): Give the instruction of your expected result.
            old_memory (list[dict]): An optional previous context of the user's instruction
            kwargs (Any): Format the variable's value in the given prompt.
        """
        prompt = await self._get_prompt()
        if not kwargs:
            kwargs = {}
        format_string = input_prompt.format(**kwargs)
        content = {
            "role": "user",
            "content": format_string
        }
        prompt.append(content)

        if old_memory:
            prompt += old_memory

        if self.system_message:
            _system_content = {
                "role": "system",
                "content": self.system_message
            }
            prompt.append(_system_content)
        return prompt