from pydantic import BaseModel


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
