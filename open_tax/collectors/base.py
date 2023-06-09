from abc import ABC, abstractmethod


class BaseCollector(ABC):
    @abstractmethod
    def collect(self) -> list[dict]:
        pass
