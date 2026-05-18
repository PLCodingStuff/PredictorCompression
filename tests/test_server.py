import pytest
from src.network.server import ServerConfig


def test_server_config():
    host: str = "127.0.0.1"
    port: int = 6000

    conf = ServerConfig(host, port)

    assert conf.host == host
    assert conf.port == port
    assert conf.timeout == 5.0
    assert conf.retries == 3
    assert conf.buffer_size == 1024


def test_server_config_host_error():
    host: str = "127.0.0."
    port: int = 6000

    with pytest.raises(ValueError, match="Invalid host name"):
        ServerConfig(host, port)


def test_server_config_port_error():
    host: str = "127.0.0.1"
    port: int = 0

    with pytest.raises(ValueError, match="Port value out of range"):
        ServerConfig(host, port)


def test_server_config_timeout_error():
    host: str = "127.0.0.1"
    port: int = 6000

    with pytest.raises(ValueError, match="Timeout value out of range"):
        ServerConfig(host, port, timeout=-1.0)


def test_server_config_retries_error():
    host: str = "127.0.0.1"
    port: int = 6000

    with pytest.raises(ValueError, match="Retries value out of range"):
        ServerConfig(host, port, retries=-1)


def test_server_config_buffer_size_error():
    host: str = "127.0.0.1"
    port: int = 6000

    with pytest.raises(ValueError, match="Invalid Buffer Size"):
        ServerConfig(host, port, buffer_size=0)
