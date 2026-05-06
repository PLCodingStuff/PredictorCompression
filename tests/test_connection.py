from Network import Connection, Client
import pytest

def test_initial_state():
    conn: Connection = Connection()

    assert not conn.state

def test_update_state_no_observers():
    # Initial state == False
    conn: Connection = Connection()

    conn.update_state() # True
    conn.update_state() # False
    conn.update_state() # True

    assert conn.state

def test_attach_one_observer():
    conn: Connection = Connection()
    client: Client = Client("",0, None)

    conn.attach(client)

    assert conn._observers
    assert conn._observers[0] == client

def test_attach_two_observer():
    conn: Connection = Connection()

    client_1: Client = Client("",0, None)
    client_2: Client = Client("", 1, None)

    conn.attach(client_1)
    conn.attach(client_2)
    
    assert len(conn._observers) == 2

def test_attach_duplicates():
    conn: Connection = Connection()

    client: Client = Client("",0, None)

    conn.attach(client)
    conn.attach(client)

    assert len(conn._observers) == 1
