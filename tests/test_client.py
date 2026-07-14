from src.network.client import ClientSocketConfig, ClientSocket, ClientManager
from src.network_components.connection import Connection
from src.network_components.framing import (
    MessageType,
    send_frame as _send_frame,
    recv_frame as _recv_frame,
)
from src.business.messages.send_message import SendMessageProcessor
from src.errors.server_errors import ConnectionLostError

import pytest
from unittest.mock import MagicMock

from threading import Event, Thread
from socket import socket, AF_INET, SOCK_STREAM
from time import sleep


class TestClientSocketConfig:
    peer_host: str = "127.0.0.1"
    peer_port: int = 6001

    def test_client_socket_config(self):
        conf = ClientSocketConfig(self.peer_host, self.peer_port)

        assert conf.peer_host == self.peer_host
        assert conf.peer_port == self.peer_port
        assert conf.retries == 3
        assert conf.timeout == 5

    def test_client_socket_config_host_error(self):
        invalid_host: str = "127.0.0."

        with pytest.raises(ValueError, match="Invalid host address"):
            ClientSocketConfig(invalid_host, self.peer_port)

    def test_client_socket_config_port_error_smaller(self):
        invalid_port: int = 0

        with pytest.raises(ValueError, match="Invalid port number"):
            ClientSocketConfig(self.peer_host, invalid_port)

    def test_client_socket_config_port_error_bigger(self):
        invalid_port: int = 700000

        with pytest.raises(ValueError, match="Invalid port number"):
            ClientSocketConfig(self.peer_host, invalid_port)

    def test_client_socket_config_retries_error(self):
        invalid_retries: int = -1

        with pytest.raises(ValueError, match="Invalid number of retries"):
            ClientSocketConfig(self.peer_host, self.peer_port, retries=invalid_retries)

    def test_client_socket_config_timeout_error(self):
        invalid_timeout: float = -1.0

        with pytest.raises(ValueError, match="Invalid timeout"):
            ClientSocketConfig(self.peer_host, self.peer_port, timeout=invalid_timeout)


class TestClientManager:
    host: str = "127.0.0.1"
    port: int = 6000
    conn: Connection = Connection()
    stop_event: Event = Event()

    client_socket_config: ClientSocketConfig = ClientSocketConfig(host, port)

    def echo_server(self):
        with socket(AF_INET, SOCK_STREAM) as server:
            server.bind((self.host, self.port))
            server.listen(1)

            conn, addr = server.accept()

            with conn:
                _send_frame(conn, MessageType.HELLO)
                msg_type, _ = _recv_frame(conn)
                assert msg_type == MessageType.HELLO

                _send_frame(conn, MessageType.ACK)
                msg_type, _ = _recv_frame(conn)
                assert msg_type == MessageType.ACK

                while True:
                    try:
                        msg_type, payload = _recv_frame(conn)
                    except ConnectionLostError:
                        break
                    if msg_type == MessageType.QUIT:
                        break
                    _send_frame(conn, msg_type, payload)

    def test_client_manager(self):
        mock_sock: MagicMock = MagicMock()
        mock_sock.__enter__.return_value = mock_sock
        mock_sock.recv_frame.side_effect = [
            (MessageType.HELLO, b""),
            (MessageType.ACK, b""),
        ]

        send_message_proc: SendMessageProcessor = SendMessageProcessor()
        cli_mock_source: MagicMock = MagicMock()
        cli_mock_source.next_message.side_effect = ["Hello World", None]

        client_manager: ClientManager = ClientManager(
            mock_sock, self.conn, self.stop_event, send_message_proc, cli_mock_source
        )
        self.conn.attach(client_manager)

        client_manager.run()

        mock_sock.send_message.assert_called_once()
        mock_sock.send_frame.assert_any_call(MessageType.QUIT)
        assert cli_mock_source.next_message.call_count == 2

    def test_client_echo(self):
        config: ClientSocketConfig = ClientSocketConfig(self.host, self.port)

        sock: ClientSocket = ClientSocket(config, family=AF_INET, type=SOCK_STREAM)

        msg_proc: SendMessageProcessor = SendMessageProcessor()

        cli_mock_source: MagicMock = MagicMock()
        cli_mock_source.next_message.side_effect = ["Hello World", None]

        client: ClientManager = ClientManager(
            sock, Connection(), Event(), msg_proc, cli_mock_source
        )

        thread = Thread(target=self.echo_server, daemon=True)
        thread.start()

        client.run()

    def test_client_manager_handshake_timeout(self):
        host: str = "127.0.0.1"
        port: int = 6003

        def silent_server():
            with socket(AF_INET, SOCK_STREAM) as server:
                server.bind((host, port))
                server.listen(1)
                peer, _ = server.accept()
                with peer:
                    sleep(2.0)  # never sends a HELLO back

        thread = Thread(target=silent_server, daemon=True)
        thread.start()

        config: ClientSocketConfig = ClientSocketConfig(host, port, retries=1, timeout=1.0)
        sock: ClientSocket = ClientSocket(config, family=AF_INET, type=SOCK_STREAM)

        msg_proc: SendMessageProcessor = SendMessageProcessor()
        cli_mock_source: MagicMock = MagicMock()
        conn: Connection = Connection()
        stop_event: Event = Event()

        client: ClientManager = ClientManager(
            sock, conn, stop_event, msg_proc, cli_mock_source
        )

        client.run()

        cli_mock_source.next_message.assert_not_called()
