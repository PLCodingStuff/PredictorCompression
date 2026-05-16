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
from src.payload_compression.decompression import Decompression
import errno


class Server(Observer):
    """
    Server class that listens for incoming client connections, receives compressed messages, decompresses them, and manages communication. The server uses a shared connection object to maintain the state of the connection.

    Attributes:
        conn (Connection): The connection object.
        _decompressor (Decompression): Instance of the Decompression class for decompressing messages.

    Methods:
        start() -> None: Starts the server, listens for incoming connections, and handles communication.
        handler() -> None: Manages message reception and decompression in a loop.
        close() -> None: Closes the server connection and terminates the socket.
    """

    def __init__(
        self,
        host: str,
        port: int,
        conn: Connection = None,
        timeout: float = 5.0,
        retries: int = 3,
    ) -> None:
        """
        Initialize the Server object with a host address, port number, and connection object.

        Args:
            host (str): The host address on which the server listens for connections.
            port (int): The port number on which the server listens for connections.
            conn (Connection): The shared connection object for maintaining the connection state.
            timeout (float): The timeout (in seconds) on receiving messages. Default is 5 seconds.

        The server socket is set up to reuse the same address to avoid binding issues during restart.
        """
        self.conn_s: socket = None
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
        self._socket = socket(AF_INET, SOCK_STREAM)
        self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self._socket.settimeout(timeout)

    def start(self) -> None:
        """
        Start the server, bind to the specified address, and listen for incoming connections.

        This method binds the server socket to a port, listens for an incoming client connection, and accepts the connection.

        Raises:
            OSError: If there is an error during binding or connection.
            PermissionError: If the port of the socket is occupied.
        """
        try:
            self._socket.bind((self._host, self._port))
            self._socket.listen(1)
            print(f"Server listening on {self._host}:{self._port}")

            addr = None
            for r in range(self._retries):
                try:
                    self.conn_s, addr = self._socket.accept()
                    print(f"{str(addr)} connected")
                    self._conn.update_state()
                    break
                except timeout:
                    if r != self._retries - 1:
                        print("No connection. Retrying...")
                    continue
            if addr is None:
                raise OSError("No connection established...\nTerminating...")

        except OSError as e:
            self._socket.close()
            self._socket = None
            if e.args[0] == errno.EACCES:
                raise PermissionError(f"Port {self._port} is occupied")
            if "No connection established" in str(e):
                print(str(e))
                return
            raise

    def start_and_handle(self):
        self.start()
        self.handler()

    def handler(self, decompressor: Decompression) -> None:
        """
        Handle incoming messages from the client, decompress them, and display the messages.

        This method continuously receives compressed data from the client, decompresses the data, and displays the messages. If the client sends an 'exit' message, the connection is terminated, and the handler exits.
        """
        while True:
            try:
                compressed_data: bytearray = self.conn_s.recv(1024)

                if not compressed_data:
                    self._conn.update_state()
                    self.conn_s.close()
                    self.conn_s = None
                    print("Peer has disconnected.")
                    return

                message: str = decompressor.payload_decompression(compressed_data)

                print(f"Received message: {message}")

                if message == "exit":
                    print("Peer requested disconnection.")
                    self._conn.update_state()
                    print("Press Enter to exit")
                    break
            except (timeout, ValueError):
                continue
            except OSError as e:
                print(str(e))
                self.close()
                break

    def close(self) -> None:
        """
        Close the server connection and terminate the socket.

        This method attempts to gracefully shut down the server connection and close the client and server sockets. If there is no active connection, it handles the associated socket error gracefully.
        """
        if self.conn_s:
            try:
                self.conn_s.shutdown(SHUT_RDWR)
            except OSError as e:
                print(f"Error Shutting Down Server Connection socket: {str(e)}")
            self.conn_s.close()
            self.conn_s = None
        self._conn.update_state()
        if self._socket:
            self._socket.close()
            self._socket = None

    def update(self, data: Connection):
        if not data.state:
            self.close()
