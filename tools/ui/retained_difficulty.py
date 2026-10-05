"""The retained difficulty choice (docs/dev/ui-visual-design.md sections 9 and
13.7): the Marine pause's Restart Level page.

Built by tools/ui/build_retained_screens.py, which writes and checks it with
the other retained screens. Section 9 "New game": difficulty choices use
section navigation plates beside a description paragraph, and the primary
action is the enlarged plate. The layout is the stock p_newgame (openQ4's own
mainmenu.gui, whose in-game Difficulty page is the same page retitled): five
b2_dark plates on a 30 u pitch from 21,172 u, the chosen one lit; the chosen
difficulty's description at 239,181 u in Lowpixel (textscale 0.25) at 0.60;
the primary plate (b6_light) at 237,222 u, 356x43 u; BACK in the bottom band
at 532,441 u.

The pause's RESTART LEVEL hands off to restartlevel.q4ui as LOAD GAME does to
its page (idSessionLocal::BeginRetainedPage): the page is the stock page's
content over the departed pause, whose carried label is the page's title. The
choice stays on the page until RESTART LEVEL restarts the level at it
(RestartLevelAtSkill), so Back changes nothing. The in-game page offers no
turbo mode, as the stock one hid it.
"""
from __future__ import annotations

from build_retained_screens import (CANVAS_W, FULL, LANGUAGES, MARKER, OLIVE, ORANGE, U, Document, absolute, action_plate,
                                    colour, font, group, keyword, label, length, linear, marker_path, number, path, rgb, solid,
                                    stroke, text_width, track, transform, typeface, vector)
from retained_saves import backing, lines_needed, section_plate, table_text

# The stock difficulties, easiest first (g_skill 0-4), with their descriptions.
DIFFICULTIES = (("#str_200014", "#str_200183"), ("#str_200015", "#str_200019"), ("#str_200016", "#str_200184"),
                ("#str_200017", "#str_200185"), ("#str_41117", "#str_41118"))
PLATES = ((21.0, 172.0), (20.0, 202.0), (20.0, 232.0), (20.0, 262.0), (20.0, 292.0))   # new_b1-new_b5 (b2_dark)
DESCRIPTION = (239.0, 181.0, 345.0, 139.0)     # new_diffDescript
DESCRIPTION_TEXT = 18.0                        # dp: Lowpixel textscale 0.25
DESCRIPTION_LINE = 23.0                        # dp
PRIMARY = (237.0, 222.0, 356.0, 43.0)          # new_bstart (b6_light)
PRIMARY_LABEL = (28.0, 6.0, 198.0, 25.0)       # new_t_bstart, from the plate's corner
PRIMARY_TEXT = 23.7                            # dp: Marine textscale 0.33


