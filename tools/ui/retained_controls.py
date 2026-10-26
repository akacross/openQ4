"""The retained CONTROLS settings page (docs/dev/ui-visual-design.md
section 7; UI-01): the stock page's key bindings
(guis/menu/settings/controls.gui) in the SYSTEM page's construction
(retained_settings_rows), its four tabs as sections: movement, weapons,
attack and look, and other.

Each row names an action and the keys bound to it, which the session
publishes (controls.<row>.keys) as the language's key names. Accept asks the
session to wait for a key (controlsBind); the session takes the next key as
the stock binding field does: Escape, Start or Back cancel, Backspace or
Delete clear, any other key binds (idSessionLocal::RetainedControlsKey).
Delete, Backspace or the west face button on a row clears it
(controlsClear). The session reads the row from the focused control. BACK,
or the back input, returns to the settings screen that opened the page."""
from __future__ import annotations

from build_retained_screens import Document
from retained_settings_rows import Templates, find, renamed, section_column, settings_page, text_node

PREFIX = "controls"
# Each section: its id, heading (the stock tab) and rows (label, binding), in
# the stock page's order; the session's RETAINED_CONTROLS_BINDINGS follows it.
SECTIONS = (
    ("move", "#str_200090", (
        ("#str_200094", "_forward"), ("#str_200095", "_back"), ("#str_200096", "_moveleft"), ("#str_200097", "_moveright"),
        ("#str_200098", "_moveUp"), ("#str_200099", "_moveDown"), ("#str_200100", "_left"), ("#str_200101", "_right"),
        ("#str_200102", "_strafe"), ("#str_200103", "_speed"),
    )),
    ("weapons", "#str_200091", (
        ("#str_200966", "_impulse0"), ("#str_200106", "_impulse1"), ("#str_200105", "_impulse2"), ("#str_200107", "_impulse3"),
        ("#str_200108", "_impulse4"), ("#str_200109", "_impulse5"), ("#str_200110", "_impulse6"), ("#str_200111", "_impulse7"),
        ("#str_200112", "_impulse8"), ("#str_200113", "_impulse9"), ("#str_222001", "_impulse10"), ("#str_222014", "buymenu"),
        ("#str_231269", "_quickChat"),
    )),
    ("attack", "#str_200092", (
        ("#str_200114", "_attack"), ("#str_200115", "_impulse15"), ("#str_200116", "_impulse14"), ("#str_200117", "_impulse13"),
        ("#str_200118", "_lookUp"), ("#str_200119", "_lookDown"), ("#str_200120", "_mlook"), ("#str_200121", "centerview"),
        ("#str_200122", "_zoom"), ("#str_200131", "_impulse19"), ("#str_200315", "_impulse50"), ("#str_200125", "screenshot"),
        ("#str_229920", "_weaponWheel"),
    )),
    ("other", "#str_200093", (
        ("#str_200123", "savegame quick"), ("#str_200124", "loadgame quick"), ("#str_200126", "clientMessageMode"),
        ("#str_200127", "clientMessageMode 1"), ("#str_200129", "_impulse28"), ("#str_200130", "_impulse29"),
        ("#str_200132", "_ingamestats"), ("#str_201009", "_impulse17"), ("#str_200311", "emote salute"),
        ("#str_200312", "emote cheer"), ("#str_200313", "emote taunt"), ("#str_200314", "emote grab_a"),
        ("#str_200959", "_voicechat"),
    )),
)
BINDINGS = tuple(binding for _section, _heading, rows in SECTIONS for _label, binding in rows)


def binding_row(doc: Document, tpl: Templates, row: int, label_key: str) -> dict:
    """The SYSTEM page's check box row as a button: the action's name over
    the keys bound to it, in the orange of a list's value."""
    ident = f"controls_bind_{row}"
    node = renamed(renamed(tpl.node("settings_shadows"), "settings_shadows", ident), "settings-", f"{PREFIX}-")
    node["properties"]["padding-right"] = {"type": "length", "value": 12, "unit": "dp"}
    label = find(node, f"{ident}-label")
    text_node(label, label_key)
    keys = renamed(tpl.node("settings_display_device-value"), "settings_display_device-value", f"{ident}-keys")
    keys["properties"]["padding-right"] = {"type": "length", "value": 0, "unit": "dp"}
    doc.bind(f"{ident}-keys.text", f"{ident}-keys", "text", {"state": f"controls.{row}.keys"})
    node["children"] = [child for child in node["children"] if child["id"] in (f"{ident}-plate", f"{ident}-focus")] + [label, keys]
    node["control"] = {"role": "button", "label": label_key, "action": "controlsBind",
                       "states": tpl.states(doc, "settings_shadows", "settings_shadows", ident)}
    return node


def controls_document() -> dict:
    tpl = Templates()
    doc = Document("openq4.controls")
    doc.state["controls.capture"] = {"type": "number", "initial": -1}
    for row in range(len(BINDINGS)):
        doc.state[f"controls.{row}.keys"] = {"type": "string", "initial": ""}
    doc.session("controlsBind", "controlsBind")
    doc.session("controlsClear", "controlsClear")
    doc.session("back", "controlsBack")
    columns, row = [], 0
    for section, heading_key, rows in SECTIONS:
        children = []
        if section == "move":
            # How to change and clear a binding, as the stock page's hint said.
            hint = renamed(tpl.node("settings_shadows-label"), "settings_shadows-label", "controls-hint")
            text_node(hint, "#str_231545")
            hint["properties"]["color"] = {"type": "color", "value": [1, 1, 1, 0.6]}
            hint["properties"]["margin-bottom"] = {"type": "length", "value": 12, "unit": "dp"}
            children.append(hint)
        for label_key, _binding in rows:
            children.append(binding_row(doc, tpl, row, label_key))
            row += 1
        columns.append(section_column(tpl, PREFIX, section, heading_key, children))
    # The west face button clears the focused row, as Delete does.
    doc.events["onSecondary"] = [{"op": "action", "action": "controlsClear"}]
    return settings_page(doc, tpl, PREFIX, "#str_200083", columns, "controls_bind_0")
