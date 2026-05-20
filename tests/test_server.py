import pytest
from unittest.mock import MagicMock

from src.network.server import (
    ServerSocketConfig,
    ServerSocketManager,
    PeerClientSocketManager,
    ServerManager,
)
from src.network_components.connection import Connection

from socket import timeout
from threading import Event
import errno


class TestConfig:
    port: int = 6000
    host: str = "127.0.0.1"
    def test_server_socket_config(self):
        conf = ServerSocketConfig(self.host, self.port)
    
        assert conf.host == self.host
        assert conf.port == self.port
        assert conf.timeout == 5.0
        assert conf.retries == 3


    def test_server_socket_config_host_error(self):
        invalid_host: str = "127.0.0."

        with pytest.raises(ValueError, match="Invalid host name"):
            ServerSocketConfig(invalid_host, self.port)


    def test_server_socket_config_port_error(self):
        invalid_port: int = 0

        with pytest.raises(ValueError, match="Port value out of range"):
            ServerSocketConfig(self.host, invalid_port)


    def test_server_socket_config_timeout_error(self):
        with pytest.raises(ValueError, match="Timeout value out of range"):
            ServerSocketConfig(self.host, self.port, timeout=-1.0)


    def test_server_socket_config_retries_error(self):
        with pytest.raises(ValueError, match="Retries value out of range"):
            ServerSocketConfig(self.host, self.port, retries=-1)


class TestServerSocketManager:
    host: str = "127.0.0.1"
    port: int = 6000
    
    def test_server_socket_manager_enter_exit(self):
        conf: ServerSocketConfig = ServerSocketConfig(self.host, self.port)
        mock_sock: MagicMock = MagicMock()
        server_sock_man: ServerSocketManager = ServerSocketManager(mock_sock, conf)

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


    def test_server_socket_manager_enter_exit_bind_fail(self):
        conf: ServerSocketConfig = ServerSocketConfig(self.host, self.port)
        mock_sock: MagicMock = MagicMock()
        mock_sock.bind.side_effect = OSError(errno.EACCES)
        server_sock_man: ServerSocketManager = ServerSocketManager(mock_sock, conf)

        try:
            with server_sock_man:
                pass
        except PermissionError:
            pass

        mock_sock.bind.assert_called
        mock_sock.listen.assert_not_called
        mock_sock.close.assert_called


    def test_server_socket_manager_enter_exit_listen_fail(self):
        conf: ServerSocketConfig = ServerSocketConfig(self.host, self.port)
        mock_sock: MagicMock = MagicMock()
        mock_sock.listen.side_effect = OSError(errno.EACCES)
        server_sock_man: ServerSocketManager = ServerSocketManager(mock_sock, conf)

        try:
            with server_sock_man:
                pass
        except OSError:
            pass

        mock_sock.bind.assert_called
        mock_sock.listen.assert_called
        mock_sock.close.assert_called


    def test_server_socket_manager_accept(self):
        conf: ServerSocketConfig = ServerSocketConfig(self.host, self.port)

        mock_sock: MagicMock = MagicMock()
        mock_client_sock: MagicMock = MagicMock()
        mock_sock.accept.return_value = (mock_client_sock, None)

        server_sock_man: ServerSocketManager = ServerSocketManager(mock_sock, conf)

        client_sock = None
        with server_sock_man as sock:
            client_sock = sock.accept()

        mock_sock.accept.assert_called
        assert client_sock == mock_client_sock


    def test_server_socket_manager_accept_fail(self):
        conf: ServerSocketConfig = ServerSocketConfig(self.host, self.port)

        mock_sock: MagicMock = MagicMock()
        mock_sock.accept.side_effect = timeout  # Raises AcceptTimeOutError

        server_sock_man: ServerSocketManager = ServerSocketManager(mock_sock, conf)

        # Fails gracefully
        with server_sock_man as sock:
            sock.accept()

        mock_sock.accept.assert_called


class TestPeerClientSocketManager:
    def test_peer_client_socket_manager(self):
        manager: PeerClientSocketManager = PeerClientSocketManager()
        mock_sock: MagicMock = MagicMock()

        manager.set_socket(mock_sock)

        with manager:
            pass

        mock_sock.close.assert_called_once()
        mock_sock.shutdown.assert_called_once()


    def test_peer_client_socket_manager_buffer_size_fail(self):
        buffer_size: int = 0

        with pytest.raises(ValueError, match="Invalid Buffer Size"):
            PeerClientSocketManager(buffer_size=buffer_size)


    def test_peer_client_socket_manager_get_message(self):
        manager: PeerClientSocketManager = PeerClientSocketManager()

        mock_sock: MagicMock = MagicMock()
        mock_sock.recv.return_value = bytearray("Hello World", encoding="ASCII")

        manager.set_socket(mock_sock)
        msg: bytearray = None
        with manager as m:
            msg = m.get_message()

        assert msg == bytearray("Hello World", encoding="ASCII")


    def test_peer_client_socket_manager_get_message_fail(self):
        manager: PeerClientSocketManager = PeerClientSocketManager()

        mock_sock: MagicMock = MagicMock()
        mock_sock.recv.return_value = bytearray()  # Raises ConnectionLostError

        manager.set_socket(mock_sock)

        # Gracefully fails
        with manager as m:
            m.get_message()


class TestServerManager:
    host: str = "127.0.0.1"
    port: int = 6000
    conn: Connection = Connection()
    stop_event: Event = Event()

    def test_server_manager(self):
        mock_sock: MagicMock = MagicMock()
        client_mock_sock: MagicMock = MagicMock()

        client_mock_sock.recv.side_effect = [
            bytearray("Hello World", encoding="ASCII"),
            bytearray(),
        ]
        mock_sock.accept.return_value = (client_mock_sock, None)

        server_socket_config: ServerSocketConfig = ServerSocketConfig(self.host, self.port)
        server_socket_manager: ServerSocketManager = ServerSocketManager(
            mock_sock, server_socket_config
        )
        peer_client_socket_manager: PeerClientSocketManager = PeerClientSocketManager()
        server_man: ServerManager = ServerManager(
            server_socket_manager, peer_client_socket_manager, self.conn, self.stop_event
        )
        self.conn.attach(server_man)

        server_man.run()

        assert client_mock_sock.recv.call_count == 2


    def test_server_manager_fail_accept_time_out(self):
        for tries in range(1, 4):
            mock_sock: MagicMock = MagicMock()

            mock_sock.accept.side_effect = timeout
            server_socket_config: ServerSocketConfig = ServerSocketConfig(self.host, self.port, retries=tries)
            server_socket_manager: ServerSocketManager = ServerSocketManager(
                mock_sock, server_socket_config
            )
            peer_client_socket_manager: PeerClientSocketManager = PeerClientSocketManager()
            server_man: ServerManager = ServerManager(
                server_socket_manager, peer_client_socket_manager, self.conn, self.stop_event
            )
            self.conn.attach(server_man)

            server_man.run()

            assert mock_sock.accept.call_count == server_socket_config.retries