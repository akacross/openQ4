"""The retained Multiplayer page (docs/dev/ui-visual-design.md section 9,
"Menu levels"; FLOW-050).

Built by tools/ui/build_retained_screens.py, which writes and checks it with
the other retained screens. MULTIPLAYER on the title hands off to
guis/menu/multiplayer.q4ui as LOAD GAME does to its page
(idSessionLocal::BeginRetainedPage): the title docks its bands and carries
its label into the title slot, and at 550 ms the page presents in the page
state Single Player holds, that label its title. It is the stock Multiplayer
page's level: its sections are the stock page's GAME BROWSER (as JOIN GAME),
CREATE SERVER and SETTINGS (as PLAYER SETUP, section 13.7's name, which keeps
it apart from the title's SETTINGS) on the home navigation plates from 181 u,
with BACK under them, and the stock FRIENDS LIST, hidden in the stock menu and
handled by nothing, is gone. A section opens its stock page for now: the
page leaves as the stock Multiplayer page leaves for one (its plates fade
over 150 ms as it sweeps 640 u toward the trailing edge over 300 ms) and the
stock page takes over at 500 ms; its Back returns here (multiplayerOpen).
BACK returns the title.
"""
from __future__ import annotations

from build_retained_screens import (BOTTOM_TO_PAGE, CANVAS_W, FULL, PAGE_TITLE_H, PAGE_TITLE_W, TITLE_SLOT, TOP_TO_PAGE, U,
                                    Document, absolute, colour, framing_bands, group, keyword, label, length, lit_field,
                                    navigation_plate, number, prompt_bar, rgb, OLIVE, track, transform, typeface)
from retained_difficulty import check_fits

NAV_TOP = 181.0    # the stock Multiplayer page's first button (mp_b1)
SECTIONS = (("join", "#str_200187", "multiplayerJoin"), ("create", "#str_200026", "multiplayerCreate"),
            ("setup", "#str_231122", "multiplayerSetup"))
DEPART_MS = 300    # the stock page's slide; the stock page arrives at 500 ms
DETAILS = (210.0, 140.0)    # the content column's box, u
DETAIL_TEXT, DETAIL_LINE = 18, 26


