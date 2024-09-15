"""
This module provides the public interface for compression and decompression functionalities.

It imports and exposes the following classes:
- Compression: A class responsible for compressing data.
- Decompression: A class responsible for decompressing data.

This module sets up the public API for data compression and decompression.

Attributes:
    __all__ (list): A list of public objects of this module. These are the names that will be imported
                    when `from module import *` is used.
"""

from .Compression import Compression
from .Decompression import Decompression

__all__ = ['Compression', 'Decompression']
