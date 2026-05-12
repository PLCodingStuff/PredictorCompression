import unittest
from unittest.mock import patch, MagicMock
from src.network.server import Server
from src.network_components.connection import Connection
from socket import socket, AF_INET, SOCK_STREAM, timeout, SOL_SOCKET, SO_REUSEADDR
import errno
import pytest


class TestMockingServer(unittest.TestCase):
    @patch("socket.socket.accept")
    def test_accept_successful(self, mock_accept):
        conn_s = socket(AF_INET, SOCK_STREAM)
        mock_accept.return_value = (conn_s, "127.0.0.1")

        conn = MagicMock()
        server: Server = Server("127.0.0.1", 6000, conn)

        server.start()

        self.assertEqual(server.conn_s, conn_s)
        conn.update_state.assert_called_once()
        server.close()

    @patch("socket.socket.accept", side_effect=timeout)
    def test_accept_timeout(self, mock_accept):
        conn = MagicMock()
        retries: int = 3
        server: Server = Server("127.0.0.1", 6000, conn=conn, retries=retries)

        server.start()

        self.assertEqual(mock_accept.call_count, retries)
        self.assertIsNone(server._socket)

    @patch("socket.socket.accept", side_effect=OSError(errno.EPERM))
    def test_accept_fail(self, mock_object):
        with self.assertRaises(OSError) as context:
            server: Server = Server("127.0.0.1", 6000)

            server.start()

        self.assertEqual(str(context.exception), str(errno.EPERM))


def test_construction_all_values():
    host: str = "127.0.0.1"
    port: int = 6000
    conn: Connection = Connection()
    timeout: float = 3.0
    retries: int = 5
    server: Server = Server(
        host=host, port=port, conn=conn, timeout=timeout, retries=retries
    )

    assert server._host == host
    assert server._port == port
    assert server._conn == conn
    assert server._socket.timeout == timeout
    assert server._retries == retries


def test_construction_defaults():
    host: str = "127.0.0.1"
    port: int = 6000
    server: Server = Server(host=host, port=port)

    assert server._host == host
    assert server._port == port
    assert server._socket.timeout == 5
    assert server._retries == 3
    assert server._conn


def test_construction_invalid_host():
    host: str = "1270.0.1"
    port: int = 6000
    with pytest.raises(ValueError, match="Invalid host name"):
        Server(host=host, port=port)


def test_construction_invalid_port():
    host: str = "127.0.0.1"
    port: int = 0
    with pytest.raises(ValueError, match="Port value out of range"):
        Server(host=host, port=port)
    
def test_construction_invalid_timeout():
    host: str = "127.0.0.1"
    port: int = 6000
    timeout: float = -1.0
    with pytest.raises(ValueError, match="Timeout value out of range"):
        Server(host=host, port=port, timeout=timeout)

def test_construction_invalid_retries():
    host: str = "127.0.0.1"
    port: int = 6000
    retries: int = -1
    with pytest.raises(ValueError, match="Retries value out of range"):
        Server(host=host, port=port, retries=retries)


def test_bind_fail_port_used():
    # Manually occupy the port
    blocker = socket(AF_INET, SOCK_STREAM)
    blocker.setsockopt(SOL_SOCKET, SO_REUSEADDR, 0)

    with pytest.raises(PermissionError, match="Port 6000 is occupied"):
        blocker.bind(("127.0.0.1", 6000))
        blocker.listen(1)

        server: Server = Server("127.0.0.1", 6000)
        server.start()

    blocker.close()


if __name__ == "__main__":
    unittest.main()
