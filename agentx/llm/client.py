from abc import ABCMeta, abstractmethod

from typing import TYPE_CHECKING, Literal, Any, Dict, List, Optional, Tuple, Union
from pydantic import (
    BaseModel,
    Field
)
import logging


class Client(metaclass=ABCMeta):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def chat_completion(self, *args, **kwargs):
        pass

    @abstractmethod
    async def achat_completion(self, *args, **kwargs):
        pass

