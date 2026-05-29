from src.interfaces.observer import Observer
from src.business.messages.receive_message import ReceiveMessageProcessor
from src.business.messages.message_output import MessageOutput
from src.network_components.connection import Connection
from src.errors.server_errors import (
    ConnectionLostError,
    AcceptTimeOutError,
    CONNECTION_LOST_ERRORS,
)

from typing import Protocol
from dataclasses import dataclass
from socket import (
    socket,
    timeout,
    SOL_SOCKET,
    SO_REUSEADDR,
    SHUT_RDWR,
    AF_INET,
    SOCK_STREAM,
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


class IServerSocket(Protocol):
    def __enter__(self) -> "IServerSocket": ...
    def __exit__(self, exc_type, exc, tb) -> bool: ...
    def accept(self) -> socket: ...


class ServerSocket(IServerSocket):
    def __init__(
        self,
        config: ServerSocketConfig,
    ) -> None:
        self._sock: socket | None = None
        self._config: ServerSocketConfig = config

    def __enter__(self) -> "IServerSocket":
        try:
            self._sock = socket(AF_INET, SOCK_STREAM)
            self._sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self._sock.settimeout(self._config.timeout)

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
        if self._sock:
            self._sock.close()
            self._sock = None

    def _bind_and_listen(self) -> None:
        self._sock.bind((self._config.host, self._config.port))
        self._sock.listen(1)

    def accept(self) -> socket:
        for _ in range(self._config.retries):
            try:
                c_sock, _ = self._sock.accept()
                return c_sock
            except timeout:
                continue
        raise AcceptTimeOutError(self._config.retries)


class PeerClientSocketManager:
    def __init__(self, buffer_size: int = 1024):
        if buffer_size <= 0:
            raise ValueError("Invalid Buffer Size")

        self._buffer_size: int = buffer_size
        self._sock: socket | None = None

    def __enter__(self) -> "PeerClientSocketManager":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._close_socket()
        if exc_type == ConnectionLostError:
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

    def get_message(self) -> bytearray:
        try:
            message: bytearray = self._sock.recv(self._buffer_size)

            if not message:
                raise ConnectionLostError("Peer disconnected gracefully.")

            return message
        except OSError as e:
            if e.errno in CONNECTION_LOST_ERRORS:
                raise ConnectionLostError(str(e))
            raise


class ServerManager(Observer):
    def __init__(
        self,
        server_sock: IServerSocket,
        peer_client_sock_man: PeerClientSocketManager,
        conn: Connection,
        stop_event: Event,
        message_proc: ReceiveMessageProcessor,
        message_output: MessageOutput
    ) -> None:
        self._sock: IServerSocket = server_sock
        self._peer_c_sock_man: PeerClientSocketManager = peer_client_sock_man
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

            self._conn.update_state()
            with self._peer_c_sock_man as peer_sock:
                while not self._stop_event.is_set():
                    try:
                        msg = peer_sock.get_message()
                        processed_msg: str = self._msg_proc.parse_received(msg)
                        self._msg_out.display(processed_msg)
                        
                    except ConnectionLostError:
                        self._conn.update_state()
