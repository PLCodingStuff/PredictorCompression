from socket import (
    socket,
    timeout,
    SOL_SOCKET,
    SO_REUSEADDR,
    SHUT_RDWR,
    # AF_INET,
    # SOCK_STREAM,
)
from ipaddress import ip_address
from src.interfaces.observer import Observer
from src.network_components.connection import Connection
import errno

CONNECTION_LOST_ERRORS = {
    errno.ECONNRESET,
    errno.ECONNABORTED,
    errno.EPIPE,
    errno.ETIMEDOUT,
}


class ServerTerminatingError(OSError):
    """Raised when the server fails to establish a connection after all retries."""

    def __init__(self, retries: int):
        self.retries = retries
        super().__init__(
            f"No connection established after {retries} retries. Terminating..."
        )


class ServerSocketManager(Observer):
    def __init__(
        self,
        host: str,
        port: int,
        sock: socket,
        timeout: float = 5.0,
        retries: int = 3,
        buffer_size: int = 1024,
    ) -> None:
        if not sock:
            raise ValueError("No socket provided")

        try:
            ip_address(host)
        except ValueError:
            raise ValueError("Invalid host name")

        if port <= 0:
            raise ValueError("Port value out of range")

        if timeout < 0.0:
            raise ValueError("Timeout value out of range")

        if retries < 0:
            raise ValueError("Retries value out of range")

        self._retries = retries
        self._host = host
        self._port = port
        self._buffer_size = buffer_size
        self._conn_s: socket | None = None
        self._socket: socket = sock
        self._should_close = False
        # self._socket = socket(AF_INET, SOCK_STREAM)
        self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self._socket.settimeout(timeout)

    def __enter__(self) -> "ServerSocketManager":
        try:
            self._bind_and_listen()
            print(f"Server listening on {self._host}:{self._port}")
            return self
        except OSError as e:
            self._close_server_socket()
            if e.errno == errno.EACCES:
                raise PermissionError(f"Port {self._port} is occupied")
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
        if self._socket:
            self._socket.close()
            self._socket = None

    def _bind_and_listen(self) -> None:
        self._socket.bind((self._host, self._port))
        self._socket.listen(1)

    def accept(self) -> str:
        for r in range(self._retries):
            try:
                self._conn_s, addr = self._socket.accept()
                return str(addr)
            except timeout:
                # if r != self._retries - 1:
                #     print("No connection. Retrying...")
                ...

        raise ServerTerminatingError(self._retries)

    def get_message(self) -> bytearray:
        message: bytearray = self._conn_s.recv(self._buffer_size)

        if not message:
            raise ConnectionResetError("Peer disconnected gracefully.")

        return message

    @property
    def should_close(self) -> bool:
        return self._should_close

    def update(self, data: Connection) -> None:
        if not data.state:
            self._should_close = True


class ServerManager:
    def __init__(self, server_sock_man: ServerSocketManager, conn: Connection) -> None:
        self._server_sock_man: ServerSocketManager = server_sock_man
        self._conn: Connection = conn

    def accept(self) -> None:
        addr: str = self._server_sock_man.accept()
        print(f"Client {addr} successfully connected")
        self._conn.update_state()

    def get_message(self) -> bytearray:
        try:
            msg: bytearray = self._server_sock_man.get_message()
            return msg
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            self._conn.update_state()
            return bytearray()
        except OSError as e:
            if e.errno in CONNECTION_LOST_ERRORS:
                self._conn.update_state()
                return bytearray()
            raise
