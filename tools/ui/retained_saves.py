"""The retained Load Game page (docs/dev/ui-visual-design.md sections 9 and 13.7).

Built by tools/ui/build_retained_screens.py, which writes and checks it with
the other retained screens. The title's and the Marine pause's LOAD GAME hand
off to it as to a stock page: the home docks its bands and carries the label
into the title slot, and at 550 ms, when the stock page would appear, the
session presents this document in the page state (idSessionLocal::
BeginRetainedPage). The page keeps the stock composition of section 9: the
selected save's preview, 183x137 u at 25,78 u in a 1 u #414624 border, with
its date and time below it on the leading side; LOAD GAME and DELETE GAME as
section navigation plates under them; the saves on the trailing side under
Lowpixel SAVE NAME and LOCATION headings and an olive rule; the prompt bar in
the bottom band, its BACK where the stock BACK plate stood at 532,441 u.

The session publishes the saves newest first. The list holds ROWS rows and
pages through more saves, so the document stays the same size however many
saves there are. A row's first Accept selects its save (the preview and the
date follow); Accept on the selected save, or LOAD GAME, loads it. DELETE GAME
asks with the stock confirmation, and the save that takes the deleted one's
place is selected. With no saves the list is the empty state of section 13.13:
a heading, one sentence and, at the title, NEW GAME. A save that cannot be
loaded or deleted says why over the foot of its preview, until another save
is chosen.

The page is the stock page's content alone. A stock page lives in the main
menu over its home's backdrop and docked bands, so the session keeps drawing
the home that handed off (the title's montage, or the pause over the softened
game) behind the page: its departed state is the page's frame, and the label
it carried into the title slot is the page's title. Back returns the home with
the bands, as from a stock page.
"""
from __future__ import annotations

import re

from build_retained_screens import (CANVAS_W, CLOSE_W, FULL, LANGUAGES, MARKER, OLIVE, ORANGE, PICTURE, RAIL_DARK, STRINGS, U,
                                    Document, absolute, action_plate, colour, confirmation, font, group, keyword, label, length,
                                    linear, localized, marker_path, number, objectives_scrollbar, page_prompts, path, picture,
                                    rgb, solid, stroke, text_width, track, transform, typeface, vector)

ROWS = 64                      # RETAINED_LOAD_ROWS in the session: the saves the list holds at a time
PLACEHOLDER = "#str_230030"    # bound labels' text before their first binding
ERROR = "#E46D56"              # a refusal's reason (section 14.18)
HEADING = [0.72, 0.76, 0.62, 1]  # text.heading
ROW_LIGHT = "#FF9C00"          # bg_line, bg_hover and bg_focus (Appendix B.1)

# Section 9 "Save and load", measured from the stock page (source units).
PREVIEW = (25.0, 78.0, 183.0, 137.0)       # the picture, its 1 u border included
ERROR_STRIP = (26.0, 177.0, 181.0, 37.0)   # load_mapshotbtm: the foot of the picture
ERROR_LINE = 17.0                          # dp: three lines of the reason fit the strip
DATE_TOP, TIME_TOP, DETAIL_LEFT, DETAIL_W = 215.0, 230.0, 37.0, 165.0
PLATES = (("load_go", "#str_200001", 21.0, 256.0, "save"), ("load_delete", "#str_200021", 20.0, 293.0, None))
LIST_LEFT, LIST_TOP, LIST_W, LIST_H = 217.0, 78.0, 410.0, 325.0
ROW_W, ROW_H = 394.0, 20.0                 # tabstops 0, 180 and 394: the scrollbar takes the last 16 u
LOCATION_X = 180.0
HEAD_TOP = 63.0
RULE_Y = 77.6                              # horiz_line2's two centre texels, drawn at 75 u by 6 u


