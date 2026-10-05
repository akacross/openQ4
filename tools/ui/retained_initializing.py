"""The retained initializing screen (docs/dev/ui-visual-design.md section 14.17).

Built by tools/ui/build_retained_screens.py with the other retained screens.
While the engine starts, before any menu exists, idCommonLocal::
PrintLoadingMessage paints one frame for each step over the stock picture
(gfx/splashScreen, splash.tga). This document is its Remastered form (FLOW-057,
ART-031): the picture rebuilt as separate vector layers on the 640x480 canvas,
the field and rings extended to any view, the plate band and the teeth turning
in opposite directions beneath the fixed clamps, emblem and lettering, four
quiet accents, and the status line over a rule of one segment per step.

The tones are measured from splash.tga, whose 512 texels square are drawn
pre-squashed (1.25 u per texel across, 0.9375 u down), so its rings are circles
on the canvas. The picture is 8-bit and its rings step by single levels, so
each ring is a run of one measured tone: the rebuild reproduces the picture's
levels rather than approximating a gradient. The rings' center measures
319.4, 214.2 u (a circle fitted to the inner ring's edge); the emblem keeps
its 260 u box centered on the canvas, so the emblem's own ring sits 20 u above
the rings' center, as in the stock picture.

The engine owns the state: init_status is the localized status line and
init_step its step (0..STEPS-1); the step event replays the line's flicker.
Reduced motion jumps every decorative track to its end, so each loop ends on
its reduced pose: the rings at rest, the sweep as the upper-left key light,
the halo at 0.80, and no embers, glint or pulse.
"""
from __future__ import annotations

import math
import random

from build_retained_screens import (EMBLEM, U, Document, absolute, colour, group, keyword, length, linear, number,
                                    rgb, solid, track, transform, typeface, vector)
from build_retained_screens import point as dp_point
from wordmark_trace import LETTERS

CANVAS_W = 960.0
STEPS = 8                       # LOADING... twice, SOUND, NETWORK, RENDER SYSTEM, USER INTERFACE, LOADING GAME, MENUS
CENTER = (319.0, 214.5)         # the rings' center on the canvas (u)
BOX = 310.0                     # half the side of the square that rotates about the center (u)
EMBLEM_BOX = (190.0, 110.0)     # the emblem's 260 u window, centered on the canvas
EMBLEM_TONE = "#0E1000"
LETTER_ORIGIN = (129.4, 148.8)  # q4text's texel (0, 0) on the canvas
LETTER_SCALE = 0.367            # u per texel
LETTER_TONE = "#F2F0EC"
STATUS_TONE = "#F09E0D"
FIELD_TONE = "#171A09"

# The field and fixed rings, measured between the teeth and away from the
# plates: (inner u, outer u, tone). The field itself is FIELD_TONE.
RING_RUNS = [
    (12, 29, "#181B09"), (29, 81, "#191C09"), (81, 104, "#191D0A"), (104, 136, "#1A1E0A"), (136, 140, "#1B1E0A"),
    (140, 161, "#1C1F0A"), (161, 163, "#1B1F0A"), (163, 164, "#1C200B"), (164, 167, "#1C210B"), (167, 169, "#1D220B"),
    (169, 170, "#1E230B"), (170, 172, "#1E240C"), (172, 177, "#1F240C"), (177, 205, "#1F250C"), (205, 206, "#1F240C"),
    (206, 210, "#20260C"), (210, 213, "#20250B"), (213, 214, "#1F250B"), (214, 215, "#1E230B"), (215, 216, "#1D210B"),
    (216, 217, "#1C200B"), (217, 219, "#1B200B"), (219, 222, "#1B1F0A"), (222, 233, "#1A1E0A"), (233, 237, "#1B1E0A"),
    (237, 243, "#1C1F0A"), (243, 249, "#1B1E0A"), (249, 265, "#1A1E0A"), (265, 272, "#191D0A"), (272, 284, "#181B09"),
    (284, 286, "#191C09"), (286, 296, "#191D0A"), (296, 298, "#191C09"), (298, 301, "#181B09"),
]
# One tooth, measured at a tooth's center: it brightens the rim where it
# attaches and runs out to the grooves.
TOOTH_RUNS = [
    (205, 206, "#20260C"), (206, 211, "#21270C"), (211, 214, "#20260C"), (214, 217, "#1E240C"), (217, 234, "#1E230C"),
    (234, 237, "#1E240C"), (237, 238, "#1E230B"), (238, 241, "#1D220B"), (241, 244, "#1C210B"), (244, 247, "#1C200B"),
    (247, 249, "#1B1F0A"),
]
TOOTH_WIDTH = 22.5              # degrees, on a 45-degree pitch from the top
PLATE_TONE = "#21270C"          # the plates' frames
PLATE_SPAN = 90.0               # degrees, centered at the top and the bottom
PLATE_INNER = (176.5, 184.0)    # the inner frame
PLATE_OUTER = (204.0, 210.0)    # the outer frame, over the rim
PLATE_SIDE = 6.0                # the side frames' width (u)
# The clamps at 3 and 9 o'clock darken what turns beneath them: 80 u tall
# from 183 u, most over the teeth. Multiply factors per span (from, to, factor).
CLAMP_SPANS = [(183.0, 212.0, 0.966), (212.0, 247.0, 0.935), (247.0, 296.0, 0.965)]
CLAMP_HALF = 40.0
CLAMP_SOFT = 6.0

