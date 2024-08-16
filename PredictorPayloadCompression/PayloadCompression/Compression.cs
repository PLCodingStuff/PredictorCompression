using System.Collections;
using System.Text;

namespace PayloadCompression;


public class Compression
{
    private static ulong HashFunction(string substring){
        ulong hash = 5381;

        hash = ((hash << 5) + hash ^ substring[0])%65536;
        hash = ((hash << 5) + hash ^ substring[1])%65536;
        // hash = (hash << 5) + hash ^ substring[2];
        // hash = (hash << 5) + hash ^ substring[3];
        
        return hash;
    }

    private static byte[] ConvertToByteArray(BitArray bitArray)
        {
            int bytes = (bitArray.Length + 7) / 8;
            byte[] arr2 = new byte[bytes];
            int bitIndex = 0;
            int byteIndex = 0;

            for (int i = 0; i < bitArray.Length; i++)
            {
                if (bitArray[i])
                {
                    arr2[byteIndex] |= (byte)(1 << bitIndex);
                }

                bitIndex++;
                if (bitIndex == 8)
                {
                    bitIndex = 0;
                    byteIndex++;
                }
            }

            return arr2;
        }

    public byte[] PayloadCompression(string S){
        ulong hash;
        const int k = 2;
        BitArray bitArray = new BitArray(S.Length, false);
        var leftovers = new List<char>();
        char[] guessTable = new char[65536];

        if(S==""){
            throw new ArgumentException("Empty string passed to compressor");
        }

        // Init leftovers
        leftovers.Add(S[0]);
        leftovers.Add(S[1]);

        // Init guess table with spaces
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

        var byteArray = ConvertToByteArray(bitArray);
        // Console.WriteLine($"Leftovers: {[.. leftovers]}");
        // Console.Write("ByteArray: ");
        // foreach(byte b in byteArray){
        //     Console.Write($"{b} ");
        // }
        // Console.WriteLine();

    /*        
        byte[] result = new byte[byteArray.Length + leftovers.Count];

        foreach(char c in leftovers){
            result.Append((byte) c);
        }
        foreach(byte b in byteArray){
            Console.WriteLine(b);
            result.Append(b);
        }
        // var stream = new MemoryStream(leftovers.Count + (bitArray.Length + 7) / 8);
        // foreach(char c in leftovers){
            // stream.WriteByte((byte) c);
        // }
        // foreach(byte b in byteArray){
            // stream.WriteByte(b);
        // }

        // return stream;

        foreach(byte b in result){
            Console.Write(b);
        }
        Console.WriteLine();
    */
        List<byte> result = [];
        foreach(char c in leftovers){
            result.Add((byte) c);
        }
        foreach(byte b in byteArray){
            result.Add(b);
        }

        // foreach(byte b in result){
        //     Console.Write(b);
        // }
        // Console.WriteLine();

        return [.. result];
    }
}
