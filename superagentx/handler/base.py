import abc
from typing import Sequence


# Base Class
class BaseHandler(abc.ABC):

    @abc.abstractmethod
    def __dir__(self) -> list[str] | tuple[str] | Sequence[str]:
        raise NotImplementedError
