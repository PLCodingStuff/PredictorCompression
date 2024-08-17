using System.Collections;
using System.Text;
namespace PayloadDecompression;

public class Decompression
{
    private static ulong HashFunction(string substring){
        ulong hash = 5381;

        hash = ((hash << 5) + hash ^ substring[0])%65536;
        hash = ((hash << 5) + hash ^ substring[1])%65536;
        
        return hash;
    }

   public string PayloadDecompression(byte[] compressedData)
    {
        const int k = 2;

        // Extract the length of the leftovers from the first byte
        int leftoversLength = compressedData[0];

        // Extract leftovers
        List<byte> leftovers = [];
        for (int i = 1; i <= leftoversLength; i++)
        {
            leftovers.Add(compressedData[i]);
        }

        // Extract flag bits
        int flagBitsStartIndex = 1 + leftoversLength;
        int flagBitsLength = compressedData.Length - flagBitsStartIndex;
        byte[] flagBitsArray = new byte[flagBitsLength];
        Array.Copy(compressedData, flagBitsStartIndex, flagBitsArray, 0, flagBitsLength);

        BitArray flagBits = new(flagBitsArray);

        // Decompress using the leftovers and flag bits
        StringBuilder decompressedText = new();
        char[] guessTable = new char[65536];

        // Initialize guess table with spaces
        for (int i = 0; i < 65536; i++)
        {
            guessTable[i] = ' ';
        }

        // Start with the first k characters (leftovers)
        for (int i = 0; i < k; i++)
        {
            decompressedText.Append((char)leftovers[i]);
        }

        int leftoversIndex = k;

        if(flagBits[0] != true || 
           flagBits[1] != true ||
           flagBits[2] != true ||
           flagBits[3] != true ||
           flagBits[4] != false ||
           flagBits[5] != false ||
           flagBits[6] != false ||
           flagBits[7] != false) throw new Exception($"Invalid bit array: {flagBits[0]}{flagBits[1]}{flagBits[2]}{flagBits[3]}{flagBits[4]}{flagBits[5]}{flagBits[6]}{flagBits[7]}");

        for (int i = k; i < leftoversLength + flagBits.Length; i++)
        {
            string substring = decompressedText.ToString(i - k, k);
            ulong hash = HashFunction(substring);

            if (flagBits[i - k])
            {
                // Use the guess from the table
                decompressedText.Append(guessTable[hash]);
            }
            else
            {
                // Use the character from the leftovers
                char actualChar = (char) leftovers[leftoversIndex++];
                decompressedText.Append(actualChar);
                guessTable[hash] = actualChar; // Update the guess table
            }
        }

        return decompressedText.ToString();
    }

}