PLATE_PERIOD_MS = 180000        # counterclockwise
TEETH_PERIOD_MS = 120000        # clockwise
SWEEP_PERIOD_MS = 10000
SWEEP_TONE = "#5E6E24"
SWEEP_EDGE_TONE = "#C9D98A"
SWEEP_PEAK = 0.26
SWEEP_RISE = 7.5                # degrees
SWEEP_TAIL = 60.0
SWEEP_REST = -38.0              # the reduced-motion key light's leading edge
HALO_TONE = "#FF8340"
HALO_PEAK = 0.10
HALO_FLAT = 70.0
HALO_REACH = 168.0
HALO_PERIOD_MS = 6000
EMBER_TONE = "#FFB070"
EMBERS = 14
GLINT_PERIOD_MS = 9000
GLINT_SWEEP_MS = 900
LETTER_HALO = (5.5, 2.25, 0.10)   # dilation (u), sigma (u), strength
STATUS_MIDDLE = 418.0
RULE_WIDTH = 168.0
RULE_TOP = 429.0
RULE_HEIGHT = 1.5
RULE_GAP = 2.0
PULSE_PERIOD_MS = 800
FLICKER_MS = 120
EASE_IN_OUT = [0.42, 0, 0.58, 1]


# ---------------------------------------------------------------- path building

class Path:
    """Path commands in a node's local dp space, built in canvas units."""

    def __init__(self, origin: tuple[float, float]):
        self.origin = origin            # the canvas point at the node's (0, 0), in u
        self.commands: list[dict] = []

    def _p(self, x: float, y: float) -> list:
        return dp_point(U * (x - self.origin[0]), U * (y - self.origin[1]))

    def _add(self, op: str, *points) -> None:
        entry = {"id": f"c{len(self.commands)}", "op": op}
        if points:
            entry["points"] = [self._p(*p) for p in points]
        self.commands.append(entry)

    def move(self, p) -> "Path":
        self._add("move", p)
        return self

    def line(self, p) -> "Path":
        self._add("line", p)
        return self

    def close(self) -> "Path":
        self._add("close")
        return self

    def arc(self, center, r: float, a0: float, a1: float) -> "Path":
        """From the current point (at angle a0) to a1, degrees clockwise from
        the top, as cubic segments of at most 45 degrees."""
        count = max(1, math.ceil(abs(a1 - a0) / 45.0))
        step = (a1 - a0) / count
        handle = 4.0 / 3.0 * math.tan(math.radians(abs(step)) / 4.0) * r * (1 if step > 0 else -1)
        for index in range(count):
            t0 = math.radians(a0 + step * index)
            t1 = math.radians(a0 + step * (index + 1))
            p0, p1 = polar(center, r, a0 + step * index), polar(center, r, a0 + step * (index + 1))
            c1 = (p0[0] + handle * math.cos(t0), p0[1] + handle * math.sin(t0))
            c2 = (p1[0] - handle * math.cos(t1), p1[1] - handle * math.sin(t1))
            self._add("cubic", c1, c2, p1)
        return self

    def polygon(self, points) -> "Path":
        self.move(points[0])
        for p in points[1:]:
            self.line(p)
        return self.close()

    def build(self, ident: str, *, fill=None, stroke=None, blend=None, rule=None, antialias=True) -> dict:
        result = {"id": ident, "commands": self.commands}
        if not antialias:
            result["antialias"] = False
        if rule:
            result["fillRule"] = rule
        if fill is not None:
            result["fill"] = fill
        if stroke is not None:
            result["stroke"] = stroke
        if blend:
            result["blend"] = blend
        return result


