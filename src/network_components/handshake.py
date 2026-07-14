from src.network_components.framing import MessageType
from src.errors.protocol_errors import HandshakeError

from typing import Protocol


class FramedPeer(Protocol):
    def send_frame(self, msg_type: MessageType, payload: bytes = b"") -> None: ...
    def recv_frame(self) -> tuple[MessageType, bytearray]: ...


def perform_handshake(peer: FramedPeer) -> None:
    try:
        peer.send_frame(MessageType.HELLO)
        msg_type, _ = peer.recv_frame()
        if msg_type != MessageType.HELLO:
            raise HandshakeError(f"Expected HELLO, got {msg_type.name}")

        peer.send_frame(MessageType.ACK)
        msg_type, _ = peer.recv_frame()
        if msg_type != MessageType.ACK:
            raise HandshakeError(f"Expected ACK, got {msg_type.name}")
    except HandshakeError:
        raise
    except (OSError, ValueError) as e:
        raise HandshakeError(str(e)) from e
