"""The retained weapon wheel (docs/dev/ui-visual-design.md section 14.6).

Built by tools/ui/build_retained_screens.py with the other retained screens.
The wheel is an openQ4 addition for controller and touch play: a held button
opens a ring of every weapon of the game mode in strip order, clockwise from
the top, around a hub that names the selection. This is the Marine wheel of a
single-player game (eleven positions), in the HUD family's construction:
plates with 2 dp corners and constant 6 dp gaps, the weapon glyphs of section
14.16 (traced into tools/ui/glyph_trace.py), the weapon number and reserve, a
curved eight-cell ammunition gauge in the weapon colour code, a tick bezel, and
a hub built from the machinegun scope's rings and compass over a signal screen.

The game owns the state through the wheel's GUI (idPlayer, src/game/Player.cpp):
wheel_selected and wheel_previous are slot indices; per slot, wheel_owned_<i>,
wheel_empty_<i> (no ammunition), wheel_fill_<i> (the reserve's share of the
weapon's maximum, 0..1), wheel_count_<i> (the reserve; negative hides it) and
wheel_key_<i> (the slot's weapon key); wheel_name and wheel_ammo fill the
center. The open, select and close events play the Marine transmission
(section 14.6 Transitions); reduced motion keeps only short opacity changes.
"""
from __future__ import annotations

import math

from build_retained_screens import (Document, absolute, colour, group, keyword, length, linear, number, rgb, solid, track,
                                    transform, typeface, vector)
from glyph_trace import GLYPHS, MASTER

SLOTS = ["blaster", "machinegun", "shotgun", "hyperblaster", "grenade", "nailgun", "rocket", "railgun", "lightning",
         "darkmatter", "fire"]
# Appendix B.4: the weapon colour code; the blaster carries no ammunition.
CODES = [None, (1, 1, 0), (1, 0.5, 0), (0, 0.45, 1), (0.2, 0.56, 0.07), (0.6, 0.8, 0.8), (1, 0.2, 0), (0, 1, 0),
         (1, 1, 0.73), (0.77, 0, 1), (1, 0.75, 0.25)]
COUNT = len(SLOTS)
PITCH = 360.0 / COUNT
BOX = 300.0                 # half the side of the wheel's square, dp
INNER, OUTER = 104.0, 232.0
GAP = 6.0                   # constant segment gap, dp
CORNER = 2.0                # plate corner radius, dp
EXTEND = 8.0                # the selection moves outward, dp
BAND = (218.0, 232.0)       # the ammunition gauge along the outer edge
CELLS = 8
NUMBER_R, GLYPH_R, RESERVE_R = 116.0, 152.0, 190.0
GLYPH_DP = 32.0
HUB, HUB_RING = 86.0, 80.0
COMPASS_R = 93.0
BACKING = 280.0
OLIVE_TICK = "#B3D06E"
ICON = "#A8A360"
SELECTED = "#FF8000"
RING = "#B2CC80"
LIGHT = "#616F26"
NAME = "#B0C891"
NO_AMMO = "#FF2020"
EASE_OUT = [0.16, 1, 0.3, 1]


def polar(r: float, degrees: float) -> tuple[float, float]:
    t = math.radians(degrees)
    return (BOX + r * math.sin(t), BOX - r * math.cos(t))


