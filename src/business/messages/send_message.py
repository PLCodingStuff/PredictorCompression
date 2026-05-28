from src.business.compression.compression import Compression


class SendMessageProcessor:
    def __init__(self):
        self._compression: Compression = Compression()

    def prepare_to_send(self, msg: str) -> bytearray:
        return self._compression.payload_compression(msg)
