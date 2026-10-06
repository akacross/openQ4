"""The retained Join Game sub-page, Multiplayer's server browser
(docs/dev/ui-visual-design.md sections 8 and 9, "Menu levels" and "Lists";
FLOW-050).

Built by tools/ui/build_retained_screens.py, which writes and checks it with
the other retained screens. JOIN GAME on the Multiplayer page goes one level
deeper to guis/menu/joingame.q4ui as CREATE SERVER goes to Create Server,
on the same sub-page frame (retained_subpage); Back climbs out onto JOIN
GAME.

The content is the stock p_mp_browse's over the stock page backing: MOD with
its spinner at 27,46 u and SOURCE with its INTERNET and LAN tags at 324,46 u;
the server list at 23,83 u under its column headings on the stock 18 u rows,
the sort's column marked (a heading sorts by its column, and again the other
way); the scan's status at 41,291 u beside CLEAR SORTING; REFRESH LIST and
GET NEW LIST at 19,330 and 19,358 u; the chosen server's levelshot at
240,337 u; JOIN SERVER at 385,330 u and the favorite toggle under it; BACK in
the bottom band. The list's symbols (favorite, password, dedicated server,
repeater) sit on their tiles as section 9's symbol table draws them; the
stock PunkBuster column is gone (a discontinued service, no replacement
column).

The session owns the list: it publishes the scan's visible servers a page of
JOIN_ROWS at a time (join.row<i>.*), their count, the scan's status, the
source, the mod filter and the sort, and the chosen server (join.selected,
its levelshot and whether it is a favorite), and each control asks through
its own verb. The stock page's JOIN IP ADDRESS and FIND PLAYER/CLAN are not
built yet, so the session keeps the page opt-in (RETAINED_JOIN_GAME_MISSING).
"""
from __future__ import annotations

import math

from build_retained_screens import (FULL, OLIVE, ORANGE, U, VALUE, Document, absolute, action_plate, group, keyword, label, length,
                                    number, objectives_scrollbar, path, rgb, solid, stroke, text_width, typeface, vector)
from retained_create_server import BACK, header_band
from retained_difficulty import check_fits, primary_plate
from retained_saves import PLACEHOLDER, pager_row, picture_frame, row_plates, row_states, table_text
from retained_subpage import subpage_document

