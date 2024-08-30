import abc
from abc import abstractmethod
from enum import Enum
from typing import Any


# Base Class
class BaseHandler (abc.ABC):

    @abstractmethod
    def handle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:
        raise NotImplementedError("Subclasses should implement this method.")

    @abstractmethod
    async def ahandle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:
        raise NotImplementedError("Subclasses should implement this method.")
