from abc import ABCMeta, abstractmethod


class BaseVectorDatabase(metaclass=ABCMeta):

    def __init__(self):
        super().__init__()

    def create(self, *args, **kwargs):
        raise NotImplementedError

    def index(self, *args, **kwargs):
        raise NotImplementedError

    def search(self, *args, **kwargs):
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        raise NotImplementedError

    def update(self, *args, **kwargs):
        raise NotImplementedError

    def exists(self, *args, ** kwargs):
        raise NotImplementedError
