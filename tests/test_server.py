import unittest
from unittest.mock import patch, MagicMock
from Network import Server
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
        retries:int = 3
        server: Server = Server("127.0.0.1", 6000,conn=conn, retries=retries)

        server.start()

        self.assertEqual(mock_accept.call_count, retries)
        self.assertIsNone(server._socket)

    @patch("socket.socket.accept", side_effect=OSError(errno.EPERM))
    def test_accept_fail(self, mock_object):
        with self.assertRaises(OSError) as context:
            server: Server = Server("127.0.0.1", 6000)

            server.start()

        self.assertEqual(str(context.exception), str(errno.EPERM))


def test_bind_fail_port_used():
    # Manually occupy the port
    blocker = socket(AF_INET, SOCK_STREAM)
    blocker.setsockopt(SOL_SOCKET, SO_REUSEADDR, 0)

    with pytest.raises(PermissionError):
        blocker.bind(("127.0.0.1", 6000))
        blocker.listen(1)

        server: Server = Server("127.0.0.1", 6000)
        server.start()

    blocker.close()

if __name__ == "__main__":
    unittest.main()
