#!/usr/bin/env python3
"""Trace the QUAKE 4 wordmark's letterforms from the stock q4text texture.

The stock wordmark (gfx/guis/mainmenu/q4text, 1024x256 texels) draws white
letters over an orange halo. The visual specification (ART-031, section 14.17)
rebuilds the letters as vector paths traced from the texture's white core, so
the retained title and initializing screens draw them at any resolution and
light them as vector light. This script derives those paths once; the result is
committed as data in tools/ui/wordmark_trace.py, so building the screens never
needs the retail asset. Nothing from the texture itself is written.

    python tools/ui/trace_wordmark.py <q4text image> [--preview out.png]

The image is a decoded copy of the retail texture (TGA or PNG), for example
from the Quake 4 asset source or a pak. The white core is isolated by the blue
channel, where the halo stays dim, and traced at its half-coverage edge on an
8x supersampled field, so each contour lands within a fraction of a texel.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "tools" / "ui" / "wordmark_trace.py"
SUPERSAMPLE = 8
EDGE = 150.0            # half coverage between the core's blue (~236) and the halo's (~64 at most)
TOLERANCE = 0.08        # contour simplification, in texels
MINIMUM_AREA = 4.0      # ignore specks smaller than this, in square texels


def trace(image_path: Path) -> list[dict]:
    texture = load(image_path)
    if texture.shape[:2] != (256, 1024):
        raise SystemExit(f"{image_path} is {texture.shape[1]}x{texture.shape[0]}; q4text is 1024x256")
    blue = texture[:, :, 2].astype(np.float32)
    field = cv2.resize(blue, (1024 * SUPERSAMPLE, 256 * SUPERSAMPLE), interpolation=cv2.INTER_CUBIC)
    mask = (field >= EDGE).astype(np.uint8)
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    letters: list[dict] = []
    if hierarchy is None:
        return letters
    for index, contour in enumerate(contours):
        if hierarchy[0][index][3] != -1:
            continue                                    # a hole; gathered with its outer contour
        outer = simplify(contour)
        if area(outer) < MINIMUM_AREA:
            continue
        holes = []
        child = hierarchy[0][index][2]
        while child != -1:
            hole = simplify(contours[child])
            if area(hole) >= MINIMUM_AREA:
                holes.append(hole)
            child = hierarchy[0][child][0]
        letters.append({"outer": outer, "holes": holes})
    letters.sort(key=lambda letter: min(x for x, _ in letter["outer"]))
    return letters


def load(image_path: Path) -> np.ndarray:
    """The texture as RGB rows (Pillow reads TGA, which OpenCV does not)."""
    with Image.open(image_path) as image:
        return np.asarray(image.convert("RGB"))


def simplify(contour) -> list[tuple[float, float]]:
    # Pixel centers sit at +0.5 in the supersampled grid; map back to texel space.
    approx = cv2.approxPolyDP(contour, TOLERANCE * SUPERSAMPLE, True)
    return [(round((p[0][0] + 0.5) / SUPERSAMPLE, 3), round((p[0][1] + 0.5) / SUPERSAMPLE, 3)) for p in approx]


def area(points) -> float:
    total = 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
        total += x0 * y1 - x1 * y0
    return abs(total) / 2


def write(letters: list[dict]) -> None:
    lines = ['"""QUAKE 4 letterforms traced from q4text\'s white core by tools/ui/trace_wordmark.py.', "",
             "Texel coordinates in the 1024x256 texture; each letter is an outer contour",
             'and its counters. Regenerate with the script rather than editing by hand."""', "",
             "LETTERS = ["]
    for letter in letters:
        lines.append("    {")
        lines.append(f"        \"outer\": {format_points(letter['outer'])},")
        lines.append("        \"holes\": [" + ", ".join(format_points(hole) for hole in letter["holes"]) + "],")
        lines.append("    },")
    lines.append("]")
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def format_points(points) -> str:
    return "[" + ", ".join(f"({x:g}, {y:g})" for x, y in points) + "]"


def preview(letters: list[dict], output: Path, image_path: Path) -> None:
    texture = cv2.cvtColor(load(image_path), cv2.COLOR_RGB2BGR)
    scale = 4
    canvas = cv2.resize(texture, (1024 * scale, 256 * scale), interpolation=cv2.INTER_NEAREST)
    for letter in letters:
        for contour in [letter["outer"], *letter["holes"]]:
            points = np.array([[int(x * scale), int(y * scale)] for x, y in contour], dtype=np.int32)
            cv2.polylines(canvas, [points], True, (0, 255, 0), 1, cv2.LINE_AA)
    cv2.imwrite(str(output), canvas)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("image", type=Path)
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()
    letters = trace(args.image)
    write(letters)
    points = sum(len(letter["outer"]) + sum(len(h) for h in letter["holes"]) for letter in letters)
    print(f"wrote {OUTPUT.relative_to(ROOT)}: {len(letters)} letters, {points} points")
    if args.preview:
        preview(letters, args.preview, args.image)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