def section_plate(doc: Document, ident: str, key: str, left: float, top: float, *, action: str | None = None,
                  event: str | None = None, label_w: float = 186, selected: dict | None = None) -> dict:
    """A section navigation plate (b2_dark drawn at 208x52 u, Appendix B.1):
    its band rows 16-45 of 64 (13-37.4 u), a lower-leading cut from row 32,
    the #CCCC51 rail along the leading edge, the cut and the bottom, a black
    fill opaque to 57 % of the width, half at 72 % and gone by 94 %, drawn at
    0.40; the corner marker 8,19 u into the rectangle and the Marine label
    (textscale 0.31, 22.3 dp) from 18 u. Hover and focus light the plate to
    0.80 and turn the marker and label orange, as on the home plates. The
    label is `label_w` u wide, past the plate's faded end where it may run.
    With `selected`, an expression, the plate lights while it holds the
    choice, as the stock New Game page lights its difficulty: the plate at
    full strength and its label orange, whatever its feedback."""
    width, height = U * 208, U * 52
    band_top, band_bottom, cut = U * 13.0, U * 37.4, U * 11.4
    fade = [(0, [0, 0, 0, 1]), (0.57, [0, 0, 0, 1]), (0.72, [0, 0, 0, 0.5]), (0.94, [0, 0, 0, 0]), (1, [0, 0, 0, 0])]
    rail = [(0, rgb(RAIL_DARK)), (0.57, rgb(RAIL_DARK)), (0.72, rgb(RAIL_DARK, 0.5)), (0.94, rgb(RAIL_DARK, 0)), (1, rgb(RAIL_DARK, 0))]
    def plate_paths() -> list:
        return [
            path("fill", [(0, band_top), (width, band_top), (width, band_bottom), (cut, band_bottom), (0, band_bottom - cut)],
                 fill=linear((0, 0), (width, 0), fade)),
            path("rail", [(0.75, band_top), (0.75, band_bottom - cut), (cut, band_bottom - 0.75), (width, band_bottom - 0.75)],
                 closed=False, stroke=stroke(linear((0, 0), (width, 0), rail), 1.5)),
        ]
    plate = vector(f"{ident}-plate", {**absolute(left=0, top=0, width=width, height=height), "opacity": number(0.4)}, plate_paths())
    focus = vector(f"{ident}-focus", {**absolute(left=0, top=0, width=width, height=height), "opacity": number(0)}, [
        path("inset", [(cut + 2, band_bottom - 3.2), (width * 0.72, band_bottom - 3.2)], closed=False, stroke=stroke(solid(rgb(ORANGE)), 1.2))])
    marker_rest = vector(f"{ident}-marker", {**absolute(left=0, top=0, width=width, height=height), "opacity": number(0.4)}, [
        marker_path("mark", U * 10.75, U * 21.75, U * 5.5, rgb(MARKER))])
    marker_hot = vector(f"{ident}-marker-hot", {**absolute(left=0, top=0, width=width, height=height), "opacity": number(0)}, [
        marker_path("mark", U * 10.75, U * 21.75, U * 5.5, rgb(ORANGE))])
    text_box = absolute(left=U * 18, top=band_top, width=U * label_w, height=band_bottom - band_top)
    text_node = label(f"{ident}-label", key, {**text_box, **typeface("marine", 22.3, band_bottom - band_top, [1, 1, 1, 0.8]),
                                              "white-space": keyword("nowrap"), "transform": transform()})
    parts = [plate, focus, marker_rest, marker_hot, text_node]
    lit, rest = number(1), number(0)
    states = {
        "default": [(f"{ident}-plate", "opacity", number(0.4)), (f"{ident}-marker", "opacity", number(0.4)),
                    (f"{ident}-marker-hot", "opacity", rest), (f"{ident}-focus", "opacity", rest),
                    (f"{ident}-label", "color", colour([1, 1, 1, 0.8])), (f"{ident}-label", "transform", transform())],
        "hover": [(f"{ident}-plate", "opacity", number(0.8)), (f"{ident}-marker", "opacity", rest),
                  (f"{ident}-marker-hot", "opacity", lit), (f"{ident}-focus", "opacity", rest),
                  (f"{ident}-label", "color", colour(rgb(ORANGE))), (f"{ident}-label", "transform", transform(sx=1.03, sy=1.03))],
        "focus": [(f"{ident}-plate", "opacity", number(0.8)), (f"{ident}-marker", "opacity", rest),
                  (f"{ident}-marker-hot", "opacity", lit), (f"{ident}-focus", "opacity", lit),
                  (f"{ident}-label", "color", colour(rgb(ORANGE))), (f"{ident}-label", "transform", transform(sx=1.03, sy=1.03))],
        "pressed": [(f"{ident}-plate", "opacity", number(1)), (f"{ident}-marker", "opacity", rest),
                    (f"{ident}-marker-hot", "opacity", lit), (f"{ident}-focus", "opacity", lit),
                    (f"{ident}-label", "color", colour(rgb(ORANGE))), (f"{ident}-label", "transform", transform(tx=1, ty=1, sx=1.03, sy=1.03))],
        "disabled": [(f"{ident}-plate", "opacity", number(0.4)), (f"{ident}-marker", "opacity", number(0.4)),
                     (f"{ident}-marker-hot", "opacity", rest), (f"{ident}-focus", "opacity", rest),
                     (f"{ident}-label", "color", colour([1, 1, 1, 0.3])), (f"{ident}-label", "transform", transform())],
    }
    if selected is not None:
        # The lit plate and label stand in while the plate holds the choice;
        # the lit label follows the label's feedback motion.
        plate_lit = vector(f"{ident}-plate-lit", {**absolute(left=0, top=0, width=width, height=height), "opacity": number(1),
                                                  "display": keyword("none"), "pointer-events": keyword("none")}, plate_paths())
        text_lit = label(f"{ident}-label-lit", key, {**text_box, **typeface("marine", 22.3, band_bottom - band_top, rgb(ORANGE)),
                                                     "white-space": keyword("nowrap"), "transform": transform(), "display": keyword("none")})
        text_node["properties"]["display"] = keyword("block")
        doc.bind(f"{ident}-plate-lit.display", f"{ident}-plate-lit", "display", {"op": "select", "args": [selected, "block", "none"]})
        doc.bind(f"{ident}-label-lit.display", f"{ident}-label-lit", "display", {"op": "select", "args": [selected, "block", "none"]})
        doc.bind(f"{ident}-label.display", f"{ident}-label", "display", {"op": "select", "args": [selected, "none", "block"]})
        parts = [plate, plate_lit, focus, marker_rest, marker_hot, text_node, text_lit]
        for state, tracks in states.items():
            moved = next(value for node, prop, value in tracks if node == f"{ident}-label" and prop == "transform")
            tracks.append((f"{ident}-label-lit", "transform", moved))
    ids = doc.states(ident, states)
    control = {"role": "button", "label": key, "states": ids}
    if action:
        control["action"] = action
    else:
        control["event"] = event
    return group(ident, absolute(left=U * left, top=U * top, width=width, height=height), parts, control=control)


def row_light(alpha: float) -> list:
    """bg_line's fill across a row: faded over its leading 5 % and its
    trailing 13 % (Appendix B.1)."""
    return [(0, rgb(ROW_LIGHT, 0)), (0.05, rgb(ROW_LIGHT, alpha)), (0.87, rgb(ROW_LIGHT, alpha)), (1, rgb(ROW_LIGHT, 0))]


def row_plates(ident: str, width: float, height: float) -> list:
    """A list row's backgrounds (bg_line, bg_hover and bg_focus, Appendix B.1):
    the light over rows 3-60 of 64, #FF9C00 at 0.01 at rest, 0.16 under the
    pointer or focus and 0.41 while the row's save is selected, with the
    white 0.50 rule at row 62 and its ends faded the same way. The focused row
    adds the orange inset of the home plates along its leading edge and foot."""
    top, bottom, rule = height * 3 / 64, height * 61 / 64, height * 62.5 / 64
    band = [(0, top), ({"fraction": 1}, top), ({"fraction": 1}, bottom), (0, bottom)]
    whole = {**absolute(left=0, top=0, width=width, height=height)}
    rule_paint = linear((0, 0), ({"fraction": 1}, 0), [(0, [1, 1, 1, 0]), (0.05, [1, 1, 1, 0.5]), (0.87, [1, 1, 1, 0.5]), (1, [1, 1, 1, 0])])
    return [
        vector(f"{ident}-line", {**whole, "pointer-events": keyword("none")}, [
            path("fill", band, fill=linear((0, 0), ({"fraction": 1}, 0), row_light(0.01))),
            path("rule", [(0, rule), ({"fraction": 1}, rule)], closed=False, stroke=stroke(rule_paint, 1))]),
        vector(f"{ident}-hover", {**whole, "opacity": number(0), "pointer-events": keyword("none")}, [
            path("fill", band, fill=linear((0, 0), ({"fraction": 1}, 0), row_light(0.16)))]),
        vector(f"{ident}-selected", {**whole, "display": keyword("none"), "pointer-events": keyword("none")}, [
            path("fill", band, fill=linear((0, 0), ({"fraction": 1}, 0), row_light(0.41)))]),
        vector(f"{ident}-focus", {**whole, "opacity": number(0), "pointer-events": keyword("none")}, [
            path("inset", [(0.75, top + 1), (0.75, bottom - 1.5), (width * 0.87, bottom - 1.5)], closed=False,
                 stroke=stroke(solid(rgb(ORANGE)), 1.2))]),
    ]


