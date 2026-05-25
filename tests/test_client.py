import pytest
from unittest.mock import MagicMock

# from socket import timeout
from threading import Event

from src.network.client import ClientSocketConfig, ClientManager
# from src.errors.client_errors import ConnectTimeOutError
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


class TestClientManager:
    host: str = "127.0.0.1"
    port: int = 6000
    conn: Connection = Connection()
    stop_event: Event = Event()

    client_socket_config: ClientSocketConfig = ClientSocketConfig(host, port)
    def test_client_manager(self):
        mock_sock: MagicMock = MagicMock()
        mock_sock.__enter__.return_value = mock_sock
        
        client_manager: ClientManager = ClientManager(mock_sock, self.conn, self.stop_event)
        self.conn.attach(client_manager)

        client_manager.run()

        mock_sock.send_message.assert_called_once()
        