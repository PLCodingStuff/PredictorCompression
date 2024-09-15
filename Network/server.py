from socket import socket, SOL_SOCKET, SO_REUSEADDR, error as sockerror, SHUT_RDWR
from .network_component import NetworkComponent, Connection
from PayloadCompression import Decompression

class Server(NetworkComponent):
    """
    Server class that listens for incoming client connections, receives compressed messages,
    decompresses them, and manages communication. The server uses a shared connection object
    to maintain the state of the connection.

    Attributes:
        conn (socket): The socket used for communication with the connected client.
        _decompressor (Decompression): Instance of the Decompression class for decompressing messages.

    Methods:
        start() -> None: Starts the server, listens for incoming connections, and handles communication.
        __decompress_data(data: bytearray) -> str: Decompresses incoming byte data into a string.
        handler() -> None: Manages message reception and decompression in a loop.
        close() -> None: Closes the server connection and terminates the socket.
    """
    def __init__(self, host: str, port: int, conn: Connection) -> None:
        """
        Initialize the Server object with a host address, port number, and connection object.

        Args:
            host (str): The host address on which the server listens for connections.
            port (int): The port number on which the server listens for connections.
            conn (Connection): The shared connection object for maintaining the connection state.

        The server socket is set up to reuse the same address to avoid binding issues during restart.
        """
        self.conn: socket = None
        self._decompressor: Decompression = Decompression()
        super().__init__(host, port, conn)
        self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    def start(self) -> None:
        """
        Start the server, bind to the specified address, and listen for incoming connections.

        This method binds the server socket to a port, listens for incoming client connections, 
        and accepts the connection. Once a client connects, it calls the `handler()` method 
        to process incoming messages.

        Raises:
            sockerror: If there is an error during binding or connection.
        """
        try:
            self._socket.bind(('0.0.0.0', self._port))
            self._socket.listen(1)
            print(f"Server listening on {self._host}:{self._port}")

            self.conn, addr = self._socket.accept()
            print(f"{str(addr)} connected")
            self.handler()
        except sockerror as e:
            if e.winerror != 10038:
                print(f"Error in server: {e}")
            self._conn.update_state()

    def __decompress_data(self, data: bytearray) -> str:
        """
        Decompress the incoming byte data into a readable string.

        Args:
            data (bytearray): The compressed data received from the client.

        Returns:
            str: The decompressed message or None if the peer has disconnected.

        This method decompresses the byte data using the Decompression class. If the data 
        is empty (indicating the client has disconnected), it updates the connection state 
        and returns None.
        """
        if not data:
            self._conn.update_state()
            print("Peer has disconnected.")
            return None

        decompressed_message: str = self._decompressor.payload_decompression(data)
        return decompressed_message

    def handler(self) -> None:
        """
        Handle incoming messages from the client, decompress them, and display the messages.

        This method continuously receives compressed data from the client, decompresses the 
        data, and displays the messages. If the client sends an 'exit' message, the connection 
        is terminated, and the handler exits.
        """
        try:
            while True:
                compressed_data: bytearray = self.conn.recv(1024)

                message:str = self.__decompress_data(compressed_data)
                print(f"Received message: {message}")

                if message == 'exit':
                    print("Peer requested disconnection.")
                    self._conn.update_state()
                    print("Press Enter to exit")
                    break
        except sockerror as e:
            # This error occurs when `close()` is called while blocked in `recv()`
            if e.winerror != 10038:
                print(f"Error handling client: {e}")

    def close(self) -> None:
        """
        Close the server connection and terminate the socket.

        This method attempts to gracefully shut down the server connection and close 
        the client and server sockets. If there is no active connection, it handles 
        the associated socket error gracefully.
        """
        if self.conn:
            try:
                self.conn.shutdown(SHUT_RDWR)
            except sockerror as e:
                # This error is due to lack of connection, so 
                # `shutdown()` cannot be called without one.
                if e.winerror != 10038:
                    print(f"Error Closing Server Connection socket: {e}")
            self.conn.close()
            self.conn = None
        if self._socket:
            self._socket.close()
            self._socket = None