def primary_plate(doc: Document, ident: str, key: str, left: float, top: float, width: float, height: float, *,
                  action: str | None = None, event: str | None = None) -> dict:
    """The enlarged primary plate (b6_light, Appendix B.1) that carries START
    GAME on the stock page: its band rows 4-27 of 32, a 45-degree lower-leading
    cut from row 14, the olive rail along the leading edge, the cut and the
    foot, and the olive fill at 0.49 to 31 % of the width, fading to nothing by
    95 %, drawn at 0.40. Its 18 u corner marker stands 11,10 u in and the Marine
    label (textscale 0.33, 23.7 dp) 28,6 u in. The pointer or focus lights the
    plate to full strength and turns the marker and label orange, as the stock
    plate lit; focus adds the orange inset of the home plates."""
    w, h = U * width, U * height
    band_top, band_bottom, cut = round(h * 4 / 32, 4), round(h * 27 / 32, 4), round(h * 13 / 32, 4)
    fill = [(0, rgb(OLIVE, 0.49)), (0.31, rgb(OLIVE, 0.49)), (0.5, rgb(OLIVE, 0.37)), (0.75, rgb(OLIVE, 0.17)),
            (0.94, rgb(OLIVE, 0.055)), (0.953, rgb(OLIVE, 0)), (1, rgb(OLIVE, 0))]
    rail = [(0, rgb(OLIVE)), (0.31, rgb(OLIVE)), (0.953, rgb(OLIVE, 0)), (1, rgb(OLIVE, 0))]
    whole = {**absolute(left=0, top=0, width=w, height=h)}
    plate = vector(f"{ident}-plate", {**whole, "opacity": number(0.4)}, [
        path("fill", [(0, band_top), (w, band_top), (w, band_bottom), (cut, band_bottom), (0, band_bottom - cut)],
             fill=linear((0, 0), (w, 0), fill)),
        path("rail", [(0.75, band_top), (0.75, band_bottom - cut), (cut, band_bottom - 0.75), (w, band_bottom - 0.75)],
             closed=False, stroke=stroke(linear((0, 0), (w, 0), rail), 1.5)),
    ])
    focus = vector(f"{ident}-focus", {**whole, "opacity": number(0)}, [
        path("inset", [(cut + 2, band_bottom - 3.2), (round(w * 0.6, 4), band_bottom - 3.2)], closed=False,
             stroke=stroke(solid(rgb(ORANGE)), 1.2))])
    # The stock corner is the 11 u one at 18 u: the marker scales with it.
    scale = 18 / 11
    mark = (round(U * (11 + 1.75 * scale), 4), round(U * (10 + 2.75 * scale), 4), round(U * 5.5 * scale, 4))
    marker_rest = vector(f"{ident}-marker", {**whole, "opacity": number(0.4)}, [marker_path("mark", *mark, rgb(MARKER))])
    marker_hot = vector(f"{ident}-marker-hot", {**whole, "opacity": number(0)}, [marker_path("mark", *mark, rgb(ORANGE))])
    x, y, label_w, label_h = PRIMARY_LABEL
    text_node = label(f"{ident}-label", key, {**absolute(left=U * x, top=U * y, width=U * label_w, height=U * label_h),
                      **typeface("marine", PRIMARY_TEXT, U * label_h, [1, 1, 1, 0.8]), "white-space": keyword("nowrap"),
                      "transform": transform()})
    lit, rest = number(1), number(0)

    def state(plate_alpha, marker, hot, inset, tint, moved):
        return [(f"{ident}-plate", "opacity", number(plate_alpha)), (f"{ident}-marker", "opacity", number(marker)),
                (f"{ident}-marker-hot", "opacity", number(hot)), (f"{ident}-focus", "opacity", number(inset)),
                (f"{ident}-label", "color", colour(tint)), (f"{ident}-label", "transform", moved)]
    ids = doc.states(ident, {
        "default": state(0.4, 0.4, 0, 0, [1, 1, 1, 0.8], transform()),
        "hover": state(1, 0, 1, 0, rgb(ORANGE), transform(sx=1.03, sy=1.03)),
        "focus": state(1, 0, 1, 1, rgb(ORANGE), transform(sx=1.03, sy=1.03)),
        "pressed": state(1, 0, 1, 1, rgb(ORANGE), transform(tx=1, ty=1, sx=1.03, sy=1.03)),
        "disabled": state(0.4, 0.4, 0, 0, [1, 1, 1, 0.3], transform()),
    })
    control = {"role": "button", "label": key, "states": ids}
    if action:
        control["action"] = action
    else:
        control["event"] = event
    return group(ident, absolute(left=U * left, top=U * top, width=w, height=h),
                 [plate, focus, marker_rest, marker_hot, text_node], control=control)


def difficulty_plates(doc: Document, key: str) -> list:
    """The five difficulty plates, each choosing its difficulty into `key`
    (the page's own state) and lit while it holds the choice."""
    chosen = {"state": key}
    plates = []
    for index, ((name, _), (left, top)) in enumerate(zip(DIFFICULTIES, PLATES)):
        event = f"chooseSkill{index}"
        doc.events[event] = [{"op": "setState", "values": {key: index}}]
        plates.append(section_plate(doc, f"skill-{index}", name, left, top, event=event,
                                    selected={"op": "==", "args": [chosen, index]}))
    return plates


