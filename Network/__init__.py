"""
This module provides the public interface for the network components used in the chat application.

It imports and exposes the following classes:
- Client: A class representing the client in the chat application.
- Server: A class representing the server in the chat application.
- Connection: A class used for managing the state of the connection between client and server.
- NetworkComponent: An abstract base class for network components in the chat application.

This module sets up the public API for network-related functionalities.

Attributes:
    __all__ (list): A list of public objects of this module. These are the names that will be imported
                    when `from module import *` is used.
"""

from .client import Client
from .server import Server
from .connection import Connection
from .network_component import NetworkComponent

__all__ = ['Client', 'Server', 'Connection', 'NetworkComponent']
