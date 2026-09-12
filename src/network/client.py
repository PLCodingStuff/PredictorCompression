from src.network_components.connection import Connection
from src.network_components.framing import MessageType, send_frame, recv_frame
from src.network_components.handshake import perform_handshake
from src.business.messages.send_message import SendMessageProcessor
from src.business.messages.message_source import MessageSource
from src.interfaces.observer import Observer
from src.errors.client_errors import ConnectTimeOutError
from src.errors.protocol_errors import HandshakeError
from src.errors.server_errors import ConnectionLostError

from dataclasses import dataclass
from threading import Event
from socket import socket, SHUT_RDWR, timeout
from ipaddress import ip_address
import sys


@dataclass
class ClientSocketConfig:
    peer_host: str
    peer_port: int
    retries: int = 3
    timeout: float = 5

    def __post_init__(self):
        try:
            ip_address(self.peer_host)
        except ValueError:
            raise ValueError("Invalid host address")

        if self.peer_port <= 0 or self.peer_port > 65535:
            raise ValueError("Invalid port number")

        if self.retries < 0:
            raise ValueError("Invalid number of retries")

        if self.timeout < 0.0:
            raise ValueError("Invalid timeout")


class ClientSocket(socket):
    def __init__(self, config: ClientSocketConfig, *args, **kwargs) -> None:
        self._config = config
        super().__init__(*args, **kwargs)

    def __enter__(self) -> "ClientSocket":

        self.settimeout(self._config.timeout)
        for _ in range(self._config.retries):
            try:
                self.connect((self._config.peer_host, self._config.peer_port))
                return self
            except timeout:
                pass

        raise ConnectTimeOutError(self._config.retries)

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._close_socket()
        return False

    def _close_socket(self):
        if not self._closed:
            try:
                self.shutdown(SHUT_RDWR)
            except OSError:
                pass
            self.close()

    def send_frame(self, msg_type: MessageType, payload: bytes = b"") -> None:
        send_frame(self, msg_type, payload)

    def recv_frame(self) -> tuple[MessageType, bytearray]:
        return recv_frame(self)

    def send_message(self, msg: bytearray):
        self.send_frame(MessageType.MSG, msg)


class ClientManager(Observer):
    def __init__(
        self,
        socket: ClientSocket,
        conn: Connection,
        stop_event: Event,
        message_proc: SendMessageProcessor,
        message_source: MessageSource,
    ) -> None:
        self._sock: ClientSocket = socket
        self._conn: Connection = conn
        self._stop_event: Event = stop_event
        self._message_proc: SendMessageProcessor = message_proc
        self._message_source: MessageSource = message_source

    def update(self, data: Connection):
        if not data.state:
            self._stop_event.set()

    def run(self):
        try:
            with self._sock as sock:
                try:
                    perform_handshake(sock)
                except HandshakeError as e:
                    print(f"Handshake failed: {e}", file=sys.stderr)
                    return

                self._conn.update_state(True)

                msg: str = ""
                while not self._stop_event.is_set():
                    msg: str | None = self._message_source.next_message()

                    if not msg:
                        try:
                            sock.send_frame(MessageType.QUIT)
                        except (ConnectionLostError, OSError):
                            pass
                        self._conn.update_state(False)
                        break

                    processed_msg: bytearray = self._message_proc.prepare_to_send(msg)
                    sock.send_message(processed_msg)

        except ConnectTimeOutError:
            return
