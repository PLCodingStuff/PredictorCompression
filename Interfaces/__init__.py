"""
This module provides the public interface for the observer pattern components.

It imports and exposes the following classes:
- Observer: An abstract base class for implementing the observer in the observer pattern.
- Observable: An abstract base class for implementing the observable in the observer pattern.

This module sets up the public API for the observer pattern related functionalities.

Attributes:
    __all__ (list): A list of public objects of this module. These are the names that will be imported
                    when `from module import *` is used.
"""
from .observer import Observer, Observable

__all__ = ["Observer", "Observable"]