def row_states(doc: Document, ident: str, text_nodes: tuple, rest_colours: tuple) -> dict:
    """A row's feedback: the pointer lights it, focus lights it and turns its
    first column orange, and a disabled row dims."""
    lit, rest = number(1), number(0)
    def text(colour_value, first_hot=False):
        return [(node, "color", colour(rgb(ORANGE)) if first_hot and index == 0 else colour(colour_value[index]))
                for index, node in enumerate(text_nodes)]
    hot = [[1, 1, 1, 1] for _ in text_nodes]
    return doc.states(ident, {
        "default": [(f"{ident}-hover", "opacity", rest), (f"{ident}-focus", "opacity", rest)] + text(rest_colours),
        "hover": [(f"{ident}-hover", "opacity", lit), (f"{ident}-focus", "opacity", rest)] + text(hot),
        "focus": [(f"{ident}-hover", "opacity", lit), (f"{ident}-focus", "opacity", lit)] + text(rest_colours, True),
        "pressed": [(f"{ident}-hover", "opacity", lit), (f"{ident}-focus", "opacity", lit)] + text(rest_colours, True),
        "disabled": [(f"{ident}-hover", "opacity", rest), (f"{ident}-focus", "opacity", rest)] + text([[1, 1, 1, 0.3]] * len(text_nodes)),
    })


NAME_TINT, LOCATION_TINT = [1, 1, 1, 0.9], [1, 1, 1, 0.65]


def save_row(doc: Document, index: int, prefix: str = "load", row_w: float = ROW_W,
             chosen: list | None = None) -> dict:
    """One of the list's rows: the save's name in the SAVE NAME column and its
    level in the LOCATION column (tabstops 0 and 180 u), Lowpixel at the stock
    list's textscale 0.22 (15.8 dp) on its 20 u pitch. Its first Accept selects
    the save; Accept on the selected save runs `chosen` (by default it loads
    it). `prefix` names the page's list state and `row_w` its row width."""
    ident, key = f"row-{index}", f"{prefix}.row{index}"
    doc.state[f"{key}.name"] = {"type": "string", "initial": ""}
    doc.state[f"{key}.location"] = {"type": "string", "initial": ""}
    width, height = U * row_w, U * ROW_H
    cell = {"white-space": keyword("nowrap"), "overflow": keyword("hidden"), "pointer-events": keyword("none")}
    name = label(f"{ident}-name", PLACEHOLDER, {**absolute(left=U * 4, top=0, width=U * (LOCATION_X - 8), height=height),
                 **typeface("lowpixel", 15.8, height, NAME_TINT), **cell})
    location = label(f"{ident}-location", PLACEHOLDER, {**absolute(left=U * LOCATION_X, top=0, width=U * (row_w - LOCATION_X - 4), height=height),
                     **typeface("lowpixel", 15.8, height, LOCATION_TINT), **cell})
    doc.bind(f"{ident}-name.text", f"{ident}-name", "text", {"state": f"{key}.name"})
    doc.bind(f"{ident}-location.text", f"{ident}-location", "text", {"state": f"{key}.location"})
    save = {"op": "+", "args": [{"state": f"{prefix}.first"}, index]}
    doc.bind(f"{ident}.display", ident, "display",
             {"op": "select", "args": [{"op": "<", "args": [save, {"state": f"{prefix}.count"}]}, "block", "none"]})
    doc.bind(f"{ident}-selected.display", f"{ident}-selected", "display",
             {"op": "select", "args": [{"op": "==", "args": [{"state": f"{prefix}.selected"}, save]}, "block", "none"]})
    event = f"{prefix}Row{index}"
    doc.events[event] = [{"op": "if", "condition": {"op": "==", "args": [{"state": f"{prefix}.selected"}, save]},
                          "then": chosen if chosen is not None else [{"op": "action", "action": "save"}],
                          "else": [{"op": "setState", "values": {f"{prefix}.pick": index}}, {"op": "action", "action": "select"}]}]
    ids = row_states(doc, ident, (f"{ident}-name", f"{ident}-location"), (NAME_TINT, LOCATION_TINT))
    return group(ident, {"position": keyword("relative"), "display": keyword("none"), "width": length(width), "height": length(height),
                         "flex-shrink": number(0)},
                 [*row_plates(ident, width, height), name, location],
                 control={"role": "button", "label": PLACEHOLDER, "event": event, "states": ids})


def pager_row(doc: Document, ident: str, key: str, action: str, shown: dict, row_w: float = ROW_W) -> dict:
    """A row that pages the list to the newer or older saves (more saves than
    the list holds): a row with the home plates' marker and a Marine label."""
    width, height = U * row_w, U * ROW_H
    marker = vector(f"{ident}-marker", {**absolute(left=U * 4, top=0, width=U * 8, height=height), "pointer-events": keyword("none")}, [
        marker_path("mark", 0, height / 2 - U * 3, U * 5, rgb(MARKER))])
    text_node = label(f"{ident}-label", key, {**absolute(left=U * 14, top=0, width=U * (row_w - 18), height=height),
                      **typeface("marine", 16, height, [1, 1, 1, 0.8]), "white-space": keyword("nowrap"), "overflow": keyword("hidden"),
                      "pointer-events": keyword("none")})
    ids = row_states(doc, ident, (f"{ident}-label",), ([1, 1, 1, 0.8],))
    doc.bind(f"{ident}.display", ident, "display", {"op": "select", "args": [shown, "block", "none"]})
    return group(ident, {"position": keyword("relative"), "display": keyword("none"), "width": length(width), "height": length(height),
                         "flex-shrink": number(0)},
                 [*row_plates(ident, width, height), marker, text_node],
                 control={"role": "button", "label": key, "action": action, "states": ids})


def picture_frame(ident: str, left: float, top: float, width: float, height: float) -> list:
    """The save's picture in the stock preview (load_mapshot): black 0.60
    behind it and a 1 u #414624 border, the picture fitted inside."""
    box = absolute(left=U * left, top=U * top, width=U * width, height=U * height)
    inner = [(0.75, 0.75), ({"fraction": 1, "dp": -0.75}, 0.75), ({"fraction": 1, "dp": -0.75}, {"fraction": 1, "dp": -0.75}),
             (0.75, {"fraction": 1, "dp": -0.75})]
    return [
        vector(f"{ident}-back", box, [path("back", [(0, 0), ({"fraction": 1}, 0), ({"fraction": 1}, {"fraction": 1}), (0, {"fraction": 1})],
                                           fill=solid([0, 0, 0, 0.6]))]),
        picture(ident, "", {**absolute(left=U * (left + 1), top=U * (top + 1), width=U * (width - 2), height=U * (height - 2))}, fit="contain"),
        vector(f"{ident}-border", {**box, "pointer-events": keyword("none")}, [path("border", inner, stroke=stroke(solid(rgb(PICTURE)), U * 1))]),
    ]


