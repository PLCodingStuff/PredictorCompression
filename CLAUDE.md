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
- Benchmarks: `py benchmark.py benchmark` (all corpora) or `py benchmark.py benchmark --test-file <name.txt>` — note the `benchmark` subcommand is required

**Set `PYTHONIOENCODING=utf-8` before running `main.py` or `benchmark.py` on a Windows console.** Both print non-cp1252 glyphs (`✓`, `✗`, `⚡`) and crash with `UnicodeEncodeError` without it. This fails *misleadingly* in `cmd_validate`: `UnicodeEncodeError` subclasses `ValueError`, so printing the `✓` on a **valid** config is caught by the command's own `except (ValueError, FileNotFoundError)` and reported as `✗ Config is invalid: 'charmap' codec can't encode...` with exit code 1.

CI (`.github/workflows/python-app.yml`) runs on `windows-latest` for pushes/PRs to `main`: installs `requirements.txt`, then runs `ruff check .` followed by `pytest`.

`.claude/skills/run-predictorcompression/` holds the scripts (`smoke_cli.py`, `drive_start.py`) for driving the CLI and a two-node chat session end-to-end — use it rather than hand-rolling a peer harness.

## Architecture

### Node = Server + Client sharing one Connection

`src/network/node.py`'s `Node` is the top-level orchestrator. It builds a `ServerManager` and a `ClientManager`, and attaches both as `Observer`s to a single shared `Connection` (`src/network_components/connection.py`, `src/interfaces/observer.py`, `src/interfaces/observable.py`). `Connection.state` is a boolean flip-flopped by `update_state()`; whichever side (accepting a peer, or losing one) toggles it, both the server and client sides get notified via `update()` and can react (e.g. set a shared `threading.Event` to stop the run loop). `start_chat()` runs the server's `run()` in a background thread and the client's `run()` on the calling thread, then joins.

- **Server side** (`src/network/server.py`): `ServerSocketConfig` validates host/port/timeout/retries; `ServerSocket` (subclasses `socket.socket`) binds/listens as a context manager and retries `accept()` up to `retries` times before raising `AcceptTimeOutError`. Once a peer connects, a `PeerClientSocketManager` wraps the accepted peer socket (`set_socket()`) and exposes `send_frame()`/`recv_frame()`. `ServerManager.run()` (an `Observer`) does `perform_handshake()` first, then drives the receive loop: `recv_frame()` → dispatch on `MessageType` — `MSG` → `ReceiveMessageProcessor.parse_received()` (decompress) → `MessageOutput.display()`; `QUIT` → display "Peer has left" and toggle `Connection`; anything else → display an "ignored control frame" notice.
- **Client side** (`src/network/client.py`): `ClientSocketConfig` validates peer host/port/retries/timeout; `ClientSocket` connects as a context manager, retrying on `socket.timeout` before raising `ConnectTimeOutError` (`src/errors/client_errors.py`), and also exposes `send_frame()`/`recv_frame()` plus a `send_message()` that wraps a payload in a `MessageType.MSG` frame. `ClientManager.run()` (an `Observer`) does `perform_handshake()` first, then drives the send loop: pull text from a `MessageSource` → `SendMessageProcessor.prepare_to_send()` (compress) → `sock.send_message()`. An empty/`None` message means the user is done: it sends a `MessageType.QUIT` frame and toggles `Connection` to end the session.
- Both managers only stop their loop when the shared `stop_event` is set (triggered by the other side's `update()` reacting to a `Connection` state change), so the two sides are coupled only through `Connection`/`Observer`, not direct references to each other.

### Wire protocol (framing + handshake)

On top of raw TCP sits a small length-prefixed message protocol (loosely SMTP-style control verbs), the layer the client/server message pipelines actually read and write:
- **Framing** (`src/network_components/framing.py`): each frame is `[body length: 4 bytes big-endian (">I")][type: 1 byte][payload bytes]`. `MessageType` is an `IntEnum` — `HELLO`, `ACK`, `MSG`, `QUIT`. `pack_frame()` builds a frame; `send_frame()`/`recv_frame()` write/read one over a socket; `_recv_exact()` loops `recv()` until `n` bytes arrive. Disconnect-related `OSError`s (`CONNECTION_LOST_ERRORS`) and a graceful empty `recv()` are both translated into `ConnectionLostError`.
- **Handshake** (`src/network_components/handshake.py`): `perform_handshake(peer)` runs a symmetric `HELLO` → `HELLO` then `ACK` → `ACK` exchange against anything satisfying the `FramedPeer` `Protocol` (`send_frame`/`recv_frame`) — i.e. both `ClientSocket` and `PeerClientSocketManager`. Any mismatch, malformed frame, timeout, or disconnect surfaces as `HandshakeError` (`src/errors/protocol_errors.py`, an `OSError` subclass). Both `run()` loops treat a failed handshake as "no session" and return early.

### Compression ("Predictor" algorithm)

`src/business/compression/compression.py` (`Compression.payload_compression`) and `decompression.py` (`Decompression.payload_decompression`) are the compression/decompression counterparts and must stay in lock-step on wire format:
- Strings of length ≤ `k` (2) are passed through as plain ASCII bytes (no framing).
- Longer strings: a 65536-entry `guess_table` keyed by a hash of the preceding `k`-character substring predicts the next character; a `bitarray` records hit(1)/miss(0) per position. Mispredicted ("leftover") characters are stored verbatim. Wire format is `[leftovers_count: 2 bytes big-endian][leftover ASCII bytes][packed bit array bytes]`.
- `SendMessageProcessor`/`ReceiveMessageProcessor` (`src/business/messages/`) are thin wrappers gluing `Compression`/`Decompression` into the client/server message pipeline; `CLIMessageSource`/`CLIMessageOutput` are the CLI-facing input/output adapters.
- There is no length field: the decoder walks `len(flag_bits)` (a multiple of 8, so it includes the bit array's trailing zero padding) and stops via the `leftovers_index >= len(leftovers)` break. Termination depends on leftovers exhausting exactly when the real payload ends — any change to how leftovers or padding are written must preserve that.
- **Input must be codepoints < 256.** Leftovers are written with `result.extend(ord(c) for c in leftovers)`, so any character above U+00FF raises `ValueError: byte must be in range(0, 256)`; the `len(S) <= k` fast path is stricter still (`encoding="ASCII"`). The `benchmarks/*emoji*.txt` corpora therefore cannot round-trip — `benchmark.py` also opens files with `encoding="ascii"`, so they fail at read time.
- The leftovers count is 2 bytes, capping a message at 65535 leftover characters.
- Both classes use name-mangled `__`-prefixed static helpers — treat `k`/hash function/wire format as one unit; changing one side without the other breaks round-tripping. `k` is not a single knob: `Compression.__hash_function` loops over the substring, but `Decompression.__hash_function` hardcodes `substring[0]`/`substring[1]`, so raising `k` silently desynchronizes the two hashes. `benchmark.py` exercises this pair against the `benchmarks/*.txt` corpora to report compression ratio, space savings, and bits-per-character.

### Config loading

`src/config/config.py`'s `read_config_json` loads a node's JSON config (`port` required; `timeout`, `retries`, `address` default if absent), then `create_server_config`/`create_client_config` build the corresponding `ServerSocketConfig`/`ClientSocketConfig` dataclasses (which do their own validation in `__post_init__`). Note `create_client_config` reads the same `port`/`address` keys as the server config but binds them to `ClientSocketConfig.peer_port`/`peer_host` — i.e. for a client config file, `port` must hold the *peer's* port, not this node's own port. `node1config.json`/`node2config.json` at the repo root are example paired configs for running two local nodes against each other.

### Tests

`tests/` mirrors `src/` one file per module (e.g. `test_compression.py` ↔ `compression.py`). Networking and protocol tests (`test_client.py`, `test_server.py`, `test_connection.py`, `test_framing.py`, `test_handshake.py`) spin up real sockets/threads on loopback rather than mocking the socket layer, since the config validation/retry/timeout behavior is what's under test. Currently uncovered: `node.py`, `src/cli/`, `src/config/`, and `src/business/messages/`. See `.claude/commands/create-python-tests.md` for the full conventions used when adding tests to this repo.

Some tests intentionally print to stdout mid-run (`Peer has left the chat.`, echoed messages), so a passing suite is not silent — that noise is expected, not a failure.

## Notes

- `main.py` still contains a large commented-out block of an older, non-CLI entry point (direct `Node(server_conf, client_conf)` construction) — the live path is `build_parser()` from `src/cli/commands.py`.
- `Node.start_chat()` starts the server in a background thread and immediately runs the client on the calling thread with no barrier — if the peer's server hasn't called `listen()` yet, connecting is a race against the client's retry/timeout config, not a guaranteed rendezvous.
- `ClientSocket.__enter__`'s `raise ConnectTimeOutError` sits *inside* the `for _ in range(retries)` body, so the first `socket.timeout` aborts and `retries` is effectively 1 — unlike `ServerSocket.accept()`, which really does loop. This makes the rendezvous race above worse than the config suggests.
- `create_client_config` passes positionally as `ClientSocketConfig(address, port, retries, timeout)` while `create_server_config` passes `ServerSocketConfig(address, port, timeout, retries)` — the two dataclasses declare those last two fields in opposite order, so the field order is correct but easy to "fix" wrongly.
- `README.md` is stale — it documents a single-argument `py main.py config.json` invocation, a flat top-level file layout, and a `NetworkComponent` base class, none of which exist any more. Trust the code over the README.
- `demo/` is a scratch area exploring CLI framework choices (argparse vs click vs typer) and is unrelated to the production CLI in `src/cli/commands.py`.
- `requirements.txt` (what CI installs) pins `bitarray==2.9.2`, while `pyproject.toml`/`uv.lock` (what `uv run` uses locally) specify `bitarray>=3.8.0` (locked to `3.8.0`) — CI and local dev can end up exercising different `bitarray` versions.

## Resuming after a break

`Predictor Compression P2P.md` at the repo root is the task backlog — read it first when picking this project back up after time away, since you (Claude) are stateless between sessions and this file is the continuity mechanism. It's organized as:
- **Now / Low-energy queue / Backlog** — priority buckets, each item tagged with effort (`#e/low`, `#e/med`, `#e/high`).
- **Topic labels** (`bug`, `testing`, `compression`, `docs`, `build/ci`, `cleanup`, `cli`, `architecture`) — an orthogonal axis layered on top of the priority buckets, not a replacement for them; see the label breakdown discussed in-session for which task belongs to which.
- **Log** — dated entries recording what was reviewed/decided/changed each session. Read this to recover *why* a task is phrased the way it is before redoing analysis that already happened.

When finishing a session that changes priorities, completes a task, or makes a non-obvious decision, add a dated entry to the Log and update the task list — this file is the only thing carrying context forward, since neither this CLAUDE.md nor conversation history persists on its own.

The user also has their own broader project-organization system (outside this repo) that has not been described here yet — don't assume `Predictor Compression P2P.md`'s structure is the whole picture. If the user brings it up, ask how this repo's task file should fit into it and update this note accordingly.
