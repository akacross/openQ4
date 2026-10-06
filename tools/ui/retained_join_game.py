"""The retained Join Game sub-page, Multiplayer's server browser
(docs/dev/ui-visual-design.md sections 8 and 9, "Menu levels" and "Lists";
FLOW-050).

Built by tools/ui/build_retained_screens.py, which writes and checks it with
the other retained screens. JOIN GAME on the Multiplayer page goes one level
deeper to guis/menu/joingame.q4ui as CREATE SERVER goes to Create Server,
on the same sub-page frame (retained_subpage); Back climbs out onto JOIN
GAME.

The content is the stock p_mp_browse's over the stock page backing: SOURCE
with its INTERNET and LAN tags at 324,46 u; the server list at 23,83 u under
its column headings on the stock 18 u rows, the sort's column
marked (a heading sorts by its column, and again the other way); the scan's
status at 41,291 u beside CLEAR SORTING; REFRESH LIST and GET NEW LIST at
19,330 and 19,358 u; JOIN SERVER at 385,330 u; BACK in the bottom band.

The session owns the list: it publishes the scan's visible servers a page of
JOIN_ROWS at a time (join.row<i>.*), their count, the scan's status, the
source and the sort, and the chosen server (join.selected), and each control
asks through its own verb. The stock page's JOIN IP ADDRESS, FIND
PLAYER/CLAN, mod filter, favorite toggle, dedicated, PunkBuster and repeater
columns and the chosen server's levelshot and details are not built yet, so
the session keeps the page opt-in (RETAINED_JOIN_GAME_MISSING).
"""
from __future__ import annotations

import math

from build_retained_screens import (FULL, OLIVE, ORANGE, U, VALUE, Document, absolute, action_plate, group, keyword, label, length,
                                    number, objectives_scrollbar, path, rgb, solid, stroke, text_width, typeface, vector)
from retained_create_server import BACK, header_band
from retained_difficulty import check_fits, primary_plate
from retained_mp_menus import padlock
from retained_saves import PLACEHOLDER, pager_row, row_plates, row_states, table_text
from retained_subpage import subpage_document

JOIN_ROWS = 64                             # RETAINED_JOIN_ROWS in the session
LIST = (23.0, 83.0, 604.0, 202.0)          # u: mp_browse_serverlist
ROW_H = 18.0                               # u: its itemheight
HEADER = (22.0, 54.0, 587.0, 37.0)         # u: mp_browse_header
HEADING_TOP = 70.0                         # u: the headings' row
# The columns: the session's sort for each (serverSort_t), its heading (an
# icon column has none), its tab stop and width in the list (u) and its sort
# verb. The icons and the name keep the stock list's tab stops; the stock
# columns after the name were too narrow for every language's heading with
# the sort's chevron, so they take what the name column spared.
COLUMNS = (
    ("fav", 6, None, 5.0, 21.0, "joinSortFavorite"),
    ("lock", 7, None, 26.0, 21.0, "joinSortLocked"),
    ("name", 1, "#str_200036", 89.0, 211.0, "joinSortName"),
    ("ping", 0, "#str_200037", 300.0, 40.0, "joinSortPing"),
    ("players", 2, "#str_200038", 340.0, 60.0, "joinSortPlayers"),
    ("type", 3, "#str_200039", 400.0, 90.0, "joinSortGameType"),
    ("map", 4, "#str_200040", 490.0, 96.0, "joinSortMap"),
)
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


def star(ident: str, size: float, tint: list) -> dict:
    """A favorite's five-pointed star."""
    points = []
    for index in range(10):
        radius = size / 2 if index % 2 == 0 else size / 5
        angle = math.pi / 2 + index * math.pi / 5
        points.append((round(size / 2 + radius * math.cos(angle), 3), round(size / 2 - radius * math.sin(angle), 3)))
    return vector(ident, {"position": keyword("absolute"), "display": keyword("none"), "width": length(size), "height": length(size),
                          "pointer-events": keyword("none")}, [path("star", points, fill=solid(tint))])


def server_row(doc: Document, index: int, row_w: float) -> dict:
    """One of the list's rows: a server's favorite star and lock, then its
    name, ping, players, game type and map at the stock tab stops. Its first
    Accept chooses the server; Accept on the chosen one moves on to JOIN
    SERVER."""
    ident, key = f"server-{index}", f"join.row{index}"
    width, height = U * row_w, U * ROW_H
    tint = [1, 1, 1, 0.8]
    cells, texts = [], []
    for column, _sort, key_text, left, column_w, _verb in COLUMNS:
        node = f"{ident}-{column}"
        if key_text is None:
            mark = U * 10
            doc.state[f"{key}.{column}"] = {"type": "boolean", "initial": False}
            if column == "fav":
                icon = star(node, mark, rgb(VALUE))
                icon["properties"].update({"left": length(U * left + (U * column_w - mark) / 2), "top": length((height - mark) / 2)})
            else:
                icon = padlock(node, [1, 1, 1, 0.7])
                icon["properties"].update({"position": keyword("absolute"), "margin-left": length(0),
                                           "left": length(U * left + (U * column_w - 12) / 2), "top": length((height - 14) / 2)})
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
    elif column == "fav":
        face = star(f"{ident}-label", U * 10, tint)
        face["properties"].update({"display": keyword("block"), "left": length((U * width - U * 10) / 2), "top": length(U * 3)})
    else:
        face = padlock(f"{ident}-label", tint)
        face["properties"].update({"position": keyword("absolute"), "display": keyword("block"), "margin-left": length(0),
                                   "left": length((U * width - 12) / 2), "top": length(U * 3 - 1)})
    sorted_by, ascending = {"op": "==", "args": [{"state": "join.sort"}, sort]}, {"state": "join.ascending"}
    # The chevron follows its heading: past the longest translation of its
    # label (check_join_fits keeps that inside the column), or past the icon,
    # so it never reads as the next column's.
    after = (max(text_width("lowpixel", text, HEADING_TEXT) for text in table_text(key).values()) if key is not None
             else (U * width + U * 10) / 2) + 3
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
    join = primary_plate(doc, "join_server", "#str_200031", *JOIN, action="joinServer", label_box=(43.0, 6.0, 180.0, 25.0), text=23.7,
                         marker=(13.0, 9.5, 18.0))
    doc.bind("join_server.enabled", "join_server", "enabled", {"op": ">=", "args": [{"state": "join.selected"}, 0]})
    back = action_plate(doc, "join_back", "#str_200018", U * BACK[0], U * BACK[1], action="back", width=U * BACK[2])
    return subpage_document(doc, "join", "#str_200002", "#str_200187", "join_newlist", [*parts, join, back], [])
