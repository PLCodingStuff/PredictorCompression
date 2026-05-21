import pytest
from src.network.client import ClientSocketConfig, ClientSocketManager, ClientManager


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