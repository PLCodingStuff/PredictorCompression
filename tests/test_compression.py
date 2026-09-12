import pytest
from src.business.compression.compression import Compression


def test_compression():
    compressor: Compression = Compression()

    test_message: str = "Hello World"
    test_byte_msg: bytearray = bytearray(b"\x00\x0aHelloWorld\x04\x00")

    compressed_msg: bytearray = compressor.payload_compression(test_message)

    assert compressed_msg == test_byte_msg


@pytest.mark.parametrize("short_msg,expected", [("Hi", "Hi"), ("A", "A")])
def test_less_than_k(short_msg, expected):
    compressor: Compression = Compression()

    test_byte_message: bytearray = bytearray(expected, encoding="ASCII")

    compressed_msg: bytearray = compressor.payload_compression(short_msg)

    assert compressed_msg == test_byte_message


def test_empty_str():
    compressor: Compression = Compression()

    test_msg: str = ""

    with pytest.raises(ValueError, match="Empty string passed to compressor"):
        compressor.payload_compression(test_msg)


def test_guess_table_persists_across_messages():
    compressor: Compression = Compression()

    test_message: str = "Hello World"

    first_pass: bytearray = compressor.payload_compression(test_message)
    second_pass: bytearray = compressor.payload_compression(test_message)

    assert len(second_pass) <= len(first_pass)
    assert second_pass != first_pass
