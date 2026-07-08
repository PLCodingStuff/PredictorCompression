# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A peer-to-peer chat application (course project for "Software Design and Development") demonstrating network programming, the observer pattern, and a custom lossless text compression scheme ("Predictor" compression, based on [RFC 1978](https://datatracker.ietf.org/doc/rfc1978/)). Each running node opens both a server socket (to accept the peer's incoming connection) and a client socket (to connect out to the peer), so two nodes can chat with each other over TCP.

Python 3.11, dependency management via `uv` (see `uv.lock`, `pyproject.toml`). `bitarray` is the only runtime dependency.

## Commands

- Run all tests: `uv run pytest` (or `pytest` if the venv is already active)
- Run a single test file: `uv run pytest tests/test_compression.py -v`
- Run a single test: `uv run pytest tests/test_server.py::TestConfig::test_server_socket_config -v`
- Lint: `ruff check .`
- CLI entry point: `py main.py` → dispatches to the `p2ppred` argparse CLI built in `src/cli/commands.py`
  - `py main.py validate <config.json>` — validate a config file
  - `py main.py compress "text"` — compress text, prints hex (or `-o file` to write raw bytes)
  - `py main.py decompress <hex>` — decompress a hex string back to text
  - `py main.py start <server_config.json> <client_config.json>` — start a two-way chat node; needs a second `start` process (with swapped server/client configs) as its peer to connect to

CI (`.github/workflows/python-app.yml`) runs on `windows-latest` for pushes/PRs to `main`: installs `requirements.txt`, then runs `ruff check .` followed by `pytest`.

## Architecture

### Node = Server + Client sharing one Connection

`src/network/node.py`'s `Node` is the top-level orchestrator. It builds a `ServerManager` and a `ClientManager`, and attaches both as `Observer`s to a single shared `Connection` (`src/network_components/connection.py`, `src/interfaces/observer.py`, `src/interfaces/observable.py`). `Connection.state` is a boolean flip-flopped by `update_state()`; whichever side (accepting a peer, or losing one) toggles it, both the server and client sides get notified via `update()` and can react (e.g. set a shared `threading.Event` to stop the run loop). `start_chat()` runs the server's `run()` in a background thread and the client's `run()` on the calling thread, then joins.

- **Server side** (`src/network/server.py`): `ServerSocketConfig` validates host/port/timeout/retries; `ServerSocket` (subclasses `socket.socket`) binds/listens as a context manager and retries `accept()` up to `retries` times before raising `AcceptTimeOutError`. Once a peer connects, a `PeerClientSocketManager` wraps the accepted peer socket and reads messages via `get_message()`, translating disconnect-related `OSError`s (see `CONNECTION_LOST_ERRORS` in `src/errors/server_errors.py`) into `ConnectionLostError`. `ServerManager` (an `Observer`) drives the receive loop: read bytes → `ReceiveMessageProcessor.parse_received()` (decompress) → `MessageOutput.display()`.
- **Client side** (`src/network/client.py`): `ClientSocketConfig` validates peer host/port/retries/timeout; `ClientSocket` connects as a context manager, retrying on `socket.timeout` before raising `ConnectTimeOutError` (`src/errors/client_errors.py`). `ClientManager` (an `Observer`) drives the send loop: pull text from a `MessageSource` → `SendMessageProcessor.prepare_to_send()` (compress) → `sock.send_message()`.
- Both managers only stop their loop when the shared `stop_event` is set (triggered by the other side's `update()` reacting to a `Connection` state change), so the two sides are coupled only through `Connection`/`Observer`, not direct references to each other.

### Compression ("Predictor" algorithm)

`src/business/compression/compression.py` (`Compression.payload_compression`) and `decompression.py` (`Decompression.payload_decompression`) are the compression/decompression counterparts and must stay in lock-step on wire format:
- Strings of length ≤ `k` (2) are passed through as plain ASCII bytes (no framing).
- Longer strings: a 65536-entry `guess_table` keyed by a hash of the preceding `k`-character substring predicts the next character; a `bitarray` records hit(1)/miss(0) per position. Mispredicted ("leftover") characters are stored verbatim. Wire format is `[leftovers_count: 2 bytes big-endian][leftover ASCII bytes][packed bit array bytes]`.
- `SendMessageProcessor`/`ReceiveMessageProcessor` (`src/business/messages/`) are thin wrappers gluing `Compression`/`Decompression` into the client/server message pipeline; `CLIMessageSource`/`CLIMessageOutput` are the CLI-facing input/output adapters.
- Both classes use name-mangled `__`-prefixed static helpers — treat `k`/hash function/wire format as one unit; changing one side without the other breaks round-tripping. `benchmark.py` exercises this pair against the `benchmarks/*.txt` corpora to report compression ratio, space savings, and bits-per-character.

### Config loading

`src/config/config.py`'s `read_config_json` loads a node's JSON config (`port` required; `timeout`, `retries`, `address` default if absent), then `create_server_config`/`create_client_config` build the corresponding `ServerSocketConfig`/`ClientSocketConfig` dataclasses (which do their own validation in `__post_init__`). Note `create_client_config` reads the same `port`/`address` keys as the server config but binds them to `ClientSocketConfig.peer_port`/`peer_host` — i.e. for a client config file, `port` must hold the *peer's* port, not this node's own port. `node1config.json`/`node2config.json` at the repo root are example paired configs for running two local nodes against each other.

### Tests

`tests/` mirrors `src/` one file per module (e.g. `test_compression.py` ↔ `compression.py`). Networking tests (`test_client.py`, `test_server.py`, `test_connection.py`) spin up real sockets/threads on loopback rather than mocking the socket layer, since the config validation/retry/timeout behavior is what's under test. See `.claude/commands/create-python-tests.md` for the full conventions used when adding tests to this repo.

## Notes

- `main.py` still contains a large commented-out block of an older, non-CLI entry point (direct `Node(server_conf, client_conf)` construction) — the live path is `build_parser()` from `src/cli/commands.py`.
- `Node.start_chat()` starts the server in a background thread and immediately runs the client on the calling thread with no barrier — if the peer's server hasn't called `listen()` yet, connecting is a race against the client's retry/timeout config, not a guaranteed rendezvous.
- `demo/` is a scratch area exploring CLI framework choices (argparse vs click vs typer) and is unrelated to the production CLI in `src/cli/commands.py`.
- `requirements.txt` (what CI installs) pins `bitarray==2.9.2`, while `pyproject.toml`/`uv.lock` (what `uv run` uses locally) specify `bitarray>=3.8.0` (locked to `3.8.0`) — CI and local dev can end up exercising different `bitarray` versions.
