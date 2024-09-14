import threading
from json import load
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
        try:
            self._client.start()
        except ConnectionAbortedError as e:
            self._connection.update_state()
            exit(1)
            

    def __disconnect(self):
        self._connection.update_state()

    def start_chat(self) -> None:
        self.__connect()
        self._client.handler()
        self.__disconnect()

def get_addresses(filename: str)->tuple[str, int, str, int]:
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