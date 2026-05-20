class ConnectTimeOutError(OSError):
    """Raised when the server fails to establish a connection after all retries."""

    def __init__(self, retries: int):
        super().__init__(
            f"No connection established after {retries} retries. Terminating..."
        )