def polar(center, r: float, degrees: float) -> tuple[float, float]:
    t = math.radians(degrees)
    return (center[0] + r * math.sin(t), center[1] - r * math.cos(t))


def circle(path: Path, center, r: float) -> Path:
    path.move(polar(center, r, 0))
    return path.arc(center, r, 0, 360).close()


def annulus(ident: str, origin, center, r0: float, r1: float, fill: dict, blend=None, antialias=True) -> dict:
    path = circle(Path(origin), center, r1)
    if r0 > 0:
        circle(path, center, r0)
    return path.build(ident, fill=fill, blend=blend, rule="evenodd", antialias=antialias)


def sector(ident: str, origin, center, r0: float, r1: float, a0: float, a1: float, fill: dict, blend=None) -> dict:
    path = Path(origin)
    path.move(polar(center, r1, a0)).arc(center, r1, a0, a1).line(polar(center, r0, a1)).arc(center, r0, a1, a0).close()
    return path.build(ident, fill=fill, blend=blend)


def tone(hex_colour: str, alpha: float = 1.0) -> dict:
    return solid(rgb(hex_colour, alpha))


# ------------------------------------------------------------------- the rings

def ring_box(ident: str, children_paths: list, extra_props: dict | None = None, **extra) -> dict:
    """A square vector centered on the rings' center, so its transform turns it
    about that center (transforms apply about a node's own box center)."""
    props = absolute(left=U * (CENTER[0] - BOX), top=U * (CENTER[1] - BOX), width=U * 2 * BOX, height=U * 2 * BOX)
    if extra_props:
        props.update(extra_props)
    return vector(ident, props, children_paths, **extra)


LOCAL = (CENTER[0] - BOX, CENTER[1] - BOX)   # the ring boxes' origin on the canvas


def field_layer() -> dict:
    # Neighbouring rings differ by a level, so their edges need no coverage
    # antialiasing, which would only cost rasterizing every row they span.
    paths = [annulus(f"ring-{index}", LOCAL, CENTER, r0, r1, tone(hex_tone), antialias=False)
             for index, (r0, r1, hex_tone) in enumerate(RING_RUNS)]
    return ring_box("rings-field", paths)


def plates_layer() -> dict:
    paths = []
    for side, middle in (("top", 0.0), ("bottom", 180.0)):
        a0, a1 = middle - PLATE_SPAN / 2, middle + PLATE_SPAN / 2
        paths.append(sector(f"plate-{side}-inner", LOCAL, CENTER, *PLATE_INNER, a0, a1, tone(PLATE_TONE)))
        paths.append(sector(f"plate-{side}-outer", LOCAL, CENTER, *PLATE_OUTER, a0, a1, tone(PLATE_TONE)))
        for edge_name, edge in (("lead", a0), ("trail", a1)):
            # A side frame keeps its width in units, not in degrees.
            def side_points(sign: float) -> list:
                points = []
                for r in (PLATE_INNER[1], PLATE_OUTER[0]):
                    across = math.degrees(PLATE_SIDE / r) * sign
                    points.append((r, edge + across))
                return points
            inward = 1.0 if edge_name == "lead" else -1.0
            (ra, aa), (rb, ab) = side_points(inward)
            outline = [polar(CENTER, PLATE_INNER[1], edge), polar(CENTER, PLATE_OUTER[0], edge),
                       polar(CENTER, rb, ab), polar(CENTER, ra, aa)]
            paths.append(Path(LOCAL).polygon(outline).build(f"plate-{side}-{edge_name}", fill=tone(PLATE_TONE)))
    return ring_box("rings-plates", paths, {"transform": rotation(0)})


