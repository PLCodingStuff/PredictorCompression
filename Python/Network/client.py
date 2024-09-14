from .network_component import NetworkComponent, Connection
import socket
from PayloadCompression import Compression
from sys import stdin

class Client(NetworkComponent):
    def __init__(self, peer_host: str, peer_port: int, conn: Connection) -> None:
        self._compressor: Compression = Compression()
        self._peer_host: str = peer_host
        self._peer_port: int = peer_port
        super().__init__(None, None, conn)
        self._socket.settimeout(10)

    def start(self) -> None:
        try:  
            self._socket.connect((self._peer_host, self._peer_port))
            print(f"Connected to {self._peer_host}:{self._peer_port}")
        except TimeoutError:
            print(f"Connection timed out.")
        except socket.error as e:
            print(str(e))
            self.close()

    def __send_message(self, msg: str):
        try:
            if not self._conn.state:
                raise ConnectionError
            compressed_msg: bytearray = self._compressor.payload_compression(msg)
            self._socket.sendall(compressed_msg)
        except ConnectionError:
            raise ConnectionError
        except socket.error as e:
            print(f"Error sending message: {e}")
        except ValueError as e:
            print(str(e))

    def handler(self):
        while True:
            message = input("")
            try:
                if message.lower() == 'exit':
                    print("Exiting chat...")
                    self.__send_message('exit')  # Send exit message to peer
                    self._conn.update_state()
                    break
                self.__send_message(message)
            except ConnectionError:
                break

    def close(self):
        if self._socket is not None:
            self._socket.shutdown(socket.SHUT_RDWR)
            self._socket.close()
            self._socket = None