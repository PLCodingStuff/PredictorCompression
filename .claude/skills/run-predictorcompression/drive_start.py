"""
Two-node driver for `p2ppred start` (the node-to-node chat command).

Spawns two node processes wired to each other over loopback, waits for both
sides to connect, sends one chat message, then sends "quit" to both and
prints each process's full output + exit code.

Usage:  uv run python .claude/skills/run-predictorcompression/drive_start.py

KNOWN BROKEN (see SKILL.md Gotchas): as of this writing, the side that sends
the first real chat message crashes with
    TypeError: a bytes-like object is required, not 'str'
in ClientManager.run() (src/network/client.py) — it sends the raw string
instead of the SendMessageProcessor's compressed bytes. This script still
exits 0 as a *driver* (it ran the app and captured the crash); read the
printed output to see whether the crash is still present.
"""

import json
import os
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

ENV = dict(os.environ)
ENV["PYTHONIOENCODING"] = "utf-8"
ENV["PYTHONUNBUFFERED"] = "1"

PORT_A = 15000
PORT_B = 16000


def write_config(path, port, peer_port):
    with open(path, "w") as f:
        json.dump({"port": port, "timeout": 2.0, "retries": 2}, f)


def spawn(server_json, client_json):
    return subprocess.Popen(
        [sys.executable, "main.py", "start", server_json, client_json, "-v"],
        cwd=ROOT,
        env=ENV,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


def main():
    with tempfile.TemporaryDirectory() as tmp:
        server_a, client_a = os.path.join(tmp, "serverA.json"), os.path.join(tmp, "clientA.json")
        server_b, client_b = os.path.join(tmp, "serverB.json"), os.path.join(tmp, "clientB.json")
        write_config(server_a, PORT_A, None)
        write_config(client_a, PORT_B, None)  # client's "port" key = the peer's port to dial
        write_config(server_b, PORT_B, None)
        write_config(client_b, PORT_A, None)

        p_a = spawn(server_a, client_a)
        p_b = spawn(server_b, client_b)

        time.sleep(5)  # let both sides bind + connect before sending anything

        print(">>> sending one chat message from node B's client to node A's server")
        try:
            p_b.stdin.write("hello from B\n")
            p_b.stdin.flush()
        except OSError as e:
            print(f"(B stdin write failed: {e} -- node B likely already exited)")

        time.sleep(3)

        print(">>> sending quit to both nodes")
        for p, name in ((p_a, "A"), (p_b, "B")):
            try:
                p.stdin.write("quit\n")
                p.stdin.flush()
            except OSError as e:
                print(f"({name} stdin write failed: {e})")

        out_a = _drain(p_a)
        out_b = _drain(p_b)

        print("\n===== NODE A output =====")
        print(out_a)
        print("===== NODE B output =====")
        print(out_b)
        print(f"A exit={p_a.returncode}  B exit={p_b.returncode}")


def _drain(p, timeout=10):
    try:
        out, _ = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        out, _ = p.communicate()
    return out


if __name__ == "__main__":
    main()
