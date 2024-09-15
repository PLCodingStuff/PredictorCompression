from abc import abstractmethod
from socket import socket, AF_INET, SOCK_STREAM

from Interfaces import Observer
from .connection import Connection

class NetworkComponent(Observer):
    """
    Abstract base class representing a network component in the system.
    
    This class implements the Observer interface to monitor the state of 
    a Connection object and take action when the connection state changes.
    It manages socket communication and provides abstract methods to start, 
    handle, and close the network component.

    Attributes:
        _host (str): The hostname or IP address to bind the component.
        _port (int): The port number to bind the component.
        _socket (socket): The socket object used for network communication.
        _conn (Connection): The connection object this component observes.
    
    Methods:
        update(data: Connection) -> None: Responds to changes in the connection's state.
        start() -> None: Abstract method to start the network component.
        handler() -> None: Abstract method to define how to handle network communication.
        close() -> None: Abstract method to close the network component.
    """
    def __init__(self, host: str, port: int, conn: Connection):
        """
        Initialize the NetworkComponent with the given host, port, and connection.

        Args:
            host (str): The hostname or IP address to bind the socket.
            port (int): The port number to bind the socket.
            conn (Connection): The connection object this component observes.
        
        This constructor creates a socket object using the specified address 
        family and socket type and stores the connection object for monitoring.
        """
        self._host: str = host
        self._port: int = port
        self._socket: socket = socket(AF_INET, SOCK_STREAM)
        self._conn = conn

    def update(self, data: Connection):
        """
        Respond to state changes in the observed Connection object.

        Args:
            data (Connection): The connection instance whose state has changed.
        
        If the connection's state becomes False (i.e., disconnected), 
        this method triggers the `close` method to shut down the network component.
        """
        if (not data._state):
            self.close()

    @abstractmethod
    def start(self) -> None:
        """
        Start the network component.
        
        This method must be implemented by subclasses to define how the network 
        component should be started, such as binding a socket or listening for connections.
        """
        pass

    @abstractmethod
    def handler(self) -> None:
        """
        Handle network communication.

        This method must be implemented by subclasses to define the behavior for handling 
        incoming or outgoing communication, such as reading from or writing to the socket.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close the network component.
        
        This method must be implemented by subclasses to define how the network component 
        should be shut down, such as closing the socket and releasing resources.
        """
        pass

