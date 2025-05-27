from pydantic import BaseModel


class InputTextParams(BaseModel):
    index: int
    text: str
    has_sensitive: bool


class GoToUrl(BaseModel):
    url: str
