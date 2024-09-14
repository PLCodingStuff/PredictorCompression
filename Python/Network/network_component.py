from abc import abstractmethod
from socket import socket, AF_INET, SOCK_STREAM

from Interfaces import Observer
from .connection import Connection

class NetworkComponent(Observer):
    def __init__(self, host: str, port: int, conn: Connection):
        self._host: str = host
        self._port: int = port
        self._socket: socket = socket(AF_INET, SOCK_STREAM)
        self._conn = conn

    def update(self, data: Connection):
        if (not data._state):
            self.close()

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def handler(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

