import pytest

from src.network_components.framing import (
    MessageType,
    pack_frame,
    send_frame,
    recv_frame,
    HEADER_SIZE,
)
from src.errors.server_errors import ConnectionLostError

import struct
import socket
import threading


class TestPackFrame:
    @pytest.mark.parametrize(
        "msg_type", [MessageType.HELLO, MessageType.ACK, MessageType.QUIT]
    )
    def test_pack_frame_control(self, msg_type):
        frame = pack_frame(msg_type)

        assert frame == bytearray(struct.pack(">I", 1)) + bytearray([msg_type])

    def test_pack_frame_msg(self):
        payload = bytearray(b"some compressed payload bytes")
        frame = pack_frame(MessageType.MSG, payload)

        length = struct.unpack(">I", frame[:HEADER_SIZE])[0]

        assert length == 1 + len(payload)
        assert frame[HEADER_SIZE] == MessageType.MSG
        assert frame[HEADER_SIZE + 1 :] == payload


class TestSendRecvFrame:
    def test_round_trip_large_payload(self):
        a, b = socket.socketpair()
        payload = bytearray(b"x" * 5000)  # exceeds the old 1024-byte recv buffer
        result: dict = {}

        def receiver():
            result["frame"] = recv_frame(b)

        t = threading.Thread(target=receiver)
        t.start()

        try:
            send_frame(a, MessageType.MSG, payload)
            t.join(timeout=5)
        finally:
            a.close()
            b.close()

        assert result["frame"] == (MessageType.MSG, payload)

    def test_recv_frame_closed_mid_frame(self):
        a, b = socket.socketpair()
        try:
            a.sendall(struct.pack(">I", 10))  # header promises 10 bytes...
            a.close()  # ...but the connection dies before sending them

            with pytest.raises(ConnectionLostError):
                recv_frame(b)
        finally:
            b.close()

    def test_recv_frame_invalid_type(self):
        a, b = socket.socketpair()
        try:
            a.sendall(struct.pack(">I", 1) + bytes([0]))  # 0 is not a valid MessageType

            with pytest.raises(ValueError):
                recv_frame(b)
        finally:
            a.close()
            b.close()
