"""The retained Strogg weapon wheel (docs/dev/ui-visual-design.md section 14.6).

Built by tools/ui/build_retained_screens.py with the other retained screens.
After Kane's stroggification the HUD takes the Strogg family, and its wheel
takes the Strogg construction rather than a recolored Marine ring: eleven
angular plates, each with a raised leading tooth on 30-degree shoulders, a
chamfered trailing corner and a notched inner edge, all straight-edged, on a
ring twisted 4 degrees backward (the polar form of the Strogg shear); eight
slanted #FF9000 cells along each outer edge under a masked grain that drifts
over the plates; an octagonal core with a lower tab, circled by two dashed
rings turning at 0.2 and 0.5 turns a second in opposite directions, joined
to every owned plate by thin circuit paths that brighten for the selection.
Every label is R_Strogg with its rune copy, so it can translate (section 8).

The game publishes the same state as the Marine wheel (retained_weapon_wheel.py)
and plays the same open, select and close events, which here play the Strogg
translation (section 14.6 Transitions); reduced motion stops the rings and
grain and changes names at once.
"""
from __future__ import annotations

import math

from build_retained_screens import (ACCEL_LATE, RUNE_SCALE, ST_LINE, ST_READ, ST_SELECT, Document, absolute, colour,
                                    group, keyword, length, number, picture, rgb, rune_rise, scan_bar, track, transform,
                                    typeface, vector)
from retained_weapon_wheel import (BOX, CELLS, COUNT, EASE_OUT, GAP, GLYPH_DP, GLYPH_R, INNER, NUMBER_R, OUTER, PITCH,
                                   RESERVE_R, SLOTS, EXTEND, P, backing, code_tone, glyph_paths, polar, prohibition,
                                   rotation, side_angle, stroke, tone)

ICON = "#F59512"        # icons at 60%
SELECTED = "#FFCC00"    # the selected icon
RING = "#F2AD0B"        # the selection's outline
CELL = "#FF9000"        # the reserve cells
FLASH = "#FFD06F"       # the boot flash
CORE_FILL = "#0A0503"
TWIST = 4.0             # degrees the outer end of each boundary trails the inner
TOOTH = 7.0             # dp the leading tooth rises above the outer edge
TOOTH_SHARE = 0.30      # the share of the outer edge the tooth covers
SHOULDER = 30.0         # degrees of the tooth's shoulders
CHAMFER = 10.0          # dp cut from the trailing outer corner
NOTCH_DEPTH, NOTCH_HALF = 4.0, 6.0
CELL_BAND = (OUTER - 16.0, OUTER - 5.0)
CELL_SLANT = 2.2        # degrees each cell's inner corners lead its outer ones
CORE_R = 74.0           # the octagon's circumradius
RING_A, RING_B = 86.0, 94.0
GRAIN_TILE = 128.0
# The plates boot and drop out in a scrambled order (the stroggification
# monitor's cascade), never clockwise.
ORDER = [6, 2, 9, 0, 4, 10, 7, 1, 8, 3, 5]
ROW_GAP = 18.0          # ms between readouts translating, clockwise from the top


def twisted(angle: float, r: float) -> float:
    return angle - TWIST * (r - INNER) / (OUTER - INNER)


def edge_angle(boundary: float, inward: int, r: float) -> float:
    """A segment side at radius r: the constant gap, then the ring's twist."""
    return twisted(side_angle(r, boundary, inward), r)


def chord(r: float, a0: float, a1: float, step: float = 8.0) -> list:
    """Points along radius r from a0 to a1 in straight chords (a0 excluded)."""
    count = max(1, math.ceil(abs(a1 - a0) / step))
    return [polar(r, a0 + (a1 - a0) * k / count) for k in range(1, count + 1)]


