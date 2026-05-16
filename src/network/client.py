from src.network_components.connection import Connection
from src.interfaces.observer import Observer
from socket import error as sockerror, SHUT_RDWR
from src.payload_compression.compression import Compression
from time import sleep


class Client(Observer):
    """
    Client class that connects to a peer server, sends compressed messages,
    and handles the communication. It uses a retry mechanism for establishing
    the connection and manages the message-sending process.

    Attributes:
        _compressor (Compression): Instance of the Compression class for message compression.
        _peer_host (str): The host address of the peer server.
        _peer_port (int): The port number of the peer server.
        _retries (int): The maximum number of connection retry attempts.
        _delay (float): The delay between each connection retry.

    Methods:
        start() -> None: Starts the client and attempts to connect to the peer server.
        __send_message(msg: str) -> None: Compresses and sends a message to the server.
        handler() -> None: Handles user input and manages message sending in a loop.
        close() -> None: Closes the client connection and shuts down the socket.
    """

    def __init__(
        self,
        peer_host: str,
        peer_port: int,
        conn: Connection,
        retries: int = 7,
        delay: float = 3.0,
    ) -> None:
        """
        Initialize the Client object with peer server details and connection parameters.

        Args:
            peer_host (str): The peer server's host address.
            peer_port (int): The peer server's port number.
            conn (Connection): The shared connection object.
            retries (int, optional): The number of connection retry attempts. Default is 7.
            delay (float, optional): The delay between connection attempts in seconds. Default is 3.0.

        The Client object uses the Connection object to monitor and manage the connection state.
        """
        self._peer_host: str = peer_host
        self._peer_port: int = peer_port
        self._retries: int = retries
        self._delay: float = delay
        self._conn = conn

    def start(self) -> None:
        """
        Attempt to connect to the peer server with retries.

        This method tries to establish a connection to the peer server. If the connection is refused or fails, it retries the connection based on the `retries` and `delay` settings. If the maximum number of retries is exceeded or a timeout occurs, appropriate exceptions are raised.

        Raises:
            ConnectionAbortedError: If the connection cannot be established after all retries.
            TimeoutError: If the connection attempt times out.
        """
        retry: int = 0
        try:
            while retry < self._retries:
                try:
                    self._socket.settimeout(10)
                    self._socket.connect((self._peer_host, self._peer_port))
                    print(f"Connected to {self._peer_host}:{self._peer_port}")
                    break
                except ConnectionRefusedError:
                    retry += 1
                    sleep(self._delay)

            if retry == self._retries:
                raise ConnectionAbortedError
        except TimeoutError:
            print("Connection timed out.")
        except ConnectionAbortedError:
            print("Peer server's not running. Terminating process.")
            raise ConnectionAbortedError


    def handler(self, compressor: Compression):
        """
        Handle user input and send messages to the peer server.

        This method continuously reads user input and sends messages to the peer server. The user can type 'exit' to terminate the communication and close the connection. If the connection is lost, the loop will break, and the client will terminate.
        """
        while True:
            message = input("")
            try:
                compressed_msg: bytearray = compressor.payload_compression(message)
                
                if not self._conn.state:
                    raise ConnectionError
                
                self._socket.sendall(compressed_msg)

                if message.lower() == "exit":
                    print("Exiting chat...")
                    break

            except ConnectionError:
                print("Error: Connection Timed Out")
                break
            except ValueError as e:
                print(str(e))
                break

    def close(self):
        """
        Close the client socket and terminate the connection.

        This method attempts to gracefully shut down the client socket. If there is no active connection, it catches the socket error and closes the socket.
        """
        if self._socket is not None:
            try:
                self._socket.shutdown(SHUT_RDWR)
            except sockerror as e:
                # This error is due to lack of connection, so
                # `shutdown()` cannot be called without one.
                if e.errno != 10057:
                    print(f"Client Error {e}")
            self._socket.close()
            self._socket = None

    def update(self, data: Connection):
        if not data.state:
            self.close()
