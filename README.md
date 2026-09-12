# Peer-To-Peer Chat Application

## Overview

This project is a simple Peer-To-Peer (P2P) chat application implemented using Python. It features a client-server architecture with data compression and decompression functionalities. The application uses the observer pattern to manage the state of the connection between the client and server, and supports basic message exchange over a network.

The compression is done using the Predictor algorithm (it can be referred from [here](https://datatracker.ietf.org/doc/rfc1978/) and [here](https://dl.acm.org/doi/10.1145/42005.42031)).

The project is designed for a course named "Software Design and Development" and demonstrates principles of software design, including network communication, data compression, and design patterns.

Python 3.11 was used for the implementation.

## Features

- **Client-Server Communication**: Each running node opens both a server socket (to accept the peer's incoming connection) and a client socket (to connect out to the peer), driven through a small length-prefixed wire protocol with a `HELLO`/`ACK` handshake.
- **Data Compression**: Uses a custom Predictor-based compression scheme to minimize the size of transmitted messages.
- **Observer Pattern**: The server and client sides are both `Observer`s of a shared `Connection`, so either side toggling the connection state (e.g. on disconnect) notifies the other.
- **Network Handling**: Dedicated error types for handshake failures, connection loss, and accept/connect timeouts.
- **CLI**: A `p2ppred` command-line tool for validating configs, compressing/decompressing text directly, and starting a chat node.

## Components

### Observer and Observable

- **Observer** / **Observable**: abstract base classes implementing the observer pattern (`src/interfaces/`).
- **Connection**: an `Observable` tracking a shared connection state, toggled when a peer connects/disconnects (`src/network_components/connection.py`).

### Wire protocol

- **Framing**: length-prefixed message frames (`HELLO`/`ACK`/`MSG`/`QUIT`) sent/received over a socket (`src/network_components/framing.py`).
- **Handshake**: a symmetric `HELLO`→`HELLO` then `ACK`→`ACK` exchange run before either side starts sending chat messages (`src/network_components/handshake.py`).

### Compression and Decompression

- **Compression** / **Decompression**: implement the Predictor compression/decompression algorithm (`src/business/compression/`).
- **SendMessageProcessor** / **ReceiveMessageProcessor**: wrap compression/decompression into the client/server message pipeline (`src/business/messages/`).

### Network Components

- **Client** (`src/network/client.py`): `ClientSocketConfig`, `ClientSocket` (connects to the peer, retries on timeout), and `ClientManager` (runs the handshake, then the send loop).
- **Server** (`src/network/server.py`): `ServerSocketConfig`, `ServerSocket` (binds/listens, retries `accept()`), `PeerClientSocketManager` (wraps the accepted peer socket), and `ServerManager` (runs the handshake, then the receive loop).

### Node

- **Node** (`src/network/node.py`): builds the server and client managers, attaches both as observers of a shared `Connection`, and runs the server in a background thread while the client runs on the calling thread.

### Config loading

- **`src/config/config.py`**: loads a node's JSON config (`port` required; `timeout`, `retries`, `address` default if absent) and builds the corresponding `ServerSocketConfig`/`ClientSocketConfig`.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/PLCodingStuff/PredictorCompression.git
   cd PredictorCompression
   ```

2. **Install dependencies:**
   This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management (see `pyproject.toml`/`uv.lock`). Install `uv`, then:
   ```bash
   uv sync
   ```

## Usage

The CLI entry point is `main.py`, which dispatches to the `p2ppred` subcommands:

```bash
py main.py validate <config.json>              # validate a config file
py main.py compress "some text"                # compress text, prints hex
py main.py decompress <hex>                     # decompress a hex string back to text
py main.py start <server_config.json> <client_config.json>   # start a two-way chat node
```

(Prefix with `uv run` instead of `py` if you're not in an activated environment, e.g. `uv run python main.py validate config.json`.)

### Configuration files

Each node needs **two** JSON config files: one for its server socket, one for its client socket (which dials the peer). Both share the same shape:

```json
{
    "address": "127.0.0.1",
    "port": 5000,
    "timeout": 5.0,
    "retries": 3
}
```

`address`, `timeout`, and `retries` are optional and default to `127.0.0.1`, `5.0`, and `3` respectively. `port` is required — for the **server** config it's this node's own listening port; for the **client** config it's the *peer's* port (the client config connects out to it). Note that the config loader only ever reads a `port` key; there is no separate `peer_port` key.

To run two local nodes against each other you need four files in total (a server + client config per node), e.g. for node A listening on `5000` and dialing node B's `6000`, and node B listening on `6000` and dialing node A's `5000`:

```bash
py main.py start nodeA_server.json nodeA_client.json   # nodeA_server.json: {"port": 5000}, nodeA_client.json: {"port": 6000}
py main.py start nodeB_server.json nodeB_client.json   # nodeB_server.json: {"port": 6000}, nodeB_client.json: {"port": 5000}
```

`node1config.json`/`node2config.json` at the repo root predate this and use a different single-file `port`/`peer_port` shape that the loader doesn't read that way — they are **not** directly usable as the `server_json`/`client_json` arguments above.

### Known issues

- Sending a chat message via `start` currently crashes: `ClientManager.run()` discards the compressed payload and sends the raw string instead, which fails at the socket layer.
- Typing `quit` only stops your own node's session — it doesn't notify the peer, which keeps running until its own accept/connect retry window lapses.

## Testing and benchmarking

```bash
uv run pytest                                   # run the test suite
py benchmark.py benchmark                       # run compression benchmarks against benchmarks/*.txt
```

## Project Structure

```
main.py                                  # CLI entry point
benchmark.py                             # compression benchmark runner
src/
  cli/commands.py                        # p2ppred argparse CLI (validate/compress/decompress/start)
  config/config.py                       # JSON config loading + ServerSocketConfig/ClientSocketConfig construction
  network/
    node.py                              # Node: orchestrates server + client over a shared Connection
    server.py                            # ServerSocketConfig, ServerSocket, PeerClientSocketManager, ServerManager
    client.py                            # ClientSocketConfig, ClientSocket, ClientManager
  network_components/
    connection.py                        # Connection (Observable)
    framing.py                           # wire frame packing/sending/receiving, MessageType
    handshake.py                         # HELLO/ACK handshake
  business/
    compression/compression.py           # Compression (Predictor algorithm)
    compression/decompression.py         # Decompression
    messages/                            # SendMessageProcessor/ReceiveMessageProcessor, CLI I/O adapters
  interfaces/
    observer.py                          # Observer
    observable.py                        # Observable
  errors/                                # client/server/protocol error types
tests/                                   # pytest suite, mirrors src/ one file per module
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