JOIN_ROWS = 64                             # RETAINED_JOIN_ROWS in the session
LIST = (23.0, 83.0, 604.0, 202.0)          # u: mp_browse_serverlist
ROW_H = 18.0                               # u: its itemheight
HEADER = (22.0, 54.0, 587.0, 37.0)         # u: mp_browse_header
HEADING_TOP = 70.0                         # u: the headings' row
# The columns: the session's sort for each (serverSort_t), its heading (a
# symbol column has none), its tab stop and width in the list (u) and its sort
# verb. The symbol columns keep the stock list's tab stops, the repeater's
# after PING as the stock list had it; without the PunkBuster column the name
# starts at its stop. The stock columns after the name were too narrow for
# every language's heading with the sort's chevron, so they take what the
# name column spared.
COLUMNS = (
    ("fav", 6, None, 5.0, 21.0, "joinSortFavorite"),
    ("lock", 7, None, 26.0, 21.0, "joinSortLocked"),
    ("ded", 8, None, 47.0, 21.0, "joinSortDedicated"),
    ("name", 1, "#str_200036", 68.0, 211.0, "joinSortName"),
    ("ping", 0, "#str_200037", 279.0, 40.0, "joinSortPing"),
    ("rep", 10, None, 319.0, 21.0, "joinSortRepeater"),
    ("players", 2, "#str_200038", 340.0, 60.0, "joinSortPlayers"),
    ("type", 3, "#str_200039", 400.0, 90.0, "joinSortGameType"),
    ("map", 4, "#str_200040", 490.0, 96.0, "joinSortMap"),
)
SYMBOL = 16.0                              # dp: a list symbol's tile
# The stock list symbols' colors (gfx/guis/mainmenu/icon_*): the server
# case's gray and its green power light, the television's gray and its
# color bars.
CASE_GRAY, CASE_PANEL, POWER_GREEN = "#A5AAB5", "#394D52", "#18BE08"
TV_GRAY, TV_SCREEN, TV_BARS = "#ADAAA5", "#141414", ("#B4B45A", "#31DBA5", "#CE1052", "#08088A")
MOD = (27.0, 46.0, 59.0)                   # u: mp_browse_mod, "MOD:" right-aligned, clear of the spinner
MOD_VALUE = (113.0, 150.0)                 # u: mp_browse_filter_mod, inside the spinner squares
MOD_SPIN = ((88.0, "joinModPrevious", "previous"), (266.0, "joinModNext", "next"))  # u: the spinner squares, 22x16
# u: mp_browse_info_mapshot, 20 u left of the stock 260 u so the favorite
# toggle, as wide as its longest translation, clears it
SHOT = (240.0, 337.0, 116.0, 88.0)
FAVORITE_TOP = 400.0                       # u: mp_b_browse_favsel
FAVORITE_KEYS = ("#str_200292", "#str_200293")  # ADD TO FAVORITES, REMOVE FAVORITE
SOURCE = (324.0, 46.0)                     # u: mp_browse_source
SOURCE_END = 613.0                         # u: where the stock LAN tag ends
# The source tags: right-aligned at SOURCE_END, each as wide as its longest
# translation (the stock 50 u LAN tag held "LAN" only).
TAG_KEYS = (("internet", "#str_200033", "joinSourceInternet", False), ("lan", "#str_200034", "joinSourceLan", True))
TAG_GAP = 6.0
STATUS = (41.0, 291.0)                     # u: mp_browse_t_sortnotice
# CLEAR SORTING ends where the stock plate does (615 u) and is as wide as its
# longest translation needs, at least the stock 181 u; the status line runs
# to 6 u before it.
CLEAR_SORT = (615.0, 286.0, 181.0)         # u: right end, top, least width
LIST_ACTIONS = (("join_refresh", "#str_200028", 19.0, 330.0, "joinRefresh"), ("join_newlist", "#str_200029", 19.0, 358.0, "joinNewList"))
JOIN = (385.0, 330.0, 230.0, 37.0)         # u: mp_browse_b4 (JOIN SERVER)
CELL_TEXT = 14.0                           # dp: the stock list's 0.2 textscale
HEADING_TEXT = 12.0
CHEVRON_ROOM = 10.0                        # dp: the sort's chevron after a heading
TAG_TEXT = 15.0


def circle_points(cx: float, cy: float, radius: float, start: float, end: float, steps: int) -> list:
    """Points along an arc, from `start` to `end` degrees (0 up, clockwise)."""
    return [(round(cx + radius * math.sin(math.radians(start + (end - start) * step / steps)), 3),
             round(cy - radius * math.cos(math.radians(start + (end - start) * step / steps)), 3)) for step in range(steps + 1)]


