---
name: run-predictorcompression
description: Build, run, and drive the p2ppred CLI (validate/compress/decompress/start) for the PredictorCompression project. Use when asked to run, test, launch, smoke-test, or screenshot-equivalent this app, or to verify a change to the compression/CLI/networking code actually works end-to-end.
---

Paths below are relative to the repo root (`C:\Users\plwos\Documents\GitHub\PredictorCompression`).

This is a Python 3.11 CLI tool (`p2ppred`, entry point `main.py`), not a
GUI/web app. It has no persistent server to curl — it's driven by invoking
`main.py` subcommands and reading stdout/exit codes, plus one interactive
two-process subcommand (`start`) for node-to-node chat.

## Prerequisites

- `uv` (already vendors the venv — `uv run` works with no extra setup).
- No OS packages needed; pure Python + `bitarray`.

## Build

Nothing to build. Dependencies resolve on first `uv run`:

```
uv run python main.py --version
```

## Run (agent path)

**CLI smoke test** — validates `validate`/`compress`/`decompress`, the
compress/decompress round trip, and the short-string (`len <= k`)
passthrough framing. This is the reliable, deterministic surface — run this
first for any change to `src/cli`, `src/business/compression`, or
`src/config`:

```
uv run python .claude/skills/run-predictorcompression/smoke_cli.py
```

Expect `All CLI smoke checks passed.` and exit 0.

**Two-node `start` driver** — spawns two node processes wired to each other
over loopback (server on :15000/:16000, client dialing the other's port),
waits for both sides to connect, sends one chat message, then sends `quit`
to both and prints full output + exit codes for each:

```
uv run python .claude/skills/run-predictorcompression/drive_start.py
```

**As of this writing this currently demonstrates a crash, not a success —
see Gotchas.** Use it to check whether that crash is still present after
touching `src/network/client.py`, `src/network/node.py`, or
`src/business/messages/send_message.py`.

## Direct invocation

For changes scoped to compression only, skip the CLI/process layer entirely:

```python
from src.business.compression.compression import Compression
from src.business.compression.decompression import Decompression
data = Compression().payload_compression("some text")
Decompression().payload_decompression(data)  # == "some text"
```

## Run (human path)

```
uv run python main.py validate node1config.json
uv run python main.py compress "some text"
uv run python main.py decompress <hex>
uv run python main.py start <server_config.json> <client_config.json> -v
```

`start` blocks on an interactive `input("> ")` prompt for chat text; type
`quit` to stop that side. It needs a second `start` process (with swapped
server/client ports) as its peer to actually connect to — see
`drive_start.py` for a working two-process pairing example, since
`node1config.json`/`node2config.json` at the repo root are NOT directly
usable as the `server_json`/`client_json` pair `start` expects (they use a
different single-file `port`/`peer_port` shape that the current config
loader doesn't read for this purpose — `read_config_json` only ever reads
the `port` key, so for the *client* config file `port` must hold the
peer's port, not this node's own port).

## Test suite

```
uv run pytest
```

As of this writing this collects 3 pre-existing failures in
`demo/test_additional_coverage.py` (`TestNodeInit`, `TestNodeStartChat`,
`TestClientSocketRetryBug`) — unrelated to anything in this skill, already
failing on a clean checkout. One of them,
`test_real_send_crashes_with_type_error`, independently confirms the
`start`-command bug documented below. Don't treat these as a regression you
introduced; only new failures under `tests/` are relevant to a change.

## Gotchas

- **Windows console + `✓`/`✗` = crash.** `cmd_validate` and `cmd_compress`
  (`src/cli/commands.py`) print literal `✓`/`✗` characters. On a plain
  Windows console (cp1252/cp437, not UTF-8), `print()` raises
  `UnicodeEncodeError`, which the CLI's own `except Exception` handler
  reports back as `"Config is invalid: 'charmap' codec can't encode..."` —
  i.e. a perfectly valid config gets reported as invalid, and a successful
  compression as failed. **Fix: always set `PYTHONIOENCODING=utf-8`** before
  invoking `main.py` (both driver scripts here do this already).
- **`start` crashes on the first real chat message, 100% reproducible.**
  `ClientManager.run()` (`src/network/client.py:101-102`) calls
  `self._message_proc.prepare_to_send(msg)` — which returns the compressed
  bytes — and **discards the return value**, then calls
  `sock.send_message(msg)` with the original *uncompressed string*.
  `ClientSocket.send_message` calls `self.sendall(msg)`, and `sendall` on a
  raw `str` raises `TypeError: a bytes-like object is required, not 'str'`.
  This is unhandled anywhere above it (`Node.start_chat`, `cmd_start`, and
  `main()` don't catch `TypeError`), so it's a full crash with traceback,
  confirmed via `drive_start.py`. The fix is one line: capture and send the
  processor's return value instead of `msg`.
- **Connecting both sides is a race, not a rendezvous.** `Node.start_chat()`
  starts the server in a background thread and immediately runs the client
  on the calling thread with no barrier — if the peer's server hasn't
  called `listen()` yet, the client's `ConnectTimeOutError` retry loop may
  or may not catch up depending on config `retries`/`timeout`. Give it a
  few seconds (`drive_start.py` sleeps 5s) before trusting a "not
  connected" result.
- **`quit` only stops your own node, not the peer.** Typing `quit` triggers
  this node's own shared `Connection.update_state()`, which only notifies
  *this process's own* server/client `Observer`s (the `Connection` object
  is per-node, not shared across the two OS processes). The peer keeps
  running until its own server's accept-retry window lapses or you quit it
  too.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `✗ Config is invalid: 'charmap' codec can't encode character '✓'...` on a valid config | Windows console isn't UTF-8 | `PYTHONIOENCODING=utf-8 uv run python main.py validate ...` |
| `git bash` / MSYS path like `-o /tmp/out.bin` resolves to `C:/Program Files/Git/tmp/out.bin` and fails with `PermissionError` | MSYS path translation rewrites leading `/tmp` | Use a `C:/...` path (or a path under the scratch dir) for `-o`, not a bare `/tmp/...` path |
| `start` crashes with `TypeError: a bytes-like object is required, not 'str'` | The send-path bug above | Known issue; not yet fixed. Not something to route around when *driving* the app — it's the accurate current behavior |