def plate_points(index: int) -> list:
    """The angular plate: inner edge (notched) trailing to leading, the
    leading side up to the tooth, the tooth back to its 30-degree shoulder,
    the outer edge to the chamfer and the trailing side down."""
    a, b = index * PITCH - PITCH / 2, index * PITCH + PITCH / 2
    trail_in, lead_in = edge_angle(a, 1, INNER), edge_angle(b, -1, INNER)
    mid = (trail_in + lead_in) / 2
    notch = math.degrees(NOTCH_HALF / INNER)
    points = [polar(INNER, trail_in)]
    points += chord(INNER, trail_in, mid - notch)
    points += [polar(INNER + NOTCH_DEPTH, mid - notch * 0.45), polar(INNER + NOTCH_DEPTH, mid + notch * 0.45),
               polar(INNER, mid + notch)]
    points += chord(INNER, mid + notch, lead_in)
    top = OUTER + TOOTH
    lead_top = edge_angle(b, -1, top)
    points.append(polar(top, lead_top))
    lead_out, trail_out = edge_angle(b, -1, OUTER), edge_angle(a, 1, OUTER)
    tooth_start = lead_out - (lead_out - trail_out) * TOOTH_SHARE
    points += chord(top, lead_top, tooth_start)
    run = math.degrees(TOOTH / math.tan(math.radians(SHOULDER)) / OUTER)
    points.append(polar(OUTER, tooth_start - run))
    chamfer = math.degrees(CHAMFER / OUTER)
    points += chord(OUTER, tooth_start - run, trail_out + chamfer)
    points.append(polar(OUTER - CHAMFER, edge_angle(a, 1, OUTER - CHAMFER)))
    return points


def polygon(points: list, ident: str, **paint) -> dict:
    p = P()
    p.move(points[0])
    for point in points[1:]:
        p.line(point)
    return p.close().build(ident, **paint)


def cell_points(index: int, cell: int) -> list:
    """One slanted reserve cell between the chamfer and the tooth."""
    a, b = index * PITCH - PITCH / 2, index * PITCH + PITCH / 2
    r0, r1 = CELL_BAND
    start = edge_angle(a, 1, r1) + math.degrees(CHAMFER / r1) + 1.0
    end = edge_angle(b, -1, r1) - 1.5
    span = (end - start) / CELLS
    gap = math.degrees(1.2 / r1)
    c0, c1 = start + span * cell + gap / 2, start + span * (cell + 1) - gap / 2
    return [polar(r1, c0), polar(r1, c1), polar(r0, c1 + CELL_SLANT), polar(r0, c0 + CELL_SLANT)]


def rune_pair(doc: Document, ident: str, centre, width: float, height: float, size: float, tint: list, value) -> list:
    """An R_Strogg readout and its rune copy on one baseline, bound to `value`.
    Both rest translated: the rune copy transparent."""
    def box(top: float) -> dict:
        return {**absolute(left=round(centre[0] - width / 2, 3), top=round(top, 3), width=width, height=height),
                "text-align": keyword("center"), "white-space": keyword("nowrap"), "transform": transform()}
    top = centre[1] - height / 2
    latin = {"id": ident, "type": "text", "properties": {"text": {"type": "text", "value": "#str_104343"},
             **box(top), **typeface("r_strogg", size, height, tint)}}
    rune = {"id": f"{ident}-rune", "type": "text", "properties": {"text": {"type": "text", "value": "#str_104343"},
            **box(top - rune_rise(size)), **typeface("strogg", round(size * RUNE_SCALE, 3), height, [*rgb(ST_SELECT)[:3], 0]),
            "pointer-events": keyword("none")}}
    doc.bind(f"{ident}.text", ident, "text", value)
    doc.bind(f"{ident}-rune.text", f"{ident}-rune", "text", value)
    return [rune, latin]


