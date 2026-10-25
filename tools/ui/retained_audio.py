"""The retained AUDIO settings page (docs/dev/ui-visual-design.md section 7;
UI-01): the stock page's rows (guis/menu/settings/audio.gui), LEVELS,
DEVICES and EFFECTS, in the SYSTEM page's construction, which it takes from
the SYSTEM document itself (guis/menu/settings/system.q4ui): its panel,
header and rail, scrolling body and footer, and a slider, a toggle and a
choice row as templates, each cloned under its own ids with its state
timelines. A change to those SYSTEM parts regenerates this page.

The page applies each change at once, as the stock page does, through the
session (session.menuValue verbs, idSessionLocal::HandleRetainedAudioRequest):
the three volumes and the subtitle size and background as whole percents,
the sound system, device, EAX, speakers and HRTF with the stock page's own
commands (sound drivar, sound eax, sound speakers), which restart the sound
system and may ask with the stock message box. The session publishes the
values it reads back (audio.*) and the device list (audio.device.<i>.label,
audio.device.count). BACK, or the back input, returns to the settings
screen that opened it."""
from __future__ import annotations

import copy
import json
import re

from build_retained_screens import PAK0, Document

SYSTEM = PAK0 / "guis" / "menu" / "settings" / "system.q4ui"
DEVICES = 16                               # the device list's rows (BuildMainMenuAudioDeviceChoices)
OPTION_H = 36.0                            # dp: a choice's option row, as the SYSTEM page sets them

# Each section: its heading and its rows (kind, id, label, verb, state, and
# the slider's range and step or the choice's options).
SECTIONS = (
    ("levels", "#str_41096", (
        ("slider", "audio_volume", "#str_201029", "audioVolume", "audio.volume", (0, 100, 10)),
        ("slider", "audio_music", "#str_201006", "audioMusic", "audio.music", (0, 100, 5)),
        ("slider", "audio_dialogue", "#str_231300", "audioDialogue", "audio.dialogue", (0, 100, 5)),
    )),
    ("devices", "#str_229962", (
        ("choice", "audio_backend", "#str_200971", "audioBackend", "audio.backend", (("#str_200970", 0, 0), ("#str_200970", 1, 1))),
        ("device", "audio_device", "#str_201005", "audioDevice", "audio.device", None),
    )),
    ("effects", "#str_229963", (
        ("toggle", "audio_eax", "#str_200972", "audioEax", "audio.eax", None),
        ("choice", "audio_speakers", "#str_200152", "audioSpeakers", "audio.speakers",
         (("#str_229980", 0, 0), ("#str_229980", 1, 1), ("#str_229980", 2, 2))),
        ("choice", "audio_hrtf", "#str_229981", "audioHrtf", "audio.hrtf",
         (("#str_229980", 0, 0), ("#str_229980", 1, 1), ("#str_229980", 2, 2))),
        ("toggle", "audio_subtitles", "#str_231308", "audioSubtitles", "audio.subtitles", None),
        ("slider", "audio_subtitle_size", "#str_231309", "audioSubtitleSize", "audio.subtitleSize", (100, 200, 10)),
        ("slider", "audio_subtitle_background", "#str_231310", "audioSubtitleBackground", "audio.subtitleBackground", (0, 100, 10)),
        ("toggle", "audio_subtitle_speakers", "#str_231311", "audioSubtitleSpeakers", "audio.subtitleSpeakers", None),
    )),
)
VERBS = tuple(row[3] for _section, _heading, rows in SECTIONS for row in rows)


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
    """The SYSTEM document's parts this page is built from."""

    def __init__(self) -> None:
        self.system = system_document()
        self.timelines = {timeline["id"]: timeline for timeline in self.system["timelines"]}

    def node(self, ident: str) -> dict:
        found = find(self.system["root"], ident)
        if found is None:
            raise SystemExit(f"the SYSTEM page no longer has {ident}, which the AUDIO page is built from")
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


def slider_row(doc: Document, tpl: Templates, ident: str, label_key: str, verb: str, state: str, bounds: tuple) -> dict:
    """The SYSTEM page's brightness row: the label over a slider and its
    number field, both of which ask the session for the new value."""
    minimum, maximum, step = bounds
    row = renamed(renamed(tpl.node("settings_brightness_row"), "settings_brightness", ident), "settings-", "audio-")
    text_node(find(row, f"{ident}-label"), label_key)
    slider = find(row, ident)
    slider["control"].update({"label": label_key, "action": verb, "value": {"state": state}, "minimum": minimum,
                              "maximum": maximum, "step": step, "decimals": 0,
                              "states": tpl.states(doc, "settings_brightness", "settings_brightness", ident)})
    number = find(row, f"{ident}_number")
    number["control"].update({"label": label_key, "action": verb, "value": {"state": state}, "minimum": minimum,
                              "maximum": maximum, "exponent": False, "maxBytes": 3,
                              "states": tpl.states(doc, "settings_brightness_number", "settings_brightness", ident)})
    return row


