from .network_component import NetworkComponent, Connection
from socket import error as sockerror, SHUT_RDWR
from PayloadCompression import Compression
from time import sleep

class Client(NetworkComponent):
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
    def __init__(self, peer_host: str, peer_port: int, 
                       conn: Connection, retries: int = 7,
                       delay: float = 3.0) -> None:
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
        self._compressor: Compression = Compression()
        self._peer_host: str = peer_host
        self._peer_port: int = peer_port
        self._retries: int = retries
        self._delay:float = delay
        super().__init__(None, None, conn)

    def start(self) -> None:
        """
        Attempt to connect to the peer server with retries.

        This method tries to establish a connection to the peer server. If the connection 
        is refused or fails, it retries the connection based on the `retries` and `delay` 
        settings. If the maximum number of retries is exceeded or a timeout occurs, 
        appropriate exceptions are raised.

        Raises:
            ConnectionAbortedError: If the connection cannot be established after all retries.
            TimeoutError: If the connection attempt times out.
        """
        retry: int = 0
        try:
            while retry < self._retries:
                try:
                    sleep(self._delay)
                    self._socket.settimeout(10)
                    self._socket.connect((self._peer_host, self._peer_port))
                    print(f"Connected to {self._peer_host}:{self._peer_port}")
                    break
                except ConnectionRefusedError:
                    retry+=1

            if retry >= self._retries:
                raise ConnectionAbortedError
        except TimeoutError:
            print(f"Connection timed out.")
        except ConnectionAbortedError:
            print(f"Peer server's not running. Terminating process.")
            raise ConnectionAbortedError

    def __send_message(self, msg: str):
        """
        Compress and send a message to the peer server.

        Args:
            msg (str): The message to be sent to the server.

        Raises:
            ConnectionError: If the connection is not active.
            ValueError: If there is an issue with compressing the message.
        
        This method compresses the message using the Compression class before sending 
        it over the socket. If the connection is not active or the message cannot be 
        compressed, appropriate exceptions are raised.
        """
        try:
            if not self._conn.state:
                raise ConnectionError
            compressed_msg: bytearray = self._compressor.payload_compression(msg)
            self._socket.sendall(compressed_msg)
        except ConnectionError:
            raise ConnectionError
        except ValueError as e:
            print(str(e))

    def handler(self):
        """
        Handle user input and send messages to the peer server.

        This method continuously reads user input and sends messages to the peer server. 
        The user can type 'exit' to terminate the communication and close the connection.
        If the connection is lost, the loop will break, and the client will terminate.
        """
        while True:
            message = input("")
            try:
                if message.lower() == 'exit':
                    print("Exiting chat...")
                    self.__send_message('exit')  # Send exit message to peer
                    self._conn.update_state()
                    break
                self.__send_message(message)
            except ConnectionError:
                break

    def close(self):
        """
        Close the client socket and terminate the connection.

        This method attempts to gracefully shut down the client socket. If there is no 
        active connection, it catches the socket error and closes the socket.
        """
        if self._socket is not None:
            try:
                self._socket.shutdown(SHUT_RDWR)
            except sockerror as e:
                # This error is due to lack of connection, so 
                # `shutdown()` cannot be called without one.
                if e.winerror != 10057:
                    print(f"Client Error {e}")
            self._socket.close()
            self._socket = None
