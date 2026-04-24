import pytest
from PayloadCompression import Compression

def test_compression():
    # TODO: Fix test
    compressor: Compression = Compression()

    test_message: str = "Hello World"
    test_byte_msg: bytearray = bytearray()
    
    compressed_msg: bytearray = compressor.payload_compression(test_message)

    assert test_byte_msg == compressed_msg

def test_empty_str():
    compressor: Compression = Compression()

    test_msg: str = ""

    with pytest.raises(ValueError, match="Empty string passed to compressor"):
        compressor.payload_compression(test_msg)
