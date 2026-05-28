from typing import Protocol

class IMessageHandler(Protocol):
    def process(data: bytearray) -> bytearray: ...