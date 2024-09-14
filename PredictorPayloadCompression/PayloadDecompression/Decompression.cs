using System.Collections;
using System.Text;
namespace PayloadDecompression;

public class Decompression
{
    const int k = 2;

    private static ulong HashFunction(string substring)
    {
        ulong hash = 5381;

        hash = ((hash << 5) + hash ^ substring[0])%65536;
        hash = ((hash << 5) + hash ^ substring[1])%65536;
        
        return hash;
    }

    private static void InitializeArrays(List<char> leftovers, StringBuilder decompressedText, char[] guessTable, byte[] compressedData) 
    {
        for (int i = 0; i < compressedData.Length; i++)
        {
            leftovers.Add(Convert.ToChar(compressedData[i]));
        }

        for (int i = 0; i < 65536; i++)
        {
            guessTable[i] = ' ';
        }

        for (int i = 0; i < k; i++)
        {
            decompressedText.Append(leftovers[i]);
        }
    }

    public string PayloadDecompression(byte[] compressedData)
    {
        int leftoversLength = compressedData[0];
        List<char> leftovers = [];
        char[] guessTable = new char[65536];
        StringBuilder decompressedText = new();
        int flagBitsStartIndex = 1 + leftoversLength;
        int flagBitsLength = compressedData.Length - flagBitsStartIndex;
        byte[] flagBitsArray = new byte[flagBitsLength];
        BitArray flagBits;

        Array.Copy(compressedData, flagBitsStartIndex, flagBitsArray, 0, flagBitsLength);
        flagBits = new(flagBitsArray);

        InitializeArrays(leftovers, decompressedText, guessTable, compressedData.Skip(1).Take(leftoversLength).ToArray());

        int leftoversIndex = k;
        for (int i = k; i < flagBits.Count; i++)
        {
            string substring = decompressedText.ToString(i - k, k);
            ulong hash = HashFunction(substring);

            if (flagBits[i])
            {
                decompressedText.Append(guessTable[hash]);
            }
            else if(leftoversIndex < leftovers.Count)
            {
                char actualChar = leftovers[leftoversIndex++];
                decompressedText.Append(actualChar);
                guessTable[hash] = actualChar;
            }
            else
                break;
        }

        return decompressedText.ToString();
    }
}