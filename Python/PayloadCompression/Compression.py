from bitarray import bitarray
# from Decompression import Decompression

class Compression:
    k = 2
    ASCII="ASCII"

    @staticmethod
    def __hash_function(substring: str) -> int:
        hash_val = 5381
        hash_val = ((hash_val << 5) + hash_val) ^ ord(substring[0])
        hash_val = ((hash_val << 5) + hash_val) ^ ord(substring[1])
        return hash_val % 65536


    @staticmethod
    def __merge_bit_array_leftovers(leftovers: list[str], bit_array: bitarray) -> bytearray:
        byte_array :bytearray = bytearray(bit_array.tobytes())
        result:bytearray = bytearray()
        
        result.append(len(leftovers))
        result.extend(ord(c) for c in leftovers)
        result.extend(byte_array)

        return result


    def __init_arrays(self, S: str)->tuple[bitarray, list[str], list[str]]:
        bit_array: bitarray = bitarray(len(S))
        bit_array.setall(0)  # Set all bits to 0 initially

        get_length: int = lambda length: Compression.k if length > Compression.k else length
        leftovers: list[str] = [S[i] for i in range(get_length(len(S)))]

        guess_table: list[str] = [' '] * 65536

        return bit_array, leftovers, guess_table


    def payload_compression(self, S: str) -> bytearray:
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
    

# if __name__ == "__main__":
#     comp = Compression()
#     decomp = Decompression()

#     data = comp.payload_compression("Hi")
#     res = decomp.payload_decompression(data)
#     print(res)
    