def teeth_layer() -> dict:
    paths = []
    for index in range(8):
        middle = 45.0 * index
        a0, a1 = middle - TOOTH_WIDTH / 2, middle + TOOTH_WIDTH / 2
        for run, (r0, r1, hex_tone) in enumerate(TOOTH_RUNS):
            paths.append(sector(f"tooth-{index}-{run}", LOCAL, CENTER, r0, r1, a0, a1, tone(hex_tone)))
    return ring_box("rings-teeth", paths, {"transform": rotation(0)})


def clamps_layer() -> dict:
    """Multiply by a measured factor, fading over CLAMP_SOFT at the top and
    bottom edges; the clamps stay fixed while the rings turn beneath."""
    paths = []
    for side, sign in (("right", 1.0), ("left", -1.0)):
        for index, (near, far, factor) in enumerate(CLAMP_SPANS):
            x0, x1 = CENTER[0] + sign * near, CENTER[0] + sign * far
            top, bottom = CENTER[1] - CLAMP_HALF - CLAMP_SOFT, CENTER[1] + CLAMP_HALF + CLAMP_SOFT
            shade = [factor, factor, factor, 1.0]
            paint = linear((0, U * (top - LOCAL[1])), (0, U * (bottom - LOCAL[1])), [
                (0.0, [1, 1, 1, 1]), (CLAMP_SOFT / (bottom - top), shade),
                (1 - CLAMP_SOFT / (bottom - top), shade), (1.0, [1, 1, 1, 1])])
            outline = [(min(x0, x1), top), (max(x0, x1), top), (max(x0, x1), bottom), (min(x0, x1), bottom)]
            paths.append(Path(LOCAL).polygon(outline).build(f"clamp-{side}-{index}", fill=paint, blend="multiply"))
    return ring_box("rings-clamps", paths)


def rotation(degrees: float) -> dict:
    return {"type": "transform", "unit": "dp", "value": [0, 0, 1, 1, round(degrees, 3)]}


# ----------------------------------------------------------------- the accents

def sweep_layer() -> dict:
    """The warm light: its leading edge at the top of the box, the light behind
    it counterclockwise. Thin sectors carry linear gradients between their
    edges' strengths, approximating the light's turn-wise profile."""
    def strength(behind: float) -> float:
        if behind <= SWEEP_RISE:
            return SWEEP_PEAK * behind / SWEEP_RISE
        t = min(1.0, (behind - SWEEP_RISE) / SWEEP_TAIL)
        return SWEEP_PEAK * (1 - t) ** 2
    edges = [0.0, 2.5, 5.0, SWEEP_RISE] + [SWEEP_RISE + 2.5 * k for k in range(1, int(SWEEP_TAIL / 2.5) + 1)]
    paths = []
    for index in range(len(edges) - 1):
        near, far = edges[index], edges[index + 1]
        for band, (r0, r1, scale) in enumerate(((161.0, 250.0, 1.0), (250.0, 300.0, 0.5))):
            rm = (r0 + r1) / 2
            a, b = polar(CENTER, rm, -near), polar(CENTER, rm, -far)
            paint = linear((U * (a[0] - LOCAL[0]), U * (a[1] - LOCAL[1])), (U * (b[0] - LOCAL[0]), U * (b[1] - LOCAL[1])), [
                (0.0, rgb(SWEEP_TONE, strength(near) * scale)), (1.0, rgb(SWEEP_TONE, strength(far) * scale))])
            paths.append(sector(f"sweep-{index}-{band}", LOCAL, CENTER, r0, r1, -far, -near, paint, blend="additive"))
    # Short arcs on the ring edges catch the leading edge.
    for index, r in enumerate((169.0, 175.0, 204.0, 210.0, 247.0)):
        a, b = polar(CENTER, r, -0.4), polar(CENTER, r, -6.0)
        paint = linear((U * (a[0] - LOCAL[0]), U * (a[1] - LOCAL[1])), (U * (b[0] - LOCAL[0]), U * (b[1] - LOCAL[1])), [
            (0.0, rgb(SWEEP_EDGE_TONE, 0.45)), (1.0, rgb(SWEEP_EDGE_TONE, 0.0))])
        paths.append(sector(f"sweep-edge-{index}", LOCAL, CENTER, r - 0.6, r + 0.6, -6.0, -0.4, paint, blend="additive"))
    return ring_box("sweep", paths, {"transform": rotation(SWEEP_REST)})