class P:
    """Path commands in the wheel square's dp space (origin at its corner)."""

    def __init__(self, origin=(0.0, 0.0)):
        self.origin = origin
        self.commands: list[dict] = []

    def _point(self, p):
        return [round(p[0] - self.origin[0], 3), round(p[1] - self.origin[1], 3)]

    def _add(self, op, *points):
        entry = {"id": f"c{len(self.commands)}", "op": op}
        if points:
            entry["points"] = [self._point(p) for p in points]
        self.commands.append(entry)
        return self

    def move(self, p):
        return self._add("move", p)

    def line(self, p):
        return self._add("line", p)

    def quad(self, c, p):
        return self._add("quadratic", c, p)

    def close(self):
        return self._add("close")

    def arc(self, r: float, a0: float, a1: float):
        count = max(1, math.ceil(abs(a1 - a0) / 45.0))
        step = (a1 - a0) / count
        handle = 4.0 / 3.0 * math.tan(math.radians(abs(step)) / 4.0) * r * (1 if step > 0 else -1)
        for index in range(count):
            t0, t1 = math.radians(a0 + step * index), math.radians(a0 + step * (index + 1))
            p0, p1 = polar(r, a0 + step * index), polar(r, a0 + step * (index + 1))
            c1 = (p0[0] + handle * math.cos(t0), p0[1] + handle * math.sin(t0))
            c2 = (p1[0] - handle * math.cos(t1), p1[1] - handle * math.sin(t1))
            self._add("cubic", c1, c2, p1)
        return self

    def circle(self, r: float):
        self.move(polar(r, 0))
        return self.arc(r, 0, 360).close()

    def build(self, ident, *, fill=None, stroke=None, blend=None, rule=None, antialias=True):
        result = {"id": ident, "commands": self.commands}
        if rule:
            result["fillRule"] = rule
        if not antialias:
            result["antialias"] = False
        if fill is not None:
            result["fill"] = fill
        if stroke is not None:
            result["stroke"] = stroke
        if blend:
            result["blend"] = blend
        return result


def tone(hex_colour: str, alpha: float = 1.0) -> dict:
    return solid(rgb(hex_colour, alpha))


def code_tone(code, alpha: float) -> dict:
    return solid([code[0], code[1], code[2], alpha])


def stroke(paint: dict, width: float) -> dict:
    return {"paint": paint, "widthDp": round(width, 3), "minimumPixels": 1, "join": "round", "cap": "butt"}


# ------------------------------------------------------------------ segments

def side_angle(r: float, boundary: float, inward: float) -> float:
    """The angle at radius r of the line GAP/2 from the radial boundary, so a
    gap keeps its width from the inner edge to the outer."""
    return boundary + inward * math.degrees(math.asin((GAP / 2) / r))


def segment_path(p: P, index: int, r0: float, r1: float) -> P:
    """An annular segment with constant-width gaps and rounded corners."""
    a, b = index * PITCH - PITCH / 2, index * PITCH + PITCH / 2
    corners = [(r1, side_angle(r1, a, 1)), (r1, side_angle(r1, b, -1)), (r0, side_angle(r0, b, -1)), (r0, side_angle(r0, a, 1))]
    o0, o1 = corners[0][1], corners[1][1]
    i1, i0 = corners[2][1], corners[3][1]
    # Fillet each corner with a quadratic through it, CORNER along both edges.
    def along_arc(r, angle, toward):
        return polar(r, angle + toward * math.degrees(CORNER / r))
    # Outer edge, leading corner to trailing corner (clockwise).
    lead_out = polar(r1, o0)
    p.move(along_arc(r1, o0, 1))
    p.arc(r1, o0 + math.degrees(CORNER / r1), o1 - math.degrees(CORNER / r1))
    trail_out = polar(r1, o1)
    p.quad(trail_out, line_point(trail_out, polar(r0, i1), CORNER))
    trail_in = polar(r0, i1)
    p.line(line_point(trail_in, trail_out, CORNER))
    p.quad(trail_in, along_arc(r0, i1, -1))
    p.arc(r0, i1 - math.degrees(CORNER / r0), i0 + math.degrees(CORNER / r0))
    lead_in = polar(r0, i0)
    p.quad(lead_in, line_point(lead_in, lead_out, CORNER))
    p.line(line_point(lead_out, lead_in, CORNER))
    p.quad(lead_out, along_arc(r1, o0, 1))
    return p.close()


def line_point(start, end, distance: float):
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    f = distance / length
    return (start[0] + (end[0] - start[0]) * f, start[1] + (end[1] - start[1]) * f)


def band_cell(p: P, index: int, cell: int, r0: float, r1: float) -> P:
    """One of the gauge's eight cells, with a 1 dp divider gap either side."""
    a, b = index * PITCH - PITCH / 2, index * PITCH + PITCH / 2
    start, end = side_angle(r1, a, 1), side_angle(r1, b, -1)
    span = (end - start) / CELLS
    divider = math.degrees(0.5 / ((r0 + r1) / 2))
    c0, c1 = start + span * cell + divider, start + span * (cell + 1) - divider
    p.move(polar(r1, c0)).arc(r1, c0, c1).line(polar(r0, c1)).arc(r0, c1, c0)
    return p.close()