def symbol(ident: str, kind: str, opacity: float = 1) -> dict:
    """A server-list symbol on its tile (section 9: a small dark tile with a
    cut upper-leading corner, part of the symbol), SYMBOL dp square: the
    favorite's gold star, the password's padlock, the dedicated server's case
    with its green power light, the repeater's television with its antennas
    and color bars."""
    s = SYMBOL
    paths = [path("tile", [(3, 0), (s, 0), (s, s), (0, s), (0, 3)], fill=solid([0, 0, 0, 0.5]))]
    if kind == "fav":
        points = []
        for index in range(10):
            radius = 6.2 if index % 2 == 0 else 2.5
            angle = math.pi / 2 + index * math.pi / 5
            points.append((round(8 + radius * math.cos(angle), 3), round(8.6 - radius * math.sin(angle), 3)))
        paths.append(path("star", points, fill=solid(rgb(VALUE)), stroke=stroke(solid(rgb("#C8501E", 0.8)), 0.8)))
    elif kind == "lock":
        paths += [path("shackle", [(5.5, 8), (5.5, 5), (6.75, 3.25), (9.25, 3.25), (10.5, 5), (10.5, 8)], closed=False,
                       stroke=stroke(solid(rgb(CASE_GRAY)), 1.5)),
                  path("body", [(3.5, 7.5), (12.5, 7.5), (12.5, 13.5), (3.5, 13.5)], fill=solid(rgb(CASE_GRAY))),
                  path("keyhole", [(7.4, 9.3), (8.6, 9.3), (8.6, 11.9), (7.4, 11.9)], fill=solid([0, 0, 0, 0.85]))]
    elif kind == "ded":
        paths += [path("case", [(4, 1.75), (12, 1.75), (12, 14.25), (4, 14.25)], fill=solid(rgb(CASE_GRAY))),
                  path("drive", [(5.25, 3), (10.75, 3), (10.75, 4.25), (5.25, 4.25)], fill=solid([0, 0, 0, 0.9])),
                  path("button", [(9.5, 5.25), (10.5, 5.25), (10.5, 6.25), (9.5, 6.25)], fill=solid([0, 0, 0, 0.9])),
                  path("panel", [(5.25, 7.5), (10.75, 7.5), (10.75, 13), (5.25, 13)], fill=solid(rgb(CASE_PANEL))),
                  path("power-ring", circle_points(8, 10.6, 1.75, 35, 325, 10), closed=False, stroke=stroke(solid(rgb(POWER_GREEN)), 0.9)),
                  path("power-bar", [(8, 8.4), (8, 10.4)], closed=False, stroke=stroke(solid(rgb(POWER_GREEN)), 0.9))]
    else:
        paths += [path("antennas", [(5, 1.5), (8, 5), (11, 1.5)], closed=False, stroke=stroke(solid(rgb(TV_GRAY)), 0.9)),
                  path("set", [(2, 5), (14, 5), (14, 14), (2, 14)], fill=solid(rgb(TV_GRAY))),
                  path("screen", [(3.25, 6.25), (12.75, 6.25), (12.75, 12.75), (3.25, 12.75)], fill=solid(rgb(TV_SCREEN)))]
        for index, colour_value in enumerate(TV_BARS):
            x0 = round(3.75 + index * 2.25, 3)
            paths.append(path(f"bar{index}", [(x0, 6.75), (x0 + 2.25, 6.75), (x0 + 2.25, 11), (x0, 11)], fill=solid(rgb(colour_value))))
    return vector(ident, {"position": keyword("absolute"), "display": keyword("none"), "width": length(s), "height": length(s),
                          "opacity": number(opacity), "pointer-events": keyword("none")}, paths)


def server_row(doc: Document, index: int, row_w: float) -> dict:
    """One of the list's rows: a server's symbols (favorite, password,
    dedicated server, repeater) and its name, ping, players, game type and map
    at the stock tab stops. Its first Accept chooses the server; Accept on the
    chosen one moves on to JOIN SERVER."""
    ident, key = f"server-{index}", f"join.row{index}"
    width, height = U * row_w, U * ROW_H
    tint = [1, 1, 1, 0.8]
    cells, texts = [], []
    for column, _sort, key_text, left, column_w, _verb in COLUMNS:
        node = f"{ident}-{column}"
        if key_text is None:
            doc.state[f"{key}.{column}"] = {"type": "boolean", "initial": False}
            icon = symbol(node, column)
            icon["properties"].update({"left": length(round(U * left + (U * column_w - SYMBOL) / 2, 3)),
                                       "top": length(round((height - SYMBOL) / 2, 3))})
            doc.bind(f"{node}.display", node, "display", {"op": "select", "args": [{"state": f"{key}.{column}"}, "block", "none"]})
            cells.append(icon)
            continue
        doc.state[f"{key}.{column}"] = {"type": "string", "initial": ""}
        cells.append(label(node, PLACEHOLDER, {**absolute(left=U * left, top=0, width=U * column_w - 4, height=height),
                                                **typeface("lowpixel", CELL_TEXT, height, tint), "white-space": keyword("nowrap"),
                                                "overflow": keyword("hidden"), "pointer-events": keyword("none")}))
        doc.bind(f"{node}.text", node, "text", {"state": f"{key}.{column}"})
        texts.append(node)
    chosen = {"op": "+", "args": [{"state": "join.first"}, index]}
    doc.bind(f"{ident}.display", ident, "display",
             {"op": "select", "args": [{"op": "<", "args": [chosen, {"state": "join.count"}]}, "block", "none"]})
    doc.bind(f"{ident}-selected.display", f"{ident}-selected", "display",
             {"op": "select", "args": [{"op": "==", "args": [{"state": "join.selected"}, chosen]}, "block", "none"]})
    event = f"serverRow{index}"
    doc.events[event] = [{"op": "if", "condition": {"op": "==", "args": [{"state": "join.selected"}, chosen]},
                          "then": [{"op": "focus", "control": "join_server"}],
                          "else": [{"op": "setState", "values": {"join.pick": index}}, {"op": "action", "action": "joinPick"}]}]
    ids = row_states(doc, ident, tuple(texts), tuple(tint for _ in texts))
    return group(ident, {"position": keyword("relative"), "display": keyword("none"), "width": length(width), "height": length(height),
                         "flex-shrink": number(0)}, [*row_plates(ident, width, height), *cells],
                 control={"role": "button", "label": PLACEHOLDER, "event": event, "states": ids})