def halo_layer() -> dict:
    """#FF8340 behind the emblem, flat to HALO_FLAT and easing out by
    HALO_REACH, in one-level steps of added light."""
    paths = [annulus("halo-core", LOCAL, CENTER, 0, HALO_FLAT, tone(HALO_TONE, HALO_PEAK), blend="additive", antialias=False)]
    step = 4.0
    r = HALO_FLAT
    index = 0
    while r < HALO_REACH - 1e-6:
        outer = min(HALO_REACH, r + step)
        t = ((r + outer) / 2 - HALO_FLAT) / (HALO_REACH - HALO_FLAT)
        strength = HALO_PEAK * 0.5 * (1 + math.cos(math.pi * t))
        paths.append(annulus(f"halo-{index}", LOCAL, CENTER, r, outer, tone(HALO_TONE, strength), blend="additive", antialias=False))
        r, index = outer, index + 1
    return ring_box("halo", paths, {"opacity": number(0.8)})


def ember_nodes(doc: Document) -> list:
    """Fourteen sparks rising through the rings, each on its own cycle: a still
    wait, then a rise with a fade in and out. Each cycle ends unseen, which is
    also where reduced motion leaves it."""
    rng = random.Random(14_17)
    nodes = []
    for index in range(EMBERS):
        size = rng.uniform(0.6, 1.2)
        angle = rng.uniform(0, 360)
        radius = rng.uniform(165, 290)
        x, y = polar(CENTER, radius, angle)
        rise = rng.uniform(28, 60)
        life = rng.uniform(6000, 11000)
        wait = rng.uniform(0, 5000)
        peak = rng.uniform(0.30, 0.50)
        ident = f"ember-{index}"
        side = U * size
        nodes.append(vector(ident, {**absolute(left=U * x - side / 2, top=U * y - side / 2, width=side, height=side),
                                    "opacity": number(0), "transform": transform()}, [
            circle(Path((x - size / 2, y - size / 2)), (x, y), size / 2).build("spark", fill=tone(EMBER_TONE), blend="additive")]))
        total = wait + life
        keys_opacity = [(0, number(0)), (round(wait), number(0)), (round(wait + life * 0.3), number(peak), EASE_IN_OUT),
                        (round(wait + life * 0.7), number(peak * 0.8), EASE_IN_OUT), (round(total), number(0))]
        keys_rise = [(0, transform()), (round(wait), transform()), (round(total), transform(0, -U * rise))]
        doc.timelines.add(f"{ident}.cycle", round(total), [
            track(ident, "opacity", keys_opacity), track(ident, "transform", keys_rise)], iterations=0)
        doc.events.setdefault("onInit", []).append({"op": "playTimeline", "timeline": f"{ident}.cycle"})
    return nodes


# ------------------------------------------------------------------ the letters

def letter_contours(tolerance: float = 0.0, origin=LETTER_ORIGIN, scale=(LETTER_SCALE, LETTER_SCALE)) -> list:
    """Every traced contour on the canvas, in u (texel (0, 0) at origin, scale
    u per texel across and down); tolerance in u simplifies."""
    contours = []
    for letter in LETTERS:
        for contour in [letter["outer"], *letter["holes"]]:
            points = [(origin[0] + scale[0] * x, origin[1] + scale[1] * y) for x, y in contour]
            contours.append(simplify(points, tolerance) if tolerance > 0 else points)
    return contours


