import pytest
from PayloadCompression import Compression

def test_compression():
    compressor: Compression = Compression()

    test_message: str = "Hello World"
    test_byte_msg: bytearray = bytearray(b"\x0AHelloWorld\x04\x00")
    
    compressed_msg: bytearray = compressor.payload_compression(test_message)

    assert compressed_msg == test_byte_msg

def test_empty_str():
    compressor: Compression = Compression()

    test_msg: str = ""

    with pytest.raises(ValueError, match="Empty string passed to compressor"):
        compressor.payload_compression(test_msg)

def test_less_than_k():
    compressor: Compression = Compression()

    test_msg: str = "Hi"
    test_byte_message: bytearray = bytearray("Hi", encoding="ASCII")

    compressed_msg: bytearray = compressor.payload_compression(test_msg)

    assert compressed_msg == test_byte_message