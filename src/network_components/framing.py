from src.errors.server_errors import ConnectionLostError, CONNECTION_LOST_ERRORS

from enum import IntEnum
from socket import socket
import struct


class MessageType(IntEnum):
    HELLO = 1
    ACK = 2
    MSG = 3
    QUIT = 4


HEADER_FORMAT = ">I"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


def pack_frame(msg_type: MessageType, payload: bytes | bytearray = b"") -> bytearray:
    body: bytearray = bytearray([msg_type]) + bytearray(payload)
    return bytearray(struct.pack(HEADER_FORMAT, len(body))) + body


def _recv_exact(sock: socket, n: int) -> bytearray:
    buf: bytearray = bytearray()
    while len(buf) < n:
        try:
            chunk: bytes = sock.recv(n - len(buf))
        except OSError as e:
            if e.errno in CONNECTION_LOST_ERRORS:
                raise ConnectionLostError(str(e))
            raise

        if not chunk:
            raise ConnectionLostError("Peer disconnected gracefully.")

        buf.extend(chunk)

    return buf


def send_frame(sock: socket, msg_type: MessageType, payload: bytes | bytearray = b"") -> None:
    try:
        sock.sendall(pack_frame(msg_type, payload))
    except OSError as e:
        if e.errno in CONNECTION_LOST_ERRORS:
            raise ConnectionLostError(str(e))
        raise


def recv_frame(sock: socket) -> tuple[MessageType, bytearray]:
    header: bytearray = _recv_exact(sock, HEADER_SIZE)
    (length,) = struct.unpack(HEADER_FORMAT, header)

    body: bytearray = _recv_exact(sock, length)
    msg_type: MessageType = MessageType(body[0])
    payload: bytearray = body[1:]

    return msg_type, payload