def simplify(points: list, tolerance: float) -> list:
    """Ramer-Douglas-Peucker on a closed contour."""
    if len(points) < 4:
        return points
    def rdp(segment: list) -> list:
        start, end = segment[0], segment[-1]
        dx, dy = end[0] - start[0], end[1] - start[1]
        length_sq = dx * dx + dy * dy
        worst, index = 0.0, 0
        for i in range(1, len(segment) - 1):
            px, py = segment[i]
            if length_sq == 0:
                distance = math.hypot(px - start[0], py - start[1])
            else:
                distance = abs(dy * px - dx * py + end[0] * start[1] - end[1] * start[0]) / math.sqrt(length_sq)
            if distance > worst:
                worst, index = distance, i
        if worst <= tolerance:
            return [start, end]
        return rdp(segment[:index + 1])[:-1] + rdp(segment[index:])
    split = len(points) // 2
    result = rdp(points[:split + 1])[:-1] + rdp(points[split:] + [points[0]])[:-1]
    return result if len(result) >= 3 else points


def contours_path(ident: str, origin, contours: list, **paint) -> dict:
    path = Path(origin)
    for contour in contours:
        path.polygon(contour)
    return path.build(ident, rule=paint.pop("rule", "evenodd"), **paint)


def wordmark(doc: Document, prefix: str, origin, halo: tuple[float, float, float], halo_tone: str,
             halo_steps: int = 8, letter_origin=LETTER_ORIGIN, letter_scale=(LETTER_SCALE, LETTER_SCALE),
             letter_blend: str | None = None) -> list:
    """The traced letters with their halo as vector light: the letters dilated
    D, blurred with sigma S and added at strength A. Strokes of rising width
    around every contour add up to the blurred dilation's falloff in steps of
    A / halo_steps; each stroke unites its contours, so no stroke adds twice."""
    dilation, sigma, strength = halo
    reach = dilation + 2.5 * sigma
    def falloff(distance: float) -> float:
        return strength * 0.5 * math.erfc((distance - dilation) / (sigma * math.sqrt(2)))
    widths = [reach * (k + 1) / halo_steps for k in range(halo_steps)]
    halo_contours = letter_contours(0.4, letter_origin, letter_scale)   # a blurred halo needs no finer outline
    paths = []
    previous = falloff(0.0)
    for index, width in enumerate(widths):
        current = falloff(width)
        alpha = previous - current
        previous = current
        if alpha <= 0.0005:
            continue
        paths.append(contours_path(f"{prefix}-halo-{index}", origin, halo_contours,
                                   stroke={"paint": tone(halo_tone, alpha), "widthDp": round(U * 2 * width, 3),
                                           "minimumPixels": 0, "join": "round", "cap": "round"},
                                   blend="additive", antialias=False))
    paths.append(contours_path(f"{prefix}-letters", origin, letter_contours(0.0, letter_origin, letter_scale),
                               fill=tone(LETTER_TONE), blend=letter_blend))
    return paths


# The title's wordmark (ART-031): the stock picture stretches q4text's 1024x256
# texels over a 376x92 u box at 6,119 u and adds it as light. The rebuild keeps
# that layout and the texture's own halo, both added as light, so the Exit
# modal and the band motion scale it through opacity as they scaled the tint.
TITLE_BOX = (6.0, 119.0, 376.0, 92.0)
TITLE_HALO = (3.7, 4.4, 0.40)
TITLE_HALO_TONE = "#FF8F40"


def title_wordmark() -> dict:
    left, top, width, height = TITLE_BOX
    scale = (width / 1024, height / 256)
    paths = wordmark(None, "wordmark", (left, top), TITLE_HALO, TITLE_HALO_TONE, halo_steps=24,
                     letter_origin=(left, top), letter_scale=scale, letter_blend="additive")
    return vector("wordmark", {**absolute(left=U * left, top=U * top, width=U * width, height=U * height),
                               "opacity": number(1)}, paths)


