using System.Net.Sockets;


namespace Client;

public class Client {
    private readonly Socket client;

    public Client() {
        client = new(SocketType.Stream, ProtocolType.Tcp);
    }

    public void SetClient(string hostName = "localhost", int port=4444) {
        client.Connect(hostName, port);
    }

    public void Run(){
        while(true){
            // Read message from terminal
            string userText = Console.ReadLine();

            // Compress message from terminal

            // Send message over network
            _ = client.Send(new byte[] { 0x70, 0x70, 0x60 });

        }
    }
}
