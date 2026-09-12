import pytest
from src.business.compression.compression import Compression
from src.business.compression.decompression import Decompression


def test_decompression():
    decompressor: Decompression = Decompression()

    test_msg: str = "Hello World"

    byte_msg: bytearray = bytearray(b"\x00\x0aHelloWorld\x04\x00")

    text_message: str = decompressor.payload_decompression(byte_msg)

    assert text_message == test_msg


@pytest.mark.parametrize("short_msg,expected", [(b"Hi", "Hi"), (b"A", "A")])
def test_less_than_k(short_msg, expected):
    decompressor: Decompression = Decompression()

    byte_msg: bytearray = bytearray(short_msg)

    text_msg: str = decompressor.payload_decompression(byte_msg)

    assert text_msg == expected


def test_empty():
    decompressor: Decompression = Decompression()

    with pytest.raises(ValueError, match="Empty byte array passed to decompressor"):
        empty_bytearray: bytearray = bytearray()
        decompressor.payload_decompression(empty_bytearray)


def test_guess_table_persists_across_messages():
    compressor: Compression = Compression()
    decompressor: Decompression = Decompression()

    test_message: str = "Hello World"

    first_pass: bytearray = compressor.payload_compression(test_message)
    second_pass: bytearray = compressor.payload_compression(test_message)

    assert len(second_pass) < len(first_pass)
    assert decompressor.payload_decompression(first_pass) == test_message
    assert decompressor.payload_decompression(second_pass) == test_message
