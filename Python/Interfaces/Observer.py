from abc import ABC, abstractmethod
from typing import Any

class Observer(ABC):
    """
    Abstract base class for the Observer in the Observer design pattern.
    
    Observers need to implement the `update` method to respond to changes in 
    the subject (Observable) they are monitoring.

    Methods:
        update(data: Any): This method is called to notify the observer of a change.
    """
    @abstractmethod
    def update(self, data: Any):
        """
        Receive updated data from the Observable.

        Args:
            data (Any): The data or information that is being passed to the observer.
        
        This method needs to be implemented by concrete observer classes to define
        what action should be taken when the subject notifies this observer.
        """
        pass

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