def slot_nodes(doc: Document, index: int) -> dict:
    name, code = SLOTS[index], (1.0, 0.5647, 0.0)
    middle = index * PITCH
    selected = {"op": "==", "args": [{"state": "wheel_selected"}, index]}
    owned = {"state": f"wheel_owned_{index}"}
    empty = {"state": f"wheel_empty_{index}"}
    square = absolute(left=0, top=0, width=2 * BOX, height=2 * BOX)
    outline = plate_points(index)
    plate = vector(f"slot-{index}-plate", {**square, "opacity": number(0.55)},
                   [polygon(outline, "plate", fill=tone("#000000"))])
    doc.bind(f"slot-{index}-plate.opacity", f"slot-{index}-plate", "opacity",
             {"op": "select", "args": [owned, {"op": "select", "args": [selected, 0.75, 0.55]}, 0.0]})
    rim = vector(f"slot-{index}-rim", {**square, "opacity": number(1)},
                 [polygon(outline, "rim", stroke=stroke(tone(ST_LINE, 0.35), 1.0))])
    doc.bind(f"slot-{index}-rim.opacity", f"slot-{index}-rim", "opacity", {"op": "select", "args": [owned, 1.0, 0.45]})
    ring = vector(f"slot-{index}-ring", {**square, "opacity": number(0)},
                  [polygon(outline, "ring", stroke=stroke(tone(RING), 2.4))])
    doc.bind(f"slot-{index}-ring.opacity", f"slot-{index}-ring", "opacity", {"op": "select", "args": [selected, 1.0, 0.0]})
    flash = vector(f"slot-{index}-flash", {**square, "opacity": number(0)},
                   [polygon(outline, "flash", fill=tone(FLASH, 0.85), blend="additive")])
    children = [plate, rim]
    # The reserve: eight slanted cells filled in proportion to it; the blaster has none.
    if index != 0:
        track_paths = [polygon(cell_points(index, cell), f"track-{cell}", fill=code_tone(code, 0.14)) for cell in range(CELLS)]
        children.append(vector(f"slot-{index}-cells", square, track_paths))
        for cell in range(CELLS):
            ident = f"slot-{index}-cell-{cell}"
            children.append(vector(ident, {**square, "opacity": number(0)},
                                   [polygon(cell_points(index, cell), "fill", fill=tone(CELL, 0.55))]))
            doc.bind(f"{ident}.opacity", ident, "opacity", {"op": "select", "args": [owned, {"op": "clamp", "args": [
                {"op": "-", "args": [{"op": "*", "args": [{"state": f"wheel_fill_{index}"}, CELLS]}, cell]}, 0, 1]}, 0.0]})
    centre = polar(GLYPH_R, twisted(middle, GLYPH_R))
    dim = vector(f"slot-{index}-glyph", {**square, "opacity": number(1)},
                 [glyph_paths(name, centre, GLYPH_DP, tone(ICON, 0.6), "glyph")])
    doc.bind(f"slot-{index}-glyph.opacity", f"slot-{index}-glyph", "opacity",
             {"op": "select", "args": [{"op": "&&", "args": [owned, {"op": "!", "args": [selected]}]}, 1.0, 0.0]})
    hot = vector(f"slot-{index}-glyph-selected", {**square, "opacity": number(0)},
                 [glyph_paths(name, centre, GLYPH_DP, tone(SELECTED), "glyph")])
    doc.bind(f"slot-{index}-glyph-selected.opacity", f"slot-{index}-glyph-selected", "opacity",
             {"op": "select", "args": [selected, 1.0, 0.0]})
    sign = vector(f"slot-{index}-noammo", {**square, "opacity": number(0)}, prohibition(centre, GLYPH_DP, "sign"))
    doc.bind(f"slot-{index}-noammo.opacity", f"slot-{index}-noammo", "opacity",
             {"op": "select", "args": [{"op": "&&", "args": [owned, empty]}, 1.0, 0.0]})
    children += [dim, hot, sign, ring]
    # The number and the reserve, each R_Strogg with its rune copy.
    key = group(f"slot-{index}-key", {**square, "opacity": number(1)},
                rune_pair(doc, f"slot-{index}-key-text", polar(NUMBER_R, twisted(middle, NUMBER_R)), 40, 14, 11,
                          rgb(ICON, 0.85), {"state": f"wheel_key_{index}"}))
    doc.bind(f"slot-{index}-key.opacity", f"slot-{index}-key", "opacity", {"op": "select", "args": [owned, 1.0, 0.3]})
    reserve = group(f"slot-{index}-reserve", {**square, "opacity": number(0)},
                    rune_pair(doc, f"slot-{index}-reserve-text", polar(RESERVE_R, twisted(middle, RESERVE_R)), 64, 18, 14,
                              rgb(ST_READ), {"op": "numberText", "args": [
                                  {"op": "max", "args": [{"state": f"wheel_count_{index}"}, 0]}], "decimals": 0}))
    doc.bind(f"slot-{index}-reserve.opacity", f"slot-{index}-reserve", "opacity", {"op": "select", "args": [
        {"op": "&&", "args": [owned, {"op": ">=", "args": [{"state": f"wheel_count_{index}"}, 0]}]}, 1.0, 0.0]})
    children += [key, reserve, flash]
    # The selection moves outward along its own direction, as in the Marine wheel.
    dx, dy = EXTEND * math.sin(math.radians(middle)), -EXTEND * math.cos(math.radians(middle))
    boot = group(f"slot-{index}-boot", {**square, "opacity": number(1)}, children)
    slot = group(f"slot-{index}", {**square, "transform": transform(), "opacity": number(1)}, [boot])
    doc.bind(f"slot-{index}.transform", f"slot-{index}", "transform", [
        {"op": "select", "args": [selected, round(dx, 3), 0.0]}, {"op": "select", "args": [selected, round(dy, 3), 0.0]}, 1, 1, 0])
    return slot


