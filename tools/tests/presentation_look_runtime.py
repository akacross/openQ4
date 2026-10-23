#!/usr/bin/env python3
"""Measure late look (HF-03) in live single-player gameplay without device input.

Runs a staged client on a retail map twice per frame cap, with in_presentationView
0 and 1, while the cheat-gated in_presentationViewProbe feeds synthetic mouse
counts through the ordinary mouse path at a constant rate. The extended
g_presentationClockCapture records, for every prepared draw, the host time, the
drawn camera yaw and the authoritative view yaw. From those it reports:

- the authoritative turn rate in each mode (input reaches the game exactly once:
  both modes must match the configured counts/second x sensitivity x m_yaw);
- input-to-draw latency: how far the drawn yaw trails the input line, in ms;
- smoothness: frame-to-frame change of the drawn yaw's residual from that line.

This is engine-side evidence on a hidden or visible window. It does not include
display scan-out, compositor or panel latency, and it is not physical input
qualification (HF-07).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import time
from pathlib import Path

from mp_round_remote_smoke import verify_runtime_is_current, write_script

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = re.compile(
    r"presentationClockSample rt=(-?\d+) t=(-?\d+) f=([-\d.]+) hrt=([-\d.]+) step=(\d+) hz=(\d+) phase=([-\d.]+)"
    r" drawYaw=([-\d.]+) authYaw=([-\d.]+) look=(\d) lookYaw=([-\d.]+) inYaw=([-\d.]+)"
    r"(?: debris=(\d+) afBlends=(\d+))?(?: listed=(\d+) afFrames=(\d+))?")


def unwrap(values):
    out, offset, previous = [], 0.0, None
    for value in values:
        if previous is not None:
            step = value - previous
            if step > 180.0:
                offset -= 360.0
            elif step < -180.0:
                offset += 360.0
        out.append(value + offset)
        previous = value
    return out


def percentile(values, fraction):
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    index = min(len(ordered) - 1, max(0, int(round(fraction * (len(ordered) - 1)))))
    return ordered[index]


def fit(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return slope, my - slope * mx


def analyse(samples, expected_rate):
    hrt = [s["hrt"] for s in samples]
    drawn = unwrap([s["drawYaw"] for s in samples])
    auth = unwrap([s["authYaw"] for s in samples])
    # The first draw of each tic sees the usercmd that was built moments before it
    # (com_asyncInput 0 builds commands as the game runs them), so those draws
    # pin the input line: authoritative yaw = input at that moment.
    first = [i for i in range(1, len(samples)) if samples[i]["t"] != samples[i - 1]["t"]]
    slope, intercept = fit([hrt[i] for i in first], [auth[i] for i in first])
    direction = 1.0 if slope >= 0 else -1.0
    # hrt is in ms, so the slope is degrees per ms and this is already ms
    latency = [((slope * hrt[i] + intercept) - drawn[i]) / slope for i in range(len(samples))]
    residual = [drawn[i] - (slope * hrt[i] + intercept) for i in range(len(samples))]
    jitter = [abs(residual[i] - residual[i - 1]) for i in range(1, len(samples))]
    intervals = [hrt[i] - hrt[i - 1] for i in range(1, len(samples))]
    result = {
        "draws": len(samples),
        "tics": len(first),
        "lookActiveFraction": sum(s["look"] for s in samples) / len(samples),
        "authoritativeRateDegPerSec": slope * 1000.0,
        "expectedRateDegPerSec": expected_rate,
        "rateError": (abs(slope * 1000.0) - abs(expected_rate)) / abs(expected_rate) if expected_rate else None,
        "latencyMs": {"mean": sum(latency) / len(latency), "p50": percentile(latency, 0.5),
                      "p95": percentile(latency, 0.95), "max": max(latency), "min": min(latency)},
        "residualStepDeg": {"p50": percentile(jitter, 0.5), "p95": percentile(jitter, 0.95), "max": max(jitter)},
        "drawIntervalMs": {"p50": percentile(intervals, 0.5), "p95": percentile(intervals, 0.95), "p99": percentile(intervals, 0.99)},
        "direction": direction,
        "latencyNote": "relative to the input line fitted at usercmd build time; both modes carry the same build-to-draw bias",
    }
    # Late look samples the generator at the draw, so the drawn yaw can be checked
    # against the input it actually saw: a constant view delta, no delay.
    active = [i for i in range(len(samples)) if samples[i]["look"]]
    if len(active) >= 16:
        sampled = unwrap([samples[i]["inYaw"] for i in active])
        drawn_active = unwrap([samples[i]["drawYaw"] for i in active])
        offsets = [d - s for d, s in zip(drawn_active, sampled)]
        median = percentile(offsets, 0.5)
        spread = [abs(o - median) for o in offsets]
        result["drawnVsSampledInputDeg"] = {"p50": percentile(spread, 0.5), "p95": percentile(spread, 0.95), "max": max(spread)}
        result["buildToDrawBiasMs"] = -result["latencyMs"]["p50"]
    return result


def parse(text):
    return [{"rt": int(m[0]), "t": int(m[1]), "f": float(m[2]), "hrt": float(m[3]), "step": int(m[4]),
             "hz": int(m[5]), "phase": float(m[6]), "drawYaw": float(m[7]), "authYaw": float(m[8]),
             "look": int(m[9]), "lookYaw": float(m[10]), "inYaw": float(m[11]),
             "debris": int(m[12] or 0), "afBlends": int(m[13] or 0),
             "listed": int(m[14] or 0), "afFrames": int(m[15] or 0)}
            for m in SAMPLE.findall(text)]


def reanalyse(output: Path, probe_rate: float) -> int:
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    for case in report["cases"]:
        log = output / case["case"] / "baseoq4/logs/openq4.log"
        samples = parse(log.read_text(encoding="utf-8", errors="replace"))
        if len(samples) >= 64:
            case.update(analyse(samples, -probe_rate * 5.0 * 0.022))
        print(json.dumps({k: case[k] for k in case if k != "errors"}), flush=True)
    (output / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    return 0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", type=Path, default=ROOT / ".install")
    parser.add_argument("--basepath", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--map", default="game/airdefense1")
    parser.add_argument("--renderer", choices=("gl", "vulkan"), default="gl")
    parser.add_argument("--fps", type=int, nargs="+", default=[240])
    parser.add_argument("--probe-rate", type=float, default=2000.0, help="synthetic mouse counts per second")
    parser.add_argument("--samples", type=int, default=512)
    parser.add_argument("--min-fps", type=float, default=30.0,
                        help="slowest draw rate the capture wait allows for (occluded or loaded machines draw slowly)")
    parser.add_argument("--viewpos", default="10200 -6800 40 0 170 0",
                        help="noclip setviewpos used by the HF-02 clock controls on airdefense1")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--scenario", nargs="+", choices=("look", "thirdperson", "death", "ragdoll", "debris"), default=["look"])
    parser.add_argument("--reanalyse", action="store_true", help="recompute report.json from an existing output directory")
    args = parser.parse_args()
    if args.reanalyse:
        return reanalyse(args.output_dir.resolve(), args.probe_rate)

    runtime, output = args.runtime_dir.resolve(), args.output_dir.resolve()
    verify_runtime_is_current(runtime)
    output.mkdir(parents=True, exist_ok=False)
    client = runtime / "openQ4-client_x64.exe"
    # sensitivity 5 x m_yaw 0.022 with no acceleration: degrees per count
    expected_rate = -args.probe_rate * 5.0 * 0.022
    report = {"runtime": str(runtime), "map": args.map, "renderer": args.renderer, "probeRate": args.probe_rate,
              "binaries": {name: sha256(runtime / name) for name in
                           ("openQ4-client_x64.exe", "baseoq4/game-sp_x64.dll", f"renderer-{args.renderer}_x64.dll")
                           if (runtime / name).is_file()},
              "cases": []}
    capture_wait = lambda fps: f"waitMsec {int(args.samples / min(fps, args.min_fps) * 1000) + 2000}"
    # name, launch cvars, cfg lines after map load
    scenarios = {
        # late look off/on while the probe turns the view
        "look": [(f"look{late}", ["in_presentationView", str(late)],
                  ["god", "notarget", "noclip", f"setviewpos {args.viewpos}", "waitMsec 500",
                   f"in_presentationViewProbe {args.probe_rate:g}", "waitMsec 1500"])
                 for late in (0, 1)],
        # HF-05: the third-person camera on the 60 Hz tic (0) or interpolated (1)
        "thirdperson": [(f"thirdperson-interp{interp}", ["in_presentationView", "0", "pm_thirdPerson", "1",
                                                          "g_presentationInterpolation", str(interp)],
                         ["god", "notarget", "noclip", f"setviewpos {args.viewpos}", "waitMsec 500",
                          f"in_presentationViewProbe {args.probe_rate:g}", "waitMsec 1500"])
                        for interp in (0, 1)],
        # HF-05: the death camera orbiting the player's falling body
        "death": [("death", ["in_presentationView", "0", "pm_thirdPersonDeath", "1"],
                   ["notarget", f"setviewpos {args.viewpos}", "waitMsec 1500",
                    f"g_presentationClockCapture {args.samples}", "testDeath"])],
        # HF-04: an articulated figure falling as a ragdoll
        "ragdoll": [("ragdoll", ["in_presentationView", "0"],
                     ["god", "notarget", "g_debugDamage 1", f"setviewpos {args.viewpos}", "waitMsec 500",
                      "spawn monster_strogg_marine name hf_ragdoll", "waitMsec 2000",
                      f"g_presentationClockCapture {args.samples}",
                      "damage hf_ragdoll 5000 damage_triggerhurt_1000"])],
        # HF-04: staged explodables throw unbound client debris (def_debris) with trails
        "debris": [("debris", ["in_presentationView", "0"],
                    ["god", "notarget", "g_debugDamage 1", f"setviewpos {args.viewpos}", "waitMsec 500",
                     "spawn launching_barrel_small name hf_barrel", "waitMsec 2000",
                     f"g_presentationClockCapture {args.samples}",
                     "damage hf_barrel 1000 damage_triggerhurt_1000"])],
    }
    for fps in args.fps:
        for scenario in args.scenario:
            for variant, cvars, lines in scenarios[scenario]:
                name = f"{fps}fps-{variant}"
                home = output / name
                game = home / "baseoq4"
                game.mkdir(parents=True)
                body = ["waitMsec 4000"] + lines
                if not any(line.startswith("g_presentationClockCapture") for line in lines):
                    body.append(f"g_presentationClockCapture {args.samples}")
                body += [capture_wait(fps), "g_presentationClockCapture 0", "in_presentationViewProbe 0", "quit"]
                write_script(game / "look_probe.cfg", body)
                extra = []
                for index in range(0, len(cvars), 2):
                    extra += ["+set", cvars[index], cvars[index + 1]]
                command = [
                    str(client),
                    "+set", "fs_basepath", str(args.basepath), "+set", "fs_savepath", str(home),
                    "+set", "fs_game", "baseoq4", "+set", "si_gameType", "singleplayer",
                    "+set", "r_renderApi", args.renderer, "+set", "ui_retained", "1",
                    "+set", "sv_cheats", "1", "+set", "developer", "1",
                    "+set", "logFile", "2", "+set", "logFileName", "logs/openq4.log",
                    "+set", "com_maxfps", str(fps), "+set", "r_swapInterval", "0",
                    "+set", "r_fullscreen", "0", "+set", "r_mode", "-1",
                    "+set", "r_customWidth", "960", "+set", "r_customHeight", "540",
                    "+set", "r_windowWidth", "960", "+set", "r_windowHeight", "540",
                    "+set", "r_borderlessDefaultMigrated", "1", "+set", "r_borderless", "0",
                    "+set", "in_mouse", "0", "+set", "in_nograb", "1",
                    "+set", "sensitivity", "5", "+set", "m_yaw", "0.022", "+set", "cl_mouseAccel", "0",
                    "+set", "m_smooth", "1", "+set", "m_filter", "0",
                ] + extra + [
                    "+set", "com_skipLoadingContinue", "1", "+set", "g_autoSkipCinematics", "1",
                    "+set", "g_autoExecAfterMapLoad", "look_probe.cfg", "+set", "g_autoExecAfterMapLoadDelayMs", "0",
                    "+map", args.map,
                ]
                (home / "launch.json").write_text(json.dumps({"cwd": str(runtime), "args": command}, indent=1), encoding="utf-8")
                started = time.monotonic()
                try:
                    exit_code = subprocess.run(command, cwd=runtime, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                               stderr=subprocess.DEVNULL, timeout=args.timeout).returncode
                except subprocess.TimeoutExpired:
                    exit_code = "timeout"
                log = game / "logs/openq4.log"
                text = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
                samples = parse(text)
                case = {"case": name, "scenario": scenario, "fps": fps, "exit": exit_code,
                        "seconds": round(time.monotonic() - started, 1), "samples": len(samples),
                        "maxDebris": max((s["debris"] for s in samples), default=0),
                        "afBlends": sum(s["afBlends"] for s in samples),
                        "afFrames": sum(s["afFrames"] for s in samples),
                        "maxListed": max((s["listed"] for s in samples), default=0)}
                if len(samples) >= 64 and scenario in ("look", "thirdperson"):
                    case.update(analyse(samples, expected_rate))
                case["errors"] = [line for line in text.splitlines()
                                  if re.search(r"\b(ERROR|FATAL)\b|Assertion failed", line)][:20]
                report["cases"].append(case)
                print(json.dumps({k: case[k] for k in case if k not in ("errors",)}, indent=None), flush=True)
    (output / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    # Scenes drawn on the authoritative clock record no samples by design (thirdperson-interp0).
    failures = [c["case"] for c in report["cases"] if c["exit"] != 0 or c["errors"] or
                (c["samples"] < 64 and not c["case"].endswith("interp0"))]
    print(f"presentation look runtime: {len(report['cases'])} cases, failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
