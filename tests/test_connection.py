from Network import Connection
from Interfaces import Observer
import pytest

TOGGLES = 1000

class HelperObserver(Observer):
    def __init__(self):
        self.counter: int = 0
        self.data = None

    def update(self, data):
        self.counter += 1
        self.data = data


def test_initial_state():
    conn: Connection = Connection()

    assert not conn.state


def test_update_state_no_observers():
    # Initial state == False
    conn: Connection = Connection()

    conn.update_state()  # True
    conn.update_state()  # False
    conn.update_state()  # True

    assert conn.state


def test_attach_one_observer():
    conn: Connection = Connection()
    obs: HelperObserver = HelperObserver()

    conn.attach(obs)

    assert conn._observers
    assert conn._observers[0] == obs


def test_attach_two_observer():
    conn: Connection = Connection()
    obs_1: HelperObserver = HelperObserver()
    obs_2: HelperObserver = HelperObserver()

    conn.attach(obs_1)
    conn.attach(obs_2)

    assert len(conn._observers) == 2


def test_attach_duplicates():
    conn: Connection = Connection()
    obs: HelperObserver = HelperObserver()

    conn.attach(obs)
    conn.attach(obs)


    assert len(conn._observers) == 1


def test_detach():
    conn: Connection = Connection()
    obs: HelperObserver = HelperObserver()

    conn.attach(obs)
    conn.detach(obs)

    assert not conn._observers


def test_detach_observer_not_in_list():
    conn: Connection = Connection()
    obs: HelperObserver = HelperObserver()

    with pytest.raises(ValueError):
        conn.detach(obs)

    assert not conn._observers


def test_update_state_behavior():
    conn: Connection = Connection()
    obs: HelperObserver = HelperObserver()

    conn.attach(obs)

    conn.update_state()

    assert obs.counter == 1

def test_update_state_two_observers_behavior():
    conn: Connection = Connection()
    obs_1: HelperObserver = HelperObserver()
    obs_2: HelperObserver = HelperObserver()

    conn.attach(obs_1)
    conn.attach(obs_2)

    conn.update_state()

    assert obs_1.counter == 1
    assert obs_2.counter == 1


def test_update_state_connection_argument():
    conn: Connection = Connection()
    obs: HelperObserver = HelperObserver()

    conn.attach(obs)
    conn.update_state()

    assert obs.data == conn


def test_state_after_repeated_toggling():
    conn: Connection = Connection()

    for _ in range(TOGGLES):
        old_state: bool = conn.state
        conn.update_state()
        assert conn.state != old_state