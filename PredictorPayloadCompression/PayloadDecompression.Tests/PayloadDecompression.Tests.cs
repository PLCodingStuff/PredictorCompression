namespace PayloadDecompression.Tests;

public class DecompressionTests
{
    [Theory]
    [InlineData(new byte[] {6, 97, 97, 97, 98, 98, 98,  0b10001000}, "aaaabbbb")]
    [InlineData(new byte[] {4, 97, 98, 97, 98, 0b11110000}, "abababab")]
    [InlineData(new byte[] {4, 97, 98, 97, 98,  0b11110000, 0b00000011}, "ababababab")]
    [InlineData(new byte[] {10, 
                            (byte) 'H',
                            (byte) 'e',
                            (byte) 'l',
                            (byte) 'l',
                            (byte) 'o',
                            (byte) 'W',
                            (byte) 'o',
                            (byte) 'r',
                            (byte) 'l',
                            (byte) 'd',
                            0b00100000,
                            0b00000000
                            }, "Hello World")]
    public void CompressionTest( byte[] byteData, string stringData)
    {
        var decompression = new Decompression();
        Console.WriteLine(byteData);

        Assert.Equal(stringData, decompression.PayloadDecompression(byteData));
    }

}