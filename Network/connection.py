from Interfaces import Observable, Observer

class Connection(Observable):
    """
    Concrete implementation of the Observable class representing a connection.
    
    The `Connection` class holds a state (boolean) and maintains a list of observers.
    It can notify its observers when the state changes.

    Attributes:
        _state (bool): Internal state of the connection, defaults to False.
        _observers (list[Observer]): List of observers attached to this connection.
    
    Methods:
        attach(observer: Observer) -> None: Attaches an observer to this connection.
        detach(observer: Observer) -> None: Detaches an observer from this connection.
        _notify() -> None: Notifies all attached observers of the state change.
        state -> bool: Property to get the current state of the connection.
        update_state() -> None: Toggles the connection state and notifies observers.
    """
    _state: bool = False
    _observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        """
        Attach an observer to the connection.

        Args:
            observer (Observer): The observer instance to attach.
        
        This method adds the observer to the internal list of observers.
        """
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        """
        Detach an observer from the connection.

        Args:
            observer (Observer): The observer instance to remove.
        
        This method removes the observer from the internal list of observers, 
        so it will no longer receive state change notifications.
        
        Raises:
            ValueError: If the observer is not found in the list.
        """
        return self._observers.remove(observer)
    
    def _notify(self) -> None:
        """
        Notify all attached observers of the state change.

        This method iterates through the list of observers and calls their `update` 
        method, passing the `Connection` instance as the subject that has changed.
        """
        for observer in self._observers:
            observer.update(self)

    @property
    def state(self)->bool:
        """
        Get the current state of the connection.

        Returns:
            bool: The current state of the connection (True or False).
        """
        return self._state

    def update_state(self)->None:
        """
        Toggle the state of the connection and notify observers.

        This method inverts the current state (from True to False or vice versa) 
        and triggers the `_notify` method to inform all observers of the state change.
        """
        self._state = not self._state
        self._notify()    
