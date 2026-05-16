from socket import (
    socket,
    timeout,
    SOL_SOCKET,
    SO_REUSEADDR,
    SHUT_RDWR,
    AF_INET,
    SOCK_STREAM,
)
from ipaddress import ip_address
from src.interfaces.observer import Observer
from src.network_components.connection import Connection
import errno


class Server(Observer):
    def __init__(
        self,
        host: str,
        port: int,
        conn: Connection,
        timeout: float = 5.0,
        retries: int = 3,
    ) -> None:
        if not conn:
            raise ValueError("Invalid connection")

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
        self._conn = conn
        self._conn_s: socket = None
        self._socket = socket(AF_INET, SOCK_STREAM)
        self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self._socket.settimeout(timeout)

    def _bind_and_listen(self):
        self._socket.bind((self._host, self._port))
        self._socket.listen(1)
        print(f"Server listening on {self._host}:{self._port}")

    def _accept(self):
        addr = None
        for r in range(self._retries):
            try:
                self._conn_s, addr = self._socket.accept()
                print(f"{str(addr)} connected")
                self._conn.update_state()
                break
            except timeout:
                if r != self._retries - 1:
                    print("No connection. Retrying...")
                continue
        if addr is None:
            raise OSError("No connection established...\nTerminating...")

    def start(self) -> None:
        try:
            self._bind_and_listen()

            self._accept()
        except OSError as e:
            self._socket.close()
            self._socket = None
            if e.args[0] == errno.EACCES:
                raise PermissionError(f"Port {self._port} is occupied")
            if "No connection established" in str(e):
                print(str(e))
                return
            raise

    def handler(self) -> bytearray:
        try:
            message: bytearray = self._conn_s.recv(1024)

            if not message:
                print("Sudden peer connection terminated.")
                print("Terminating")
                self.close()

            return message
        except OSError as e:
            print(str(e))
            print("Terminating")
            self.close()

    def close(self) -> None:
        if self._conn_s:
            try:
                self._conn_s.shutdown(SHUT_RDWR)
            except OSError as e:
                print(f"Error Shutting Down Server Connection socket: {str(e)}")
            self._conn_s.close()
            self._conn_s = None
        self._conn.update_state()
        if self._socket:
            self._socket.close()
            self._socket = None

    def update(self, data: Connection):
        if not data.state:
            self.close()
