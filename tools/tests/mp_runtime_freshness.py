#!/usr/bin/env python3
"""Exercise the multiplayer smoke tools' staged-runtime freshness guard."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import mp_round_remote_smoke as smoke


def expect_stale(runtime: Path, executable: str | None, filename: str) -> None:
    try:
        smoke.verify_runtime_is_current(runtime, executable)
    except SystemExit as error:
        message = str(error)
        assert filename in message and "Re-stage it before running" in message, message
    else:
        raise AssertionError(f"stale {filename} was accepted")


def main() -> None:
    temporary_root = Path(__file__).resolve().parents[2] / ".tmp"
    temporary_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mp-runtime-freshness-", dir=temporary_root) as directory:
        root = Path(directory)
        runtime, build = root / ".install", root / "builddir"
        runtime.mkdir()
        build.mkdir()
        executable = "openQ4-client_x64.exe" if os.name == "nt" else "openQ4-client_x64"
        for parent in (runtime, build):
            (parent / "baseoq4").mkdir()
            for name in (executable, "custom-client", "baseoq4/game-mp.test"):
                path = parent / name
                path.write_bytes(b"independent test fixture")
                os.utime(path, (1000, 1000))

        with patch.object(smoke, "ROOT", root), patch.dict(os.environ, {"OPENQ4_ALLOW_STALE_RUNTIME": ""}):
            # An omitted argument, argparse's None and older callers' empty
            # string must all inspect the same executable that will be launched.
            smoke.verify_runtime_is_current(runtime)
            for name in (None, "", executable, "custom-client"):
                smoke.verify_runtime_is_current(runtime, name)
            os.utime(build / executable, (1010, 1010))
            for name in (None, "", executable):
                expect_stale(runtime, name, executable)
            smoke.verify_runtime_is_current(runtime, "custom-client")
            with patch.dict(os.environ, {"OPENQ4_ALLOW_STALE_RUNTIME": "1"}):
                smoke.verify_runtime_is_current(runtime)

            # Keep the existing timestamp tolerance and module checks intact.
            os.utime(runtime / executable, (1009, 1009))
            smoke.verify_runtime_is_current(runtime)
            os.utime(build / "baseoq4/game-mp.test", (1010, 1010))
            expect_stale(runtime, None, "game-mp.test")
            os.utime(runtime / "baseoq4/game-mp.test", (1010, 1010))
            smoke.verify_runtime_is_current(runtime)
    print("PASS: default/custom multiplayer executables, timestamp tolerance, stale modules and explicit override")


if __name__ == "__main__":
    main()
