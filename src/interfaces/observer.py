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
