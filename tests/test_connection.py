import sys
print(sys.path)
from Network import Connection, Server, Client


def test_attach():
    conn = Connection()
    server = Server("localhost", 7777, conn)
    conn.attach(server)
    assert conn.state
    
