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
from src.network_components.framing import (
    MessageType,
    pack_frame,
    send_frame as _send_frame,
    recv_frame as _recv_frame,
)
from src.business.compression.compression import Compression

from threading import Event, Thread
import socket
from time import sleep


def _recv_stream(*frames: bytes):
    """Builds a MagicMock-compatible recv() side effect that honors the requested
    byte count, regardless of how the frames were chunked when constructed."""
    buf = bytearray()
    for f in frames:
        buf.extend(f)

    def _recv(n: int) -> bytes:
        if not buf:
            return b""
        chunk = bytes(buf[:n])
        del buf[:n]
        return chunk

    return _recv


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

    def test_peer_client_socket_manager_recv_frame(self):
        manager: PeerClientSocketManager = PeerClientSocketManager()

        payload = bytearray("Hello World", encoding="ASCII")
        mock_sock: MagicMock = MagicMock()
        mock_sock.recv.side_effect = _recv_stream(pack_frame(MessageType.MSG, payload))

        manager.set_socket(mock_sock)
        msg_type: MessageType = None
        received_payload: bytearray = None
        with manager as m:
            msg_type, received_payload = m.recv_frame()

        assert msg_type == MessageType.MSG
        assert received_payload == payload

    def test_peer_client_socket_manager_recv_frame_fail(self):
        manager: PeerClientSocketManager = PeerClientSocketManager()

        mock_sock: MagicMock = MagicMock()
        mock_sock.recv.return_value = bytearray()  # Raises ConnectionLostError

        manager.set_socket(mock_sock)

        # Gracefully fails
        with manager as m:
            m.recv_frame()


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

        compressed: bytearray = Compression().payload_compression("Hello World")
        client_mock_sock.recv.side_effect = _recv_stream(
            pack_frame(MessageType.HELLO),
            pack_frame(MessageType.ACK),
            pack_frame(MessageType.MSG, compressed),
        )

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

        output_mock.display.assert_called_once_with("Hello World")

    def test_server_manager_receives_quit(self):
        conn: Connection = Connection()
        stop_event: Event = Event()

        client_mock_sock: MagicMock = MagicMock()
        client_mock_sock.recv.side_effect = _recv_stream(
            pack_frame(MessageType.HELLO),
            pack_frame(MessageType.ACK),
            pack_frame(MessageType.QUIT),
        )

        server_sock: MagicMock = MagicMock()
        server_sock.__enter__.return_value = server_sock
        server_sock.accept.return_value = client_mock_sock

        output_mock: MagicMock = MagicMock()

        peer_client_socket_manager: PeerClientSocketManager = PeerClientSocketManager()
        receive_message_proc: ReceiveMessageProcessor = ReceiveMessageProcessor()

        server_man: ServerManager = ServerManager(
            server_sock,
            peer_client_socket_manager,
            conn,
            stop_event,
            receive_message_proc,
            output_mock,
        )
        conn.attach(server_man)

        server_man.run()

        output_mock.display.assert_called_once_with("Peer has left the chat.")
        assert stop_event.is_set()

    def test_server_manager_handshake_failure(self):
        conn: Connection = Connection()
        stop_event: Event = Event()

        client_mock_sock: MagicMock = MagicMock()
        client_mock_sock.recv.side_effect = _recv_stream(b"garbage, not a valid frame")

        server_sock: MagicMock = MagicMock()
        server_sock.__enter__.return_value = server_sock
        server_sock.accept.return_value = client_mock_sock

        output_mock: MagicMock = MagicMock()

        peer_client_socket_manager: PeerClientSocketManager = PeerClientSocketManager()
        receive_message_proc: ReceiveMessageProcessor = ReceiveMessageProcessor()

        server_man: ServerManager = ServerManager(
            server_sock,
            peer_client_socket_manager,
            conn,
            stop_event,
            receive_message_proc,
            output_mock,
        )

        server_man.run()

        output_mock.display.assert_not_called()
        assert server_man._peer_c_sock_man._sock is None

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

    def _client_handshake(self, client: socket.socket) -> None:
        _send_frame(client, MessageType.HELLO)
        _recv_frame(client)
        _send_frame(client, MessageType.ACK)
        _recv_frame(client)

    def echo_client(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((self.host, self.port))

        self._client_handshake(client)
        _send_frame(client, MessageType.MSG, Compression().payload_compression("hello"))
        _send_frame(client, MessageType.QUIT)
        client.close()

    def echo_client_sudden_disconnect(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((self.host, self.port))

        self._client_handshake(client)
        _send_frame(client, MessageType.MSG, Compression().payload_compression("hello"))
        client.close()

    def echo_client_delay(self):
        delay: float = 2.0
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((self.host, self.port))

        self._client_handshake(client)
        _send_frame(client, MessageType.MSG, Compression().payload_compression("hello"))
        sleep(delay)
        _send_frame(client, MessageType.QUIT)
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
            Connection(),
            Event(),
            msg_proc,
            msg_out,
        )

        thread = Thread(target=server.run, daemon=True)
        thread.start()

        self.echo_client()


    def test_server_manager_sudden_disconnect(self):
        server_conf: ServerSocketConfig = ServerSocketConfig(self.host, self.port)
        server_sock: ServerSocket = ServerSocket(server_conf, socket.AF_INET, socket.SOCK_STREAM)

        msg_proc: ReceiveMessageProcessor = ReceiveMessageProcessor()
        msg_out: CLIMessageOutput = CLIMessageOutput()

        peer_client: PeerClientSocketManager = PeerClientSocketManager()

        server: ServerManager = ServerManager(
            server_sock,
            peer_client,
            Connection(),
            Event(),
            msg_proc,
            msg_out,
        )

        thread = Thread(target=server.run, daemon=True)
        thread.start()

        self.echo_client_sudden_disconnect()

    @pytest.mark.skip(reason="TODO")
    def test_server_manager_delayed_client(self):
        server_conf: ServerSocketConfig = ServerSocketConfig(self.host, self.port)
        server_sock: ServerSocket = ServerSocket(server_conf, socket.AF_INET, socket.SOCK_STREAM)

        msg_proc: ReceiveMessageProcessor = ReceiveMessageProcessor()
        msg_out: CLIMessageOutput = CLIMessageOutput()

        peer_client: PeerClientSocketManager = PeerClientSocketManager()

        server: ServerManager = ServerManager(
            server_sock,
            peer_client,
            Connection(),
            Event(),
            msg_proc,
            msg_out,
        )

        thread = Thread(target=server.run, daemon=True)
        thread.start()

        self.echo_client_delay()
