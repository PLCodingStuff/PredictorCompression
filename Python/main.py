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
        self._connection.update_state()
        server_thread.start()
        self._client.start()

    def __disconnect(self):
        self._connection.update_state()

    def start_chat(self) -> None:
        self.__connect()
        self._client.handler()
        self.__disconnect()

def get_addresses()->tuple[str, int, str, int]:
    address: str = "127.0.0.1"
    peer_address: str = "127.0.0.1"

    choice = input("Would you like to use the default localhost address for the host (y/n)?")
    if choice.lower() == "n":
        address = input("Enter the address you'd like to use")

    port:int = int(input("Enter the port for the host you would like to use: "))
    
    choice = input("Does the peer also use the default localhost address(y/n)?")
    if choice.lower() == "n":
        peer_address = input("Enter the peer's address ")

    peer_port:int = int(input("Enter the port of the peer: "))
    print()

    return address, port, peer_address, peer_port

def main():
    host, port, peer_host, peer_port = get_addresses()

    node = Node(host, port, peer_host, peer_port)
    node.start_chat()

if __name__ == "__main__":
    main()