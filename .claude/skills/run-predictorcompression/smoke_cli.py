"""
Smoke test for the p2ppred CLI (validate / compress / decompress).

Usage:  uv run python .claude/skills/run-predictorcompression/smoke_cli.py
Run from the repo root. Exits non-zero if any check fails.
"""

import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

ENV = dict(os.environ)
ENV["PYTHONIOENCODING"] = "utf-8"  # see SKILL.md Gotchas: without this, cmd_validate/cmd_compress crash on Windows

failures = []


def run(*args):
    return subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=ROOT,
        env=ENV,
        capture_output=True,
        text=True,
    )


def check(label, cond, detail=""):
    status = "ok" if cond else "FAIL"
    print(f"[{status}] {label}")
    if not cond:
        failures.append(f"{label}: {detail}")


# --- validate ---
r = run("validate", os.path.join(ROOT, "node1config.json"))
check("validate: valid config exits 0", r.returncode == 0, r.stdout + r.stderr)
check("validate: prints checkmark", "Config is valid" in r.stdout, r.stdout)

r = run("validate", os.path.join(ROOT, "does_not_exist.json"))
check("validate: missing file exits 1", r.returncode == 1, r.stdout + r.stderr)

r = run("validate", os.path.join(ROOT, "README.md"))
check("validate: wrong suffix exits 1", r.returncode == 1, r.stdout + r.stderr)

# --- compress / decompress round trip ---
text = "the quick brown fox jumps over the lazy dog the quick brown fox"
r = run("compress", text)
check("compress: exits 0", r.returncode == 0, r.stdout + r.stderr)
hexval = r.stdout.strip()
check("compress: prints hex", len(hexval) > 0 and all(c in "0123456789abcdef" for c in hexval), hexval)

r = run("decompress", hexval)
check("decompress: round-trips to original text", r.stdout.strip() == text, repr(r.stdout))

# --- short string (<=k, k=2) passthrough: no framing, raw ascii ---
with tempfile.TemporaryDirectory() as tmp:
    out_path = os.path.join(tmp, "short.bin")
    r = run("compress", "hi", "-o", out_path)
    check("compress -o: exits 0 for short string", r.returncode == 0, r.stdout + r.stderr)
    with open(out_path, "rb") as f:
        raw = f.read()
    check("compress -o: short string passed through verbatim", raw == b"hi", raw)

if failures:
    print("\n=== FAILURES ===")
    for f in failures:
        print(f" - {f}")
    sys.exit(1)

print("\nAll CLI smoke checks passed.")