def band_track(p: P, index: int, r0: float, r1: float) -> P:
    a, b = index * PITCH - PITCH / 2, index * PITCH + PITCH / 2
    o0, o1 = side_angle(r1, a, 1), side_angle(r1, b, -1)
    i0, i1 = side_angle(r0, a, 1), side_angle(r0, b, -1)
    p.move(polar(r1, o0)).arc(r1, o0, o1).line(polar(r0, i1)).arc(r0, i1, i0)
    return p.close()


def glyph_paths(name: str, centre, size: float, tint: dict, ident: str) -> dict:
    """The weapon glyph, upright, centred on centre (wheel dp), size dp high."""
    scale = size / MASTER
    x0, y0 = centre[0] - size / 2, centre[1] - size / 2
    p = P()
    for contour in GLYPHS[name]:
        p.move((x0 + contour[0][0] * scale, y0 + contour[0][1] * scale))
        for x, y in contour[1:]:
            p.line((x0 + x * scale, y0 + y * scale))
        p.close()
    return p.build(ident, fill=tint, rule="evenodd")


def prohibition(centre, size: float, ident: str) -> list:
    """The red prohibition sign over a glyph without ammunition."""
    r = size * 0.42
    width = size * 0.09
    ring = P()
    ring.move((centre[0], centre[1] - r))
    count = 8
    for k in range(1, count + 1):
        t0, t1 = math.radians(360 * (k - 1) / count), math.radians(360 * k / count)
        h = 4.0 / 3.0 * math.tan((t1 - t0) / 4.0) * r
        p0 = (centre[0] + r * math.sin(t0), centre[1] - r * math.cos(t0))
        p1 = (centre[0] + r * math.sin(t1), centre[1] - r * math.cos(t1))
        ring._add("cubic", (p0[0] + h * math.cos(t0), p0[1] + h * math.sin(t0)), (p1[0] - h * math.cos(t1), p1[1] - h * math.sin(t1)), p1)
    ring.close()
    slash = P()
    d = r / math.sqrt(2)
    slash.move((centre[0] - d, centre[1] - d)).line((centre[0] + d, centre[1] + d))
    return [ring.build(f"{ident}-ring", stroke=stroke(tone(NO_AMMO, 0.9), width)),
            slash.build(f"{ident}-slash", stroke=stroke(tone(NO_AMMO, 0.9), width))]


def text_box(ident: str, centre, width: float, height: float, face: str, size: float, tint, value_state: str | None = None,
             number_state: str | None = None, extra=None) -> dict:
    props = {**absolute(left=round(centre[0] - width / 2, 3), top=round(centre[1] - height / 2, 3), width=width, height=height),
             **typeface(face, size, height, tint), "text-align": keyword("center"), "white-space": keyword("nowrap"),
             "opacity": number(1)}
    if extra:
        props.update(extra)
    return {"id": ident, "type": "text", "properties": {"text": {"type": "text", "value": "#str_104343"}, **props}}


# ------------------------------------------------------------------- the wheel