def check_multiplayer_fits() -> None:
    """Every shipped language's labels fit: the section labels in the plate's
    314 u label box at the focus scale (1.03), the title in its slot and the
    description in the content column's lines."""
    labels = [key for _, key, _ in SECTIONS] + ["#str_230045"]
    check_fits(tuple((key, "marine", 24, U * 314 / 1.03) for key in labels) +
               (("#str_200002", "marine", 18, U * PAGE_TITLE_W),),
               (("#str_231121", "lowpixel", DETAIL_TEXT, U * DETAILS[0], int(U * DETAILS[1] // DETAIL_LINE)),))


def multiplayer_document() -> dict:
    """The Multiplayer page in the page state (sections 8 and 9): the bands
    docked, the title in the top band's slot at 39,19 u, the sections on the
    home navigation plates and the page's description in the content column
    at 395,190 u, over the lit field; the prompt bar's Select and Back.
    onActivate   every arrival: the plates at once, the description fading in
                 over 150 ms (content.in);
    depart       a section opens its stock page: the plates fade over 150 ms
                 while the page sweeps 640 u toward the trailing edge over
                 300 ms, and the title and description go with them;
    onDeactivate places it at rest while it is hidden, so it never presents
                 moved."""
    check_multiplayer_fits()
    doc = Document("openq4.multiplayer")
    doc.session("back", "multiplayerBack")
    doc.events["onBack"] = [{"op": "action", "action": "back"}]
    buttons = []
    for ident, key, action in SECTIONS:
        doc.session(action, action)
        buttons.append(navigation_plate(doc, ident, key, action=action))
    buttons.append(navigation_plate(doc, "back", "#str_230045", action="back"))
    description = label("description", "#str_231121", {**absolute(left=0, top=0, width=U * DETAILS[0], height=U * DETAILS[1]),
                                                       **typeface("lowpixel", DETAIL_TEXT, DETAIL_LINE, rgb(OLIVE))})
    bands = framing_bands("band")
    page_top = transform(*TOP_TO_PAGE)
    bands[0]["properties"]["transform"] = page_top
    bands[1]["properties"]["transform"] = transform(*BOTTOM_TO_PAGE)
    canvas = {**absolute(top=0, width=CANVAS_W, height=720), "left": length(50, "%"), "margin-left": length(-CANVAS_W / 2)}
    content = group("content", {**canvas, "transform": transform(), "opacity": number(1)}, [
        group("navigation", {**absolute(left=0, top=U * NAV_TOP, width=U * 357), "display": keyword("flex"),
                             "flex-direction": keyword("column"), "opacity": number(1)}, buttons),
        group("details", {**absolute(left=U * 395, top=U * 190, width=U * DETAILS[0], height=U * DETAILS[1]), "opacity": number(0)},
              [description]),
    ])
    titles = group("titles", {**canvas, "pointer-events": keyword("none")}, [
        group("title-clip", {**absolute(left=U * TITLE_SLOT[0], top=0, width=U * PAGE_TITLE_W, height=U * 40), "overflow": keyword("hidden")}, [
            label("title", "#str_200002", {**absolute(left=0, top=U * TITLE_SLOT[1], width=U * PAGE_TITLE_W, height=U * PAGE_TITLE_H),
                                           **typeface("marine", 18, U * PAGE_TITLE_H, [1, 1, 1, 0.5]), "white-space": keyword("nowrap"),
                                           "transform": transform()})]),
    ])
    white = lambda alpha: colour([1, 1, 1, alpha])
    identity, swept = transform(), transform(640 * U, 0)
    doc.timelines.add("arrive", 150, [
        track("content", "opacity", [(0, number(1)), (1, number(1)), (150, number(1))]),
        track("content", "transform", [(0, identity), (1, identity), (150, identity)]),
        track("details", "opacity", [(0, number(0)), (1, number(0)), (150, number(1))]),
        track("title", "color", [(0, white(0.5)), (1, white(0.5)), (150, white(0.5))]),
        track("prompts", "opacity", [(0, number(1)), (1, number(1)), (150, number(1))]),
    ])
    doc.timelines.add("rest", 1, [
        track("band-top", "transform", [(0, page_top), (1, page_top)]),
        track("content", "transform", [(0, identity), (1, identity)]),
        track("content", "opacity", [(0, number(1)), (1, number(1))]),
        track("details", "opacity", [(0, number(0)), (1, number(0))]),
        track("title", "color", [(0, white(0.5)), (1, white(0.5))]),
        track("prompts", "opacity", [(0, number(1)), (1, number(1))]),
    ])
    doc.timelines.add("depart", DEPART_MS, [
        track("content", "opacity", [(0, number(1)), (150, number(0)), (DEPART_MS, number(0))]),
        track("content", "transform", [(0, identity), (DEPART_MS, swept)]),
        track("title", "color", [(0, white(0.5)), (150, white(0)), (DEPART_MS, white(0))]),
        track("prompts", "opacity", [(0, number(1)), (150, number(0)), (DEPART_MS, number(0))]),
    ])
    doc.events["onActivate"] = [{"op": "playTimeline", "timeline": "arrive"}]
    doc.events["onDeactivate"] = [{"op": "playTimeline", "timeline": "rest"}]
    doc.events["depart"] = [{"op": "playTimeline", "timeline": "depart"}]
    return doc.build(group("screen", {**FULL, "background-color": colour([0, 0, 0, 1])}, [
        *lit_field("field", 0.7), *bands, content, titles,
        prompt_bar(doc, [("#str_107019", "#str_200747"), ("#str_107020", "#str_230045")]),
    ]))
