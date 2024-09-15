import threading
from json import load
from sys import argv
from Network import Client, Server, Connection

class Node:
    """
    A Node class representing a chat system that connects a client and server over a network.
    The Node creates both a client and server instance, shares a common connection state, 
    and manages the chat session.

    Attributes:
        _connection (Connection): A shared connection object for managing the state of the connection.
        _server (Server): The server instance to listen for incoming connections.
        _client (Client): The client instance to connect to a peer node.

    Methods:
        __connect() -> None: Starts the server in a new thread and attempts to connect the client to a peer.
        __disconnect() -> None: Disconnects the node by updating the connection state.
        start_chat() -> None: Initiates the chat by connecting, handling client interaction, and then disconnecting.
    """

    def __init__(self, my_host: str, my_port: int, peer_host: str, peer_port: int) -> None:
        """
        Initialize the Node with the addresses and ports for both the server and client.

        Args:
            my_host (str): The host address of the server node.
            my_port (int): The port number for the server node.
            peer_host (str): The peer client's host address to connect to.
            peer_port (int): The peer client's port number.

        The connection object is shared between both the client and the server, and both
        are attached as observers to the connection state.
        """
        self._connection: Connection = Connection()
        self._server: Server = Server(my_host, my_port, self._connection)
        self._client: Client = Client(peer_host,peer_port, self._connection)
        self._connection.attach(self._server)
        self._connection.attach(self._client)

    def __connect(self):
        """
        Start the server in a separate thread and attempt to connect the client to a peer.

        This method launches the server in a background thread and then starts the client to 
        connect to the specified peer. If the connection to the peer fails, it raises 
        a ConnectionAbortedError and updates the connection state to disconnected.
        """
        server_thread = threading.Thread(target=self._server.start)
        self._connection.update_state()
        server_thread.start()
        try:
            self._client.start()
        except ConnectionAbortedError as e:
            self._connection.update_state()
            exit(1)
            

    def __disconnect(self):
        """
        Disconnect the node by updating the connection state.

        This method updates the connection state to indicate that the client has disconnected
        from the chat session.
        """
        self._connection.update_state()

    def start_chat(self) -> None:
        """
        Initiate the chat session by connecting the client, handling client interaction, and then disconnecting.

        This method calls the connection method to start the client-server interaction, 
        hands off the control to the client's handler for message exchange, and then ensures 
        the disconnection at the end of the session.
        """
        self.__connect()
        self._client.handler()
        self.__disconnect()

def get_addresses(filename: str)->tuple[str, int, str, int]:
    """
    Parse the JSON file to extract server and peer addresses and ports.

    Args:
        filename (str): The name of the JSON file containing address configuration.

    Returns:
        tuple: A tuple containing the host address, port, peer address, and peer port.

    Raises:
        FileNotFoundError: If the file doesn't end with .json or the file is not found.
        ValueError: If port or peer_port is missing in the JSON file.
    """
    address: str = "127.0.0.1"
    peer_address: str = "127.0.0.1"

    if not filename.endswith('.json'):
        raise FileNotFoundError("Invalid suffix.")

    with open(filename) as js:
        addressess = load(js)
        if "address" in addressess:
            address = addressess["address"]
        if "peer_address" in addressess:
            peer_address = addressess["peer_address"]
        if "port" not in addressess:
            raise ValueError("Port is not provided in JSON file.")
        if "peer_port" not in addressess:
            raise ValueError("Peer port is not provided in JSON file.")
        
        port = addressess["port"]
        peer_port = addressess["peer_port"]

    return address, port, peer_address, peer_port

def main():
    """
    Main entry point for the chat node application.

    This function parses the command-line arguments, extracts the address configuration 
    from the provided JSON file, and starts the Node for the chat session.
    
    If an error occurs during loading of the JSON file or if the provided arguments 
    are invalid, an error message is printed and the program terminates.
    """
    try:
        if len(argv) != 2:
            raise ValueError("Invalid number of command line arguments")
        host, port, peer_host, peer_port = get_addresses(argv[1])

        node = Node(host, port, peer_host, peer_port)
        node.start_chat()
    except ValueError as e:
        print(f"Error while loading: {e}")
    except FileNotFoundError as e:
        print(f"Error while loading: {e}")
    print("Terminating Process")

if __name__ == "__main__":
    main()