def grain(doc: Document) -> dict:
    """The stock Strogg HUD static, added warm and faint over the plates and
    masked to them, drifting a tile every 8 s."""
    tiles = []
    count = math.ceil(2 * BOX / GRAIN_TILE) + 1
    for row in range(count):
        for column in range(count):
            tiles.append(picture(f"grain-{row}-{column}", "gfx/guis/hud/s_static",
                                 {**absolute(left=column * GRAIN_TILE - GRAIN_TILE, top=row * GRAIN_TILE - GRAIN_TILE,
                                             width=GRAIN_TILE, height=GRAIN_TILE),
                                  "image-blend": keyword("additive"), "image-color": colour([1, 0.75, 0.4, 0.5])}, fit="fill"))
    drift = group("grain-drift", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "transform": transform()}, tiles)
    doc.timelines.add("grainDrift", 8000, [track("grain-drift", "transform", [(0, transform()),
                                                                              (8000, transform(GRAIN_TILE, GRAIN_TILE))])],
                      iterations=0)
    doc.events.setdefault("onInit", []).append({"op": "playTimeline", "timeline": "grainDrift"})
    return group("grain", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "opacity": number(0.2),
                           "pointer-events": keyword("none")}, [drift],
                 mask={"paths": [polygon(plate_points(index), f"plate-{index}", fill=tone("#FFFFFF")) for index in range(COUNT)]})


def circuits(doc: Document) -> dict:
    """Thin paths from the core to every owned plate, brighter for the
    selection: out from the octagon, a 45-degree jog, on to the plate's notch."""
    nodes = []
    for index in range(COUNT):
        middle = index * PITCH
        jog = 3.0 if index % 2 else -3.0
        points = [polar(CORE_R + 2, middle), polar(RING_B + 6, middle), polar(RING_B + 12, middle + jog),
                  polar(INNER - 2, twisted(middle, INNER) + jog)]
        p = P()
        p.move(points[0])
        for point in points[1:]:
            p.line(point)
        dot = P().circle_at(points[-1], 1.8)
        ident = f"circuit-{index}"
        nodes.append(vector(ident, {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "opacity": number(0)},
                            [p.build("trace", stroke=stroke(tone(ST_LINE), 0.9)), dot.build("dot", fill=tone(ST_LINE))]))
        selected = {"op": "==", "args": [{"state": "wheel_selected"}, index]}
        doc.bind(f"{ident}.opacity", ident, "opacity", {"op": "select", "args": [selected, 0.9, {"op": "select", "args": [
            {"state": f"wheel_owned_{index}"}, 0.32, 0.06]}]})
    return group("circuits", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "transform": transform(),
                              "opacity": number(1)}, nodes)


