using System.Collections;
using System.Text;

namespace PayloadCompression;


public class Compression
{
    private static ulong HashFunction(string substring){
        ulong hash = 5381;

        hash = ((hash << 5) + hash ^ substring[0])%65536;
        hash = ((hash << 5) + hash ^ substring[1])%65536;
        
        return hash;
    }

    private static byte[] ConvertToByteArray(BitArray bitArray)
    {
        int bytes = (bitArray.Count + 7) / 8;
        byte[] result = new byte[bytes];
        int bitIndex;
        int byteIndex;

        for (int i = 0; i < bitArray.Count; i++)
        {
            bitIndex = i % 8;
            byteIndex = i >> 3;

            if (bitArray[i])
                result[byteIndex] |= (byte)(1 << bitIndex);
        }

        return result;
    }

    private static byte[] MergeBitArrayLeftovers(List<char> leftovers, BitArray bitArray) {
        var byteArray = ConvertToByteArray(bitArray);
        List<byte> result = [];

        result.Add((byte)leftovers.Count);
        foreach(char c in leftovers){
            result.Add((byte) c);
        }
        foreach(byte b in byteArray){
            result.Add(b);
        }

        return [.. result];
    }

    public byte[] PayloadCompression(string S)
    {
        ulong hash;
        const int k = 2;
        BitArray bitArray = new(S.Length, false);
        List<char> leftovers;
        char[] guessTable = new char[65536];

        if(S==""){
            throw new ArgumentException("Empty string passed to compressor");
        }

        leftovers = [S[0], S[1]];
        
        for(int c = 0; c < 65536; c++){
             guessTable[c] = ' ';
        }

        for(int i = k; i < S.Length; i++){
            hash = HashFunction(S.Substring(i-k, k));
            if (guessTable[hash] == S[i])
                bitArray[i] = true;
            else {
                leftovers.Add(S[i]);
                guessTable[hash] = S[i];
            }
        }

        return MergeBitArrayLeftovers(leftovers, bitArray);
    }
}
