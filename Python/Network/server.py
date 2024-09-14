from socket import socket, SOL_SOCKET, SO_REUSEADDR, error as sockerror, SHUT_RDWR
from .network_component import NetworkComponent, Connection
from PayloadCompression import Decompression

class Server(NetworkComponent):
    def __init__(self, host: str, port: int, conn: Connection) -> None:
        self.conn: socket = None
        self._decompressor: Decompression = Decompression()
        super().__init__(host, port, conn)
        self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    def start(self) -> None:
        try:
            self._socket.bind(('0.0.0.0', self._port))
            self._socket.listen(1)
            print(f"Server listening on {self._host}:{self._port}")

            self.conn, addr = self._socket.accept()
            print(f"{str(addr)} connected")
            self.handler()
        except sockerror as e:
            if e.winerror != 10038:
                print(f"Error in server: {e}")
            self._conn.update_state()

    def __decompress_data(self, data: bytearray) -> str:
        if not data:
            self._conn.update_state()
            print("Peer has disconnected.")
            return None

        decompressed_message: str = self._decompressor.payload_decompression(data)
        return decompressed_message

    def handler(self) -> None:
        try:
            while True:
                compressed_data: bytearray = self.conn.recv(1024)

                message:str = self.__decompress_data(compressed_data)
                print(f"Received message: {message}")

                if message == 'exit':
                    print("Peer requested disconnection.")
                    self._conn.update_state()
                    print("Press Enter to exit")
                    break
        except sockerror as e:
            # This error occurs when `close()` is called while blocked in `recv()`
            if e.winerror != 10038:
                print(f"Error handling client: {e}")

    def close(self) -> None:
        if self.conn:
            try:
                self.conn.shutdown(SHUT_RDWR)
            except sockerror as e:
                # This error is due to lack of connection, so 
                # `shutdown()` cannot be called without one.
                if e.winerror != 10038:
                    print(f"Error Closing Server Connection socket: {e}")
            self.conn.close()
            self.conn = None
        if self._socket:
            self._socket.close()
            self._socket = None
