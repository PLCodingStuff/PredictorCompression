from .network_component import NetworkComponent, Connection
from socket import error as sockerror, SHUT_RDWR
from PayloadCompression import Compression
from time import sleep

class Client(NetworkComponent):
    def __init__(self, peer_host: str, peer_port: int, 
                       conn: Connection, retries: int = 10,
                       delay: float = 5.0) -> None:
        self._compressor: Compression = Compression()
        self._peer_host: str = peer_host
        self._peer_port: int = peer_port
        self._retries: int = retries
        self._delay:float = delay
        super().__init__(None, None, conn)

    def start(self) -> None:
        retry: int = 0
        try:
            while retry < self._retries:
                try:
                    sleep(self._delay)
                    self._socket.settimeout(10)
                    self._socket.connect((self._peer_host, self._peer_port))
                    print(f"Connected to {self._peer_host}:{self._peer_port}")
                except ConnectionRefusedError:
                    retry+=1
        except TimeoutError:
            print(f"Connection timed out.")
        except sockerror as e:
            print(f"Error while starting client: {e}")
            self._conn.update_state()
            return

    def __send_message(self, msg: str):
        try:
            if not self._conn.state:
                raise ConnectionError
            compressed_msg: bytearray = self._compressor.payload_compression(msg)
            self._socket.sendall(compressed_msg)
        except ConnectionError:
            raise ConnectionError
        except sockerror as e:
            print(f"Error sending message: {e}")
            self._conn.update_state()
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
            self._socket.shutdown(SHUT_RDWR)
            self._socket.close()
            self._socket = None