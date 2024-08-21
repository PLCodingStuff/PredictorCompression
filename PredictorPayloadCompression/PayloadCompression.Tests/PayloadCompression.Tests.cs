namespace PayloadCompression.Tests;

public class PayloadCompressionTests
{
    [Theory]
    [InlineData("aaaabbbb", new byte[] {6, 97, 97, 97, 98, 98, 98, 0b10001000})]
    [InlineData("abababab", new byte[] {4, 97, 98, 97, 98, 0b11110000})]
    [InlineData("ababababab", new byte[] {4, 97, 98, 97, 98, 0b11110000, 0b00000011})]
    [InlineData("abababababc", new byte[] {5, 97, 98, 97, 98, 99, 0b11110000, 0b00000011})]
    [InlineData("Hello World", new byte[] {10, 
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
                                            })]
    public void CompressionTest(string stringData, byte[] byteData)
    {
        var compression = new Compression();
        Console.WriteLine(byteData);

        Assert.Equal(byteData, compression.PayloadCompression(stringData));
    }

    [Fact]
    public void CompressionArgumentException(){
        var compression = new Compression();

        Assert.Throws<ArgumentException>(() => compression.PayloadCompression(""));
    }
}