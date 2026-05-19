import pytest
from unittest.mock import MagicMock

from src.network.server import (
    ServerSocketConfig,
    ServerSocketManager,
    AcceptTimeOutError,
    PeerClientSocketManager,
    ConnectionLostError,
)

from socket import timeout
import errno


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
    mock_sock.setsockopt.assert_called_once()
    mock_sock.settimeout.assert_called_once()

    # Socket changed states
    mock_sock.bind.assert_called_once()
    mock_sock.listen.assert_called_once()

    # Socket closed
    mock_sock.close.assert_called_once()

    # Accept was not called
    mock_sock.accept.assert_not_called


def test_server_socket_manager_enter_exit_bind_fail():
    host: str = "127.0.0.1"
    port: int = 6000

    conf: ServerSocketConfig = ServerSocketConfig(host, port)
    mock_sock: MagicMock = MagicMock()
    mock_sock.bind.side_effect = OSError(errno.EACCES)
    server_sock_man: ServerSocketManager = ServerSocketManager(conf, mock_sock)

    try:
        with server_sock_man:
            pass
    except PermissionError:
        pass

    mock_sock.bind.assert_called
    mock_sock.listen.assert_not_called
    mock_sock.close.assert_called


def test_server_socket_manager_enter_exit_listen_fail():
    host: str = "127.0.0.1"
    port: int = 6000

    conf: ServerSocketConfig = ServerSocketConfig(host, port)
    mock_sock: MagicMock = MagicMock()
    mock_sock.listen.side_effect = OSError(errno.EACCES)
    server_sock_man: ServerSocketManager = ServerSocketManager(conf, mock_sock)

    try:
        with server_sock_man:
            pass
    except OSError:
        pass

    mock_sock.bind.assert_called
    mock_sock.listen.assert_called
    mock_sock.close.assert_called


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

    mock_sock.accept.assert_called
    assert client_sock == mock_client_sock


def test_server_socket_manager_accept_fail():
    host: str = "127.0.0.1"
    port: int = 6000

    conf: ServerSocketConfig = ServerSocketConfig(host, port)

    mock_sock: MagicMock = MagicMock()
    mock_sock.accept.side_effect = timeout

    server_sock_man: ServerSocketManager = ServerSocketManager(conf, mock_sock)

    try:
        with server_sock_man as sock:
            sock.accept()
    except AcceptTimeOutError:
        pass

    mock_sock.accept.assert_called


def test_peer_client_socket_manager():
    manager: PeerClientSocketManager = PeerClientSocketManager()
    mock_sock: MagicMock = MagicMock()

    manager.set_socket(mock_sock)

    with manager:
        pass

    mock_sock.close.assert_called_once()
    mock_sock.shutdown.assert_called_once()


def test_peer_client_socket_manager_buffer_size_fail():
    buffer_size: int = 0

    with pytest.raises(ValueError, match="Invalid Buffer Size"):
        PeerClientSocketManager(buffer_size=buffer_size)


def test_peer_client_socket_manager_get_message():
    manager: PeerClientSocketManager = PeerClientSocketManager()

    mock_sock: MagicMock = MagicMock()
    mock_sock.recv.return_value = bytearray("Hello World", encoding="ASCII")

    manager.set_socket(mock_sock)
    msg: bytearray = None
    with manager as m:
        msg = m.get_message()

    assert msg == bytearray("Hello World", encoding="ASCII")


def test_peer_client_socket_manager_get_message_fail():
    manager: PeerClientSocketManager = PeerClientSocketManager()

    mock_sock: MagicMock = MagicMock()
    mock_sock.recv.return_value = bytearray()

    manager.set_socket(mock_sock)
    
    with pytest.raises(ConnectionLostError):
        with manager as m:
            m.get_message()