def heading(doc: Document, column: str, sort: int, key: str | None, left: float, width: float, verb: str) -> dict:
    """A column's heading in the header band: its label (an icon column's
    icon), a button sorting by the column, and the sort's chevron while the
    list is sorted by it, pointing up while it runs ascending."""
    ident = f"heading-{column}"
    doc.session(verb, verb)
    height = U * 16
    tint = [1, 1, 1, 0.6]
    if key is not None:
        face = label(f"{ident}-label", key, {**absolute(left=0, top=0, width=U * width - CHEVRON_ROOM, height=height),
                                              **typeface("lowpixel", HEADING_TEXT, height, tint), "white-space": keyword("nowrap"),
                                              "overflow": keyword("hidden"), "pointer-events": keyword("none")})
    else:
        face = symbol(f"{ident}-label", column, 0.6)
        face["properties"].update({"display": keyword("block"), "left": length(round((U * width - SYMBOL) / 2, 3)),
                                   "top": length(round((height - SYMBOL) / 2, 3))})
    sorted_by, ascending = {"op": "==", "args": [{"state": "join.sort"}, sort]}, {"state": "join.ascending"}
    # The chevron follows its heading: past the longest translation of its
    # label (check_join_fits keeps that inside the column), or past the icon,
    # so it never reads as the next column's.
    after = (max(text_width("lowpixel", text, HEADING_TEXT) for text in table_text(key).values()) if key is not None
             else (U * width + SYMBOL) / 2) + 3
    chevrons = []
    for name, points, top, shown in (("up", [(0, 5), (4, 0), (8, 5)], height / 2 - 3, ascending),
                                     ("down", [(0, 0), (4, 5), (8, 0)], height / 2 - 2, {"op": "!", "args": [ascending]})):
        node = f"{ident}-{name}"
        chevrons.append(vector(node, {**absolute(left=round(min(after, U * width - CHEVRON_ROOM + 1), 3), top=top, width=8, height=5),
                                      "display": keyword("none"), "pointer-events": keyword("none")},
                               [path("chevron", points, closed=False, stroke=stroke(solid(rgb(VALUE)), 1.5))]))
        doc.bind(f"{node}.display", node, "display", {"op": "select", "args": [{"op": "&&", "args": [sorted_by, shown]}, "block", "none"]})
    rule = vector(f"{ident}-focus", {**FULL, "opacity": number(0), "pointer-events": keyword("none")},
                  [path("rule", [(0, {"fraction": 1, "dp": -1}), ({"fraction": 1}, {"fraction": 1, "dp": -1})], closed=False,
                        stroke=stroke(solid(rgb(ORANGE)), 1.5))])
    ids = doc.states(ident, {
        "default": [(f"{ident}-focus", "opacity", number(0))], "hover": [(f"{ident}-focus", "opacity", number(0.6))],
        "focus": [(f"{ident}-focus", "opacity", number(1))], "pressed": [(f"{ident}-focus", "opacity", number(1))],
        "disabled": [(f"{ident}-focus", "opacity", number(0))],
    })
    return group(ident, absolute(left=U * (LIST[0] + left), top=U * HEADING_TOP, width=U * width, height=height),
                 [face, *chevrons, rule], control={"role": "button", "label": key or PLACEHOLDER, "action": verb, "states": ids})


