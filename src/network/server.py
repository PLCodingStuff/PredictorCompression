from socket import (
    socket,
    timeout,
    SOL_SOCKET,
    SO_REUSEADDR,
    SHUT_RDWR,
    AF_INET,
    SOCK_STREAM,
)
from typing import Callable, ParamSpec, TypeAlias
from dataclasses import dataclass
import errno
from threading import Event
from ipaddress import ip_address
from src.interfaces.observer import Observer
from src.network_components.connection import Connection

CONNECTION_LOST_ERRORS = {
    errno.ECONNRESET,
    errno.ECONNABORTED,
    errno.EPIPE,
    errno.ETIMEDOUT,
}

P = ParamSpec("P")
SocketFactory: TypeAlias = Callable[P, socket]


class ConnectionLostError(OSError):
    """Raised when the client disconnects suddenly."""

    ...


class ServerTerminatingError(OSError):
    """Raised when the server fails to establish a connection after all retries."""

    def __init__(self, retries: int):
        super().__init__(
            f"No connection established after {retries} retries. Terminating..."
        )


def default_socket_factory(timeout: int) -> socket:

    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.settimeout(timeout)
    return sock


@dataclass
class ServerConfig:
    host: str
    port: int
    timeout: float = 5.0
    buffer_size: int = 1024
    retries: int = 5

    def __post_init__(self):
        try:
            ip_address(self.host)
        except ValueError:
            raise ValueError("Invalid host name")

        if self.port <= 0 or self.port > 65536:
            raise ValueError("Port value out of range")

        if self.timeout < 0.0:
            raise ValueError("Timeout value out of range")

        if self.retries < 0:
            raise ValueError("Retries value out of range")


class ServerSocketManager:
    def __init__(
        self,
        config: ServerConfig,
        socket_factory: SocketFactory = default_socket_factory,
    ) -> None:
        self._conn_s: socket | None = None
        self._sock: socket | None = None
        self._config: ServerConfig = config
        self._socket_factory: SocketFactory = socket_factory

    def __enter__(self) -> "ServerSocketManager":
        try:
            self._sock: socket = self._socket_factory(self._config.timeout)

            self._bind_and_listen()
            return self
        except OSError as e:
            self._close_server_socket()
            if e.errno == errno.EACCES:
                raise PermissionError(f"Port {self._config.port} is occupied")
            raise

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._close_conn_socket()
        self._close_server_socket()
        return False

    def _close_conn_socket(self) -> None:
        if self._conn_s:
            try:
                self._conn_s.shutdown(SHUT_RDWR)
            except OSError:
                pass
            self._conn_s.close()
            self._conn_s = None

    def _close_server_socket(self) -> None:
        if self._sock:
            self._sock.close()
            self._sock = None

    def _bind_and_listen(self) -> None:
        self._sock.bind((self._config.host, self._config.port))
        self._sock.listen(1)

    def accept(self) -> str:
        for _ in range(self._config.retries):
            try:
                self._conn_s, addr = self._sock.accept()
                return str(addr)
            except timeout:
                continue
        raise ServerTerminatingError(self._config.retries)

    def get_message(self) -> bytearray:
        try:
            message: bytearray = self._conn_s.recv(self._config.buffer_size)

            if not message:
                raise ConnectionResetError("Peer disconnected gracefully.")

            return message
        except OSError as e:
            if e.errno in CONNECTION_LOST_ERRORS:
                raise ConnectionLostError(str(e))
            raise


class ServerManager(Observer):
    def __init__(
        self, server_sock_man: ServerSocketManager, conn: Connection, stop_event: Event
    ) -> None:
        self._sock_man: ServerSocketManager = server_sock_man
        self._conn: Connection = conn
        self._stop_event = stop_event

    def update(self, data: Connection) -> None:
        if not data.state:
            self._stop_event.set()

    def run(self) -> None:
        with self._sock_man as server:
            try:
                server.accept()
            except ServerTerminatingError:
                self._conn.update_state()
                return

            while not self._stop_event.is_set():
                try:
                    msg = server.get_message()
                    msg
                    # handle msg
                except ConnectionLostError:
                    self._conn.update_state()
                    
