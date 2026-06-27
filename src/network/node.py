from src.network.server import (
    ServerManager,
    ServerSocket,
    ServerSocketConfig,
    PeerClientSocketManager,
)
from src.network.client import ClientManager, ClientSocket, ClientSocketConfig
from src.network_components.connection import Connection
from src.business.messages.receive_message import ReceiveMessageProcessor
from src.business.messages.send_message import SendMessageProcessor
from src.business.messages.message_source import CLIMessageSource
from src.business.messages.message_output import CLIMessageOutput

import threading
from socket import AF_INET, SOCK_STREAM


class Node:
    """
    A Node class representing a chat system that connects a client and server over a network. The Node creates both a client and server instance, shares a common connection state, and manages the chat session.

    Attributes:
        _connection (Connection): A shared connection object for managing the state of the connection.
        _server (Server): The server instance to listen for incoming connections.
        _client (Client): The client instance to connect to a peer node.

    Methods:
        __connect() -> None: Starts the server in a new thread and attempts to connect the client to a peer.
        __disconnect() -> None: Disconnects the node by updating the connection state.
        start_chat() -> None: Initiates the chat by connecting, handling client interaction, and then disconnecting.
    """

    def __init__(
        self, node_host: str, node_port: int, peer_host: str, peer_port: int
    ) -> None:
        """
        Initialize the Node with the addresses and ports for both the server and client.

        Args:
            node_host (str): The host address of the server node.
            node_port (int): The port number for the server node.
            peer_host (str): The peer client's host address to connect to.
            peer_port (int): The peer client's port number.

        The connection object is shared between both the client and the server, and both
        are attached as observers to the connection state.
        """
        self._connection: Connection = Connection()
        self._stop_event: threading.Event = threading.Event()

        self._server: ServerManager = self.__init_server(node_host, node_port)

        self._client: ClientManager = self.__init_client(peer_host, peer_port)

        self._connection.attach(self._server)
        self._connection.attach(self._client)

    def __init_server(self, host: str, port: int) -> ServerManager:
        server_conf: ServerSocketConfig = ServerSocketConfig(host, port)
        server_sock: ServerSocket = ServerSocket(server_conf, family=AF_INET, type=SOCK_STREAM)

        msg_proc: ReceiveMessageProcessor = ReceiveMessageProcessor()
        msg_out: CLIMessageOutput = CLIMessageOutput()

        peer_client: PeerClientSocketManager = PeerClientSocketManager()

        return ServerManager(
            server_sock,
            peer_client,
            self._connection,
            self._stop_event,
            msg_proc,
            msg_out,
        )

    def __init_client(self, host, port) -> ClientManager:
        client_conf: ClientSocketConfig = ClientSocketConfig(host, port)
        client_sock: ClientSocket = ClientSocket(client_conf)

        msg_proc: SendMessageProcessor = SendMessageProcessor()
        msg_source: CLIMessageSource = CLIMessageSource()

        return ClientManager(
            client_sock, self._connection, self._stop_event, msg_proc, msg_source
        )

    def start_chat(self) -> None:
        """
        Initiate the chat session by connecting the client, handling client interaction, and then disconnecting.

        This method calls the connection method to start the client-server interaction, hands off the control to the client's handler for message exchange, and then ensures the disconnection at the end of the session.
        """
        server_thread = threading.Thread(target=self._server.run)
        server_thread.start()

        self._client.run()

        server_thread.join()
