import pytest
from unittest.mock import MagicMock
from src.network.server import ServerSocketConfig, ServerSocketManager


def test_server_socket_config():
    host: str = "127.0.0.1"
    port: int = 6000

    conf = ServerSocketConfig(host, port)

    assert conf.host == host
    assert conf.port == port
    assert conf.timeout == 5.0
    assert conf.retries == 3


def test_server_socket_config_host_error():
    host: str = "127.0.0."
    port: int = 6000

    with pytest.raises(ValueError, match="Invalid host name"):
        ServerSocketConfig(host, port)


def test_server_socket_config_port_error():
    host: str = "127.0.0.1"
    port: int = 0

    with pytest.raises(ValueError, match="Port value out of range"):
        ServerSocketConfig(host, port)


def test_server_socket_config_timeout_error():
    host: str = "127.0.0.1"
    port: int = 6000

    with pytest.raises(ValueError, match="Timeout value out of range"):
        ServerSocketConfig(host, port, timeout=-1.0)


def test_server_socket_config_retries_error():
    host: str = "127.0.0.1"
    port: int = 6000

    with pytest.raises(ValueError, match="Retries value out of range"):
        ServerSocketConfig(host, port, retries=-1)


def test_server_socket_manager_enter_exit():
    host: str = "127.0.0.1"
    port: int = 6000

    conf: ServerSocketConfig = ServerSocketConfig(host, port)
    mock_sock: MagicMock = MagicMock()
    server_sock_man: ServerSocketManager = ServerSocketManager(conf, mock_sock)

    with server_sock_man:
        pass

    # Server socket setup
    assert mock_sock.setsockopt.called_once()
    assert mock_sock.settimeout.called_once()

    # Socket changed states
    assert mock_sock.bind.called_once()
    assert mock_sock.listen.called_once()

    # Socket closed
    assert mock_sock.close.called_once()

    # Accept was not called
    assert not mock_sock.accept.called

def test_server_socket_manager_accept():
    host: str = "127.0.0.1"
    port: int = 6000

    conf: ServerSocketConfig = ServerSocketConfig(host, port)

    mock_sock: MagicMock = MagicMock()
    mock_client_sock: MagicMock = MagicMock()
    mock_sock.accept.return_value = (mock_client_sock, None)

    server_sock_man: ServerSocketManager = ServerSocketManager(conf, mock_sock)

    client_sock = None
    with server_sock_man as sock:
        client_sock = sock.accept()

    assert mock_sock.accept.called
    assert client_sock == mock_client_sock