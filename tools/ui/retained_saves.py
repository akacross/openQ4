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
Lowpixel SAVE NAME and LOCATION headings and an olive rule; BACK in the bottom
band at 532,441 u.

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

from build_retained_screens import (CANVAS_W, FULL, LANGUAGES, MARKER, OLIVE, ORANGE, PICTURE, RAIL_DARK, STRINGS, U,
                                    Document, absolute, action_plate, colour, confirmation, font, group, keyword, label, length,
                                    linear, localized, marker_path, number, objectives_scrollbar, path, picture, rgb, solid,
                                    stroke, text_width, track, transform, typeface, vector)

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
                  event: str | None = None) -> dict:
    """A section navigation plate (b2_dark drawn at 208x52 u, Appendix B.1):
    its band rows 16-45 of 64 (13-37.4 u), a lower-leading cut from row 32,
    the #CCCC51 rail along the leading edge, the cut and the bottom, a black
    fill opaque to 57 % of the width, half at 72 % and gone by 94 %, drawn at
    0.40; the corner marker 8,19 u into the rectangle and the Marine label
    (textscale 0.31, 22.3 dp) from 18 u. Hover and focus light the plate to
    0.80 and turn the marker and label orange, as on the home plates."""
    width, height = U * 208, U * 52
    band_top, band_bottom, cut = U * 13.0, U * 37.4, U * 11.4
    fade = [(0, [0, 0, 0, 1]), (0.57, [0, 0, 0, 1]), (0.72, [0, 0, 0, 0.5]), (0.94, [0, 0, 0, 0]), (1, [0, 0, 0, 0])]
    rail = [(0, rgb(RAIL_DARK)), (0.57, rgb(RAIL_DARK)), (0.72, rgb(RAIL_DARK, 0.5)), (0.94, rgb(RAIL_DARK, 0)), (1, rgb(RAIL_DARK, 0))]
    plate = vector(f"{ident}-plate", {**absolute(left=0, top=0, width=width, height=height), "opacity": number(0.4)}, [
        path("fill", [(0, band_top), (width, band_top), (width, band_bottom), (cut, band_bottom), (0, band_bottom - cut)],
             fill=linear((0, 0), (width, 0), fade)),
        path("rail", [(0.75, band_top), (0.75, band_bottom - cut), (cut, band_bottom - 0.75), (width, band_bottom - 0.75)],
             closed=False, stroke=stroke(linear((0, 0), (width, 0), rail), 1.5)),
    ])
    focus = vector(f"{ident}-focus", {**absolute(left=0, top=0, width=width, height=height), "opacity": number(0)}, [
        path("inset", [(cut + 2, band_bottom - 3.2), (width * 0.72, band_bottom - 3.2)], closed=False, stroke=stroke(solid(rgb(ORANGE)), 1.2))])
    marker_rest = vector(f"{ident}-marker", {**absolute(left=0, top=0, width=width, height=height), "opacity": number(0.4)}, [
        marker_path("mark", U * 10.75, U * 21.75, U * 5.5, rgb(MARKER))])
    marker_hot = vector(f"{ident}-marker-hot", {**absolute(left=0, top=0, width=width, height=height), "opacity": number(0)}, [
        marker_path("mark", U * 10.75, U * 21.75, U * 5.5, rgb(ORANGE))])
    text_node = label(f"{ident}-label", key, {**absolute(left=U * 18, top=band_top, width=U * 186, height=band_bottom - band_top),
                      **typeface("marine", 22.3, band_bottom - band_top, [1, 1, 1, 0.8]), "white-space": keyword("nowrap"),
                      "transform": transform()})
    lit, rest = number(1), number(0)
    ids = doc.states(ident, {
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
    })
    control = {"role": "button", "label": key, "states": ids}
    if action:
        control["action"] = action
    else:
        control["event"] = event
    return group(ident, absolute(left=U * left, top=U * top, width=width, height=height),
                 [plate, focus, marker_rest, marker_hot, text_node], control=control)


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


