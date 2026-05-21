import pytest
from unittest.mock import MagicMock

from socket import timeout
from threading import Event

from src.network.client import ClientSocketConfig, ClientSocketManager, ClientManager
from src.errors.client_errors import ConnectTimeOutError
from src.network_components.connection import Connection


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


class TestClientSocketManager:
    host: str = "127.0.0.1"
    port: int = 6000
    client_sock_config: ClientSocketConfig = ClientSocketConfig(host, port)

    def test_client_socket_manager(self):
        mock_sock: MagicMock = MagicMock()

        client_sock_man: ClientSocketManager = ClientSocketManager(mock_sock, self.client_sock_config)

        with client_sock_man:
            pass

    def test_client_socket_manager_accept_fail(self):
        mock_sock: MagicMock = MagicMock()

        mock_sock.connect.side_effect = timeout
        client_sock_man: ClientSocketManager = ClientSocketManager(mock_sock, self.client_sock_config)

        with pytest.raises(ConnectTimeOutError, match=f"No connection established after {self.client_sock_config.retries} retries. Terminating..."):
            with client_sock_man:
                pass

    def test_client_socket_manager_send_message(self):
        mock_sock: MagicMock = MagicMock()

        client_sock_man: ClientSocketManager = ClientSocketManager(mock_sock, self.client_sock_config) 

        message: bytearray = bytearray("Hello World", encoding="ASCII")
        with client_sock_man as csm:
            csm.send_message(message)

        mock_sock.sendall.assert_called_once()


class TestClientManager:
    host: str = "127.0.0.1"
    port: int = 6000

    client_socket_config: ClientSocketConfig = ClientSocketConfig(host, port)
    def test_client_manager(self):
        mock_sock: MagicMock = MagicMock()
        conn: Connection = Connection()
        stop_event: Event = Event()

        client_socket_man: ClientSocketManager = ClientSocketManager(mock_sock, self.client_socket_config)

        client_manager: ClientManager = ClientManager(client_socket_man, conn, stop_event)
        conn.attach(client_manager)

        client_manager.run()

        mock_sock.sendall.assert_called_once()
        