# The stock page's backing (grad2): bg_darkgrad2 drawn black at 0.60 across the
# whole view, from 11 u before the canvas's leading edge to 32 u past its
# trailing one, stretched with the view. Across its width the texture is clear
# to 18.4 %, opaque from 34 % to 91.8 % and clear again by 97.3 %.
BACKING_ALPHA = 0.6
BACKING_STOPS = ((0.184, 0.0), (0.34, 1.0), (0.918, 1.0), (0.973, 0.0))


def backing_x(f: float) -> dict:
    """A fraction of the stretched backing as a view position: the texture
    spans x = -11 - E to 672 + E u, E the view's expansion each side, so a
    fraction f lies at f of the view's width plus U (683 f - 11) - 960 f dp."""
    return {"fraction": f, "dp": round(U * (683 * f - 11) - CANVAS_W * f, 4)}


def backing(ident: str = "load-backing") -> dict:
    first, last = BACKING_STOPS[0][0], BACKING_STOPS[-1][0]
    stops = [(round((f - first) / (last - first), 4), [0, 0, 0, round(BACKING_ALPHA * alpha, 4)]) for f, alpha in BACKING_STOPS]
    whole = [(0, 0), ({"fraction": 1}, 0), ({"fraction": 1}, {"fraction": 1}), (0, {"fraction": 1})]
    return vector(ident, {**FULL, "opacity": number(1), "pointer-events": keyword("none")}, [
        path("backing", whole, fill=linear((backing_x(first), 0), (backing_x(last), 0), stops))])


def table_text(key: str) -> dict:
    """`key` in every shipped language, as the engine resolves it: a
    language's openQ4 table, else the stock GUI table that openQ4 ships for
    every language (a few stock strings are corrected in some languages'
    openQ4 tables only)."""
    found = localized(key)
    for language in LANGUAGES:
        if language in found:
            continue
        for line in (STRINGS / f"{language}_guis.lang").read_text(encoding="utf-8").splitlines():
            match = re.match(r'\s*"(#str_\d+)"\s+"(.*)"\s*$', line)
            if match and match.group(1) == key:
                found[language] = match.group(2)
    return found


def lines_needed(face: str, text: str, size: float, width: float) -> int:
    """Lines `text` takes at `width` dp, broken at spaces as the host breaks it."""
    lines, current = 1, ""
    for word in text.split(" "):
        candidate = f"{current} {word}" if current else word
        if current and text_width(face, candidate, size) > width:
            lines, current = lines + 1, word
        else:
            current = candidate
    return lines


def newgame_width() -> float:
    """NEW GAME's plate: its label in the widest shipped language, the
    marker before it and a 20 dp margin after it, never under 180 dp."""
    widest = max(text_width("marine", text, 20) for text in table_text("#str_200000").values())
    return max(180.0, round(widest + 30 + 20))


def check_text_fits() -> None:
    """Every shipped language's text fits its box: the plates, headings and
    pager labels on one line, the empty state's sentence on two and a reason
    on the three lines of the strip over the picture. Generation fails
    otherwise."""
    one_line = (("#str_200001", "marine", 22.3, U * 186), ("#str_200021", "marine", 22.3, U * 186),
                ("#str_200925", "lowpixel", 13, U * (LOCATION_X - 4)), ("#str_200926", "lowpixel", 13, U * (ROW_W - LOCATION_X)),
                ("#str_231100", "marine", 20, U * ROW_W), ("#str_231106", "marine", 16, U * (ROW_W - 18)),
                ("#str_231107", "marine", 16, U * (ROW_W - 18)), ("#str_200000", "marine", 20, newgame_width() - 30))
    wrapped = (("#str_231101", "lowpixel", 17, U * ROW_W, 2),) + tuple(
        (key, "lowpixel", 15, U * (ERROR_STRIP[2] - 8), 3) for key in ("#str_231102", "#str_231103", "#str_231104", "#str_231105"))
    for key, face, size, width in one_line:
        texts = table_text(key)
        if sorted(texts) != sorted(LANGUAGES):
            raise SystemExit(f"{key} is missing from {sorted(set(LANGUAGES) - set(texts))}")
        for language, text in texts.items():
            if text_width(face, text, size) > width:
                raise SystemExit(f"{key} in {language} ({text!r}) needs {text_width(face, text, size):.0f} dp of {width:.0f}")
    for key, face, size, width, allowed in wrapped:
        texts = table_text(key)
        if sorted(texts) != sorted(LANGUAGES):
            raise SystemExit(f"{key} is missing from {sorted(set(LANGUAGES) - set(texts))}")
        for language, text in texts.items():
            if lines_needed(face, text, size, width) > allowed:
                raise SystemExit(f"{key} in {language} needs {lines_needed(face, text, size, width)} lines of {allowed}")


