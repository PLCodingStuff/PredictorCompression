import unittest
from unittest.mock import patch
from Network import Server, Connection
from socket import socket, AF_INET, SOCK_STREAM
import errno
from os import strerror

def _error_msg(error: int) -> str:
    return f"OSError {error}: {strerror(error)}"

class TestServer(unittest.TestCase):
    @patch("socket.socket.bind", side_effect=OSError(errno.EADDRINUSE))
    def test_start_fail_bind_eaddrinuse(self, mock_bind):
        with self.assertRaises(OSError) as context:
            conn: Connection = Connection()
            server: Server = Server("127.0.0.1", 6000, conn)

            server.start()

        msg: str = _error_msg(errno.EADDRINUSE)
        self.assertEqual(str(context.exception), msg)

    @patch("socket.socket.bind", side_effect=OSError(errno.EACCES))
    def test_start_fail_bind_eaccess(self, mock_bind):
        with self.assertRaises(OSError) as context:
            conn: Connection = Connection()
            server: Server = Server("127.0.0.1", 6000, conn)

            server.start()
        msg: str = _error_msg(errno.EACCES)
        self.assertEqual(str(context.exception), msg)

    @patch("socket.socket.listen", side_effect=OSError(errno.EADDRINUSE))
    def test_start_fail_listen(self, mock_bind):
        with self.assertRaises(OSError) as context:
            conn: Connection = Connection()
            server: Server = Server("127.0.0.1", 6000, conn)

            server.start()

        msg: str = _error_msg(errno.EADDRINUSE)
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

    @patch("socket.socket.accept", side_effect=OSError(errno.EAGAIN))
    def test_accept_fail_eagain(self, mock_object):
        with self.assertRaises(OSError) as context:
            conn: Connection = Connection()
            server: Server = Server("127.0.0.1", 6000, conn)

            server.start()

        msg: str = _error_msg(errno.EAGAIN)
        self.assertEqual(str(context.exception), msg)

    @patch("socket.socket.accept", side_effect=OSError(errno.EWOULDBLOCK))
    def test_accept_fail_ewouldblock(self, mock_object):
        with self.assertRaises(OSError) as context:
            conn: Connection = Connection()
            server: Server = Server("127.0.0.1", 6000, conn)

            server.start()

        msg: str = _error_msg(errno.EWOULDBLOCK)
        self.assertEqual(str(context.exception), msg)

    @patch("socket.socket.accept", side_effect=OSError(errno.ECONNABORTED))
    def test_accept_fail_econnaborted(self, mock_object):
        with self.assertRaises(OSError) as context:
            conn: Connection = Connection()
            server: Server = Server("127.0.0.1", 6000, conn)

            server.start()

        msg: str = _error_msg(errno.ECONNABORTED)
        self.assertEqual(str(context.exception), msg)

    @patch("socket.socket.accept", side_effect=OSError(errno.ETIMEDOUT))
    def test_accept_fail_etimedout(self, mock_object):
        with self.assertRaises(OSError) as context:
            conn: Connection = Connection()
            server: Server = Server("127.0.0.1", 6000, conn)

            server.start()

        msg: str = _error_msg(errno.ETIMEDOUT)
        self.assertEqual(str(context.exception), msg)

    @patch("socket.socket.accept", side_effect=OSError(errno.EPERM))
    def test_accept_fail_eperm(self, mock_object):
        with self.assertRaises(OSError) as context:
            conn: Connection = Connection()
            server: Server = Server("127.0.0.1", 6000, conn)

            server.start()

        msg: str = _error_msg(errno.EPERM)
        self.assertEqual(str(context.exception), msg)

if __name__ == "__main__":
    unittest.main()
