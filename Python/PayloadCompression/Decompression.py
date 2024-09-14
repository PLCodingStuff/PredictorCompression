from bitarray import bitarray

class Decompression:
    k = 2
    ASCII="ASCII"

    @staticmethod
    def __hash_function(substring: str) -> int:
        hash_val: int = 5381
        hash_val = ((hash_val << 5) + hash_val) ^ ord(substring[0])
        hash_val = ((hash_val << 5) + hash_val) ^ ord(substring[1])

        return hash_val % 65536


    def __init_arrays(self, compressed_data: bytearray)->tuple[list[str], list[str], bitarray, list[str]]:
        leftovers_length: int = compressed_data[0]+1
        leftovers: list[str] = [chr(b) for b in compressed_data[1:leftovers_length]]

        get_length: int = lambda length: Decompression.k if length > Decompression.k else length
        decompressed_text: list[str] = [leftovers[i] for i in range(get_length(leftovers_length))]

        flag_bits = bitarray()
        flag_bits.frombytes(compressed_data[leftovers_length:])
        
        guess_table: list[str] = [' '] * 65536

        return leftovers, decompressed_text, flag_bits, guess_table


    def payload_decompression(self, compressed_data: bytearray)->str:
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
