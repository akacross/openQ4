#!/usr/bin/env python3
"""Give the SYSTEM page its initial focus (visual specification 13.4).

The page opened with nothing focused, so a controller's first Accept did
nothing. Its activation now asks for the focus on its first row, the
performance preset selector, after beginning the settings draft. The row is
enabled only once the draft is open; the runtime keeps a focus its control
cannot take yet and tries it again after the next frame's layout, by when
the session has opened the draft. This tool owns that focus step of
onActivate. --check verifies reproducible generation without writing.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
from update_system_number_fields import index_nodes, load

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('content/baseoq4/pak0/guis/menu/settings/system.q4ui')
INITIAL = 'settings_preset'


def compose(document):
    result = copy.deepcopy(document)
    control = index_nodes(result['root']).get(INITIAL)
    if not control or not control.get('control'):
        raise ValueError(f'{INITIAL} is no longer a SYSTEM control; review the initial focus')
    program = [step for step in result['events']['onActivate'] if step.get('op') != 'focus']
    begins = [index for index, step in enumerate(program) if step == {'op': 'action', 'action': 'begin'}]
    if len(begins) != 1:
        raise ValueError('SYSTEM activation no longer begins the settings draft once; review the initial focus')
    program.insert(begins[0] + 1, {'op': 'focus', 'control': INITIAL})
    result['events']['onActivate'] = program
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--source', type=Path, default=ROOT / SOURCE)
    parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    prefix, document = load(args.source); result = compose(document)
    if args.check:
        if result != document: raise SystemExit('SYSTEM activation differs from its initial focus definition')
    else: args.source.write_text(prefix + json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__': main()
