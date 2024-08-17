namespace PayloadDecompression.Tests;

public class UnitTest1
{
    [Theory]
    [InlineData(new byte[] {6, 97, 97, 97, 98, 98, 98, 136}, "aaaabbbb")]
    [InlineData(new byte[] {4, 97, 98, 97, 98, 240}, "abababab")]
    public void CompressionTest( byte[] byteData, string stringData)
    {
        var decompression = new Decompression();
        Console.WriteLine(byteData);

        Assert.Equal(stringData, decompression.PayloadDecompression(byteData));
    }

}