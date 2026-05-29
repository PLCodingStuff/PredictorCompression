from json import load
from sys import argv

from src.network.node import Node



def get_addresses(filename: str) -> tuple[str, int, str, int]:
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

    if not filename.endswith(".json"):
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

    This function parses the command-line arguments, extracts the address configuration from the provided JSON file, and starts the Node for the chat session.

    If an error occurs during loading of the JSON file or if the provided arguments are invalid, an error message is printed and the program terminates.
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
    ...

        
