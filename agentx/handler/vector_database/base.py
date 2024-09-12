from abc import ABCMeta, abstractmethod


class BaseVectorDatabase(metaclass=ABCMeta):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def create(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def index(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def search(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def delete(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def update(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def exists(self, *args, ** kwargs):
        raise NotImplementedError
