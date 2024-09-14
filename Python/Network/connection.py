from Interfaces import Observable, Observer

class Connection(Observable):
    _state: bool = False
    _observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        return self._observers.remove(observer)
    
    def _notify(self) -> None:
        for observer in self._observers:
            observer.update(self)

    @property
    def state(self)->bool:
        return self._state

    def update_state(self)->None:
        self._state = not self._state
        self._notify()    