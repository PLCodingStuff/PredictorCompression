# from sys import argv

# from src.network.node import Node
# from src.network.server import ServerSocketConfig
# from src.network.client import ClientSocketConfig
# from src.config.config import create_client_config, create_server_config
from src.cli.commands import build_parser

import sys

def main():
    """
    Main entry point for the chat node application.

    This function parses the command-line arguments, extracts the address configuration from the provided JSON file, and starts the Node for the chat session.

    If an error occurs during loading of the JSON file or if the provided arguments are invalid, an error message is printed and the program terminates.
    """
    # try:
    #     if len(argv) != 2:
    #         raise ValueError("Invalid number of command line arguments")

    #     json_file = argv[1]
    #     server_conf: ServerSocketConfig = create_server_config(json_file)
    #     client_conf: ClientSocketConfig = create_client_config(json_file)
    # except ValueError as e:
    #     print(f"Error while loading: {str(e)}")
    #     print("Terminating Process")
    #     return
    # except FileNotFoundError as e:
    #     print(f"Error while loading: {str(e)}")
    #     print("Terminating Process")
    #     return

    # node = Node(server_conf, client_conf)
    # node.start_chat()
    p2ppred = build_parser()
    args = p2ppred.parse_args()

    if not hasattr(args, 'func'):
        p2ppred.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