def difficulty_description(doc: Document, ident: str, key: str) -> dict:
    """The chosen difficulty's description beside the plates."""
    left, top, width, height = DESCRIPTION
    node = label(ident, DIFFICULTIES[1][1], {**absolute(left=U * left, top=U * top, width=U * width, height=U * height),
                 **typeface("lowpixel", DESCRIPTION_TEXT, DESCRIPTION_LINE, [1, 1, 1, 0.6]), "white-space": keyword("normal"),
                 "overflow": keyword("hidden")})
    text = DIFFICULTIES[0][1]
    for index in range(1, len(DIFFICULTIES)):
        text = {"op": "select", "args": [{"op": "==", "args": [{"state": key}, index]}, DIFFICULTIES[index][1], text]}
    doc.bind(f"{ident}.text", ident, "text", text)
    return node


def focus_chosen(key: str) -> list:
    """Steps that focus the plate holding the choice; the last request wins."""
    steps = [{"op": "focus", "control": "skill-0"}]
    for index in range(1, len(DIFFICULTIES)):
        steps.append({"op": "if", "condition": {"op": "==", "args": [{"state": key}, index]},
                      "then": [{"op": "focus", "control": f"skill-{index}"}]})
    return steps


def check_fits(one_line: tuple, wrapped: tuple) -> None:
    """Every shipped language's text fits its box; generation fails otherwise."""
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


def restart_level_document() -> dict:
    lines = int(U * DESCRIPTION[3] // DESCRIPTION_LINE)
    check_fits(tuple((name, "marine", 22.3, U * 186) for name, _ in DIFFICULTIES) +
               (("#str_229983", "marine", PRIMARY_TEXT, U * PRIMARY_LABEL[2]), ("#str_200018", "marine", 20, U * 109 - 30)),
               tuple((text, "lowpixel", DESCRIPTION_TEXT, U * DESCRIPTION[2], lines) for _, text in DIFFICULTIES))
    doc = Document("openq4.restartlevel")
    doc.state["restart.skill"] = {"type": "number", "initial": 1}
    doc.session("back", "restartBack")
    doc.session("go", "restartGo")
    doc.events["onBack"] = [{"op": "action", "action": "back"}]
    plates = difficulty_plates(doc, "restart.skill")
    description = difficulty_description(doc, "restart-description", "restart.skill")
    go = primary_plate(doc, "restart_go", "#str_229983", *PRIMARY, action="go")
    back = action_plate(doc, "restart_back", "#str_200018", U * 532, U * 441, action="back", width=U * 109)
    # The plates show at once, under the title the pause carried; the panel
    # and the backing fade in over 150 ms (content.in), as a stock page's do.
    panel = group("restart-panel", {**FULL, "opacity": number(1)}, [description, go, back])
    stage = group("restart-stage", {**absolute(top=0, width=CANVAS_W, height=720), "left": length(50, "%"),
                                    "margin-left": length(-CANVAS_W / 2)}, [*plates, panel])
    doc.timelines.add("arrive", 150, [track(node, "opacity", [(0, number(0)), (1, number(0)), (150, number(1))])
                                      for node in ("restart-panel", "restart-backing")])
    doc.timelines.add("rest", 1, [track(node, "opacity", [(0, number(0)), (1, number(0))])
                                  for node in ("restart-panel", "restart-backing")])
    # Each arrival focuses the plate holding the level's difficulty.
    doc.events["onActivate"] = [{"op": "playTimeline", "timeline": "arrive"}, *focus_chosen("restart.skill")]
    doc.events["onDeactivate"] = [{"op": "playTimeline", "timeline": "rest"}]
    root = group("screen", {**FULL, "font-family": font("marine"), "font-size": length(16), "color": colour([1, 1, 1, 0.8])},
                 [backing("restart-backing"), stage])
    return doc.build(root)
