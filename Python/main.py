import threading
from sys import argv
from Network import Client, Server, Connection

class Node:
    def __init__(self, my_host: str, my_port: int, peer_host: str, peer_port: int) -> None:
        self._connection: Connection = Connection()
        self._server: Server = Server(my_host, my_port, self._connection)
        self._client: Client = Client(peer_host,peer_port, self._connection)
        self._connection.attach(self._server)
        self._connection.attach(self._client)

    def __connect(self):
        server_thread = threading.Thread(target=self._server.start)
        server_thread.start()
        self._client.start()
        self._connection.update_state()

    def __disconnect(self):
        self._connection.update_state()

    def start_chat(self) -> None:
        self.__connect()
        self._client.handler()
        self.__disconnect()


if __name__ == "__main__":
    # Example: Replace with actual IPs and ports
    my_host = "127.0.0.1"  # This peer's host
    my_port = int(argv[1])  # This peer's port

    peer_host = "127.0.0.1"  # Peer host (can be different IP)
    peer_port = int(argv[2])  # Peer port

    node = Node(my_host, my_port, peer_host, peer_port)
    node.start_chat()