def source_tag(doc: Document, ident: str, key: str, left: float, width: float, verb: str, lan: bool) -> dict:
    """A source's cut tag (section 7's filter tags, built like the header
    band): the list's source lit and resting at 0.60, the other at 0.28."""
    doc.session(verb, verb)
    height, cut = U * 16, U * 5
    shape = [(cut, 0), (U * width, 0), (U * width, height), (0, height), (0, cut)]
    chosen = {"state": "join.lan"} if lan else {"op": "!", "args": [{"state": "join.lan"}]}
    tag = vector(f"{ident}-tag", {**FULL, "opacity": number(0.28), "pointer-events": keyword("none")},
                 [path("tag", shape, fill=solid(rgb(OLIVE, 0.5)), stroke=stroke(solid(rgb(OLIVE)), 1))])
    lit = vector(f"{ident}-lit", {**FULL, "display": keyword("none"), "opacity": number(0.6), "pointer-events": keyword("none")},
                 [path("tag", shape, fill=solid(rgb(ORANGE, 0.35)), stroke=stroke(solid(rgb(ORANGE)), 1))])
    doc.bind(f"{ident}-lit.display", f"{ident}-lit", "display", {"op": "select", "args": [chosen, "block", "none"]})
    caption = label(f"{ident}-label", key, {**absolute(left=U * 6, top=0, width=U * width - U * 8, height=height),
                                             **typeface("marine", TAG_TEXT, height, [1, 1, 1, 0.85]), "white-space": keyword("nowrap"),
                                             "overflow": keyword("hidden"), "pointer-events": keyword("none")})
    ids = doc.states(ident, {
        "default": [(f"{ident}-tag", "opacity", number(0.28))], "hover": [(f"{ident}-tag", "opacity", number(0.7))],
        "focus": [(f"{ident}-tag", "opacity", number(1))], "pressed": [(f"{ident}-tag", "opacity", number(1))],
        "disabled": [(f"{ident}-tag", "opacity", number(0.2))],
    })
    return group(ident, absolute(left=U * left, top=U * SOURCE[1], width=U * width, height=height), [tag, lit, caption],
                 control={"role": "button", "label": key, "action": verb, "states": ids})


def source_tags() -> list:
    """The source tags' layout: (ident, key, left u, width u, verb, lan)."""
    right, layout = SOURCE_END, []
    for ident, key, verb, lan in reversed(TAG_KEYS):
        width = float(math.ceil(max(text_width("marine", text, TAG_TEXT) for text in table_text(key).values()) / U + 8))
        right -= width
        layout.append((ident, key, right, width, verb, lan))
        right -= TAG_GAP
    return list(reversed(layout))


def mod_filter(doc: Document) -> list:
    """MOD (the stock page's mod filter): the label, the filter's value (the
    session's join.mod, "All" when it shows every mod) and its spinner
    squares, each asking the session for the previous or next mod the list
    holds."""
    doc.state["join.mod"] = {"type": "string", "initial": ""}
    height = U * 16
    parts = [label("join-mod", "#str_223005", {**absolute(left=U * MOD[0], top=U * MOD[1], width=U * MOD[2], height=height),
                                                **typeface("marine", TAG_TEXT, height, [1, 1, 1, 0.5]), "white-space": keyword("nowrap"),
                                                "overflow": keyword("hidden"), "text-align": keyword("right")}),
             label("join-mod-value", PLACEHOLDER, {**absolute(left=U * MOD_VALUE[0], top=U * MOD[1], width=U * MOD_VALUE[1], height=height),
                                                   **typeface("marine", TAG_TEXT, height, rgb(VALUE, 0.8)), "white-space": keyword("nowrap"),
                                                   "overflow": keyword("hidden"), "pointer-events": keyword("none")})]
    doc.bind("join-mod-value.text", "join-mod-value", "text", {"state": "join.mod"})
    for left, verb, name in MOD_SPIN:
        doc.session(verb, verb)
        ident = f"join_mod_{name}"
        width = U * 22
        points = [(width / 2 + 3, height / 2 - 4.5), (width / 2 - 3, height / 2), (width / 2 + 3, height / 2 + 4.5)]
        if name == "next":
            points = [(width - x, y) for x, y in points]
        square = vector(f"{ident}-square", {**FULL, "opacity": number(0.6), "pointer-events": keyword("none")},
                        [path("square", [(0, 0), (width, 0), (width, height), (0, height)], fill=solid([0, 0, 0, 0.7]),
                              stroke=stroke(solid(rgb(OLIVE)), 1))])
        arrow = vector(f"{ident}-arrow", {**FULL, "pointer-events": keyword("none")}, [path("arrow", points, fill=solid(rgb(VALUE)))])
        ids = doc.states(ident, {
            "default": [(f"{ident}-square", "opacity", number(0.6))], "hover": [(f"{ident}-square", "opacity", number(0.85))],
            "focus": [(f"{ident}-square", "opacity", number(1))], "pressed": [(f"{ident}-square", "opacity", number(1))],
            "disabled": [(f"{ident}-square", "opacity", number(0.3))],
        })
        parts.append(group(ident, absolute(left=U * left, top=U * MOD[1], width=width, height=height), [square, arrow],
                           control={"role": "button", "label": "#str_223005", "action": verb, "states": ids}))
    return parts