def glint(doc: Document) -> dict:
    """A narrow white light crossing QUAKE 4 in 900 ms every 9 s, clipped to
    the letters by a mask of their contours."""
    left, right = LETTER_ORIGIN[0] + LETTER_SCALE * 90, LETTER_ORIGIN[0] + LETTER_SCALE * 950
    top, bottom = LETTER_ORIGIN[1] + LETTER_SCALE * 76, LETTER_ORIGIN[1] + LETTER_SCALE * 184
    band = 9.0
    start = left - band
    travel = right - start
    origin = (start, top)
    paint = linear((0, 0), (U * band, 0), [(0.0, [1, 1, 1, 0]), (0.5, [1, 1, 1, 0.85]), (1.0, [1, 1, 1, 0])])
    light = vector("glint-light", {**absolute(left=0, top=0, width=U * band, height=U * (bottom - top)),
                                   "transform": transform(U * travel)}, [
        Path(origin).polygon([(start, top), (start + band, top), (start + band, bottom), (start, bottom)]).build(
            "light", fill=paint, blend="additive")])
    mask_origin = origin
    mask = {"paths": [contours_path("letters", mask_origin, letter_contours(), fill=tone("#FFFFFF"))]}
    node = group("glint", absolute(left=U * start, top=U * top, width=U * (travel + band), height=U * (bottom - top)),
                 [light], mask=mask)
    # A play starts from the presented value, so the light steps back to the
    # left edge in the first millisecond before it crosses.
    doc.timelines.add("glint", GLINT_PERIOD_MS, [track("glint-light", "transform", [
        (0, transform(U * travel)), (1, transform(0)), (1 + GLINT_SWEEP_MS, transform(U * travel)),
        (GLINT_PERIOD_MS, transform(U * travel))])], iterations=0)
    doc.events.setdefault("onInit", []).append({"op": "playTimeline", "timeline": "glint"})
    return node


# ------------------------------------------------------------------- the status

def status_nodes(doc: Document) -> list:
    # Segments with gaps only between them, so the rule spans RULE_WIDTH exactly.
    pitch = (RULE_WIDTH + RULE_GAP) / STEPS
    left = 320.0 - RULE_WIDTH / 2
    # The flicker animates a group around the text, as the other screens'
    # text effects do.
    label = group("status-line", {**absolute(left=0, top=U * STATUS_MIDDLE - 12, width=CANVAS_W, height=24),
                                  "opacity": number(1)}, [{"id": "status", "type": "text", "properties": {
        "text": {"type": "text", "value": "#str_104343"},   # LOADING..., until the engine publishes a step
        **absolute(left=0, top=0, width=CANVAS_W, height=24),
        **typeface("marine", 16, 24, rgb(STATUS_TONE)), "text-align": keyword("center"),
        "white-space": keyword("nowrap")}}])
    doc.bind("status.text", "status", "text", {"state": "init_status"})
    segments = []
    for index in range(STEPS):
        ident = f"rule-{index}"
        x = U * (left + pitch * index)
        segments.append(vector(ident, {**absolute(left=x, top=U * RULE_TOP, width=U * (pitch - RULE_GAP),
                                                  height=U * RULE_HEIGHT), "opacity": number(0.15)}, [
            Path((0, 0)).polygon([(0, 0), (pitch - RULE_GAP, 0), (pitch - RULE_GAP, RULE_HEIGHT), (0, RULE_HEIGHT)]).build(
                "segment", fill=tone(STATUS_TONE))]))
        step = {"state": "init_step"}
        doc.bind(f"{ident}.opacity", ident, "opacity", {"op": "select", "args": [
            {"op": ">", "args": [step, index]}, 0.55,
            {"op": "select", "args": [{"op": "==", "args": [step, index]}, 0.0, 0.15]}]})
    pulse = vector("rule-pulse", {**absolute(left=U * left, top=U * RULE_TOP, width=U * (pitch - RULE_GAP),
                                             height=U * RULE_HEIGHT), "opacity": number(0.95)}, [
        Path((0, 0)).polygon([(0, 0), (pitch - RULE_GAP, 0), (pitch - RULE_GAP, RULE_HEIGHT), (0, RULE_HEIGHT)]).build(
            "segment", fill=tone(STATUS_TONE))])
    doc.bind("rule-pulse.left", "rule-pulse", "left", {"op": "+", "args": [
        round(U * left, 3), {"op": "*", "args": [{"op": "clamp", "args": [{"state": "init_step"}, 0, STEPS - 1]},
                                                 round(U * pitch, 3)]}]})
    doc.timelines.add("rulePulse", PULSE_PERIOD_MS, [track("rule-pulse", "opacity", [
        (0, number(0.95), EASE_IN_OUT), (PULSE_PERIOD_MS / 2, number(0.62), EASE_IN_OUT), (PULSE_PERIOD_MS, number(0.95))])],
        iterations=0)
    # A play starts from the presented value: the line drops to 0.35 in the
    # first millisecond, then rises over FLICKER_MS.
    doc.timelines.add("statusFlicker", FLICKER_MS + 1, [track("status-line", "opacity", [
        (0, number(1)), (1, number(0.35)), (FLICKER_MS + 1, number(1))])])
    doc.events.setdefault("onInit", []).append({"op": "playTimeline", "timeline": "rulePulse"})
    doc.events["step"] = [{"op": "playTimeline", "timeline": "statusFlicker"}]
    return [label, group("rule", absolute(left=0, top=0, width=CANVAS_W, height=720), segments + [pulse])]


