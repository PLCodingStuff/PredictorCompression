import pytest
from src.network.server import ServerConfig
# from src.network_components.connection import Connection


def test_server_config_port():
    host: str = "127.0.0.1"
    port: int = 0

    with pytest.raises(ValueError, match="Port value out of range"):
        ServerConfig(host, port)
