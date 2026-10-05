#!/usr/bin/env python3
"""Trace the stock weapon glyphs (gfx/guis/hud/icons/item_<weapon>, 32x32
texels of flat white with alpha) into vector silhouettes.

The visual specification (section 14.16) redraws every item icon as vector
paths on a master 24 units high that keeps the stock frame; traces of the
stock masks are its starting point. This script derives those traces once and
commits them as data in tools/ui/glyph_trace.py, so the retained documents
never need the retail textures. Nothing from the textures themselves is
written.

    python tools/ui/trace_glyphs.py <directory holding item_<weapon>.tga> [--preview out.png]

Each glyph's alpha is traced at half coverage on an 8x supersampled field, so
its contours land within a fraction of a texel, then simplified.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "tools" / "ui" / "glyph_trace.py"
WEAPONS = ["blaster", "machinegun", "shotgun", "hyperblaster", "grenade", "nailgun", "rocket", "railgun", "lightning",
           "darkmatter", "fire", "gauntlet"]
SUPERSAMPLE = 8
TOLERANCE = 0.12        # texels
MINIMUM_AREA = 0.5      # square texels
MASTER = 24.0           # units high; the 32-texel frame maps onto it


def trace(path: Path) -> tuple[list[list[tuple[float, float]]], int]:
    with Image.open(path) as image:
        rgba = np.asarray(image.convert("RGBA")).astype(np.float32)
    size = rgba.shape[0]
    # Coverage: the alpha where the glyph is white (some stock glyphs carry
    # straight white in an opaque frame; the luminance then holds the mask).
    alpha = rgba[:, :, 3]
    mask = alpha if alpha.min() < 250 else rgba[:, :, :3].mean(axis=2)
    field = cv2.resize(mask, (size * SUPERSAMPLE, size * SUPERSAMPLE), interpolation=cv2.INTER_CUBIC)
    binary = (field >= 127.5).astype(np.uint8)
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    scale = MASTER / size
    result = []
    for contour in contours:
        approx = cv2.approxPolyDP(contour, TOLERANCE * SUPERSAMPLE, True)
        points = [((p[0][0] + 0.5) / SUPERSAMPLE, (p[0][1] + 0.5) / SUPERSAMPLE) for p in approx]
        if len(points) < 3 or abs(area(points)) < MINIMUM_AREA:
            continue
        result.append([(round(x * scale, 3), round(y * scale, 3)) for x, y in points])
    return result, size


def area(points) -> float:
    total = 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
        total += x0 * y1 - x1 * y0
    return total / 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("directory", type=Path)
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()
    lines = ['"""Weapon glyphs traced from the stock item_<weapon> masks by tools/ui/trace_glyphs.py.', "",
             "Each glyph is a list of contours (fill them even-odd) in master units: the",
             "stock 32-texel frame maps onto 24 units square. Regenerate with the script",
             'rather than editing by hand."""', "", "MASTER = 24.0", "", "GLYPHS = {"]
    previews = []
    for name in WEAPONS:
        contours, size = trace(args.directory / f"item_{name}.tga")
        lines.append(f'    "{name}": [')
        for contour in contours:
            lines.append("        [" + ", ".join(f"({x:g}, {y:g})" for x, y in contour) + "],")
        lines.append("    ],")
        previews.append((name, contours))
        print(f"{name}: {len(contours)} contours, {sum(len(c) for c in contours)} points")
    lines.append("}")
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    if args.preview:
        cell = 192
        sheet = np.full((cell * 3, cell * 4, 3), 40, np.uint8)
        for index, (name, contours) in enumerate(previews):
            x0, y0 = (index % 4) * cell, (index // 4) * cell
            canvas = np.zeros((cell, cell), np.uint8)
            polys = [np.array([[int(16 + x * 160 / MASTER), int(16 + y * 160 / MASTER)] for x, y in c], np.int32) for c in contours]
            cv2.fillPoly(canvas, polys, 255)
            # Even-odd: XOR each contour's fill.
            canvas[:] = 0
            for poly in polys:
                layer = np.zeros_like(canvas)
                cv2.fillPoly(layer, [poly], 255)
                canvas ^= layer
            sheet[y0:y0 + cell, x0:x0 + cell][canvas > 0] = (230, 230, 230)
        Image.fromarray(sheet).save(args.preview)
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
