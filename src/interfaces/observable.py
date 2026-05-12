from src.interfaces.observer import Observer
from abc import ABC, abstractmethod


class Observable(ABC):
    """
    Abstract base class for the Observable (subject) in the Observer design pattern.
    
    This class manages observers and notifies them when changes occur. Concrete
    implementations will handle attaching, detaching, and notifying observers.

    Methods:
        attach(observer: Observer) -> None: Attach an observer to the subject.
        detach(observer: Observer) -> None: Detach an observer from the subject.
        _notify() -> None: Notify all attached observers of a change.
    """

    @abstractmethod
    def attach(self, observer: Observer)->None:
        """
        Attach an observer to the subject.

        Args:
            observer (Observer): The observer instance to be attached.

        This method adds the observer to a collection of observers that will be 
        notified when the subject's state changes.
        """
        pass

    @abstractmethod
    def detach(self, observer: Observer)->None:
        """
        Detach an observer from the subject.

        Args:
            observer (Observer): The observer instance to be removed.

        This method removes the observer from the collection, so it no longer 
        receives notifications about the subject's state changes.
        """
        pass

    @abstractmethod
    def _notify(self)->None:
        """
        Notify all attached observers of a change in the subject's state.
        
        This method should iterate over all the observers that have been attached 
        and call their `update` method, passing any necessary data.
        """
        pass
