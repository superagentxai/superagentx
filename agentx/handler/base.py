import abc
from typing import Sequence


# Base Class
class BaseHandler(abc.ABC):

    @abc.abstractmethod
    def __dir__(self):
        raise NotImplementedError
