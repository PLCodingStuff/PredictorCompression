from src.network_components.connection import Connection
from src.interfaces.observer import Observer
from src.errors.client_errors import ConnectTimeOutError

from dataclasses import dataclass
from threading import Event
from socket import socket, SHUT_RDWR, timeout
from ipaddress import ip_address


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

        if self.peer_port <= 0 or self.peer_port > 65355:
            raise ValueError("Invalid port number")

        if self.retries < 0:
            raise ValueError("Invalid number of retries")

        if self.timeout < 0.0:
            raise ValueError("Invalid timeout")


class ClientSocketManager:
    def __init__(self, sock: socket, config: ClientSocketConfig):
        self._config = config
        self._sock = sock

    def __enter__(self) -> "ClientSocketManager":
        self._sock.settimeout(self._config.timeout)

        for _ in range(self._config.retries):
            try:
                self._sock.connect((self._config.peer_host, self._config.peer_port))
                return self
            except timeout:
                pass

            raise ConnectTimeOutError(self._config.retries)

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._close_socket()
        return False

    def _close_socket(self):
        if self._sock is not None:
            try:
                self._sock.shutdown(SHUT_RDWR)
            except OSError:
                pass
            self._sock.close()
            self._sock = None

    def send_message(self, msg: bytearray):
        self._sock.sendall(msg)


class ClientManager(Observer):
    def __init__(
        self,
        client_socket_man: ClientSocketManager,
        conn: Connection,
        stop_event: Event,
    ) -> None:
        self._c_sock_man: ClientSocketManager = client_socket_man
        self._conn: Connection = conn
        self._stop_event: Event = stop_event

    def update(self, data: Connection):
        if not data.state:
            self._stop_event.set()

    def run(self):
        try: 
            with self._c_sock_man as c_man:
                self._conn.update_state()

                msg: bytearray = bytearray()
                while not self._stop_event.is_set():
                    # TODO: add message pipeline
                    c_man.send_message(msg)

                    if not msg:
                        self._conn.update_state()

                    # Or
                    # if msg == "exit":
                    #   self._conn.update_state()
        except ConnectTimeOutError:
            return