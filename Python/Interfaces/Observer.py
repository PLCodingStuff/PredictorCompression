from abc import ABC, abstractmethod
from typing import Any

class Observer(ABC):
    @abstractmethod
    def update(self, data: Any):
        pass

class Observable(ABC):
    @abstractmethod
    def attach(self, observer: Observer)->None:
        pass

    @abstractmethod
    def detach(self, observer: Observer)->None:
        pass

    @abstractmethod
    def _notify(self)->None:
        pass
