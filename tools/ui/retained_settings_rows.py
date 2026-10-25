"""The settings pages' construction (docs/dev/ui-visual-design.md section 7;
UI-01), taken from the SYSTEM document itself
(guis/menu/settings/system.q4ui): its panel, header and rail, scrolling body
and footer, a section column and heading, and a slider, a toggle and a choice
row as templates, each cloned under a page's own ids with its state
timelines. The AUDIO and GAME pages are built from these, so a change to
those SYSTEM parts regenerates them."""
from __future__ import annotations

import copy
import json
import re

from build_retained_screens import PAK0, Document

SYSTEM = PAK0 / "guis" / "menu" / "settings" / "system.q4ui"
OPTION_H = 36.0                            # dp: a choice's option row, as the SYSTEM page sets them


def system_document() -> dict:
    text = SYSTEM.read_text(encoding="utf-8")
    return json.loads(re.sub(r"^\s*//.*$", "", text, flags=re.M))


def find(node: dict, wanted: str) -> dict:
    if node.get("id") == wanted:
        return node
    for child in node.get("children", []):
        found = find(child, wanted)
        if found is not None:
            return found
    return None


def renamed(value, old: str, new: str):
    """A deep copy of `value` with every id, part and timeline name that
    starts with `old` starting with `new` instead."""
    text = json.dumps(value)
    text = text.replace(f'"{old}', f'"{new}')
    return json.loads(text)


class Templates:
    """The SYSTEM document's parts the settings pages are built from."""

    def __init__(self) -> None:
        self.system = system_document()
        self.timelines = {timeline["id"]: timeline for timeline in self.system["timelines"]}

    def node(self, ident: str) -> dict:
        found = find(self.system["root"], ident)
        if found is None:
            raise SystemExit(f"the SYSTEM page no longer has {ident}, which the settings pages are built from")
        return copy.deepcopy(found)

    def states(self, doc: Document, control: str, old: str, new: str) -> dict:
        """The control's state timelines, cloned under the new ids."""
        ids = {}
        for state in ("default", "hover", "focus", "pressed", "disabled"):
            timeline = self.timelines.get(f"{control}.{state}")
            if timeline is None:
                raise SystemExit(f"the SYSTEM page's {control} has no {state} timeline")
            clone = renamed(timeline, old, new)
            doc.timelines.items.append(clone)
            ids[state] = clone["id"]
        return ids


def text_node(node: dict, key) -> None:
    node["properties"]["text"] = {"type": "text", "value": key} if isinstance(key, str) else key


def slider_row(doc: Document, tpl: Templates, prefix: str, ident: str, label_key: str, action: str, state: str, bounds: tuple,
               decimals: int = 0, max_bytes: int = 3, integer: bool | None = None) -> dict:
    """The SYSTEM page's brightness row: the label over a slider and its
    number field, both of which request `action` with the new value.
    `integer` marks a number field that takes whole numbers only."""
    minimum, maximum, step = bounds
    row = renamed(renamed(tpl.node("settings_brightness_row"), "settings_brightness", ident), "settings-", f"{prefix}-")
    text_node(find(row, f"{ident}-label"), label_key)
    slider = find(row, ident)
    slider["control"].update({"label": label_key, "action": action, "value": {"state": state}, "minimum": minimum,
                              "maximum": maximum, "step": step, "decimals": decimals,
                              "states": tpl.states(doc, "settings_brightness", "settings_brightness", ident)})
    number = find(row, f"{ident}_number")
    number["control"].update({"label": label_key, "action": action, "value": {"state": state}, "minimum": minimum,
                              "maximum": maximum, "exponent": False, "maxBytes": max_bytes,
                              "states": tpl.states(doc, "settings_brightness_number", "settings_brightness", ident)})
    if integer is not None:
        number["control"]["integer"] = integer
    return row


def toggle_row(doc: Document, tpl: Templates, prefix: str, ident: str, label_key: str, action: str, state: str) -> dict:
    """The SYSTEM page's shadows row: the label and its check box."""
    row = renamed(renamed(tpl.node("settings_shadows"), "settings_shadows", ident), "settings-", f"{prefix}-")
    text_node(find(row, f"{ident}-label"), label_key)
    row["control"].update({"label": label_key, "action": action, "value": {"state": state},
                           "states": tpl.states(doc, "settings_shadows", "settings_shadows", ident)})
    return row