def slot_nodes(doc: Document, index: int) -> dict:
    name, code = SLOTS[index], CODES[index]
    middle = index * PITCH
    selected = {"op": "==", "args": [{"state": "wheel_selected"}, index]}
    owned = {"state": f"wheel_owned_{index}"}
    empty = {"state": f"wheel_empty_{index}"}
    children = []
    plate = vector(f"slot-{index}-plate", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "opacity": number(0.5)},
                   [segment_path(P(), index, INNER, OUTER).build("plate", fill=tone("#000000"))])
    doc.bind(f"slot-{index}-plate.opacity", f"slot-{index}-plate", "opacity",
             {"op": "select", "args": [owned, {"op": "select", "args": [selected, 0.70, 0.50]}, 0.0]})
    outline = vector(f"slot-{index}-outline", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "opacity": number(0)},
                     [segment_path(P(), index, INNER, OUTER).build("outline", stroke=stroke(tone("#FFFFFF", 0.15), 1.2))])
    doc.bind(f"slot-{index}-outline.opacity", f"slot-{index}-outline", "opacity", {"op": "select", "args": [owned, 0.0, 1.0]})
    light = vector(f"slot-{index}-light", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "opacity": number(0)},
                   [segment_path(P(), index, INNER, OUTER).build("light", fill=tone(LIGHT, 0.35), blend="additive")])
    ring = vector(f"slot-{index}-ring", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "opacity": number(0)},
                  [segment_path(P(), index, INNER, OUTER).build("ring", stroke=stroke(tone(RING), 2.4))])
    for node in (light, ring):
        doc.bind(f"{node['id']}.opacity", node["id"], "opacity", {"op": "select", "args": [selected, 1.0, 0.0]})
    children += [plate, outline, light]
    # The ammunition gauge: a track and eight cells filled in proportion to
    # the reserve (wheel_fill_<i>), each with its bevel; the blaster has none.
    if code is not None:
        band = [band_track(P(), index, *BAND).build("track", fill=code_tone(code, 0.20))]
        cells = []
        for cell in range(CELLS):
            ident = f"slot-{index}-cell-{cell}"
            cells.append(vector(ident, {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "opacity": number(0)}, [
                band_cell(P(), index, cell, BAND[0], BAND[1]).build("fill", fill=code_tone(code, 0.35)),
                band_cell(P(), index, cell, BAND[1] - 1.5, BAND[1]).build("bevel", fill=code_tone(code, 0.45))]))
            doc.bind(f"{ident}.opacity", ident, "opacity", {"op": "select", "args": [owned, {"op": "clamp", "args": [
                {"op": "-", "args": [{"op": "*", "args": [{"state": f"wheel_fill_{index}"}, CELLS]}, cell]}, 0, 1]}, 0.0]})
        children.append(vector(f"slot-{index}-band", absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), band))
        children += cells
    # The glyph, dim or selected, the no-ammunition sign, number and reserve.
    centre = polar(GLYPH_R, middle)
    dim = vector(f"slot-{index}-glyph", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "opacity": number(1)},
                 [glyph_paths(name, centre, GLYPH_DP, tone(ICON, 0.6), "glyph")])
    doc.bind(f"slot-{index}-glyph.opacity", f"slot-{index}-glyph", "opacity",
             {"op": "select", "args": [{"op": "&&", "args": [owned, {"op": "!", "args": [selected]}]}, 1.0, 0.0]})
    hot = vector(f"slot-{index}-glyph-selected", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "opacity": number(0)},
                 [glyph_paths(name, centre, GLYPH_DP, tone(SELECTED), "glyph")])
    doc.bind(f"slot-{index}-glyph-selected.opacity", f"slot-{index}-glyph-selected", "opacity",
             {"op": "select", "args": [selected, 1.0, 0.0]})
    sign = vector(f"slot-{index}-noammo", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "opacity": number(0)},
                  prohibition(centre, GLYPH_DP, "sign"))
    doc.bind(f"slot-{index}-noammo.opacity", f"slot-{index}-noammo", "opacity",
             {"op": "select", "args": [{"op": "&&", "args": [owned, empty]}, 1.0, 0.0]})
    key = text_box(f"slot-{index}-key", polar(NUMBER_R, middle), 40, 14, "lowpixel", 12, rgb(NAME, 0.8))
    doc.bind(f"slot-{index}-key.text", f"slot-{index}-key", "text", {"state": f"wheel_key_{index}"})
    doc.bind(f"slot-{index}-key.opacity", f"slot-{index}-key", "opacity", {"op": "select", "args": [owned, 1.0, 0.25]})
    reserve = text_box(f"slot-{index}-reserve", polar(RESERVE_R, middle), 60, 20, "chain", 17, rgb(NAME))
    doc.bind(f"slot-{index}-reserve.text", f"slot-{index}-reserve", "text",
             {"op": "numberText", "args": [{"op": "max", "args": [{"state": f"wheel_count_{index}"}, 0]}], "decimals": 0})
    doc.bind(f"slot-{index}-reserve.opacity", f"slot-{index}-reserve", "opacity", {"op": "select", "args": [
        {"op": "&&", "args": [owned, {"op": ">=", "args": [{"state": f"wheel_count_{index}"}, 0]}]}, 1.0, 0.0]})
    children += [dim, hot, sign, ring, key, reserve]
    # The selection moves outward along its own direction.
    dx, dy = EXTEND * math.sin(math.radians(middle)), -EXTEND * math.cos(math.radians(middle))
    # The segment deploys from 90% about the wheel's center; its own transform
    # carries the selection's outward move.
    deploy = group(f"slot-{index}-deploy", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "transform": transform()},
                   children)
    slot = group(f"slot-{index}", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "transform": transform(),
                                   "opacity": number(1)}, [deploy])
    doc.bind(f"slot-{index}.transform", f"slot-{index}", "transform", [
        {"op": "select", "args": [selected, round(dx, 3), 0.0]}, {"op": "select", "args": [selected, round(dy, 3), 0.0]}, 1, 1, 0])
    return slot