def load_game_document() -> dict:
    check_text_fits()
    doc = Document("openq4.loadgame")
    doc.state.update({
        "load.ingame": {"type": "boolean", "initial": False},
        "load.count": {"type": "number", "initial": 0},
        "load.first": {"type": "number", "initial": 0},
        "load.selected": {"type": "number", "initial": -1},
        "load.pick": {"type": "number", "initial": -1},
        "load.shot": {"type": "string", "initial": ""},
        "load.date": {"type": "string", "initial": ""},
        "load.time": {"type": "string", "initial": ""},
        "load.error": {"type": "string", "initial": ""},
    })
    for action, command in (("back", "loadBack"), ("select", "loadSelect"), ("save", "loadSave"), ("delete", "loadDelete"),
                            ("newer", "loadNewer"), ("older", "loadOlder"), ("newGame", "loadNewGame")):
        doc.session(action, command)
    doc.events["onBack"] = [{"op": "action", "action": "back"}]
    chosen = {"op": ">=", "args": [{"state": "load.selected"}, 0]}

    # The leading side: the selected save's picture, its date and time, and
    # the section plates.
    shot_parts = picture_frame("load-shot", *PREVIEW)
    doc.bind("load-shot.image", "load-shot", "image", {"state": "load.shot"})
    error_box = absolute(left=U * ERROR_STRIP[0], top=U * ERROR_STRIP[1], width=U * ERROR_STRIP[2], height=U * ERROR_STRIP[3])
    error = group("load-error", {**error_box, "display": keyword("none"), "background-color": colour([0, 0, 0, 0.8])}, [
        label("load-error-text", PLACEHOLDER, {**absolute(left=U * 4, top=U * 1, width=U * (ERROR_STRIP[2] - 8), height=U * (ERROR_STRIP[3] - 2)),
              **typeface("lowpixel", 15, ERROR_LINE, rgb(ERROR)), "white-space": keyword("normal"), "overflow": keyword("hidden")})])
    doc.bind("load-error.display", "load-error", "display",
             {"op": "select", "args": [{"op": "!=", "args": [{"state": "load.error"}, ""]}, "block", "none"]})
    doc.bind("load-error-text.text", "load-error-text", "text", {"state": "load.error"})
    stamp = {"white-space": keyword("nowrap"), "overflow": keyword("hidden")}
    date = label("load-date", PLACEHOLDER, {**absolute(left=U * DETAIL_LEFT, top=U * DATE_TOP, width=U * DETAIL_W, height=U * 16),
                 **typeface("lowpixel", 18, U * 16, [1, 1, 1, 0.8]), **stamp})
    time_node = label("load-time", PLACEHOLDER, {**absolute(left=U * DETAIL_LEFT, top=U * TIME_TOP, width=U * DETAIL_W, height=U * 16),
                      **typeface("lowpixel", 18, U * 16, [1, 1, 1, 0.8]), **stamp})
    doc.bind("load-date.text", "load-date", "text", {"state": "load.date"})
    doc.bind("load-time.text", "load-time", "text", {"state": "load.time"})
    plates = []
    for ident, key, left, top, action in PLATES:
        plates.append(section_plate(doc, ident, key, left, top, action=action, event=None if action else "deleteModalShow"))
        doc.bind(f"{ident}.enabled", ident, "enabled", chosen)

    # The trailing side: headings over an olive rule, then the list.
    heading = {**typeface("lowpixel", 13, U * 14, [1, 1, 1, 0.4]), "white-space": keyword("nowrap"), "overflow": keyword("hidden")}
    headings = [
        label("load-head-name", "#str_200925", {**absolute(left=U * LIST_LEFT, top=U * HEAD_TOP, width=U * (LOCATION_X - 4), height=U * 14), **heading}),
        label("load-head-location", "#str_200926", {**absolute(left=U * (LIST_LEFT + LOCATION_X - 1), top=U * HEAD_TOP,
              width=U * (ROW_W - LOCATION_X), height=U * 14), **heading}),
        vector("load-rule", absolute(left=U * LIST_LEFT, top=U * RULE_Y - 0.6, width=U * LIST_W, height=1.2), [
            path("rule", [(0, 0.6), ({"fraction": 1}, 0.6)], closed=False, stroke=stroke(solid(rgb(OLIVE, 0.26)), 1.2))]),
    ]
    rows = [save_row(doc, index) for index in range(ROWS)]
    newer = pager_row(doc, "page-newer", "#str_231106", "newer", {"op": ">", "args": [{"state": "load.first"}, 0]})
    older = pager_row(doc, "page-older", "#str_231107", "older",
                      {"op": "<", "args": [{"op": "+", "args": [{"state": "load.first"}, ROWS]}, {"state": "load.count"}]})
    column = group("load-column", {"position": keyword("relative"), "display": keyword("flex"), "flex-direction": keyword("column")},
                   [newer, *rows, older])
    viewport = group("load-list", {**absolute(left=U * LIST_LEFT, top=U * LIST_TOP, width=U * ROW_W, height=U * LIST_H),
                                   "overflow": keyword("auto")}, [column])
    # The bar's trough sits in the list's last 16 u, where the stock bar ran.
    scrollbar = objectives_scrollbar(doc, "load_scroll", "load-list", OLIVE, ORANGE, U * (LIST_LEFT + ROW_W + 8) - 18, U * LIST_TOP, U * LIST_H,
                                     line_step=U * ROW_H, key="#str_200001")

    # No saves: the empty state of section 13.13 in the list's place; at the
    # title NEW GAME opens the Single Player page.
    newgame = action_plate(doc, "load_newgame", "#str_200000", 0, U * 74, action="newGame", width=newgame_width())
    newgame["properties"]["display"] = keyword("block")
    empty = group("load-empty", {**absolute(left=U * LIST_LEFT, top=U * LIST_TOP, width=U * ROW_W, height=U * 150), "display": keyword("none")}, [
        label("load-empty-heading", "#str_231100", {**absolute(left=0, top=U * 10, width=U * ROW_W, height=U * 16),
              **typeface("marine", 20, U * 16, HEADING), "white-space": keyword("nowrap")}),
        label("load-empty-text", "#str_231101", {**absolute(left=0, top=U * 32, width=U * ROW_W, height=U * 36),
              **typeface("lowpixel", 17, 22, [1, 1, 1, 0.8]), "white-space": keyword("normal"), "overflow": keyword("hidden")}),
        newgame,
    ])
    doc.bind("load-empty.display", "load-empty", "display",
             {"op": "select", "args": [{"op": "==", "args": [{"state": "load.count"}, 0]}, "block", "none"]})
    doc.bind("load_newgame.display", "load_newgame", "display", {"op": "select", "args": [{"state": "load.ingame"}, "none", "block"]})

    back = page_prompts(doc, "load_back", action="back")
    # The plates show at once, under the title the home carried; the panel
    # and the backing fade in over 150 ms (content.in), as a stock page's do.
    panel = group("load-panel", {**FULL, "opacity": number(1)}, [*shot_parts, error, date, time_node, *headings, viewport, scrollbar,
                                                                  empty, back])
    stage = group("load-stage", {**absolute(top=0, width=CANVAS_W, height=720), "left": length(50, "%"), "margin-left": length(-CANVAS_W / 2)},
                  [*plates, panel])

    modal = confirmation(doc, "deleteModal", "#str_200021", "#str_200245", None, yes_event="deleteConfirmed")
    doc.events["deleteConfirmed"] = [{"op": "call", "event": "deleteModalHide"}, {"op": "action", "action": "delete"}]

    doc.timelines.add("arrive", 150, [track(node, "opacity", [(0, number(0)), (1, number(0)), (150, number(1))])
                                      for node in ("load-panel", "load-backing")])
    doc.timelines.add("rest", 1, [track(node, "opacity", [(0, number(0)), (1, number(0))]) for node in ("load-panel", "load-backing")])
    # Each arrival focuses the first row (the newest save, selected), else
    # NEW GAME at the title, else BACK; the last request wins.
    focus = [{"op": "focus", "control": "load_back"},
             {"op": "if", "condition": {"op": "!", "args": [{"state": "load.ingame"}]}, "then": [{"op": "focus", "control": "load_newgame"}]},
             {"op": "if", "condition": {"op": ">", "args": [{"state": "load.count"}, 0]}, "then": [{"op": "focus", "control": "row-0"}]}]
    doc.events["onActivate"] = [{"op": "playTimeline", "timeline": "arrive"}, *focus]
    doc.events["onDeactivate"] = [{"op": "playTimeline", "timeline": "rest"}]
    # Paging selects the first save of the older page or the last of the newer.
    doc.events["pagedOlder"] = [{"op": "focus", "control": "row-0"}]
    doc.events["pagedNewer"] = [{"op": "focus", "control": f"row-{ROWS - 1}"}]
    root = group("screen", {**FULL, "font-family": font("marine"), "font-size": length(16), "color": colour([1, 1, 1, 0.8])},
                 [backing(), stage, modal])
    return doc.build(root)