def delayed(start: float, value_from: dict, value_to: dict, length: float, easing=EASE_OUT) -> list:
    """Keys that hold `value_from` from the play's first millisecond until
    `start`, then ease to `value_to` over `length` ms."""
    keys = [(0, value_from), (1, value_from, easing if start <= 1 else None)]
    if start > 1:
        keys.append((start, value_from, easing))
    keys.append((max(start, 1) + length, value_to))
    return keys


def octagon(r: float) -> list:
    return [polar(r, 22.5 + 45 * k) for k in range(8)]


def core(doc: Document) -> list:
    """The octagonal plate with a lower tab (after the boss bar) and its two
    dashed rings, turning at 0.2 and 0.5 turns a second in opposite directions."""
    body = octagon(CORE_R)
    # The lower tab hangs from the bottom face of the octagon.
    left, right = polar(CORE_R, 202.5), polar(CORE_R, 157.5)
    tab = [right, (right[0] - 8, right[1] + 12), (left[0] + 8, left[1] + 12), left]
    plate = vector("core-plate", absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), [
        polygon(body, "body", fill=tone(CORE_FILL, 0.82)), polygon(tab, "tab", fill=tone(CORE_FILL, 0.82)),
        polygon(body, "rim", stroke=stroke(tone(ST_LINE, 0.55), 1.4)),
        polygon(octagon(CORE_R - 5), "inner", stroke=stroke(tone(ST_LINE, 0.22), 0.8))])

    def dashes(ident: str, r: float, count: int, share: float, width: float, alpha: float) -> dict:
        p = P()
        span = 360.0 / count
        for k in range(count):
            a0 = k * span
            p.move(polar(r, a0)).arc(r, a0, a0 + span * share)
        return vector(ident, {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "transform": rotation(0)},
                      [p.build("dashes", stroke=stroke(tone(ST_LINE, alpha), width))])
    ring_a = dashes("core-ring-a", RING_A, 24, 0.6, 1.6, 0.6)
    ring_b = dashes("core-ring-b", RING_B, 48, 0.5, 1.1, 0.45)
    doc.timelines.add("coreRings", 10000, [track("core-ring-a", "transform", [(0, rotation(0)), (10000, rotation(720))]),
                                           track("core-ring-b", "transform", [(0, rotation(0)), (10000, rotation(-1800))])],
                      iterations=0)
    doc.events.setdefault("onInit", []).append({"op": "playTimeline", "timeline": "coreRings"})
    # Spinning up on open is a turn of the rings' holder, settling on rest.
    rings = group("core-rings", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "transform": rotation(0),
                                 "opacity": number(1)}, [ring_a, ring_b])
    # The name, in R_Strogg over its rune copy, sits in a box that fits it and
    # is centered on the core, so the scan bar that slides in behind it as it
    # translates rests with its head 12 dp past the name in any language.
    size, line = 12.0, 18.0
    value = {"state": "wheel_name"}
    latin = {"id": "name-text", "type": "text", "properties": {"text": {"type": "text", "value": "#str_104343"},
             "position": keyword("relative"), "display": keyword("block"), "margin-left": length(12), "margin-right": length(12),
             **typeface("r_strogg", size, line, rgb(ST_READ)), "white-space": keyword("nowrap"), "transform": transform()}}
    rune = {"id": "name-text-rune", "type": "text", "properties": {"text": {"type": "text", "value": "#str_104343"},
            **absolute(left=12, top=round(-rune_rise(size), 3)), **typeface("strogg", round(size * RUNE_SCALE, 3), line,
                                                                           [*rgb(ST_SELECT)[:3], 0]),
            "white-space": keyword("nowrap"), "transform": transform(), "pointer-events": keyword("none")}}
    doc.bind("name-text.text", "name-text", "text", value)
    doc.bind("name-text-rune.text", "name-text-rune", "text", value)
    bar = scan_bar("name-bar", 12, {**absolute(left=0, top=3, height=12), "right": length(0), "pointer-events": keyword("none")})
    fit = group("name-fit", {"position": keyword("relative"), "display": keyword("inline-block")}, [bar, rune, latin])
    name = group("name", {**absolute(left=BOX - 90, top=BOX - 26, width=180, height=line), "text-align": keyword("center"),
                          "opacity": number(1)}, [fit])
    ammo = group("ammo", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "opacity": number(1)},
                 rune_pair(doc, "ammo-text", (BOX, BOX + 14), 128, 24, 17, rgb(ST_READ), {"state": "wheel_ammo"}))
    centre = group("centre", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "opacity": number(1)}, [name, ammo])
    return [plate, rings, centre]