def previous_notch(doc: Document) -> dict:
    """A notch on the inner edge marks the weapon a tap returns to: a small
    wedge, turned to the previous slot."""
    p = P()
    tip = polar(INNER - 1, 0)
    p.move((tip[0] - 5, tip[1] - 7)).line((tip[0] + 5, tip[1] - 7)).line(tip).close()
    node = vector("previous", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "transform": rotation(0),
                               "opacity": number(0)}, [p.build("notch", fill=tone(RING, 0.85))])
    doc.bind("previous.transform", "previous", "transform",
             [0, 0, 1, 1, {"op": "*", "args": [{"state": "wheel_previous"}, round(PITCH, 6)]}])
    doc.bind("previous.opacity", "previous", "opacity",
             {"op": "select", "args": [{"op": ">=", "args": [{"state": "wheel_previous"}, 0]}, 1.0, 0.0]})
    return node


def rotation(degrees: float) -> dict:
    return {"type": "transform", "unit": "dp", "value": [0, 0, 1, 1, round(degrees, 3)]}


def bezel() -> dict:
    paths = []
    fine = P()
    for k in range(120):
        a = k * 3.0
        fine.move(polar(247, a)).line(polar(252, a))
    paths.append(fine.build("fine", stroke={"paint": tone(OLIVE_TICK, 0.18), "widthDp": 1, "minimumPixels": 1, "join": "miter",
                                            "cap": "butt"}))
    long = P()
    for k in range(COUNT):
        a = k * PITCH + PITCH / 2
        long.move(polar(242, a)).line(polar(253, a))
    paths.append(long.build("long", stroke={"paint": tone(OLIVE_TICK, 0.5), "widthDp": 1.5, "minimumPixels": 1, "join": "miter",
                                            "cap": "butt"}))
    return vector("bezel", absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), paths)


def backing() -> dict:
    """A black radial wash at 0.35 out to BACKING dp; no blur. Flat to 230 dp,
    then easing out in steps."""
    paths = [P().circle(230).build("core", fill=tone("#000000", 0.35), antialias=False)]
    r, k = 230.0, 0
    while r < BACKING - 1e-6:
        outer = min(BACKING, r + 5)
        t = ((r + outer) / 2 - 230) / (BACKING - 230)
        alpha = 0.35 * 0.5 * (1 + math.cos(math.pi * t))
        ring = P().circle(outer)
        ring.circle(r)
        paths.append(ring.build(f"wash-{k}", fill=tone("#000000", alpha), rule="evenodd", antialias=False))
        r, k = outer, k + 1
    return vector("backing", absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), paths)