# ----------------------------------------------------------------- the document

def initializing_document() -> dict:
    doc = Document("openq4.initializing")
    doc.state.update({
        "init_status": {"type": "string", "initial": ""},
        "init_step": {"type": "number", "initial": 0},
    })
    halo = halo_layer()
    doc.timelines.add("halo", HALO_PERIOD_MS, [track("halo", "opacity", [
        (0, number(0.8), EASE_IN_OUT), (1300, number(1.0), EASE_IN_OUT), (4300, number(0.4), EASE_IN_OUT),
        (HALO_PERIOD_MS, number(0.8))])], iterations=0)
    doc.timelines.add("rings", TEETH_PERIOD_MS, [track("rings-teeth", "transform", [(0, rotation(0)), (TEETH_PERIOD_MS, rotation(360))])],
                      iterations=0)
    doc.timelines.add("plates", PLATE_PERIOD_MS, [track("rings-plates", "transform", [(0, rotation(0)), (PLATE_PERIOD_MS, rotation(-360))])],
                      iterations=0)
    doc.timelines.add("sweep", SWEEP_PERIOD_MS, [track("sweep", "transform", [
        (0, rotation(SWEEP_REST)), (SWEEP_PERIOD_MS, rotation(SWEEP_REST + 360))])], iterations=0)
    for timeline in ("rings", "plates", "sweep", "halo"):
        doc.events.setdefault("onInit", []).append({"op": "playTimeline", "timeline": timeline})
    emblem_origin = (EMBLEM_BOX[0], EMBLEM_BOX[1])
    emblem = vector("emblem", absolute(left=U * EMBLEM_BOX[0], top=U * EMBLEM_BOX[1], width=U * 260, height=U * 260), [
        Path(emblem_origin).polygon([(EMBLEM_BOX[0] + x, EMBLEM_BOX[1] + y) for x, y in EMBLEM]).build(
            "emblem", fill=tone(EMBLEM_TONE))])
    letters_origin = (0.0, 0.0)
    letters = vector("wordmark", absolute(left=0, top=0, width=CANVAS_W, height=720),
                     wordmark(doc, "wordmark", letters_origin, LETTER_HALO, HALO_TONE))
    stage = group("stage", {**absolute(top=0, width=CANVAS_W, height=720), "left": length(50, "%"),
                            "margin-left": length(-CANVAS_W / 2)}, [
        field_layer(), plates_layer(), teeth_layer(), sweep_layer(), clamps_layer(), halo,
        *ember_nodes(doc), emblem, letters, glint(doc), *status_nodes(doc),
    ])
    root = group("screen", {**absolute(left=0, top=0), "width": length(100, "%"), "height": length(100, "%"),
                            "background-color": colour(rgb(FIELD_TONE)), "font-family": {"type": "font", "value": "marine"},
                            "font-size": length(16), "color": colour(rgb(STATUS_TONE))}, [stage])
    return doc.build(root)
