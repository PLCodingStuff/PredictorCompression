from json import load
from src.network.server import ServerSocketConfig
from src.network.client import ClientSocketConfig


def read_config_json(filename: str) -> dict:
    if not filename.endswith(".json"):
        raise FileNotFoundError("Invalid suffix.")

    with open(filename) as js:
        config = load(js)

    if "port" not in config:
        raise ValueError("Port is not provided in configuration file.")

    if "timeout" not in config:
        config["timeout"] = 5.0

    if "retries" not in config:
        config["retries"] = 3

    if "address" not in config:
        config["address"] = "127.0.0.1"

    return config


def create_server_config(filename: str) -> ServerSocketConfig:
    config: dict = read_config_json(filename)

    return ServerSocketConfig(
        config["address"], config["port"], config["timeout"], config["retries"]
    )


def create_client_config(filename: str) -> ClientSocketConfig:
    config: dict = read_config_json(filename)

    return ClientSocketConfig(
        config["address"], config["port"], config["retries"], config["timeout"]
    )
