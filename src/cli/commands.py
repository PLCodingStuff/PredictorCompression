import sys
from argparse import ArgumentParser
from src.network.node import Node
from src.config.config import (
    ClientSocketConfig,
    ServerSocketConfig,
    create_client_config,
    create_server_config,
)


def cmd_validate(args):
    from src.config.config import read_config_json

    try:
        config: dict = read_config_json(args.file)
        print("✓ Config is valid")
        print(f"  Node   :  {config['address']}:{config['port']}")
        print(f"  Timeout:  {config['timeout']}")
        print(f"  Retries:  {config['retries']}")
    except (ValueError, FileNotFoundError) as e:
        print(f"✗ Config is invalid: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_compress(args):
    """Compress text"""
    from src.business.compression.compression import Compression

    try:
        comp = Compression()
        compressed = comp.payload_compression(args.text)

        if args.output:
            with open(args.output, "wb") as f:
                f.write(compressed)
            print(f"✓ Compressed and saved to {args.output}")
        else:
            print(compressed.hex())

    except Exception as e:
        print(f"Compression failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_decompress(args):
    """Decompress data (hex string)"""
    from src.business.compression.decompression import Decompression

    try:
        decompressed_bytes = bytes.fromhex(args.data)
        decomp = Decompression()
        result = decomp.payload_decompression(decompressed_bytes)
        print(result)
    except Exception as e:
        print(f"Decompression failed: {e}", file=sys.stderr)
        sys.exit(1)


def add_validate_subparser(subparsers):
    validate = subparsers.add_parser(
        name="validate", help="Validate configuration file"
    )

    validate.add_argument("file", type=str, help="Path to configuration JSON file")

    validate.set_defaults(func=cmd_validate)


def add_compress_subparser(subparsers):
    compress_parser = subparsers.add_parser("compress", help="Compress text")
    compress_parser.add_argument("text", type=str, help="Text to compress")
    compress_parser.add_argument(
        "-o", "--output", type=str, help="Save compressed data to file"
    )
    compress_parser.set_defaults(func=cmd_compress)


def add_decompress_subparser(subparsers):
    decompress_parser = subparsers.add_parser(
        "decompress", help="Decompress data (hex string)"
    )
    decompress_parser.add_argument(
        "data", type=str, help="Hex-encoded data to decompress"
    )
    decompress_parser.set_defaults(func=cmd_decompress)


def cmd_start(args):
    """Start a chat node"""
    try:
        if args.verbose:
            print(f"Loading server config from: {args.server_json}")
            print(f"Loading client config from: {args.client_json}")

        server_conf: ServerSocketConfig = create_server_config(args.server_json)
        client_conf: ClientSocketConfig = create_client_config(args.client_json)

        if args.verbose:
            print(f"Node: {server_conf.host}:{server_conf.port}")
            print(f"Peer: {client_conf.peer_host}:{client_conf.peer_port}")

        node = Node(server_conf, client_conf)
        print("Starting chat...")
        node.start_chat()

    except ValueError as e:
        print(f"Error while loading: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error while loading: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        print("Terminating Process")


def add_start_subparser(subarsers):
    start_parser = subarsers.add_parser(
        "start", help="Start a node"
    )

    start_parser.add_argument("server_json", help="The server configuration JSON")

    start_parser.add_argument("client_json", help="The client configuration JSON")

    start_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    start_parser.set_defaults(func=cmd_start)


def build_parser() -> ArgumentParser:
    p2ppred: ArgumentParser = ArgumentParser(
        prog="p2ppred",
        usage="%(prog)s [COMMAND] [OPTIONS]",
        description="p2ppred creates a p2p server between 2 peers, using the Predictor Compression algorithm for message compression.",
    )

    p2ppred.add_argument(
        "--version",
        "-v",
        action="version",
        version="%(prog)s 1.0.0",
        help="Print current version of %(prog)s.",
    )

    p2ppred_subparsers = p2ppred.add_subparsers(
        title="Subcommands",
        prog="p2ppred",
    )

    add_validate_subparser(p2ppred_subparsers)
    add_compress_subparser(p2ppred_subparsers)
    add_decompress_subparser(p2ppred_subparsers)
    add_start_subparser(p2ppred_subparsers)

    return p2ppred
