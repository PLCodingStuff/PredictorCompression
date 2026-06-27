from json import load

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
        config = load(js)

        if "address" in config:
            address = config["address"]
        if "port" not in config:
            raise ValueError("Port is not provided in JSON file.")
        if "peer_address" in config:
            peer_address = config["peer_address"]
        if "peer_port" not in config:
            raise ValueError("Peer port is not provided in JSON file.")

        return (
            address,
            config["port"],
            peer_address,
            config["peer_port"],
        )