def favorite_width() -> float:
    """The favorite toggle's plate width (u): its longer label and the plate's
    30 dp, at least JOIN SERVER's width."""
    longest = max(text_width("marine", text, 20) for key in FAVORITE_KEYS for text in table_text(key).values())
    return float(max(JOIN[2], math.ceil((longest + 30) / U)))


def clear_sort_width() -> float:
    """CLEAR SORTING's plate width (u): its label and the plate's 30 dp."""
    longest = max(text_width("marine", text, 20) for text in table_text("#str_200951").values())
    return float(max(CLEAR_SORT[2], math.ceil((longest + 30) / U)))


def check_join_fits() -> None:
    """Every shipped language's labels fit on one line: the headings in their
    columns, the source and its tags, the list's empty line and pagers, and
    the plates' labels."""
    one_line = [(key, "lowpixel", HEADING_TEXT, U * width - CHEVRON_ROOM) for _c, _s, key, _l, width, _v in COLUMNS if key is not None]
    tags = source_tags()
    one_line += [("#str_200032", "marine", TAG_TEXT, U * (tags[0][2] - TAG_GAP - SOURCE[0]))]
    one_line += [(key, "marine", TAG_TEXT, U * width - U * 8) for _i, key, _l, width, _v, _lan in tags]
    one_line += [("#str_231133", "lowpixel", 15, U * (LIST[2] - 16)), ("#str_231131", "marine", 16, U * (LIST[2] - 16 - 18)),
                 ("#str_231132", "marine", 16, U * (LIST[2] - 16 - 18)), ("#str_200951", "marine", 20, U * clear_sort_width() - 30)]
    one_line += [(key, "marine", 20, U * 208 - 30) for _i, key, _l, _t, _v in LIST_ACTIONS]
    one_line += [("#str_223005", "marine", TAG_TEXT, U * MOD[2])]
    one_line += [(key, "marine", 20, U * favorite_width() - 30) for key in FAVORITE_KEYS]
    check_fits(tuple(one_line), ())


