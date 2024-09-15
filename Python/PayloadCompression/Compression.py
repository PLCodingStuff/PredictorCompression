from bitarray import bitarray

class Compression:
    """
    Class for compressing a string payload using a basic dictionary-based 
    compression scheme. It uses a fixed-length substring hashing approach to 
    reduce the size of the input string.

    Attributes:
        k (int): The length of the substring used for hashing. Default is 2.
        ASCII (str): The encoding format used for compressing small strings.
    
    Methods:
        payload_compression(S: str) -> bytearray: Compresses the input string.
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
        hash_val = 5381
        hash_val = ((hash_val << 5) + hash_val) ^ ord(substring[0])
        hash_val = ((hash_val << 5) + hash_val) ^ ord(substring[1])
        return hash_val % 65536


    @staticmethod
    def __merge_bit_array_leftovers(leftovers: list[str], bit_array: bitarray) -> bytearray:
        """
        Merge the leftover characters and the bit array into a bytearray.

        Args:
            leftovers (list[str]): A list of characters not found in the guess table.
            bit_array (bitarray): A bit array representing matches between substrings 
                                  and the guess table.
        
        Returns:
            bytearray: A bytearray containing the number of leftovers, their ASCII values,
                       and the bit array's binary data.
        
        The result starts with the number of leftover characters, followed by their 
        ASCII values, and then the binary data of the bit array.
        """
        byte_array :bytearray = bytearray(bit_array.tobytes())
        result:bytearray = bytearray()
        
        result.append(len(leftovers))
        result.extend(ord(c) for c in leftovers)
        result.extend(byte_array)

        return result


    def __init_arrays(self, S: str)->tuple[bitarray, list[str], list[str]]:
        """
        Initialize the bit array, leftovers list, and guess table for compression.

        Args:
            S (str): The string to be compressed.
        
        Returns:
            tuple: A tuple containing:
                   - bit_array: A bitarray initialized with all bits set to 0.
                   - leftovers: A list of initial leftover characters.
                   - guess_table: A preallocated list for storing guessed characters.
        
        The `leftovers` list starts with the first few characters of `S`, and 
        the `guess_table` is a lookup table for guessed characters based on hashes.
        """
        bit_array: bitarray = bitarray(len(S))
        bit_array.setall(0)  # Set all bits to 0 initially

        get_length: int = lambda length: Compression.k if length > Compression.k else length
        leftovers: list[str] = [S[i] for i in range(get_length(len(S)))]

        guess_table: list[str] = [' '] * 65536

        return bit_array, leftovers, guess_table


    def payload_compression(self, S: str) -> bytearray:
        """
        Compress a string using a basic dictionary-based compression method.

        Args:
            S (str): The input string to be compressed.
        
        Returns:
            bytearray: The compressed representation of the string.
        
        Raises:
            ValueError: If an empty string is provided as input.
        
        If the input string is shorter than or equal to the defined substring 
        length `k`, it is returned as a bytearray encoded in ASCII. Otherwise, 
        the string is compressed by creating a bit array and merging it with 
        leftover characters.
        """
        if not S:
            raise ValueError("Empty string passed to compressor")

        if(len(S) <= Compression.k):
            return bytearray(S, encoding=Compression.ASCII)

        bit_array, leftovers, guess_table = self.__init_arrays(S)

        for i in range(Compression.k, len(S)):
            substring = S[i - Compression.k:i]
            hash_val = self.__hash_function(substring)

            if guess_table[hash_val] == S[i]:
                bit_array[i] = 1
            else:
                leftovers.append(S[i])
                guess_table[hash_val] = S[i]

        return self.__merge_bit_array_leftovers(leftovers, bit_array)