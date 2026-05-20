from errno import ECONNRESET, ECONNABORTED, EPIPE, ETIMEDOUT

CONNECTION_LOST_ERRORS = {
    ECONNRESET,
    ECONNABORTED,
    EPIPE,
    ETIMEDOUT
}


class ConnectionLostError(OSError):
    """Raised when the client disconnects suddenly."""

    ...


class AcceptTimeOutError(OSError):
    """Raised when the server fails to establish a connection after all retries."""

    def __init__(self, retries: int):
        super().__init__(
            f"No connection established after {retries} retries. Terminating..."
        )