def join_game_document() -> dict:
    """The Join Game sub-page (see the module's description)."""
    check_join_fits()
    doc = Document("openq4.joingame")
    doc.session("back", "joinBack")
    doc.session("joinPick", "joinPick")
    doc.session("joinServer", "joinServer")
    doc.session("joinClearSort", "joinClearSort")
    doc.session("serversNewer", "joinNewer")
    doc.session("serversOlder", "joinOlder")
    doc.events["onBack"] = [{"op": "action", "action": "back"}]
    doc.state.update({
        "join.count": {"type": "number", "initial": 0},
        "join.first": {"type": "number", "initial": 0},
        "join.selected": {"type": "number", "initial": -1},
        "join.pick": {"type": "number", "initial": -1},
        "join.sort": {"type": "number", "initial": 0},
        "join.ascending": {"type": "boolean", "initial": True},
        "join.lan": {"type": "boolean", "initial": False},
        "join.scanning": {"type": "boolean", "initial": False},
        "join.status": {"type": "string", "initial": ""},
    })
    heading_tint = {**typeface("marine", TAG_TEXT, U * 16, [1, 1, 1, 0.5]), "white-space": keyword("nowrap"), "overflow": keyword("hidden")}
    tags = source_tags()
    parts = [header_band("join-header", *HEADER),
             label("join-source", "#str_200032", {**absolute(left=U * SOURCE[0], top=U * SOURCE[1],
                                                             width=U * (tags[0][2] - TAG_GAP - SOURCE[0]), height=U * 16), **heading_tint})]
    parts += [source_tag(doc, f"join_{ident}", key, left, width, verb, lan) for ident, key, left, width, verb, lan in tags]
    parts += mod_filter(doc)
    parts += [heading(doc, column, sort, key, left, width, verb) for column, sort, key, left, width, verb in COLUMNS]

    left, top, list_w, list_h = LIST
    row_w = list_w - 16
    newer = pager_row(doc, "servers-newer", "#str_231131", "serversNewer", {"op": ">", "args": [{"state": "join.first"}, 0]}, row_w=row_w)
    older = pager_row(doc, "servers-older", "#str_231132", "serversOlder",
                      {"op": "<", "args": [{"op": "+", "args": [{"state": "join.first"}, JOIN_ROWS]}, {"state": "join.count"}]},
                      row_w=row_w)
    servers = group("servers-column", {"position": keyword("relative"), "display": keyword("flex"), "flex-direction": keyword("column")},
                    [newer, *[server_row(doc, index, row_w) for index in range(JOIN_ROWS)], older])
    parts.append(group("servers-list", {**absolute(left=U * left, top=U * top, width=U * row_w, height=U * list_h),
                                        "overflow": keyword("auto")}, [servers]))
    parts.append(objectives_scrollbar(doc, "servers_scroll", "servers-list", OLIVE, ORANGE, U * (left + list_w) - 16, U * top, U * list_h,
                                      line_step=U * ROW_H, key="#str_200187"))
    # An empty list says how to fill it, unless the scan is still running.
    empty = label("join-empty", "#str_231133", {**absolute(left=U * (left + 4), top=U * (top + 6), width=U * (list_w - 16), height=U * 16),
                                                 **typeface("lowpixel", 15, U * 16, [1, 1, 1, 0.6]), "white-space": keyword("nowrap"),
                                                 "overflow": keyword("hidden"), "display": keyword("none")})
    doc.bind("join-empty.display", "join-empty", "display", {"op": "select", "args": [
        {"op": "&&", "args": [{"op": "==", "args": [{"state": "join.count"}, 0]}, {"op": "!", "args": [{"state": "join.scanning"}]}]},
        "block", "none"]})
    clear_w = clear_sort_width()
    status = label("join-status", PLACEHOLDER, {**absolute(left=U * STATUS[0], top=U * STATUS[1],
                                                           width=U * (CLEAR_SORT[0] - clear_w - 6 - STATUS[0]), height=U * 16),
                                                 **typeface("lowpixel", 14, U * 16, [1, 1, 1, 0.7]), "white-space": keyword("nowrap"),
                                                 "overflow": keyword("hidden")})
    doc.bind("join-status.text", "join-status", "text", {"state": "join.status"})
    parts += [empty, status, action_plate(doc, "join_clearsort", "#str_200951", U * (CLEAR_SORT[0] - clear_w), U * CLEAR_SORT[1] - 5,
                                          action="joinClearSort", width=U * clear_w)]
    for ident, key, x, y, verb in LIST_ACTIONS:
        doc.session(verb, verb)
        parts.append(action_plate(doc, ident, key, U * x, U * y - 5, action=verb, width=U * 208))
    # The chosen server's levelshot (the session's join.shot), in the stock
    # frame between the list's actions and JOIN SERVER.
    doc.state["join.shot"] = {"type": "string", "initial": ""}
    parts += picture_frame("join-shot", *SHOT)
    doc.bind("join-shot.image", "join-shot", "image", {"state": "join.shot"})
    join = primary_plate(doc, "join_server", "#str_200031", *JOIN, action="joinServer", label_box=(43.0, 6.0, 180.0, 25.0), text=23.7,
                         marker=(13.0, 9.5, 18.0))
    doc.bind("join_server.enabled", "join_server", "enabled", {"op": ">=", "args": [{"state": "join.selected"}, 0]})
    # The favorite toggle under it, ending where it ends: ADD TO FAVORITES, or
    # REMOVE FAVORITE while the chosen server is one (join.favorite).
    doc.state["join.favorite"] = {"type": "boolean", "initial": False}
    doc.session("joinFavorite", "joinFavorite")
    favorite_w = favorite_width()
    favorite = action_plate(doc, "join_favorite", FAVORITE_KEYS[0], U * (JOIN[0] + JOIN[2] - favorite_w), U * FAVORITE_TOP - 5,
                            action="joinFavorite", width=U * favorite_w)
    doc.bind("join_favorite-label.text", "join_favorite-label", "text",
             {"op": "select", "args": [{"state": "join.favorite"}, FAVORITE_KEYS[1], FAVORITE_KEYS[0]]})
    doc.bind("join_favorite.enabled", "join_favorite", "enabled", {"op": ">=", "args": [{"state": "join.selected"}, 0]})
    back = action_plate(doc, "join_back", "#str_200018", U * BACK[0], U * BACK[1], action="back", width=U * BACK[2])
    return subpage_document(doc, "join", "#str_200002", "#str_200187", "join_newlist", [*parts, join, favorite, back], [])