def hub(doc: Document) -> list:
    disc = vector("hub-disc", absolute(left=0, top=0, width=2 * BOX, height=2 * BOX),
                  [P().circle(HUB).build("disc", fill=tone("#000000", 0.55))])
    # The signal screen: torn video bands at their 0.06 rest and additive
    # scanlines at 0.11 rolling down the disc, clipped to it.
    lines = P()
    for k in range(-60, 61):
        y = BOX + k * 3.0
        lines.move((BOX - HUB, y)).line((BOX + HUB, y)).line((BOX + HUB, y + 1.0)).line((BOX - HUB, y + 1.0)).close()
    bands = P()
    for top, height in ((BOX - 52, 9), (BOX - 6, 5), (BOX + 31, 12)):
        bands.move((BOX - HUB, top)).line((BOX + HUB, top)).line((BOX + HUB, top + height)).line((BOX - HUB, top + height)).close()
    screen = group("hub-screen", absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), [
        vector("hub-scan", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "transform": transform()}, [
            lines.build("scanlines", fill=tone(NAME, 0.11), blend="additive"),
            bands.build("bands", fill=tone("#FFFFFF", 0.06), blend="additive")])],
        mask={"paths": [P().circle(HUB - 1).build("disc", fill=tone("#FFFFFF"))]})
    doc.timelines.add("hubScan", 2400, [track("hub-scan", "transform", [(0, transform()), (2400, transform(0, 3 * 8))])], iterations=0)
    doc.events.setdefault("onInit", []).append({"op": "playTimeline", "timeline": "hubScan"})
    rings = vector("hub-rings", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "opacity": number(1)}, [
        P().circle(HUB).build("outer", stroke=stroke(tone(OLIVE_TICK, 0.35), 1.5)),
        P().circle(HUB_RING).build("inner", stroke=stroke(tone(OLIVE_TICK, 0.35), 1.2))])
    dots = []
    for k in range(16):
        a = k * 22.5
        x, y = polar(COMPASS_R, a)
        r = 2.0 if k == 0 else 1.2
        dots.append(P().circle_at((x, y), r).build(f"dot-{k}", fill=tone(OLIVE_TICK, 0.9 if k == 0 else 0.35)))
    compass = vector("compass", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "transform": rotation(0)}, dots)
    doc.bind("compass.transform", "compass", "transform",
             [0, 0, 1, 1, {"op": "*", "args": [{"op": "max", "args": [{"state": "wheel_selected"}, 0]}, round(PITCH, 6)]}])
    pointer = P()
    tip = polar(INNER - 3, 0)
    pointer.move((tip[0] - 4, tip[1] + 6)).line((tip[0] + 4, tip[1] + 6)).line(tip).close()
    pointer_node = vector("pointer", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "transform": rotation(0)},
                          [pointer.build("pointer", fill=tone(OLIVE_TICK, 0.8))])
    doc.bind("pointer.transform", "pointer", "transform",
             [0, 0, 1, 1, {"op": "*", "args": [{"op": "max", "args": [{"state": "wheel_selected"}, 0]}, round(PITCH, 6)]}])
    name = {"id": "name", "type": "text", "properties": {"text": {"type": "text", "value": "#str_104343"},
            **absolute(left=BOX - 70, top=BOX - 30, width=140, height=32), **typeface("marine", 12, 16, rgb(NAME)),
            "text-align": keyword("center")}}
    doc.bind("name.text", "name", "text", {"state": "wheel_name"})
    ammo = {"id": "ammo", "type": "text", "properties": {"text": {"type": "text", "value": "#str_104343"},
            **absolute(left=BOX - 70, top=BOX + 6, width=140, height=26), **typeface("chain", 21, 26, rgb(NAME)),
            "text-align": keyword("center"), "white-space": keyword("nowrap")}}
    doc.bind("ammo.text", "ammo", "text", {"state": "wheel_ammo"})
    centre = group("centre", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "opacity": number(1)}, [name, ammo])
    return [disc, screen, rings, compass, pointer_node, centre]


def _circle_at(self: P, centre, r: float) -> P:
    self.move((centre[0], centre[1] - r))
    count = 4
    for k in range(1, count + 1):
        t0, t1 = math.radians(360 * (k - 1) / count), math.radians(360 * k / count)
        h = 4.0 / 3.0 * math.tan((t1 - t0) / 4.0) * r
        p0 = (centre[0] + r * math.sin(t0), centre[1] - r * math.cos(t0))
        p1 = (centre[0] + r * math.sin(t1), centre[1] - r * math.cos(t1))
        self._add("cubic", (p0[0] + h * math.cos(t0), p0[1] + h * math.sin(t0)), (p1[0] - h * math.cos(t1), p1[1] - h * math.sin(t1)), p1)
    return self.close()


P.circle_at = _circle_at