def choice_row(doc: Document, tpl: Templates, prefix: str, ident: str, label_key: str, action: str, state: str, options: list,
               count: dict | None = None) -> dict:
    """The SYSTEM page's display row: the label, the chosen value in orange
    and its chevron, and the list it unfolds. `options` are (label, value,
    label index or None, enabled or None)."""
    row = renamed(renamed(tpl.node("settings_display_device"), "settings_display_device", ident), "settings-", f"{prefix}-")
    text_node(find(row, f"{ident}-label"), label_key)
    content = find(row, f"{ident}-content")
    template = copy.deepcopy(content["children"][0])
    old_option = template["id"]
    content["children"] = []
    specs = []
    for index, (option_label, value, label_index, enabled) in enumerate(options):
        node_id = f"{ident}-option-{index}"
        node = renamed(template, old_option, node_id)
        # A row the session fills keeps the template's text; its option's
        # label names what it shows, as the SYSTEM page's display list does.
        option_text = find(node, f"{node_id}-label")
        if option_text is not None and isinstance(option_label, str):
            text_node(option_text, option_label)
        content["children"].append(node)
        spec = {"id": node_id, "node": node_id, "label": option_label, "value": value,
                "parts": {"label": f"{node_id}-label", "selected": f"{node_id}-selected", "highlight": f"{node_id}-highlight"}}
        if label_index is not None:
            spec["labelIndex"] = label_index
        if enabled is not None:
            spec["enabled"] = enabled
        specs.append(spec)
    visible = min(8, len(options))
    for part in (f"{ident}-popup", f"{ident}-viewport"):
        find(row, part)["properties"]["height"] = {"type": "length", "value": OPTION_H * visible, "unit": "dp"}
    row["control"].update({"label": label_key, "action": action, "value": {"state": state}, "visibleRows": visible, "options": specs,
                           "states": tpl.states(doc, "settings_display_device", "settings_display_device", ident)})
    # A list the session fills says how many of its rows hold an option.
    row["control"].pop("optionCount", None)
    if count is not None:
        row["control"]["optionCount"] = count
    return row


def section_column(tpl: Templates, prefix: str, section: str, heading_key: str, children: list) -> dict:
    """A section: the SYSTEM page's column with its heading over the rows."""
    column = renamed(tpl.node("image-column"), "image-column", f"{prefix}-{section}-column")
    heading = renamed(tpl.node("image-heading"), "image-heading", f"{prefix}-{section}-heading")
    text_node(heading, heading_key)
    column["children"] = [heading, *children]
    return column


def settings_page(doc: Document, tpl: Templates, prefix: str, title_key: str, columns: list, first: str,
                  activate: list | None = None) -> dict:
    """The frame: the SYSTEM page's panel, header and rail, scrolling body
    and footer, with BACK alone in the footer. The page opens on `first`, or
    runs `activate`; BACK and the back input run the document's back action."""
    panel = renamed(tpl.node("settings-panel"), "settings", prefix)
    panel = renamed(panel, "settings_", f"{prefix}_")
    header_body = find(panel, f"{prefix}-header-body")
    title = find(header_body, f"{prefix}-title")
    text_node(title, title_key)
    header_body["children"] = [title]
    body = find(panel, f"{prefix}-body")
    body["children"] = columns
    actions = find(panel, f"{prefix}-actions")
    back = find(actions, f"{prefix}_back")
    actions["children"] = [back]
    actions["properties"]["width"] = {"type": "length", "value": 160, "unit": "dp"}
    for control, old in ((f"{prefix}_back", "settings_back"), (f"{prefix}_header_scrollbar", "settings_header_scrollbar"),
                         (f"{prefix}_body_scrollbar", "settings_body_scrollbar")):
        node = find(panel, control)
        node["control"]["states"] = tpl.states(doc, old, old, control)
    root = renamed({key: value for key, value in tpl.system["root"].items() if key != "children"}, "settings", prefix)
    root["children"] = [panel]
    doc.events["onActivate"] = activate or [{"op": "focus", "control": first}]
    doc.events["onBack"] = [{"op": "action", "action": "back"}]
    result = doc.build(root)
    result.pop("canvas", None)
    return result