def save_row(doc: Document, index: int) -> dict:
    """One of the list's rows: the save's name in the SAVE NAME column and its
    level in the LOCATION column (tabstops 0 and 180 u), Lowpixel at the stock
    list's textscale 0.22 (15.8 dp) on its 20 u pitch. Its first Accept selects
    the save; Accept on the selected save loads it."""
    ident, key = f"row-{index}", f"load.row{index}"
    doc.state[f"{key}.name"] = {"type": "string", "initial": ""}
    doc.state[f"{key}.location"] = {"type": "string", "initial": ""}
    width, height = U * ROW_W, U * ROW_H
    cell = {"white-space": keyword("nowrap"), "overflow": keyword("hidden"), "pointer-events": keyword("none")}
    name = label(f"{ident}-name", PLACEHOLDER, {**absolute(left=U * 4, top=0, width=U * (LOCATION_X - 8), height=height),
                 **typeface("lowpixel", 15.8, height, NAME_TINT), **cell})
    location = label(f"{ident}-location", PLACEHOLDER, {**absolute(left=U * LOCATION_X, top=0, width=U * (ROW_W - LOCATION_X - 4), height=height),
                     **typeface("lowpixel", 15.8, height, LOCATION_TINT), **cell})
    doc.bind(f"{ident}-name.text", f"{ident}-name", "text", {"state": f"{key}.name"})
    doc.bind(f"{ident}-location.text", f"{ident}-location", "text", {"state": f"{key}.location"})
    save = {"op": "+", "args": [{"state": "load.first"}, index]}
    doc.bind(f"{ident}.display", ident, "display",
             {"op": "select", "args": [{"op": "<", "args": [save, {"state": "load.count"}]}, "block", "none"]})
    doc.bind(f"{ident}-selected.display", f"{ident}-selected", "display",
             {"op": "select", "args": [{"op": "==", "args": [{"state": "load.selected"}, save]}, "block", "none"]})
    event = f"loadRow{index}"
    doc.events[event] = [{"op": "if", "condition": {"op": "==", "args": [{"state": "load.selected"}, save]},
                          "then": [{"op": "action", "action": "save"}],
                          "else": [{"op": "setState", "values": {"load.pick": index}}, {"op": "action", "action": "select"}]}]
    ids = row_states(doc, ident, (f"{ident}-name", f"{ident}-location"), (NAME_TINT, LOCATION_TINT))
    return group(ident, {"position": keyword("relative"), "display": keyword("none"), "width": length(width), "height": length(height),
                         "flex-shrink": number(0)},
                 [*row_plates(ident, width, height), name, location],
                 control={"role": "button", "label": PLACEHOLDER, "event": event, "states": ids})


def pager_row(doc: Document, ident: str, key: str, action: str, shown: dict) -> dict:
    """A row that pages the list to the newer or older saves (more saves than
    the list holds): a row with the home plates' marker and a Marine label."""
    width, height = U * ROW_W, U * ROW_H
    marker = vector(f"{ident}-marker", {**absolute(left=U * 4, top=0, width=U * 8, height=height), "pointer-events": keyword("none")}, [
        marker_path("mark", 0, height / 2 - U * 3, U * 5, rgb(MARKER))])
    text_node = label(f"{ident}-label", key, {**absolute(left=U * 14, top=0, width=U * (ROW_W - 18), height=height),
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


def backing() -> dict:
    first, last = BACKING_STOPS[0][0], BACKING_STOPS[-1][0]
    stops = [(round((f - first) / (last - first), 4), [0, 0, 0, round(BACKING_ALPHA * alpha, 4)]) for f, alpha in BACKING_STOPS]
    whole = [(0, 0), ({"fraction": 1}, 0), ({"fraction": 1}, {"fraction": 1}), (0, {"fraction": 1})]
    return vector("load-backing", {**FULL, "opacity": number(1), "pointer-events": keyword("none")}, [
        path("backing", whole, fill=linear((backing_x(first), 0), (backing_x(last), 0), stops))])


def table_text(key: str) -> dict:
    """`key` in every shipped language: the openQ4 tables, else the stock
    GUI tables that openQ4 ships for every language."""
    texts = localized(key)
    if texts:
        return texts
    found = {}
    for language in LANGUAGES:
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
                ("#str_231107", "marine", 16, U * (ROW_W - 18)), ("#str_200000", "marine", 20, newgame_width() - 30),
                ("#str_200018", "marine", 20, U * 109 - 30))
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

    back = action_plate(doc, "load_back", "#str_200018", U * 532, U * 441, action="back", width=U * 109)
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
