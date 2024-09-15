from bitarray import bitarray

class Decompression:
    """
    Class for decompressing a byte array payload that was compressed using a 
    fixed-length substring hashing approach. This class reconstructs the 
    original string from the compressed data.

    Attributes:
        k (int): The length of the substring used for hashing. Default is 2.
        ASCII (str): The encoding format used for decompressing small strings.
    
    Methods:
        payload_decompression(compressed_data: bytearray) -> str: Decompresses the input byte array.
    """
    k = 2
    ASCII="ASCII"

    @staticmethod
    def __hash_function(substring: str) -> int:
        """
        Hash a substring into a 16-bit integer using a simple hash function.

        Args:
            substring (str): A string of length 2 to be hashed.
        
        Returns:
            int: A 16-bit hash value of the substring.
        
        This function uses bitwise shifts and XOR to generate a hash from the 
        ASCII values of the first two characters in the substring.
        """
        hash_val: int = 5381
        hash_val = ((hash_val << 5) + hash_val) ^ ord(substring[0])
        hash_val = ((hash_val << 5) + hash_val) ^ ord(substring[1])

        return hash_val % 65536


    def __init_arrays(self, compressed_data: bytearray)->tuple[list[str], list[str], bitarray, list[str]]:
        """
        Initialize the leftovers, decompressed text, flag bits, and guess table.

        Args:
            compressed_data (bytearray): The compressed byte array.
        
        Returns:
            tuple: A tuple containing:
                   - leftovers: A list of characters not found in the guess table.
                   - decompressed_text: The partially decompressed text.
                   - flag_bits: A bitarray representing the flags used during compression.
                   - guess_table: A preallocated list for storing guessed characters.
        
        The leftovers are extracted from the first part of the compressed data, 
        and the bit array is derived from the remaining bytes.
        """
        leftovers_length: int = compressed_data[0]+1
        leftovers: list[str] = [chr(b) for b in compressed_data[1:leftovers_length]]

        get_length: int = lambda length: Decompression.k if length > Decompression.k else length
        decompressed_text: list[str] = [leftovers[i] for i in range(get_length(leftovers_length))]

        flag_bits = bitarray()
        flag_bits.frombytes(compressed_data[leftovers_length:])
        
        guess_table: list[str] = [' '] * 65536

        return leftovers, decompressed_text, flag_bits, guess_table


    def payload_decompression(self, compressed_data: bytearray)->str:
        """
        Decompress a byte array into the original string.

        Args:
            compressed_data (bytearray): The compressed byte array to be decompressed.
        
        Returns:
            str: The decompressed string.
        
        Raises:
            ValueError: If an empty byte array is provided as input.
        
        If the input byte array is small enough (equal to or less than the 
        defined substring length `k`), it is returned as an ASCII string. 
        Otherwise, the decompression process reconstructs the original string 
        using the leftover characters, the flag bits, and the guess table.
        """
        if not compressed_data:
            raise ValueError("Empty byte array passed to decompressor")

        if(len(compressed_data) <= Decompression.k):  # e.g. "Hi" <= (k is 2)
            return str(compressed_data, encoding=Decompression.ASCII)

        leftovers, decompressed_text, flag_bits, guess_table = self.__init_arrays(compressed_data)

        leftovers_index:int = self.k
        for i in range(self.k, len(flag_bits)):
            substring = ''.join(decompressed_text[i - self.k:i])
            hash_val = self.__hash_function(substring)

            if flag_bits[i]:
                decompressed_text.append(guess_table[hash_val])
            elif leftovers_index < len(leftovers):
                actual_char = leftovers[leftovers_index]
                leftovers_index += 1
                decompressed_text.append(actual_char)
                guess_table[hash_val] = actual_char
            else:
                break

        return ''.join(decompressed_text)