def transitions(doc: Document) -> None:
    """The Marine wheel opens, selects and closes as a transmission (section
    14.6). The wheel selects from its first frame; plates and icons read by
    150 ms; reduced motion keeps short opacity changes."""
    open_tracks = [
        track("hub", "transform", [(0, transform(sx=0.55, sy=0.06)), (1, transform(sx=0.55, sy=0.06), EASE_OUT), (150, transform()),
                                   (250, transform()), (300, transform(sx=0.9, sy=0.9)), (350, transform())]),
        track("static", "opacity", [(0, number(0)), (1, number(0)), (150, number(0.40)), (650, number(0))]),
        track("centre", "opacity", [(0, number(0)), (1, number(0)), (200, number(1))]),
    ]
    for index in range(COUNT):
        start = 1 + 8 * index
        open_tracks.append(track(f"slot-{index}", "opacity", [(0, number(0)), (start, number(0), EASE_OUT), (start + 90, number(1))]))
        open_tracks.append(track(f"slot-{index}-deploy", "transform",
                                 [(0, transform(sx=0.9, sy=0.9)), (start, transform(sx=0.9, sy=0.9), EASE_OUT), (start + 90, transform())]))
    doc.timelines.add("wheel.open", 650, open_tracks)
    doc.timelines.add("wheel.select", 301, [
        track("static", "opacity", [(0, number(0)), (1, number(0.40)), (301, number(0))]),
        track("centre", "opacity", [(0, number(1)), (1, number(0.2)), (121, number(1))])])
    close_tracks = [track("hub", "transform", [(0, transform()), (150, transform(sx=0.55, sy=0.06))]),
                    track("static", "opacity", [(0, number(0)), (1, number(0.80)), (150, number(0))]),
                    track("centre", "opacity", [(0, number(1)), (60, number(0))])]
    for index in range(COUNT):
        close_tracks.append(track(f"slot-{index}", "opacity", [(0, number(1)), (60, number(0))]))
    doc.timelines.add("wheel.close", 150, close_tracks)
    doc.events["open"] = [{"op": "playTimeline", "timeline": "wheel.open"}]
    doc.events["select"] = [{"op": "playTimeline", "timeline": "wheel.select"}]
    doc.events["close"] = [{"op": "playTimeline", "timeline": "wheel.close"}]


def static_layer() -> dict:
    """The transmission's static: torn bands of light across the hub, added."""
    p = P()
    rows = [(-70, 3), (-41, 2), (-22, 4), (-5, 2), (12, 5), (29, 2), (47, 3), (66, 2)]
    for offset, height in rows:
        y = BOX + offset
        p.move((BOX - HUB, y)).line((BOX + HUB, y)).line((BOX + HUB, y + height)).line((BOX - HUB, y + height)).close()
    return group("static", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "opacity": number(0)}, [
        vector("static-bands", absolute(left=0, top=0, width=2 * BOX, height=2 * BOX),
               [p.build("bands", fill=tone("#FFFFFF", 1.0), blend="additive")])],
        mask={"paths": [P().circle(HUB - 1).build("disc", fill=tone("#FFFFFF"))]})


def weapon_wheel_document() -> dict:
    doc = Document("openq4.weaponwheel")
    doc.state.update({"wheel_selected": {"type": "number", "initial": -1},
                      "wheel_previous": {"type": "number", "initial": -1},
                      "wheel_name": {"type": "string", "initial": ""},
                      "wheel_ammo": {"type": "string", "initial": ""}})
    for index in range(COUNT):
        doc.state.update({f"wheel_owned_{index}": {"type": "boolean", "initial": False},
                          f"wheel_empty_{index}": {"type": "boolean", "initial": False},
                          f"wheel_fill_{index}": {"type": "number", "initial": 0},
                          f"wheel_count_{index}": {"type": "number", "initial": -1},
                          f"wheel_key_{index}": {"type": "string", "initial": ""}})
    slots = [slot_nodes(doc, index) for index in range(COUNT)]
    hub_nodes = hub(doc)
    hub_group = group("hub", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "transform": transform()},
                      hub_nodes + [static_layer()])
    wheel = group("wheel", {**absolute(width=2 * BOX, height=2 * BOX), "left": length(50, "%"), "top": length(50, "%"),
                            "margin-left": length(-BOX), "margin-top": length(-BOX)},
                  [backing(), bezel(), *slots, previous_notch(doc), hub_group])
    transitions(doc)
    root = group("screen", {**absolute(left=0, top=0), "width": length(100, "%"), "height": length(100, "%"),
                            "font-family": {"type": "font", "value": "marine"}, "font-size": length(16),
                            "color": colour(rgb(NAME))}, [wheel])
    return doc.build(root)
