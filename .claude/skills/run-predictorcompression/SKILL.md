---
name: run-predictorcompression
description: Build, run, and drive the p2ppred CLI (validate/compress/decompress/start) for the PredictorCompression project. Use when asked to run, test, launch, smoke-test, or screenshot-equivalent this app, or to verify a change to the compression/CLI/networking code actually works end-to-end.
---

Paths below are relative to the repo root (`C:\Users\plwos\Documents\GitHub\PredictorCompression`).

This is a Python 3.11 CLI tool (`p2ppred`, entry point `p2ppred.py`), not a
GUI/web app. It has no persistent server to curl — it's driven by invoking
`p2ppred.py` subcommands and reading stdout/exit codes, plus one interactive
two-process subcommand (`start`) for node-to-node chat.

## Prerequisites

- `uv` (already vendors the venv — `uv run` works with no extra setup).
- No OS packages needed; pure Python + `bitarray`.

## Build

Nothing to build. Dependencies resolve on first `uv run`:

```
uv run python p2ppred.py --version
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

Expect both nodes to exit 0, with node A's output showing the peer's chat
message displayed and, after `quit`, `Peer has left the chat.` — see
Gotchas for the last-known-good behavior this was verified against. Rerun
this after touching `src/network/client.py`, `src/network/node.py`, or
`src/business/messages/send_message.py` to make sure it still holds.

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
uv run python p2ppred.py validate node1config.json
uv run python p2ppred.py compress "some text"
uv run python p2ppred.py decompress <hex>
uv run python p2ppred.py start <server_config.json> <client_config.json> -v
```

`start` blocks on an interactive `input("> ")` prompt for chat text; type
`quit` to stop that side. It needs a second `start` process (with swapped
server/client configs) as its peer to actually connect to. `node1config.json`
(port `5000`) and `node2config.json` (port `6000`) at the repo root are a
ready-to-run pair, used in swapped order — verified live:

```
uv run python p2ppred.py start node1config.json node2config.json   # node 1
uv run python p2ppred.py start node2config.json node1config.json   # node 2
```

(Earlier revisions of this skill claimed these two files used a
`port`/`peer_port` shape the loader couldn't read for this purpose — that
was true before commit `6cea579` ("Updated demo node1config.json and
node2config.json to the schema of the config files."), which rewrote both
to the plain `address`/`port`/`timeout`/`retries` schema. Don't reintroduce
that claim without re-checking the files' actual current contents.)

See `drive_start.py` for a scripted two-process pairing example (it uses
its own temp-file configs rather than these two).

## Test suite

```
uv run pytest
```

As of this writing this passes cleanly: 61 passed, 1 skipped (a
`@pytest.mark.skip(reason="TODO")` in `tests/test_server.py`). There is no
`demo/` directory in the current checkout — an earlier version of this
skill referenced pre-existing failures there; that's stale, ignore it. Any
failure under `tests/` today is a real regression worth investigating.

## Gotchas

- **Windows console + `✓`/`✗` = crash.** `cmd_validate` and `cmd_compress`
  (`src/cli/commands.py`) print literal `✓`/`✗` characters. On a plain
  Windows console (cp1252/cp437, not UTF-8), `print()` raises
  `UnicodeEncodeError`, which the CLI's own `except Exception` handler
  reports back as `"Config is invalid: 'charmap' codec can't encode..."` —
  i.e. a perfectly valid config gets reported as invalid, and a successful
  compression as failed. **Fix: always set `PYTHONIOENCODING=utf-8`** before
  invoking `p2ppred.py` (both driver scripts here do this already).
- **Connecting both sides is a race, not a rendezvous.** `Node.start_chat()`
  starts the server in a background thread and immediately runs the client
  on the calling thread with no barrier — if the peer's server hasn't
  called `listen()` yet, the client's `ConnectTimeOutError` retry loop may
  or may not catch up depending on config `retries`/`timeout`. Give it a
  few seconds (`drive_start.py` sleeps 5s) before trusting a "not
  connected" result.
- **`quit` does reach the peer.** Typing `quit` sends a `MessageType.QUIT`
  frame to the peer and updates this node's own `Connection` state.
  `ServerManager.run()` on the *receiving* side (`src/network/server.py:
  190-192`) handles that frame by printing `Peer has left the chat.` and
  calling its own `Connection.update_state()`, which (via the
  `Observer`/`Observable` wiring in `Node.__init__`) notifies that peer's
  own `ServerManager` *and* `ClientManager`. Verified live with a probe
  script: node A exited cleanly (code 0, printed `Peer has left the
  chat.`) after node B sent `quit`, without A's own stdin ever being
  touched. Note the peer's `ClientManager` loop is otherwise blocked in a
  plain `input()` call with no timeout (`message_source.py`), so if you
  see a peer *not* exiting promptly after a `quit`, that blocking read is
  the first place to look — but in practice it has not reproduced as a
  hang.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `✗ Config is invalid: 'charmap' codec can't encode character '✓'...` on a valid config | Windows console isn't UTF-8 | `PYTHONIOENCODING=utf-8 uv run python p2ppred.py validate ...` |
| `git bash` / MSYS path like `-o /tmp/out.bin` resolves to `C:/Program Files/Git/tmp/out.bin` and fails with `PermissionError` | MSYS path translation rewrites leading `/tmp` | Use a `C:/...` path (or a path under the scratch dir) for `-o`, not a bare `/tmp/...` path |
