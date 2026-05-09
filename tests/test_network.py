import unittest
from unittest.mock import patch
from Network import Server, Connection
from socket import socket, AF_INET, SOCK_STREAM
import errno


class TestServer(unittest.TestCase):
    @patch("socket.socket.bind", side_effect=OSError(errno.EADDRINUSE))
    def test_start_fail_bind_eaddrinuse(self, mock_bind):
        with self.assertRaises(OSError) as context:
            conn: Connection = Connection()
            server: Server = Server("127.0.0.1", 6000, conn)

            server.start()

        self.assertEqual(str(context.exception), str(errno.EADDRINUSE))

    @patch("socket.socket.bind", side_effect=OSError(errno.EACCES))
    def test_start_fail_bind_eaccess(self, mock_bind):
        with self.assertRaises(OSError) as context:
            conn: Connection = Connection()
            server: Server = Server("127.0.0.1", 6000, conn)

            server.start()

        self.assertEqual(str(context.exception), str(errno.EACCES))

    @patch("socket.socket.accept")
    def test_accept_successful(self, mock_accept):
        conn_s = socket(AF_INET, SOCK_STREAM)
        mock_accept.return_value = (conn_s, "127.0.0.1")

        conn: Connection = Connection()
        server: Server = Server("127.0.0.1", 6000, conn)

        server.start()

        self.assertEqual(server.conn_s, conn_s)
        server.close()


if __name__ == "__main__":
    unittest.main()