# The Save Game page: the stock p_savegame (section 9 "Save and load"). The
# Marine pause's SAVE GAME hands off to it as LOAD GAME does to its page. The
# saves fill the content column under SAVE NAME and LOCATION headings, 570 u
# wide; the name plate (b1_dark) and the SAVE GAME plate (b2_dark) stand under
# the list, and the prompt bar in the bottom band.
SAVE_LIST_LEFT, SAVE_LIST_TOP, SAVE_LIST_H = 35.0, 78.0, 285.0
SAVE_ROW_W = 550.0                          # tabstops 0, 180 and 550: the scrollbar takes the last 20 u
SAVE_LIST_W = 570.0
SAVE_HEAD_TOP = 62.0
NAME_PLATE = (4.0, 370.0, 484.0, 52.0)      # save_filenamebg: b1_dark at 0.40
NAME_FIELD = (49.0, 382.0, 344.0, 20.0)     # save_filename: Lowpixel at textscale 0.28
NAME_BYTES = 32                              # the stock field held 20 characters; the list column shows about 30
SAVE_PLATE = (397.0, 370.0)                  # save_b1: b2_dark, its corner marker and the SAVE GAME label
SAVE_LABEL_W = 221.0                         # the label may run past the plate to the canvas edge, as the stock one did
NAME_TEXT = 20.0                             # dp: textscale 0.28
VALIDATION = [0.8941, 0.4275, 0.3373, 1]     # a field's validation message (#E46D56)
TITLE_W = 316.0                              # dp: a dialog's title slot, from the slot's leading foot to its trailing flank
WIDE_TITLE_W = 437.2                         # dp: a wide dialog title, from the slot's leading foot to 6 dp short of the frame's edge


def name_plate() -> dict:
    """The name's plate, b1_dark drawn at 484x52 u at 0.40: its band rows
    16-45 of 64 (13-37.4 u), starting 33 of its 512 texels in, with the rail
    up the leading edge, down the 14-texel lower-leading cut and along the
    foot, and the black fill opaque to 44 % of the width, half at 62 % and
    gone by 88 % (Appendix B.1, as the home's navigation plates)."""
    left, top, width, height = NAME_PLATE
    w = U * width
    band_top, band_bottom = U * 13.0, U * 37.4
    lead, cut_x, cut_y = round(w * 33 / 512, 4), round(w * 14 / 512, 4), U * 11.4
    fade = [(0, [0, 0, 0, 1]), (0.44, [0, 0, 0, 1]), (0.62, [0, 0, 0, 0.5]), (0.88, [0, 0, 0, 0]), (1, [0, 0, 0, 0])]
    rail = [(0, rgb(RAIL_DARK)), (0.44, rgb(RAIL_DARK)), (0.62, rgb(RAIL_DARK, 0.5)), (0.88, rgb(RAIL_DARK, 0)), (1, rgb(RAIL_DARK, 0))]
    return vector("save-name-plate", {**absolute(left=U * left, top=U * top, width=w, height=U * height), "opacity": number(0.4),
                                      "pointer-events": keyword("none")}, [
        path("fill", [(lead, band_top), (w, band_top), (w, band_bottom), (lead + cut_x, band_bottom), (lead, band_bottom - cut_y)],
             fill=linear((0, 0), (w, 0), fade)),
        path("rail", [(lead + 0.75, band_top), (lead + 0.75, band_bottom - cut_y), (lead + cut_x, band_bottom - 0.75), (w, band_bottom - 0.75)],
             closed=False, stroke=stroke(linear((0, 0), (w, 0), rail), 1.5)),
    ])


