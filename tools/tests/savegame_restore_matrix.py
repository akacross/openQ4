#!/usr/bin/env python3
"""Restore existing saves with a staged client and classify each outcome.

This is an opt-in runtime test: it needs the retail Quake 4 PK4s and real saves.
It answers the question the contract tests cannot: does *this* build restore a
save written by *another* build? For each input save it copies the slot into an
isolated savepath, launches the client with ``+loadGame``, and requires one of:

* ``restored`` -- the map was rebuilt from the save, an after-load config ran,
  and no ``ERROR:`` was printed; or
* ``rejected`` -- with ``--expect-reject``, the payload preflight refused the
  save and the map was never torn down for it.

Each input file is hashed before and after its run; a changed original is a
failure whatever the outcome. ``--restamp-build N`` adds a variant whose only
difference is the payload build number (CRC recomputed). Build numbers are
commit counts, so a source archive stamps 0 and a shallow clone 1; a payload
layout that is not build-dependent must restore identically for any value.

Saves are player data. Point this at copies or designated fixtures; the harness
never writes to the input paths.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shutil
import struct
import subprocess
import sys
import time
import zlib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
LOG_NAME = "savegame-restore-matrix.log"
AFTER_LOAD_CFG = "savegame_restore_matrix/after_load.cfg"
ACTIVE_MARKER = "OPENQ4_RESTORE_MATRIX_ACTIVE"
DONE_MARKER = "OPENQ4_RESTORE_MATRIX_DONE"
PAYLOAD_MAGIC = b"OQ4S"
INTEGRITY_MAGIC = int.from_bytes(b"OQ4I", "little")

ERROR_PATTERN = re.compile(r"^(?:\^[0-9])?ERROR:.*$", re.MULTILINE)
SIGNAL_PATTERN = re.compile(r"signal caught|segmentation fault|Sys_Error:", re.IGNORECASE)
RESTORE_STARTED = re.compile(r"Game Map Init SaveGame")
PREFLIGHT_REJECTED = re.compile(r"WARNING:.*Savegame '[^']+' (?:has|was|wire|is|failed)[^\r\n]*")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_stamp(data: bytes) -> dict[str, Any]:
    """Return the openQ4 payload stamp, or an empty dict for unstamped payloads."""
    offset = data.find(PAYLOAD_MAGIC)
    if offset < 0 or offset + 16 > len(data):
        return {}
    version, build = struct.unpack_from("<ii", data, offset + 4)
    cursor = offset + 12
    (length,) = struct.unpack_from("<i", data, cursor)
    source = data[cursor + 4 : cursor + 4 + length].decode("latin-1")
    cursor += 4 + length
    (file_count,) = struct.unpack_from("<i", data, cursor)
    cursor += 4
    (length,) = struct.unpack_from("<i", data, cursor)
    abi = data[cursor + 4 : cursor + 4 + length].decode("latin-1")
    return {
        "payloadOffset": offset,
        "version": version,
        "build": build,
        "source": source,
        "sourceFileCount": file_count,
        "wireAbi": abi,
    }


def restamp_build(data: bytes, build: int) -> bytes:
    """Rewrite only the payload build number and refresh the integrity CRC."""
    stamp = read_stamp(data)
    if not stamp or stamp["version"] < 3:
        raise ValueError("only stamped v3+ payloads carry a build number and integrity trailer")
    patched = bytearray(data)
    struct.pack_into("<i", patched, stamp["payloadOffset"] + 8, build)
    marker, version, protected_length, _ = struct.unpack_from("<4I", patched, len(patched) - 16)
    if marker != INTEGRITY_MAGIC or version != 1 or protected_length != len(patched) - 16:
        raise ValueError("save has no recognised integrity trailer")
    struct.pack_into("<I", patched, len(patched) - 4, zlib.crc32(bytes(patched[:protected_length])) & 0xFFFFFFFF)
    return bytes(patched)


def client_path(install_root: Path) -> Path:
    machine = platform.machine().lower()
    arch = "arm64" if machine in ("arm64", "aarch64") else "x64"
    suffix = ".exe" if sys.platform == "win32" else ""
    return install_root / f"openQ4-client_{arch}{suffix}"


def stage_slot(source: Path, home: Path, slot: str, payload: bytes | None) -> None:
    savegames = home / "baseoq4" / "savegames"
    savegames.mkdir(parents=True, exist_ok=True)
    for extension in (".txt", ".tga"):
        companion = source.with_suffix(extension)
        if companion.is_file():
            shutil.copyfile(companion, savegames / f"{slot}{extension}")
    target = savegames / f"{slot}.save"
    if payload is None:
        shutil.copyfile(source, target)
    else:
        target.write_bytes(payload)


def write_after_load_cfg(home: Path, settle_frames: int) -> None:
    cfg = home / "baseoq4" / AFTER_LOAD_CFG
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(
        "\n".join(
            (
                f"echo {ACTIVE_MARKER}",
                f"wait {max(1, settle_frames)}",
                f"echo {DONE_MARKER}",
                "quit",
                "",
            )
        ),
        encoding="utf-8",
    )


def runtime_text(home: Path, stdout_path: Path) -> str:
    texts = []
    for candidate in (home / "baseoq4" / "logs" / LOG_NAME, stdout_path):
        if candidate.is_file():
            texts.append(candidate.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(texts)


def run_case(args: argparse.Namespace, client: Path, source: Path, label: str, payload: bytes | None) -> dict[str, Any]:
    run_dir = args.output_root / label
    if run_dir.exists():
        shutil.rmtree(run_dir)
    home = run_dir / "home"
    slot = "restore_matrix"
    stage_slot(source, home, slot, payload)
    write_after_load_cfg(home, args.settle_frames)
    staged = home / "baseoq4" / "savegames" / f"{slot}.save"
    stamp = read_stamp(staged.read_bytes())

    command = [str(client)]
    for name, value in (
        ("sys_allowMultipleInstances", "1"),
        ("logFile", "2"),
        ("logFileName", f"logs/{LOG_NAME}"),
        ("fs_homepath", home),
        ("fs_savepath", home),
        ("r_fullscreen", "0"),
        ("r_mode", "3"),
        ("r_renderApi", args.render_api),
        ("com_skipLogoVideos", "1"),
        ("com_skipLoadingContinue", "1"),
        ("com_loadingContinueAutoAdvance", "1"),
        ("g_autoExecAfterMapLoad", AFTER_LOAD_CFG),
        ("g_autoExecAfterMapLoadDelayMs", "1000"),
    ):
        command += ["+set", name, str(value)]
    for name, value in args.set:
        command += ["+set", name, value]
    command += ["+loadGame", slot]

    stdout_path = run_dir / "stdout.txt"
    started = time.monotonic()
    timed_out = False
    with stdout_path.open("w", encoding="utf-8", errors="replace") as stdout:
        process = subprocess.Popen(
            command,
            cwd=client.parent,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=subprocess.STDOUT,
        )
        deadline = started + args.timeout
        while process.poll() is None and time.monotonic() < deadline:
            text = runtime_text(home, stdout_path)
            # Either outcome is final: an error ends the restore, and a preflight
            # rejection leaves the client at the menu with nothing left to load.
            if ERROR_PATTERN.search(text) or SIGNAL_PATTERN.search(text) or PREFLIGHT_REJECTED.search(text):
                break
            time.sleep(0.5)
        if process.poll() is None:
            timed_out = time.monotonic() >= deadline
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=15)

    text = runtime_text(home, stdout_path)
    errors = ERROR_PATTERN.findall(text) + SIGNAL_PATTERN.findall(text)
    rejections = PREFLIGHT_REJECTED.findall(text)
    restore_started = RESTORE_STARTED.search(text) is not None
    if args.expect_reject:
        passed = bool(rejections) and not restore_started and not errors
        outcome = "rejected" if passed else ("torn-down" if restore_started else "not-rejected")
    else:
        passed = restore_started and DONE_MARKER in text and not errors and not rejections
        outcome = "restored" if passed else ("timeout" if timed_out else "failed")
    return {
        "label": label,
        "source": str(source),
        "stamp": stamp,
        "outcome": outcome,
        "passed": passed,
        "restoreStarted": restore_started,
        "errors": errors[:5],
        "preflightRejections": rejections[:5],
        "seconds": round(time.monotonic() - started, 1),
        "runDir": str(run_dir),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("saves", nargs="+", type=Path, help=".save files or directories of them (read only).")
    parser.add_argument("--install-root", type=Path, default=ROOT / ".install", help="Staged package root.")
    parser.add_argument("--output-root", type=Path, default=ROOT / ".tmp" / "savegame-restore-matrix")
    parser.add_argument("--render-api", default="gl", help="r_renderApi for the client (default gl).")
    parser.add_argument("--timeout", type=float, default=240.0, help="Seconds allowed per save.")
    parser.add_argument("--settle-frames", type=int, default=60, help="Frames to run after the restore.")
    parser.add_argument("--restamp-build", type=int, action="append", default=[],
                        help="Also load a copy whose payload build number is rewritten to N.")
    parser.add_argument("--set", nargs=2, action="append", default=[], metavar=("CVAR", "VALUE"),
                        help="Extra client cvar, for example --set ui_retained 1.")
    parser.add_argument("--expect-reject", action="store_true",
                        help="Pass only when preflight refuses every save before map teardown.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    args.output_root = args.output_root.resolve()
    client = client_path(args.install_root.resolve())
    if not client.is_file():
        raise SystemExit(f"client not found: {client}")

    sources: list[Path] = []
    for entry in args.saves:
        sources += sorted(entry.glob("*.save")) if entry.is_dir() else [entry]
    if not sources:
        raise SystemExit("no .save files given")

    before = {source: sha256_file(source) for source in sources}
    results = []
    for source in sources:
        variants: list[tuple[str, bytes | None]] = [(source.stem, None)]
        for build in args.restamp_build:
            variants.append((f"{source.stem}-build{build}", restamp_build(source.read_bytes(), build)))
        for label, payload in variants:
            result = run_case(args, client, source, label, payload)
            results.append(result)
            stamp = result["stamp"]
            print(f"{'PASS' if result['passed'] else 'FAIL'} {label}: {result['outcome']} "
                  f"(v{stamp.get('version', '?')} build {stamp.get('build', '?')} {stamp.get('wireAbi', 'unstamped')})"
                  + (f" -- {result['errors'][0]}" if result["errors"] else ""))

    modified = [str(source) for source in sources if sha256_file(source) != before[source]]
    report = {"client": str(client), "results": results, "modifiedInputs": modified}
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if modified:
        print("FAIL input saves were modified: " + ", ".join(modified))
    failed = [result for result in results if not result["passed"]]
    print(f"savegame_restore_matrix: {len(results) - len(failed)}/{len(results)} passed; inputs unchanged: {not modified}")
    return 1 if failed or modified else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
