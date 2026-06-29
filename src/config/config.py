from json import load


def read_config_json(filename: str) -> dict:
    if not filename.endswith(".json"):
        raise FileNotFoundError("Invalid suffix.")

    with open(filename) as js:
        config = load(js)

    if "port" not in config:
        raise ValueError("Port is not provided in configuration file.")

    if "timeout" not in config:
        config["timeout"] = 5.0

    if "retires" not in config:
        config["retries"] = 3.0

    if "address" not in config:
        config["address"] = "127.0.0.1"

    return config
