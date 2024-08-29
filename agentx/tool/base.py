from abc import ABC
from typing import Any

from pydantic import BaseModel


# Base Class
class BaseHandler (BaseModel, ABC):

    def handle(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("Subclasses should implement this method.")
