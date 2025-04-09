from __future__ import annotations

import json
from typing import Annotated, Any, Optional, TypeVar, Union

import pydantic
from pydantic import SkipValidation
from pydantic.v1 import BaseModel

# Union type needs to be last assignment to PydanticBaseModel to make mypy happy.
PydanticBaseModel = Union[BaseModel, pydantic.BaseModel]  # type: ignore

TBaseModel = TypeVar("TBaseModel", bound=PydanticBaseModel)

JSON_FORMAT_INSTRUCTIONS = """The output should be formatted as a JSON instance that conforms to the JSON schema below.

As an example, for the schema {{"properties": {{"foo": {{"title": "Foo", "description": "a list of strings", "type": "array", "items": {{"type": "string"}}}}}}, "required": ["foo"]}}
the object {{"foo": ["bar", "baz"]}} is a well-formatted instance of the schema. The object {{"properties": {{"foo": ["bar", "baz"]}}}} is not well-formatted.

Here is the output schema:
```
{schema}
```"""


class JsonOutputParser:
    """Parse the output of an LLM call to a JSON object.

    When used in streaming mode, it will yield partial JSON objects containing
    all the keys that have been returned so far.

    In streaming, if `diff` is set to `True`, yields JSONPatch operations
    describing the difference between the previous and the current object.
    """

    def __init__(
            self,
            pydantic_object: Annotated[Optional[type[TBaseModel]], SkipValidation()] = None  # type: ignore
    ):
        self.pydantic_object = pydantic_object
    """The Pydantic object to use for validation.
    If None, no validation is performed."""

    # @staticmethod
    # def _diff(self, prev: Optional[Any], next: Any) -> Any:
    #     return jsonpatch.make_patch(prev, next).patch

    @staticmethod
    def _get_schema(pydantic_object: type[TBaseModel]) -> dict[str, Any]:
        if issubclass(pydantic_object, pydantic.BaseModel):
            return pydantic_object.model_json_schema()
        elif issubclass(pydantic_object, pydantic.v1.BaseModel):
            return pydantic_object.schema()

    def get_format_instructions(self) -> str:
        """Return the format instructions for the JSON output.

        Returns:
            The format instructions for the JSON output.
        """
        if self.pydantic_object is None:
            return "Return a JSON object."
        else:
            # Copy schema to avoid altering original Pydantic schema.
            schema = dict(self._get_schema(self.pydantic_object).items())

            # Remove extraneous fields.
            reduced_schema = schema
            if "title" in reduced_schema:
                del reduced_schema["title"]
            if "type" in reduced_schema:
                del reduced_schema["type"]
            # Ensure json in context is well-formed with double quotes.
            schema_str = json.dumps(reduced_schema, ensure_ascii=False)
            return JSON_FORMAT_INSTRUCTIONS.format(schema=schema_str)

    @property
    def _type(self) -> str:
        return "simple_json_output_parser"


# For backwards compatibility
SimpleJsonOutputParser = JsonOutputParser