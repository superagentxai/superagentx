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
            prompt_type: str | Enum | None = None
    ):
        self.prompt_type = prompt_type
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
            **kwargs: Any
    ) -> list[dict]:
        """
        To construct the message structure based on the user's prompt type

        Args:
            input_prompt (str): Give the instruction of your expected result.
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
        return prompt
