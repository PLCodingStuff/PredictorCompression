namespace PayloadCompression.Tests;

public class PayloadCompressionTests
{
    [Theory]
    [InlineData("aaaabbbb", new byte[] {6, 97, 97, 97, 98, 98, 98, 136})]
    [InlineData("abababab", new byte[] {4, 97, 98, 97, 98, 240})]
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