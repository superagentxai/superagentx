from abc import ABCMeta


class BaseEmbeddings(metaclass=ABCMeta):

    def __init__(self):
        super().__init__()

    def embed(self, text):
        raise NotImplementedError
