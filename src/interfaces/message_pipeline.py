from typing import Protocol

class IMessagePipeline(Protocol):
    def process(data: bytearray) -> bytearray: ...