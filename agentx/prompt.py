from enum import Enum


class PromptTemplate:

    def __init__(
            self,
            *,
            prompt_type: str | Enum | None = None
    ):
        self.prompt_type = prompt_type

    async def get_message(
            self,
            *,
            input_prompt: str,
            **kwargs
    ) -> list[dict]:
        pass
