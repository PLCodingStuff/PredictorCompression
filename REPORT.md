# Code Review Report

Review scope: new files added this session — `CLAUDE.md`, `.claude/skills/run-predictorcompression/` (`SKILL.md`, `smoke_cli.py`, `drive_start.py`), and pre-existing staged `.claude/commands/*.md` / `karpathy-modified-guidelines/SKILLS.md`.

## Findings

1. **`drive_start.py:38` — CONFIRMED.** The fixture config writes `"retries": 2`, but the pre-existing `"retires"`/`"retries"` key typo in `src/config/config.py:19` unconditionally overwrites it back to `3` (`if "retires" not in config:` is always true). The driver silently doesn't test the retry count it claims to.

2. **`smoke_cli.py:22` — PLAUSIBLE.** `subprocess.run(text=True)` decodes the child's captured stdout using the *parent's* locale encoding, not the `PYTHONIOENCODING=utf-8` set only in the child's env. On a non-Western-European Windows locale (e.g. cp936/cp949/cp950), this could raise `UnicodeDecodeError` and crash the driver itself instead of producing a clean pass/fail.

3. **`drive_start.py:36` — CONFIRMED.** `write_config(path, port, peer_port)` accepts a `peer_port` parameter that's never used in the body; all four call sites pass `None`. Dead parameter — simplify to `write_config(path, port)`.

4. **`smoke_cli.py:13` — PLAUSIBLE, low severity.** `ROOT` path computation and `ENV`/`PYTHONIOENCODING` setup are duplicated verbatim between `smoke_cli.py` and `drive_start.py` instead of a shared helper.

## Also discovered (pre-existing production bugs, documented in the new skill, not fixed — out of scope for this task)

- **`src/network/client.py:101-102`** — `ClientManager.run()` discards `prepare_to_send()`'s compressed-bytes return value and sends the raw string instead, crashing `start` with `TypeError: a bytes-like object is required, not 'str'` on the first real chat message. 100% reproducible via `drive_start.py`.
- **Windows console encoding** — `cmd_validate`/`cmd_compress` print literal `✓`/`✗`; on a non-UTF-8 console this raises `UnicodeEncodeError`, reported back as a false "invalid"/"failed" result. Workaround: `PYTHONIOENCODING=utf-8`.
- **`src/config/config.py:19`** — `"retires"` vs `"retries"` typo, already noted in `CLAUDE.md`.
