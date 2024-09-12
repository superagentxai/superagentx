from enum import Enum
from typing import Any

from agentx.handler.base import BaseHandler


class VectorDatabaseHandler(BaseHandler):

    def __init__(
            self,
    ):
        pass

    def handle(self, *, action: str | Enum, **kwargs) -> Any:
        pass

    async def ahandle(self, *, action: str | Enum, **kwargs) -> Any:
        pass
