import unittest
from unittest.mock import patch, MagicMock
from Network import Server, Connection
from socket import socket, AF_INET, SOCK_STREAM, timeout
import errno
from os import strerror


def _error_msg(error: int) -> str:
    return f"OSError {error}: {strerror(error)}"


class TestServer(unittest.TestCase):
    @patch("socket.socket.bind", side_effect=OSError(errno.EACCES))
    def test_start_fail_bind_eaccess(self, mock_bind):
        with self.assertRaises(OSError) as context:
            conn: Connection = Connection()
            server: Server = Server("127.0.0.1", 6000, conn)

            server.start()
        msg: str = _error_msg(errno.EACCES)
        self.assertEqual(str(context.exception), msg)

    @patch("socket.socket.accept")
    def test_accept_successful(self, mock_accept):
        conn_s = socket(AF_INET, SOCK_STREAM)
        mock_accept.return_value = (conn_s, "127.0.0.1")

        conn: Connection = Connection()
        server: Server = Server("127.0.0.1", 6000, conn)

        server.start()

        self.assertEqual(server.conn_s, conn_s)
        server.close()

    @patch("socket.socket.accept", side_effect=timeout)
    def test_accept_timeout(self, mock_accept):
        conn = MagicMock()
        retries: int = 3
        server: Server = Server("127.0.0.1", 6000, conn, timeout=1, retries=retries)

        server.start()

        self.assertEqual(mock_accept.call_count, retries)
        self.assertIsNone(server._socket)
        conn.update_state.assert_called_once()

    @patch("socket.socket.accept", side_effect=OSError(errno.EPERM))
    def test_accept_fail(self, mock_object):
        with self.assertRaises(OSError) as context:
            conn: Connection = Connection()
            server: Server = Server("127.0.0.1", 6000, conn)

            server.start()

        self.assertEqual(str(context.exception), str(errno.EPERM))


if __name__ == "__main__":
    unittest.main()
