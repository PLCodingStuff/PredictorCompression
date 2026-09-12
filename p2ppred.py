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
    """
    p2ppred = build_parser()
    args = p2ppred.parse_args()

    if not hasattr(args, 'func'):
        p2ppred.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
