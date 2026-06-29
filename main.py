from sys import argv

from src.network.node import Node
from src.config.config import read_config_json


def main():
    """
    Main entry point for the chat node application.

    This function parses the command-line arguments, extracts the address configuration from the provided JSON file, and starts the Node for the chat session.

    If an error occurs during loading of the JSON file or if the provided arguments are invalid, an error message is printed and the program terminates.
    """
    try:
        if len(argv) != 2:
            raise ValueError("Invalid number of command line arguments")

        json_file = argv[1]
        host, port, peer_host, peer_port = read_config_json(json_file)
    except ValueError as e:
        print(f"Error while loading: {str(e)}")
        print("Terminating Process")
        return
    except FileNotFoundError as e:
        print(f"Error while loading: {str(e)}")
        print("Terminating Process")
        return

    node = Node(host, port, peer_host, peer_port)
    node.start_chat()


if __name__ == "__main__":
    main()
