#!/usr/bin/env python3
"""Exercise Arena pause/resume and a result with engine commands and null OpenAL.

This observes actual sound-world clocks and menu routing, not audible physical
device output. A shared isolated --profile also checks persisted result ledgers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from mp_round_remote_smoke import verify_runtime_is_current, write_script

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", type=Path, default=ROOT / ".install")
    parser.add_argument("--basepath", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--outcome", choices=("win", "loss", "draw"), default="win")
    parser.add_argument("--renderer", choices=("gl", "vulkan"), default="gl")
    parser.add_argument("--port", type=int, default=28990)
    parser.add_argument("--timeout", type=int, default=220)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("an unprivileged UDP port is required")
    runtime, output = args.runtime_dir.resolve(), args.output_dir.resolve()
    verify_runtime_is_current(runtime)
    output.mkdir(parents=True, exist_ok=False)
    profile = args.profile.resolve() if args.profile else output / "save"
    game = profile / "baseoq4"
    game.mkdir(parents=True, exist_ok=True)
    config = game / "openQ4Config.cfg"
    before = config.read_text(encoding="utf-8", errors="replace") if config.is_file() else ""
    (output / "config-before.cfg").write_text(before, encoding="utf-8")
    log = game / "logs/openq4.log"
    # Preserve a previous run's log when deliberately sharing its isolated home.
    if log.is_file():
        (output / "previous-openq4.log").write_bytes(log.read_bytes())
        log.unlink()
    for name in ("arena-pause1", "arena-pause2", "arena-result"):
        (game / "screenshots" / (name + ".tga")).unlink(missing_ok=True)
    write_script(game / "arena_bootstrap.cfg", [
        "waitMsec 1800", "campaignSelect arena", "waitMsec 1500",
        "openq4_retainedGui focus arena_start", "openq4_retainedGui menu accept 1",
        "openq4_retainedGui menu accept 0",
    ])
    script = ["waitMsec 30000", "echo ARENA_SAMPLE_live", "openq4_arenaCeremony status", "s_soundWorlds"]
    for cycle, hold in ((1, 3500), (2, 1800)):
        script += ["openq4_assertMenuActivation 5000 game", "waitMsec 500",
                   f"echo ARENA_SAMPLE_pause{cycle}a", "openq4_arenaCeremony status", "s_soundWorlds",
                   f"waitMsec {hold}", f"echo ARENA_SAMPLE_pause{cycle}b", "openq4_arenaCeremony status",
                   "s_soundWorlds", f'screenshot "screenshots/arena-pause{cycle}.tga"',
                   "openq4_retainedGui event onBack", "waitMsec 1000",
                   f"echo ARENA_SAMPLE_resume{cycle}", "openq4_arenaCeremony status", "s_soundWorlds"]
    # Victory review (6 s), scoreboard (5 s), stats (6 s), fades and the
    # browser handoff must finish before observing the archived result.
    script += [f"openq4_arenaCeremony {args.outcome}", "waitMsec 30000", "echo ARENA_SAMPLE_result",
               "s_soundWorlds", "ui_arenaProgress", "ui_arenaBest", "openq4_retainedGui report",
               'screenshot "screenshots/arena-result.tga"', "echo ARENA_SOUND_COMPLETE", "wait 5", "quit"]
    write_script(game / "arena_probe.cfg", script)
    settings = {
        "fs_basepath": str(args.basepath.resolve()), "fs_savepath": str(profile), "fs_devpath": str(profile),
        # The campaign browser belongs to SP and its Start action switches to
        # MP. Starting in MP first would reload to SP and discard the remainder
        # of this config script before it can activate the match.
        "fs_game": "baseoq4", "com_gameMode": "SP", "si_gameType": "singleplayer", "ui_autoJoin": "1",
        "ui_retained": "1", "ui_arenaSelectedTier": "0", "ui_arenaSelectedMatch": "0",
        "win_allowMultipleInstances" if os.name == "nt" else "sys_allowMultipleInstances": "1",
        "r_renderApi": args.renderer, "r_fullscreen": "0", "r_fullscreenDesktop": "0", "r_borderless": "0",
        "r_borderlessDefaultMigrated": "1", "r_hiddenWindow": "1", "r_mode": "-1", "r_customWidth": "960",
        "r_customHeight": "540", "r_windowWidth": "960", "r_windowHeight": "540", "com_maxfps": "60",
        "r_swapInterval": "0", "in_mouse": "0", "in_joystick": "0", "s_noSound": "0", "s_muteUnfocused": "0",
        "logFile": "2", "logFileName": "logs/openq4.log", "developer": "1", "net_port": str(args.port),
        "net_ip": "127.0.0.1", "net_enableIPv6": "0", "net_allowCheats": "1", "com_skipLoadingContinue": "1",
        "g_autoExecAfterMapLoad": "arena_probe.cfg", "g_autoExecAfterMapLoadDelayMs": "500",
    }
    executable = runtime / ("openQ4-client_x64.exe" if os.name == "nt" else "openQ4-client_x64")
    command = [str(executable), *(part for key, value in settings.items() for part in ("+set", key, value)),
               "+exec", "arena_bootstrap.cfg"]
    environment = dict(os.environ, ALSOFT_DRIVERS="null", ALSOFT_LOGFILE=str(output / "openal.log"), ALSOFT_LOGLEVEL="3")
    report = {"status": "fail", "outcome": args.outcome, "renderer": args.renderer, "command": command,
              "audio_backend": "OpenAL Soft null (no physical output)", "capture_method": "engine screenshot command",
              "source": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "runtime_sha256": {}, "samples": {}, "world_samples": {}, "failures": []}
    for path in (executable, runtime / "baseoq4/game-mp_x64.dll", runtime / "baseoq4/game-mp_x64.so",
                 runtime / "baseoq4/pak0.pk4", runtime / "baseoq4/pak1.pk4"):
        if path.is_file():
            with path.open("rb") as source:
                report["runtime_sha256"][path.relative_to(runtime).as_posix()] = hashlib.file_digest(source, "sha256").hexdigest()
    with (output / "console.log").open("w", encoding="utf-8") as stream:
        process = subprocess.Popen(command, cwd=runtime, stdout=stream, stderr=subprocess.STDOUT, env=environment,
                                   stdin=subprocess.DEVNULL)
        deadline = time.monotonic() + args.timeout
        try:
            while process.poll() is None:
                current = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
                if re.search(r"RETAINED_GUI_OPERATION \w+ failed|Unknown command|FATAL ERROR", current):
                    report["failures"].append("diagnostic action failed; terminated the isolated fixture")
                    process.terminate()
                    break
                if time.monotonic() >= deadline:
                    raise subprocess.TimeoutExpired(command, args.timeout)
                time.sleep(0.25)
            report["exit_code"] = process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.terminate(); process.wait(timeout=20)
            report["exit_code"] = process.returncode
            report["failures"].append("Arena runtime timed out")
    text = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
    (output / "openq4.log").write_text(text, encoding="utf-8")
    after = config.read_text(encoding="utf-8", errors="replace") if config.is_file() else ""
    (output / "config-after.cfg").write_text(after, encoding="utf-8")
    if report["exit_code"] != 0 or "ARENA_SOUND_COMPLETE" not in text:
        report["failures"].append("runtime did not finish cleanly")
    if re.search(r"ERROR:|FATAL ERROR|Unknown command|usage: openq4_|requires a retained test", text):
        report["failures"].append("engine or diagnostic command failed")
    if "OpenAL renderer: OpenAL Soft" not in text or "No Output" not in text:
        report["failures"].append("OpenAL Soft null device was not initialized")
    for marker, block in re.findall(r"ARENA_SAMPLE_(\w+)\s*\n(.*?)(?=ARENA_SAMPLE_|\Z)", text, re.S):
        rows = re.findall(r"SOUND_WORLD id=(\d+) paused=(\d+) time=(-?\d+) active=(\d+) channels=(\d+)", block)
        report["samples"][marker] = {world: dict(zip(("paused", "time", "active", "channels"), map(int, values)))
                                     for world, *values in rows}
        state = re.search(r"arena campaign: ceremony phase (\d+) state (\d+) pending (\d+) reported (\d+) outcome (\d+) paused (\d+) clock (\S+)", block)
        if state:
            report["world_samples"][marker] = {"paused": int(state[6]), "clock": state[7]}
    samples = report["samples"]
    try:
        for cycle, hold in ((1, 3500), (2, 1800)):
            first, last, resumed = (samples[f"{name}{cycle}{suffix}"] for name, suffix in (("pause", "a"), ("pause", "b"), ("resume", "")))
            assert first["1"]["paused"] == last["1"]["paused"] == 1
            assert first["1"]["time"] == last["1"]["time"]
            assert first["1"]["active"] == last["1"]["active"] == 0
            assert first["2"]["paused"] == last["2"]["paused"] == 0
            assert first["2"]["active"] == last["2"]["active"] == 1
            assert last["2"]["time"] - first["2"]["time"] >= hold - 100
            assert resumed["1"]["paused"] == 0 and resumed["1"]["active"] == 1
            assert resumed["1"]["time"] - last["1"]["time"] >= 800
            old_world, new_world = (report["world_samples"][f"pause{cycle}{suffix}"] for suffix in ("a", "b"))
            assert old_world == new_world and old_world["paused"] == 1
            assert report["world_samples"][f"resume{cycle}"]["paused"] == 0
    except (KeyError, AssertionError):
        report["failures"].append("game/menu sound clocks or route did not satisfy pause/resume")
    if samples.get("result", {}).get("2", {}).get("active") != 1:
        report["failures"].append("result browser did not restore the menu sound world")
    if not re.search(rf"arena campaign: reporting result token \d+ \({args.outcome},", text):
        report["failures"].append("authoritative result handoff missing")
    for phase, cfg in (("before", before), ("after", after)):
        report["ledger_" + phase] = {name: value for name, value in re.findall(r'^seta (ui_arena(?:Best|Progress)) "([^"]*)"', cfg, re.M)}
    if not report["ledger_after"].get("ui_arenaBest"):
        report["failures"].append("no persisted best-result ledger")
    else:
        try:
            def records(ledger):
                return {int(row.split(":")[0]): tuple(map(int, row.split(":")[1:]))
                        for row in ledger.get("ui_arenaBest", "").split()}
            old = records(report["ledger_before"]).get(0)
            new = records(report["ledger_after"])[0]
            expected = {"loss": 0, "win": 1, "draw": 2}[args.outcome]
            rank = {0: 0, 2: 1, 1: 2}
            assert len(new) == 4
            if old is None or rank[expected] > rank[old[0]]:
                assert new[0] == expected
            elif rank[expected] < rank[old[0]]:
                assert new == old
            progress = int(report["ledger_after"]["ui_arenaProgress"])
            assert bool(progress & 1) == (new[0] == 1)
            assert (new[1] > new[2] if new[0] == 1 else new[1] == new[2] if new[0] == 2 else new[1] < new[2])
        except (ValueError, KeyError, AssertionError):
            report["failures"].append("persisted first-match result/progression or best-result ordering is incorrect")
    for name in ("arena-pause1", "arena-pause2", "arena-result"):
        capture = game / "screenshots" / (name + ".tga")
        if capture.is_file():
            (output / (name + ".tga")).write_bytes(capture.read_bytes())
        else:
            report["failures"].append("missing engine capture " + name)
    report["status"] = "fail" if report["failures"] else "pass"
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "outcome", "exit_code", "samples", "ledger_before", "ledger_after", "failures")}, indent=2))
    return int(bool(report["failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