def name_field(doc: Document) -> dict:
    """The save's name (save_filename): a text field in Lowpixel at the stock
    field's textscale 0.28 (20 dp), white 0.80, on the name plate. Accept or
    typing opens it, and Enter saves under the name (the stock field's
    onEnter). An empty field says what it wants; while it is being edited
    empty, the validation line above the plate asks for a name."""
    left, top, width, height = NAME_FIELD
    ident = "save-name"
    w, line = U * width, U * height
    parts = {part: f"{ident}-{part}" for part in ("viewport", "text", "selection", "caret", "composition", "validation")}
    def paint(part: str, thickness: float, tall: float, tint: list) -> dict:
        return group(parts[part], {**absolute(left=0, top=0, width=thickness, height=tall), "background-color": colour(tint),
                                   "pointer-events": keyword("none"), "display": keyword("block"), "opacity": number(1)})
    text_node = label(parts["text"], PLACEHOLDER, {**absolute(left=0, top=0, width=4096, height=line),
                      **typeface("lowpixel", NAME_TEXT, line, [1, 1, 1, 0.8]), "white-space": keyword("pre"), "text-align": keyword("left")})
    viewport = group(parts["viewport"], {**absolute(left=0, top=0, width=w, height=line), "overflow": keyword("hidden")}, [
        paint("selection", 0, line, rgb(ORANGE, 0.4)), text_node, paint("caret", 1.5, line, [1, 1, 1, 1]),
        paint("composition", 0, 1, rgb(ORANGE))])
    validation = label(parts["validation"], "#str_231108", {**absolute(left=0, top=-U * 13, width=w, height=U * 11),
                       **typeface("lowpixel", 14, U * 11, VALIDATION), "white-space": keyword("nowrap"), "overflow": keyword("hidden"),
                       "display": keyword("none")})
    # The name the field wants, until it holds one or is being typed into.
    hint = label(f"{ident}-hint", "#str_231109", {**absolute(left=0, top=0, width=w, height=line),
                 **typeface("lowpixel", NAME_TEXT, line, [1, 1, 1, 0.35]), "white-space": keyword("nowrap"), "overflow": keyword("hidden"),
                 "pointer-events": keyword("none"), "display": keyword("block")})
    doc.bind(f"{ident}-hint.display", f"{ident}-hint", "display",
             {"op": "select", "args": [{"op": "&&", "args": [{"op": "==", "args": [{"state": "save.name"}, ""]},
                                                              {"op": "!", "args": [{"state": "ui.numberDraftsPending"}]}]}, "block", "none"]})
    # Focus draws the plates' orange inset under the name; the pointer half of it.
    focus = vector(f"{ident}-focus", {**absolute(left=0, top=0, width=w, height=line + U * 4), "opacity": number(0),
                                      "pointer-events": keyword("none")}, [
        path("inset", [(0, line + U * 2), (round(w * 0.9, 4), line + U * 2)], closed=False, stroke=stroke(solid(rgb(ORANGE)), 1.2))])
    rest, half, lit = number(0), number(0.5), number(1)
    ids = doc.states(ident, {
        "default": [(f"{ident}-focus", "opacity", rest), (parts["text"], "color", colour([1, 1, 1, 0.8]))],
        "hover": [(f"{ident}-focus", "opacity", half), (parts["text"], "color", colour([1, 1, 1, 1]))],
        "focus": [(f"{ident}-focus", "opacity", lit), (parts["text"], "color", colour([1, 1, 1, 1]))],
        "pressed": [(f"{ident}-focus", "opacity", lit), (parts["text"], "color", colour([1, 1, 1, 1]))],
        "disabled": [(f"{ident}-focus", "opacity", rest), (parts["text"], "color", colour([1, 1, 1, 0.3]))],
    })
    control = {"role": "text", "label": "#str_200925", "action": "rename", "value": {"state": "save.name"},
               "maxBytes": NAME_BYTES, "parts": parts, "states": ids}
    return group(ident, absolute(left=U * left, top=U * top, width=w, height=line), [focus, hint, viewport, validation], control=control)


def check_save_text_fits() -> None:
    """Every shipped language's text fits its box on the Save Game page: the
    plates, headings, pager labels, field hint and validation on one line,
    the empty state's sentence on two, and each dialog's body on the three
    lines above its actions (the overwrite dialog keeps the third for the
    save's name). Generation fails otherwise."""
    one_line = (("#str_200003", "marine", 22.3, U * SAVE_LABEL_W), ("#str_200925", "lowpixel", 13, U * (LOCATION_X - 4)),
                ("#str_200926", "lowpixel", 13, U * (SAVE_ROW_W - LOCATION_X)), ("#str_231100", "marine", 20, U * SAVE_ROW_W),
                ("#str_231106", "marine", 16, U * (SAVE_ROW_W - 18)), ("#str_231107", "marine", 16, U * (SAVE_ROW_W - 18)),
                ("#str_200923", "marine", 20, CLOSE_W - 30),
                ("#str_231108", "lowpixel", 14, U * NAME_FIELD[2]), ("#str_231109", "lowpixel", NAME_TEXT, U * NAME_FIELD[2]),
                ("#str_200252", "marine", 20, WIDE_TITLE_W), ("#str_200266", "marine", 20, TITLE_W))
    body = 480 - 66
    wrapped = (("#str_231101", "lowpixel", 17, U * SAVE_ROW_W, 2), ("#str_200253", "lowpixel", 17, body, 2)) + tuple(
        (key, "lowpixel", 17, body, 3) for key in ("#str_200982", "#str_231110", "#str_231111", "#str_231112", "#str_231113"))
    for key, face, size, width in one_line:
        texts = table_text(key)
        if sorted(texts) != sorted(LANGUAGES):
            raise SystemExit(f"{key} is missing from {sorted(set(LANGUAGES) - set(texts))}")
        # A dialog title is set 0.075 em tighter between its glyphs.
        tighten = 0.075 * size if width in (TITLE_W, WIDE_TITLE_W) else 0
        for language, text in texts.items():
            needed = text_width(face, text, size) - tighten * (len(text) - 1)
            if needed > width:
                raise SystemExit(f"{key} in {language} ({text!r}) needs {needed:.0f} dp of {width:.0f}")
    for key, face, size, width, allowed in wrapped:
        texts = table_text(key)
        if sorted(texts) != sorted(LANGUAGES):
            raise SystemExit(f"{key} is missing from {sorted(set(LANGUAGES) - set(texts))}")
        for language, text in texts.items():
            if lines_needed(face, text, size, width) > allowed:
                raise SystemExit(f"{key} in {language} needs {lines_needed(face, text, size, width)} lines of {allowed}")


