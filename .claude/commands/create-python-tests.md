# Writing Tests for PredictorCompression

## Running Tests

- **All tests**: `uv run pytest tests/ -v`
- **Coverage**: `uv run pytest tests/ --cov=src --cov-report=term-missing`
- **Specific file**: `uv run pytest tests/test_compression.py -v`
- **Specific test**: `uv run pytest tests/test_compression.py::test_empty_str -v`
- **Show print statements**: `uv run pytest -s`
- **Stop on first failure**: `uv run pytest -x`

## Critical Rules

### 1. Be Pragmatic
Write tests that add real value. If a test requires overly complex mocking or doesn't validate meaningful behavior, skip it. It's better to have no test than a brittle one that breaks with every minor change. If fighting with mocks (e.g. deep socket/threading internals), consider testing at a slightly higher level (real local sockets on ephemeral ports, as the existing tests already do) instead.

### 2. Test Behavior, Not Implementation
Focus on what the code does, not how. Don't test that specific internal methods were called or verify exact sequences of internal function calls.

### 3. No Historical Comments in Code
No `# Added in TASK-0025` or `# Testing new implementation`. Historical context belongs in git commits. Tests should be self-explanatory.

### 4. Extend Existing Tests Before Creating New Ones
When code already has test coverage, prefer modifying or extending existing tests to cover new behavior rather than creating new test functions that largely duplicate what's already there. Add cases to existing `@pytest.mark.parametrize` tables when the scenario fits.

### 5. All Tests Must Pass
New tests are done ONLY when they ALL pass 100%. Don't leave failing tests. If a test is too complex to get right, don't write it.

### 6. No Documentation Files Unless Explicitly Requested
DO NOT create summary documents, README files, or any markdown documentation files (like test coverage summaries, test reports, etc.) unless the user explicitly asks for them. Focus exclusively on creating the actual test code.

## Project Conventions

- **Test framework**: `pytest`, run via `uv run pytest` (this project uses `uv`, see `uv.lock` / `pyproject.toml`)
- **Mocking**: `unittest.mock` (`MagicMock`, `patch`) — used for message processors, connections, and CLI output objects that don't need real I/O
- **Real sockets over mocks for networking**: `test_client.py` and `test_server.py` spin up real `socket`/`threading.Thread` pairs on loopback (`127.0.0.1`) rather than mocking the socket layer, because the config/handshake/retry logic is the thing under test. Follow this pattern for `src/network/*` and `src/network_components/*` changes instead of mocking `socket.socket`.
- **Parameterized tests**: Use `@pytest.mark.parametrize` for multiple similar cases (see `tests/test_compression.py`)
- **Error assertions**: Use `pytest.raises(ExceptionType, match="...")` matching the exact message raised by validation code (see `ServerSocketConfig`/`ClientSocketConfig` validation, `Compression.payload_compression`)
- **Test organization**: `tests/` at the project root mirrors `src/`
  - `tests/test_compression.py` ↔ `src/business/compression/`
  - `tests/test_client.py` ↔ `src/network/client.py`
  - `tests/test_server.py` ↔ `src/network/server.py`
  - `tests/test_connection.py` ↔ `src/network_components/connection.py`
  - `tests/test_decrompression.py` ↔ decompression logic (`src/cli/commands.py` / compression package)
  - For a new module `src/foo/bar.py`, create `tests/test_bar.py`
- **Test naming**: `test_*` for functions, `Test*` for grouping classes (used in `test_client.py`/`test_server.py` for config classes, plain functions in `test_compression.py`)
- **No pytest markers currently in use** — this project does not use `unit`/`integration` markers or `pytest.ini_options` marker config. Don't introduce them unless the user asks; keep new tests consistent with the flat structure already in place.
- **No async code / `pytest-asyncio`** in this codebase — networking is synchronous, thread-based (`threading.Thread`, `threading.Event`). Don't add async test scaffolding unless the code under test is actually async.

## Approach

1. **Read the implementation** — understand the public API (classes/functions in `src/`), expected behavior, and error handling (custom exceptions in `src/errors/`)
2. **Check existing tests** in `tests/` for the same or a sibling module to match established patterns
3. **Determine what to test**: happy path, edge cases (empty input, boundary values like port 0 or >65535, short strings shorter than any block/key size), error handling
4. **Choose the right level**: plain unit tests with `MagicMock` for isolated logic (compression, message processors); real local socket + thread tests for networking code, matching `test_client.py` / `test_server.py`
5. **Write mostly straightforward unit tests** — each test independent, no shared mutable state, no execution-order dependencies. When a test spins up threads/sockets, always clean up (close sockets, join threads, use `Event` for synchronization) so tests don't leak resources or hang.

## Pitfalls

- Don't over-mock — keep it simple, or test at the socket/thread level like the existing networking tests
- Don't test the framework (pytest, `bitarray`, `socket`, `threading`)
- Don't hardcode ports that may collide across test runs if running in parallel; prefer ephemeral ports (`0`) or the same fixed ports already used consistently across the existing suite if that's the established pattern
- Don't depend on execution order or leftover state between tests
- Don't assert unrelated things in one test — split them
- Don't leave sockets/threads running or unjoined after a test — always tear down in the test body (no shared fixtures exist yet for this)
- Don't leave `print()` statements — use `assert` messages or remove them

## Setup Requirements

Test dependencies and pytest config already exist in `pyproject.toml` under `[dependency-groups] dev` and `[tool.pytest.ini_options]`. Only touch these if a new kind of test genuinely requires a new dependency (e.g. `pytest-cov` for coverage, if not already present) — check `uv.lock` first before assuming something is missing.

---

**BE PRACTICAL. CREATE ONLY TESTS THAT BRING REAL VALUE. DO NOT DUPLICATE TESTS.**

**DO NOT CREATE DOCUMENTATION OR SUMMARY FILES UNLESS EXPLICITLY REQUESTED.**

**Now create tests for the requested part of PredictorCompression following the above guidelines.**