def toggle_row(doc: Document, tpl: Templates, ident: str, label_key: str, verb: str, state: str) -> dict:
    """The SYSTEM page's shadows row: the label and its check box."""
    row = renamed(renamed(tpl.node("settings_shadows"), "settings_shadows", ident), "settings-", "audio-")
    text_node(find(row, f"{ident}-label"), label_key)
    row["control"].update({"label": label_key, "action": verb, "value": {"state": state},
                           "states": tpl.states(doc, "settings_shadows", "settings_shadows", ident)})
    return row


def choice_row(doc: Document, tpl: Templates, ident: str, label_key: str, verb: str, state: str, options: list,
               count: dict | None = None) -> dict:
    """The SYSTEM page's display row: the label, the chosen value in orange
    and its chevron, and the list it unfolds. `options` are (label, value,
    label index or None, enabled or None)."""
    row = renamed(renamed(tpl.node("settings_display_device"), "settings_display_device", ident), "settings-", "audio-")
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
    row["control"].update({"label": label_key, "action": verb, "value": {"state": state}, "visibleRows": visible, "options": specs,
                           "states": tpl.states(doc, "settings_display_device", "settings_display_device", ident)})
    # A list the session fills says how many of its rows hold an option.
    row["control"].pop("optionCount", None)
    if count is not None:
        row["control"]["optionCount"] = count
    return row


def audio_document() -> dict:
    tpl = Templates()
    doc = Document("openq4.audio")
    doc.state.update({
        "audio.volume": {"type": "number", "initial": 0}, "audio.music": {"type": "number", "initial": 0},
        "audio.dialogue": {"type": "number", "initial": 0}, "audio.backend": {"type": "number", "initial": 1},
        "audio.device": {"type": "number", "initial": 0}, "audio.device.count": {"type": "number", "initial": 0},
        "audio.eax": {"type": "boolean", "initial": False}, "audio.speakers": {"type": "number", "initial": 0},
        "audio.hrtf": {"type": "number", "initial": 0}, "audio.subtitles": {"type": "boolean", "initial": False},
        "audio.subtitleSize": {"type": "number", "initial": 100}, "audio.subtitleBackground": {"type": "number", "initial": 0},
        "audio.subtitleSpeakers": {"type": "boolean", "initial": False},
    })
    for row in range(DEVICES):
        doc.state[f"audio.device.{row}.label"] = {"type": "string", "initial": ""}
    for _section, _heading, rows in SECTIONS:
        for kind, _ident, _label_key, verb, _state, _extra in rows:
            boolean = kind == "toggle"
            doc.actions[verb] = {"operation": "session.menuValue", "input": "boolean" if boolean else "number",
                                 "arguments": {"command": verb, "value": {"input": "value"}}}
    doc.session("back", "audioBack")
    first = None
    columns = []
    for section, heading_key, rows in SECTIONS:
        column = renamed(tpl.node("image-column"), "image-column", f"audio-{section}-column")
        heading = renamed(tpl.node("image-heading"), "image-heading", f"audio-{section}-heading")
        text_node(heading, heading_key)
        children = [heading]
        for kind, ident, label_key, verb, state, extra in rows:
            if kind == "slider":
                node = slider_row(doc, tpl, ident, label_key, verb, state, extra)
                control = ident
            elif kind == "toggle":
                node = toggle_row(doc, tpl, ident, label_key, verb, state)
                control = ident
            elif kind == "choice":
                node = choice_row(doc, tpl, ident, label_key, verb, state, [(key, value, index, None) for key, value, index in extra])
                control = ident
            else:
                options = [({"state": f"audio.device.{row}.label"}, row, None,
                            {"op": "<", "args": [row, {"state": "audio.device.count"}]}) for row in range(DEVICES)]
                node = choice_row(doc, tpl, ident, label_key, verb, state, options, {"state": "audio.device.count"})
                control = ident
            first = first or control
            children.append(node)
        column["children"] = children
        columns.append(column)

    # The frame: the SYSTEM page's panel, header and rail, scrolling body
    # and footer, with BACK alone in the footer.
    panel = renamed(tpl.node("settings-panel"), "settings", "audio")
    panel = renamed(panel, "settings_", "audio_")
    header_body = find(panel, "audio-header-body")
    title = find(header_body, "audio-title")
    text_node(title, "#str_200151")
    header_body["children"] = [title]
    body = find(panel, "audio-body")
    body["children"] = columns
    actions = find(panel, "audio-actions")
    back = find(actions, "audio_back")
    actions["children"] = [back]
    actions["properties"]["width"] = {"type": "length", "value": 160, "unit": "dp"}
    for control, old in (("audio_back", "settings_back"), ("audio_header_scrollbar", "settings_header_scrollbar"),
                         ("audio_body_scrollbar", "settings_body_scrollbar")):
        node = find(panel, control)
        node["control"]["states"] = tpl.states(doc, old, old, control)
    root = renamed({key: value for key, value in tpl.system["root"].items() if key != "children"}, "settings", "audio")
    root["children"] = [panel]
    doc.events["onActivate"] = [{"op": "focus", "control": first}]
    doc.events["onBack"] = [{"op": "action", "action": "back"}]
    result = doc.build(root)
    result.pop("canvas", None)
    return result