def save_game_document() -> dict:
    check_save_text_fits()
    doc = Document("openq4.savegame")
    doc.state.update({
        "save.count": {"type": "number", "initial": 0},
        "save.first": {"type": "number", "initial": 0},
        "save.selected": {"type": "number", "initial": -1},
        "save.pick": {"type": "number", "initial": -1},
        "save.name": {"type": "string", "initial": ""},
        "save.target": {"type": "string", "initial": ""},
        "save.notice": {"type": "string", "initial": ""},
        # The adapter keeps this: the name field holds text not yet entered.
        "ui.numberDraftsPending": {"type": "boolean", "initial": False},
    })
    for action, command in (("back", "saveBack"), ("select", "saveSelect"), ("save", "saveSave"), ("overwrite", "saveOverwrite"),
                            ("newer", "saveNewer"), ("older", "saveOlder")):
        doc.session(action, command)
    # Entering the name writes it into save.name, then saves under it.
    doc.actions["rename"] = {"input": "string", "operation": "ui.state.set",
                             "arguments": {"key": "save.name", "value": {"input": "value"}, "event": "nameEntered"}}
    doc.actions["editName"] = {"operation": "ui.numberDrafts.focus", "arguments": {}}
    doc.events["nameEntered"] = [{"op": "action", "action": "save"}]
    # SAVE GAME saves under the entered name. A name typed but not entered
    # takes the focus back, where Enter saves under it.
    doc.events["saveRequested"] = [{"op": "if", "condition": {"state": "ui.numberDraftsPending"},
                                    "then": [{"op": "action", "action": "editName"}], "else": [{"op": "action", "action": "save"}]}]
    doc.events["onBack"] = [{"op": "action", "action": "back"}]

    # The list: headings over an olive rule, the saves, newest first, and the
    # pages either side of them. A row's first Accept selects its save, whose
    # name the field then shows; Accept on the selected save saves over it.
    heading = {**typeface("lowpixel", 13, U * 14, [1, 1, 1, 0.4]), "white-space": keyword("nowrap"), "overflow": keyword("hidden")}
    headings = [
        label("save-head-name", "#str_200925", {**absolute(left=U * SAVE_LIST_LEFT, top=U * SAVE_HEAD_TOP, width=U * (LOCATION_X - 4),
                                                          height=U * 14), **heading}),
        label("save-head-location", "#str_200926", {**absolute(left=U * (SAVE_LIST_LEFT + LOCATION_X - 1), top=U * SAVE_HEAD_TOP,
                                                              width=U * (SAVE_ROW_W - LOCATION_X), height=U * 14), **heading}),
        vector("save-rule", absolute(left=U * SAVE_LIST_LEFT, top=U * RULE_Y - 0.6, width=U * SAVE_LIST_W, height=1.2), [
            path("rule", [(0, 0.6), ({"fraction": 1}, 0.6)], closed=False, stroke=stroke(solid(rgb(OLIVE, 0.26)), 1.2))]),
    ]
    chosen = [{"op": "call", "event": "saveRequested"}]
    rows = [save_row(doc, index, "save", SAVE_ROW_W, chosen) for index in range(ROWS)]
    newer = pager_row(doc, "page-newer", "#str_231106", "newer", {"op": ">", "args": [{"state": "save.first"}, 0]}, SAVE_ROW_W)
    older = pager_row(doc, "page-older", "#str_231107", "older",
                      {"op": "<", "args": [{"op": "+", "args": [{"state": "save.first"}, ROWS]}, {"state": "save.count"}]}, SAVE_ROW_W)
    column = group("save-column", {"position": keyword("relative"), "display": keyword("flex"), "flex-direction": keyword("column")},
                   [newer, *rows, older])
    viewport = group("save-list", {**absolute(left=U * SAVE_LIST_LEFT, top=U * SAVE_LIST_TOP, width=U * SAVE_ROW_W, height=U * SAVE_LIST_H),
                                   "overflow": keyword("auto")}, [column])
    scrollbar = objectives_scrollbar(doc, "save_scroll", "save-list", OLIVE, ORANGE, U * (SAVE_LIST_LEFT + SAVE_ROW_W + 8) - 18,
                                     U * SAVE_LIST_TOP, U * SAVE_LIST_H, line_step=U * ROW_H, key="#str_200003")
    # No saves yet: the empty state of section 13.13 in the list's place.
    empty = group("save-empty", {**absolute(left=U * SAVE_LIST_LEFT, top=U * SAVE_LIST_TOP, width=U * SAVE_ROW_W, height=U * 80),
                                 "display": keyword("none")}, [
        label("save-empty-heading", "#str_231100", {**absolute(left=0, top=U * 10, width=U * SAVE_ROW_W, height=U * 16),
              **typeface("marine", 20, U * 16, HEADING), "white-space": keyword("nowrap")}),
        label("save-empty-text", "#str_231101", {**absolute(left=0, top=U * 32, width=U * SAVE_ROW_W, height=U * 36),
              **typeface("lowpixel", 17, 22, [1, 1, 1, 0.8]), "white-space": keyword("normal"), "overflow": keyword("hidden")}),
    ])
    doc.bind("save-empty.display", "save-empty", "display",
             {"op": "select", "args": [{"op": "==", "args": [{"state": "save.count"}, 0]}, "block", "none"]})

    # Under the list: the name on its plate, then SAVE GAME, which needs a
    # name, entered or typed.
    save_plate = section_plate(doc, "save_go", "#str_200003", *SAVE_PLATE, event="saveRequested", label_w=SAVE_LABEL_W)
    doc.bind("save_go.enabled", "save_go", "enabled",
             {"op": "||", "args": [{"op": "!=", "args": [{"state": "save.name"}, ""]}, {"state": "ui.numberDraftsPending"}]})
    field = name_field(doc)
    back = page_prompts(doc, "save_back", action="back")
    panel = group("save-panel", {**FULL, "opacity": number(1)}, [*headings, viewport, scrollbar, empty, name_plate(), field, back])
    stage = group("save-stage", {**absolute(top=0, width=CANVAS_W, height=720), "left": length(50, "%"), "margin-left": length(-CANVAS_W / 2)},
                  [save_plate, panel])

    # Saving over a save asks first and names it; an autosave, or a save the
    # session refuses, says why.
    overwrite = confirmation(doc, "overwriteModal", "#str_200252", "#str_200253", None, yes_event="overwriteConfirmed",
                             wide_title=True)
    doc.events["overwriteConfirmed"] = [{"op": "call", "event": "overwriteModalHide"}, {"op": "action", "action": "overwrite"}]
    target = label("overwriteModal-target", PLACEHOLDER, {**absolute(left=33, top=71 + 44, width=480 - 66, height=22),
                   **typeface("lowpixel", 17, 22, rgb(ORANGE)), "white-space": keyword("nowrap"), "overflow": keyword("hidden")})
    doc.bind("overwriteModal-target.text", "overwriteModal-target", "text", {"state": "save.target"})
    contents = next(child for child in walk(overwrite) if child.get("id") == "overwriteModal-contents")
    contents["children"].append(target)
    notice = confirmation(doc, "noticeModal", "#str_200266", PLACEHOLDER, None, close_key="#str_200923")
    doc.bind("noticeModal-body.text", "noticeModal-body", "text", {"state": "save.notice"})

    doc.timelines.add("arrive", 150, [track(node, "opacity", [(0, number(0)), (1, number(0)), (150, number(1))])
                                      for node in ("save-panel", "save-backing")])
    doc.timelines.add("rest", 1, [track(node, "opacity", [(0, number(0)), (1, number(0))]) for node in ("save-panel", "save-backing")])
    # Each arrival focuses the name, ready for typing, as the stock page's
    # field took the keys.
    doc.events["onActivate"] = [{"op": "playTimeline", "timeline": "arrive"}, {"op": "focus", "control": "save-name"}]
    doc.events["onDeactivate"] = [{"op": "playTimeline", "timeline": "rest"}]
    doc.events["pagedOlder"] = [{"op": "focus", "control": "row-0"}]
    doc.events["pagedNewer"] = [{"op": "focus", "control": f"row-{ROWS - 1}"}]
    root = group("screen", {**FULL, "font-family": font("marine"), "font-size": length(16), "color": colour([1, 1, 1, 0.8])},
                 [backing("save-backing"), stage, overwrite, notice])
    return doc.build(root)


def walk(node: dict):
    """`node` and every node under it."""
    yield node
    for child in node.get("children", ()):
        yield from walk(child)
