from src.interfaces.observer import Observer
from src.business.messages.receive_message import ReceiveMessageProcessor
from src.business.messages.message_output import MessageOutput
from src.network_components.connection import Connection
from src.network_components.framing import MessageType, send_frame, recv_frame
from src.network_components.handshake import perform_handshake
from src.errors.server_errors import (
    ConnectionLostError,
    AcceptTimeOutError,
)
from src.errors.protocol_errors import HandshakeError


from dataclasses import dataclass
from socket import (
    socket,
    timeout,
    SOL_SOCKET,
    SO_REUSEADDR,
    SHUT_RDWR,
)
import errno
from threading import Event
from ipaddress import ip_address


@dataclass
class ServerSocketConfig:
    host: str
    port: int
    timeout: float = 5.0
    retries: int = 3

    def __post_init__(self):
        try:
            ip_address(self.host)
        except ValueError:
            raise ValueError("Invalid host name")

        if self.port <= 0 or self.port > 65535:
            raise ValueError("Port value out of range")

        if self.timeout < 0.0:
            raise ValueError("Timeout value out of range")

        if self.retries < 0:
            raise ValueError("Retries value out of range")


class ServerSocket(socket):
    def __init__(self, config: ServerSocketConfig, *args, **kwargs) -> None:
        self._config: ServerSocketConfig = config
        super().__init__(*args, **kwargs)

    def __enter__(self) -> "ServerSocket":
        try:
            self.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.settimeout(self._config.timeout)

            self._bind_and_listen()
            return self
        except OSError as e:
            self._close_socket()
            if e.args[0] == errno.EACCES:
                raise PermissionError(f"Port {self._config.port} is occupied")
            raise

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._close_socket()
        if exc_type == AcceptTimeOutError:
            return True
        return False

    def _close_socket(self) -> None:
        if not self._closed:
            self.close()

    def _bind_and_listen(self) -> None:
        self.bind((self._config.host, self._config.port))
        self.listen(1)

    def accept(self) -> socket:
        for _ in range(int(self._config.retries)):
            try:
                c_sock, _ = super().accept()
                return c_sock
            except timeout:
                continue
        raise AcceptTimeOutError(self._config.retries)


class PeerClientSocketManager:
    def __init__(self, buffer_size: int = 1024, timeout: float = 5.0):
        if buffer_size <= 0:
            raise ValueError("Invalid Buffer Size")

        self._buffer_size: int = buffer_size
        self._timeout: float = timeout
        self._sock: socket | None = None

    def __enter__(self) -> "PeerClientSocketManager":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._close_socket()
        if exc_type in (ConnectionLostError, HandshakeError):
            return True
        return False

    def _close_socket(self):
        if self._sock:
            try:
                self._sock.shutdown(SHUT_RDWR)
            except OSError:
                pass
            self._sock.close()
            self._sock = None

    def set_socket(self, sock: socket):
        self._sock = sock
        self._sock.settimeout(self._timeout)

    def send_frame(self, msg_type: MessageType, payload: bytes = b"") -> None:
        send_frame(self._sock, msg_type, payload)

    def recv_frame(self) -> tuple[MessageType, bytearray]:
        return recv_frame(self._sock)


class ServerManager(Observer):
    def __init__(
        self,
        server_sock: socket,
        peer_client_sock_man: PeerClientSocketManager,
        conn: Connection,
        stop_event: Event,
        message_proc: ReceiveMessageProcessor,
        message_output: MessageOutput,
    ) -> None:
        if not server_sock:
            raise ValueError("No socket provided")
        if not peer_client_sock_man:
            raise ValueError("No peer socket provided")
        if not conn:
            raise ValueError("No connection provided")
        if not stop_event:
            raise ValueError("No stop event provided")
        if not message_proc:
            raise ValueError("No message processor provided")
        if not message_output:
            raise ValueError("No message output provided")

        self._peer_c_sock_man: PeerClientSocketManager = peer_client_sock_man
        self._sock: socket = server_sock
        self._conn: Connection = conn
        self._stop_event = stop_event
        self._msg_proc: ReceiveMessageProcessor = message_proc
        self._msg_out: MessageOutput = message_output

    def update(self, data: Connection) -> None:
        if not data.state:
            self._stop_event.set()

    def run(self) -> None:
        with self._sock as server:
            try:
                self._peer_c_sock_man.set_socket(server.accept())
            except AcceptTimeOutError:
                return

            with self._peer_c_sock_man as peer_sock:
                try:
                    perform_handshake(peer_sock)
                except HandshakeError:
                    return

                self._conn.update_state()
                while not self._stop_event.is_set():
                    try:
                        msg_type, payload = peer_sock.recv_frame()
                    except ConnectionLostError:
                        self._conn.update_state()
                        break
                    except timeout:
                        continue

                    if msg_type == MessageType.MSG:
                        processed_msg: str = self._msg_proc.parse_received(payload)
                        self._msg_out.display(processed_msg)
                    elif msg_type == MessageType.QUIT:
                        self._msg_out.display("Peer has left the chat.")
                        self._conn.update_state()
                    else:
                        self._msg_out.display(
                            f"Ignored unexpected control frame: {msg_type.name}"
                        )
