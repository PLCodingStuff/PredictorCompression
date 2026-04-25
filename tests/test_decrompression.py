import pytest
from PayloadCompression import Decompression


def test_decompression():
    decompressor: Decompression = Decompression()

    test_msg: str = "Hello World"

    byte_msg: bytearray = bytearray(b"\x0aHelloWorld\x04\x00")

    text_message: str = decompressor.payload_decompression(byte_msg)

    assert text_message == test_msg

def test_less_than_k():
    decompressor: Decompression = Decompression()

    test_msg = "Hi"
    byte_msg: bytearray = bytearray(b"Hi")

    text_msg: str = decompressor.payload_decompression(byte_msg)

    assert text_msg == test_msg

def test_empty():
    decompressor: Decompression = Decompression()

    with pytest.raises(ValueError, match="Empty byte array passed to decompressor"):
        empty_bytearray: bytearray = bytearray()
        decompressor.payload_decompression(empty_bytearray)
