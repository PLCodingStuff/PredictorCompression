import pytest

from src.network_components.framing import MessageType, send_frame, recv_frame
from src.network_components.handshake import perform_handshake
from src.errors.protocol_errors import HandshakeError

import socket
import threading


class _SocketPeer:
    """Minimal send_frame/recv_frame adapter around a raw socket, for exercising
    perform_handshake() directly without a full ClientSocket/PeerClientSocketManager."""

    def __init__(self, sock: socket.socket):
        self._sock = sock

    def send_frame(self, msg_type: MessageType, payload: bytes = b"") -> None:
        send_frame(self._sock, msg_type, payload)

    def recv_frame(self):
        return recv_frame(self._sock)


class TestPerformHandshake:
    def test_successful_handshake(self):
        a, b = socket.socketpair()
        errors: list = []

        def run_other_side():
            try:
                perform_handshake(_SocketPeer(b))
            except HandshakeError as e:
                errors.append(e)

        t = threading.Thread(target=run_other_side)
        t.start()

        try:
            perform_handshake(_SocketPeer(a))
            t.join(timeout=5)
        finally:
            a.close()
            b.close()

        assert not errors

    def test_garbage_instead_of_hello(self):
        a, b = socket.socketpair()
        try:
            a.sendall(b"not a valid frame at all")
            a.close()

            with pytest.raises(HandshakeError):
                perform_handshake(_SocketPeer(b))
        finally:
            b.close()

    def test_peer_closes_after_local_hello(self):
        a, b = socket.socketpair()

        def close_after_hello():
            recv_frame(b)  # consume the HELLO sent by the local side
            b.close()

        t = threading.Thread(target=close_after_hello)
        t.start()

        try:
            with pytest.raises(HandshakeError):
                perform_handshake(_SocketPeer(a))
            t.join(timeout=5)
        finally:
            a.close()