def readout_tracks(prefix: str, start: float, duration: float, rest: list, white: bool = False) -> list:
    """A line arriving in runes and translating: the rune copy fades from
    #FFCC00 at 0.80 as the R_Strogg copy fades in, both popping 6% and
    settling; a heading arrives white and settles to its color."""
    runes, hidden = [*rgb(ST_SELECT)[:3], 0.8], [*rgb(ST_SELECT)[:3], 0]

    def steps(a, b):
        # A play retargets the first key to the current value; the 1 ms key
        # puts the line back in runes before its own start.
        return [(0, a), (1, a), *([(start, a)] if start > 1 else []), (max(start, 1) + duration, b)]
    tracks = [track(f"{prefix}-rune", "color", [(at, colour(value)) for at, value in steps(runes, hidden)]),
              track(f"{prefix}-rune", "transform", [(at, value) for at, value in steps(transform(sx=1.06, sy=1.06), transform())]),
              track(prefix, "transform", [(at, value) for at, value in steps(transform(sx=1.054, sy=1.054), transform())])]
    if white:
        finish = max(start, 1) + duration
        tracks.append(track(prefix, "color", [(at, colour(value)) for at, value in steps([1, 1, 1, 0], [1, 1, 1, 1])] +
                            [(finish + 60, colour([1, 1, 1, 1])), (finish + 210, colour(rest))]))
    else:
        tracks.append(track(prefix, "color", [(at, colour(value)) for at, value in steps([*rest[:3], 0], rest)]))
    return tracks


