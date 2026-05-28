from src.business.compression.decompression import Decompression


class ReceiveMessageProcessor:
    def __init__(self):
        self._decompression: Decompression = Decompression()

    def parse_received(self, data: bytearray) -> str:
        return self._decompression.payload_decompression(data)
