import pytest
from unittest.mock import MagicMock

from src.network.server import (
    ServerSocketConfig,
    PeerClientSocketManager,
    ServerManager,
    ServerSocket,
)
from src.business.messages.message_output import CLIMessageOutput

from src.business.messages.receive_message import ReceiveMessageProcessor

from src.errors.server_errors import AcceptTimeOutError
from src.network_components.connection import Connection

from threading import Event, Thread
import socket


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

    def test_server_socket_config_port_error_smaller(self):
        invalid_port: int = 0

        with pytest.raises(ValueError, match="Port value out of range"):
            ServerSocketConfig(self.host, invalid_port)

    def test_server_socket_config_port_error_bigger(self):
        invalid_port: int = 700000

        with pytest.raises(ValueError, match="Port value out of range"):
            ServerSocketConfig(self.host, invalid_port)

    def test_server_socket_config_timeout_error(self):
        with pytest.raises(ValueError, match="Timeout value out of range"):
            ServerSocketConfig(self.host, self.port, timeout=-1.0)

    def test_server_socket_config_retries_error(self):
        with pytest.raises(ValueError, match="Retries value out of range"):
            ServerSocketConfig(self.host, self.port, retries=-1)


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


class TestServerManagerInit:
    server_sock: MagicMock = MagicMock()
    peer_client_socket_manager: MagicMock = MagicMock()
    conn: MagicMock = MagicMock()
    stop_event: MagicMock = MagicMock()
    receive_message_proc: MagicMock = MagicMock()
    output: MagicMock = MagicMock()

    def test_server_manager_init(self):
        assert ServerManager(
            self.server_sock,
            self.peer_client_socket_manager,
            self.conn,
            self.stop_event,
            self.receive_message_proc,
            self.output,
        )

    def test_server_manager_init_fail_server_sock(self):
        with pytest.raises(ValueError):
            ServerManager(
                None,
                self.peer_client_socket_manager,
                self.conn,
                self.stop_event,
                self.receive_message_proc,
                self.output,
            )

    def test_server_manager_init_fail_peer_client_socket_manager(self):
        with pytest.raises(ValueError):
            ServerManager(
                self.server_sock,
                None,
                self.conn,
                self.stop_event,
                self.receive_message_proc,
                self.output,
            )

    def test_server_manager_init_fail_connection(self):
        with pytest.raises(ValueError):
            ServerManager(
                self.server_sock,
                self.peer_client_socket_manager,
                None,
                self.stop_event,
                self.receive_message_proc,
                self.output,
            )

    def test_server_manager_init_fail_stop_event(self):
        with pytest.raises(ValueError):
            ServerManager(
                self.server_sock,
                self.peer_client_socket_manager,
                self.conn,
                None,
                self.receive_message_proc,
                self.output,
            )

    def test_server_manager_init_fail_receive_message_proc(self):
        with pytest.raises(ValueError):
            ServerManager(
                self.server_sock,
                self.peer_client_socket_manager,
                self.conn,
                self.stop_event,
                None,
                self.output,
            )

    def test_server_manager_init_fail_output(self):
        with pytest.raises(ValueError):
            ServerManager(
                self.server_sock,
                self.peer_client_socket_manager,
                self.conn,
                self.stop_event,
                self.receive_message_proc,
                None,
            )

class TestServerManager:
    host: str = "127.0.0.1"
    port: int = 6000
    conn: Connection = Connection()
    stop_event: Event = Event()

    def test_mock_server_manager(self):
        client_mock_sock: MagicMock = MagicMock()

        client_mock_sock.recv.side_effect = [
            bytearray("Hello World", encoding="ASCII"),
            bytearray(),
        ]

        server_sock: MagicMock = MagicMock()
        server_sock.__enter__.return_value = server_sock
        server_sock.accept.return_value = client_mock_sock

        output_mock: MagicMock = MagicMock()

        peer_client_socket_manager: PeerClientSocketManager = PeerClientSocketManager()

        receive_message_proc: ReceiveMessageProcessor = ReceiveMessageProcessor()

        server_man: ServerManager = ServerManager(
            server_sock,
            peer_client_socket_manager,
            self.conn,
            self.stop_event,
            receive_message_proc,
            output_mock,
        )
        self.conn.attach(server_man)

        server_man.run()

        assert client_mock_sock.recv.call_count == 2

    def test_mock_server_manager_fail_accept_time_out(self):
        retries: int = 3

        server_sock: MagicMock = MagicMock()
        server_sock.__enter__.return_value = server_sock
        server_sock.accept.side_effect = AcceptTimeOutError(retries)

        peer_client_socket_manager: PeerClientSocketManager = PeerClientSocketManager()
        receive_message_proc: ReceiveMessageProcessor = ReceiveMessageProcessor()
        output_mock: MagicMock = MagicMock()

        server_man: ServerManager = ServerManager(
            server_sock,
            peer_client_socket_manager,
            self.conn,
            self.stop_event,
            receive_message_proc,
            output_mock,
        )
        self.conn.attach(server_man)

        server_man.run()

        assert not server_man._peer_c_sock_man._sock

    def echo_client(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((self.host, self.port))

        client.sendall(b"hello")
        client.sendall(b"")
        client.close()

    def echo_client_sudden_disconnect(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((self.host, self.port))

        client.sendall(b"hello")
        client.close()

    def test_server_manager(self):
        server_conf: ServerSocketConfig = ServerSocketConfig(self.host, self.port)
        server_sock: ServerSocket = ServerSocket(server_conf, socket.AF_INET, socket.SOCK_STREAM)

        msg_proc: ReceiveMessageProcessor = ReceiveMessageProcessor()
        msg_out: CLIMessageOutput = CLIMessageOutput()

        peer_client: PeerClientSocketManager = PeerClientSocketManager()

        server: ServerManager = ServerManager(
            server_sock,
            peer_client,
            self.conn,
            self.stop_event,
            msg_proc,
            msg_out,
        )

        thread = Thread(target=server.run, daemon=True)
        thread.start()

        self.echo_client()


    # @pytest.mark.skip(reason="TODO")
    def test_server_manager_sudden_disconnect(self):
        server_conf: ServerSocketConfig = ServerSocketConfig(self.host, self.port)
        server_sock: ServerSocket = ServerSocket(server_conf, socket.AF_INET, socket.SOCK_STREAM)

        msg_proc: ReceiveMessageProcessor = ReceiveMessageProcessor()
        msg_out: CLIMessageOutput = CLIMessageOutput()

        peer_client: PeerClientSocketManager = PeerClientSocketManager()

        server: ServerManager = ServerManager(
            server_sock,
            peer_client,
            self.conn,
            self.stop_event,
            msg_proc,
            msg_out,
        )

        thread = Thread(target=server.run, daemon=True)
        thread.start()

        self.echo_client_sudden_disconnect()
