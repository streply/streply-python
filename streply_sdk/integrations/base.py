from abc import ABC, abstractmethod


class Integration(ABC):
    @staticmethod
    @abstractmethod
    def is_available():
        pass

    @abstractmethod
    def setup(self, client):
        pass
