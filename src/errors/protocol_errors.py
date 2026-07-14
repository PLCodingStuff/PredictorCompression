class HandshakeError(OSError):
    """Raised when the HELLO/ACK handshake fails: bad type byte, malformed frame,
    timeout, or unexpected disconnection during the handshake exchange."""

    ...