def transitions(doc: Document) -> None:
    """The Strogg wheel opens, selects and closes as a translation (section
    14.6). The wheel selects from its first frame; plates read by 150 ms."""
    open_tracks, close_tracks = [], []
    for index in range(COUNT):
        # A play starts each track from the value it finds, so a 1 ms key
        # first puts every plate out before its own boot.
        boot = 1 + 12 * ORDER.index(index)
        open_tracks.append(track(f"slot-{index}-boot", "opacity", delayed(boot, number(0), number(1), 40)))
        open_tracks.append(track(f"slot-{index}-flash", "opacity", [(0, number(0)), (1, number(0)),
                                                                   *([(boot, number(0))] if boot > 1 else []),
                                                                   (boot + 1, number(1)), (boot + 151, number(0))]))
        # The first plate drops at once; the rest wait their turn.
        drop = 8 * ORDER.index(index)
        wait = [(drop, None)] if drop > 0 else []
        close_tracks.append(track(f"slot-{index}-flash", "opacity", [(0, number(0)), *[(at, number(0)) for at, _ in wait],
                                                                    (drop + 1, number(0.8)), (drop + 60, number(0))]))
        close_tracks.append(track(f"slot-{index}-boot", "opacity", [(0, number(1)), *[(at, number(1)) for at, _ in wait],
                                                                   (drop + 60, number(0))]))
    # The rings spin up, the circuits trace out from the core and the grain settles.
    open_tracks += [track("core-rings", "transform", [(0, rotation(-120)), (1, rotation(-120), EASE_OUT), (300, rotation(0))]),
                    track("circuits", "transform", [(0, transform(sx=0.62, sy=0.62)), (1, transform(sx=0.62, sy=0.62), EASE_OUT),
                                                    (150, transform())]),
                    track("circuits", "opacity", [(0, number(0)), (1, number(0)), (150, number(1))]),
                    track("grain", "opacity", [(0, number(0.6)), (1, number(0.6)), (400, number(0.2))])]
    # Every label arrives in runes and translates: the readouts clockwise
    # from the top, 18 ms apart, as list rows; the name as a heading.
    for index in range(COUNT):
        delay = 60 + ROW_GAP * index
        open_tracks += readout_tracks(f"slot-{index}-key-text", delay, 150, rgb(ICON, 0.85))
        open_tracks += readout_tracks(f"slot-{index}-reserve-text", delay, 150, rgb(ST_READ))
    open_tracks += readout_tracks("name-text", 120, 300, rgb(ST_READ), white=True)
    open_tracks += readout_tracks("ammo-text", 135, 150, rgb(ST_READ), white=True)
    doc.timelines.add("wheel.open", 700, open_tracks)
    # Select: the new name translates with the heading recipe after 40 ms, the
    # scan bar slides in behind it over 90 ms and dims, and the ammunition
    # translates as a name 15 ms later.
    select_tracks = readout_tracks("name-text", 40, 300, rgb(ST_READ), white=True)
    select_tracks += readout_tracks("ammo-text", 55, 150, rgb(ST_READ), white=True)
    parked, rested = length(100, "%"), length(0, "%")
    select_tracks += [track("name-bar", "right", [(0, parked), (1, parked), (40, parked, ACCEL_LATE), (130, rested)]),
                      track("name-bar", "opacity", [(0, number(0)), (1, number(0)), (40, number(0)), (41, number(1)), (340, number(0))])]
    doc.timelines.add("wheel.select", 600, select_tracks)
    # Close: the plates flash and drop out in scrambled order, 8 ms apart over
    # 60 ms each, then the core, rings and grain fade over 120 ms.
    fade = 8 * (COUNT - 1) + 60
    close_tracks += [track(node, "opacity", [(0, number(1)), (fade, number(1)), (fade + 120, number(0))])
                     for node in ("core", "circuits")]
    close_tracks.append(track("grain", "opacity", [(0, number(0.2)), (fade, number(0.2)), (fade + 120, number(0))]))
    doc.timelines.add("wheel.close", fade + 120, close_tracks)
    doc.events["open"] = [{"op": "playTimeline", "timeline": "wheel.open"}]
    doc.events["select"] = [{"op": "playTimeline", "timeline": "wheel.select"}]
    doc.events["close"] = [{"op": "playTimeline", "timeline": "wheel.close"}]


def weapon_wheel_strogg_document() -> dict:
    doc = Document("openq4.weaponwheel.strogg")
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
    # The previous weapon's mark: a slanted notch on the inner edge.
    notch = P()
    tip = polar(INNER - 1, 0)
    notch.move((tip[0] - 6, tip[1] - 7)).line((tip[0] + 4, tip[1] - 7)).line((tip[0] + 1, tip[1])).close()
    previous = vector("previous", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "transform": rotation(0),
                                   "opacity": number(0)}, [notch.build("notch", fill=tone(RING, 0.85))])
    doc.bind("previous.transform", "previous", "transform",
             [0, 0, 1, 1, {"op": "*", "args": [{"state": "wheel_previous"}, round(PITCH, 6)]}])
    doc.bind("previous.opacity", "previous", "opacity",
             {"op": "select", "args": [{"op": ">=", "args": [{"state": "wheel_previous"}, 0]}, 1.0, 0.0]})
    core_nodes = core(doc)
    core_group = group("core", {**absolute(left=0, top=0, width=2 * BOX, height=2 * BOX), "opacity": number(1)}, core_nodes)
    wheel = group("wheel", {**absolute(width=2 * BOX, height=2 * BOX), "left": length(50, "%"), "top": length(50, "%"),
                            "margin-left": length(-BOX), "margin-top": length(-BOX)},
                  [backing(), circuits(doc), *slots, grain(doc), previous, core_group])
    transitions(doc)
    root = group("screen", {**absolute(left=0, top=0), "width": length(100, "%"), "height": length(100, "%"),
                            "font-family": {"type": "font", "value": "r_strogg"}, "font-size": length(16),
                            "color": colour(rgb(ST_READ))}, [wheel])
    return doc.build(root)
