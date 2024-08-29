import abc
from enum import Enum
from typing import Any


# Base Class
class BaseHandler (abc.ABC):

    def handle(
            self,
            action: str | Enum,
            *args,
            **kwargs
    ) -> Any:
        raise NotImplementedError("Subclasses should implement this method.")
