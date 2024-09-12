from agentx.utils.parsers.base import BaseParser
from typing import List
import re


class CommaSeparatedListOutputParser(BaseParser):

    async def parse(self, text: str) -> List[str]:
        """Parse the output of an LLM call.

          Args:
               text: The output of an LLM call.

          Returns:
               A list of strings.
         """
        return [part.strip() for part in text.split(",")]

    async def get_format_instructions(self) -> str:
        """Return the format instructions for the comma-separated list output."""
        return (
            "Your response should be a list of comma separated values, "
            "eg: `foo, bar, baz` or `foo,bar,baz`"
        )


class NumberedListOutputParser(BaseParser):
    """Parse a numbered list."""

    pattern: str = r"\d+\.\s([^\n]+)"
    """The pattern to match a numbered list item."""

    def get_format_instructions(self) -> str:
        return (
            "Your response should be a numbered list with each item on a new line. "
            "For example: \n\n1. foo\n\n2. bar\n\n3. baz"
        )

    def parse(self, text: str) -> List[str]:
        """Parse the output of an LLM call.

        Args:
            text: The output of an LLM call.

        Returns:
            A list of strings.
        """
        return re.findall(self.pattern, text)


class MarkdownListOutputParser(BaseParser):
    """Parse a Markdown list."""

    pattern: str = r"^\s*[-*]\s([^\n]+)$"
    """The pattern to match a Markdown list item."""

    def get_format_instructions(self) -> str:
        """Return the format instructions for the Markdown list output."""
        return "Your response should be a markdown list, " "eg: `- foo\n- bar\n- baz`"

    def parse(self, text: str) -> List[str]:
        """Parse the output of an LLM call.

        Args:
            text: The output of an LLM call.

        Returns:
            A list of strings.
        """
        return re.findall(self.pattern, text, re.MULTILINE)
