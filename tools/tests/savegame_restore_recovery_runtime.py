#!/usr/bin/env python3
"""Reject semantically damaged current saves, show recovery UI and load again.

All fixtures retain a valid outer CRC, so this exercises restore-time validation
after map teardown. Engine console scripts issue game commands and screenshots;
no OS input or screen capture is used. Source saves are never modified.
"""
from pathlib import Path
import argparse
import json
import os
import re
import struct
import subprocess
import time
import zlib

from savegame_restore_cleanup_runtime import ROOT, checksum_fixture, sha


def damaged_fixtures(data):
    _, metadata = checksum_fixture(data)
    position = metadata['server_info_sync']
    sequence = 0

    def integer():
        nonlocal position
        value = struct.unpack_from('<i', data, position)[0]
        position += 4
        return value

    def string():
        nonlocal position
        size = integer()
        assert 0 <= size < 1048576
        value = data[position:position+size]
        assert len(value) == size
        position += size
        return value

    def dictionary():
        nonlocal sequence
        assert integer() == int.from_bytes(b'OQ4Y', 'little') and integer() == sequence
        sequence += 1
        count = integer()
        assert -1 <= count < 65536
        for _ in range(max(0, count)):
            string()
            string()

    def capacity(symbol):
        text = (ROOT/'src/game/Game_local.h').read_text()
        bits = int(re.search(r'#define\s+'+symbol+r'\s+(\d+)', text)[1])
        assert bits == 12, 'Review save fixture parsing if table capacities change.'
        return 1 << bits

    def table(count):
        result = []
        for index in range(count):
            offset = position
            reference, spawn_id = integer(), integer()
            assert 0 <= reference <= metadata['objects']
            if reference:
                result.append(dict(slot=index, offset=offset, reference=reference, spawn_id=spawn_id))
        assert len(result) > 2
        assert len({item['reference'] for item in result}) == len(result)
        return result

    dictionary()  # serverInfo
    clients = integer()
    assert 0 <= clients <= 32
    for _ in range(clients):
        dictionary()  # persistentPlayerInfo
    entities = table(capacity('GENTITYNUM_BITS'))
    client_entities = table(capacity('CENTITYNUM_BITS'))
    first_free_offset = position
    assert 0 <= integer() < capacity('GENTITYNUM_BITS')
    definitions = [
        ('BadObjectIndex', entities[1]['offset'], 2147483647, 'invalid object index 2147483647'),
        ('DuplicateEntity', entities[1]['offset'], entities[0]['reference'], 'invalid entity registration'),
        ('DuplicateClient', client_entities[1]['offset'], client_entities[0]['reference'], 'invalid client entity registration'),
        ('WrongClientType', client_entities[0]['offset'], entities[0]['reference'], "expected 'rvClientEntity'"),
        ('BadFreeIndex', first_free_offset, capacity('GENTITYNUM_BITS'), 'invalid first free entity index 4096'),
    ]
    fixtures = {}
    for name, offset, value, expected in definitions:
        changed = bytearray(data)
        original = struct.unpack_from('<i', data, offset)[0]
        assert original != value
        struct.pack_into('<i', changed, offset, value)
        struct.pack_into('<I', changed, len(changed)-4, zlib.crc32(changed[:-16]))
        fixtures[name] = (bytes(changed), dict(offset=offset, original=original, replacement=value, expected=expected))
    metadata.update(clients=clients, registered_entities=len(entities), registered_clients=len(client_entities))
    return fixtures, metadata


def render_handle_fixture(data):
    """Locate a v4 entity with empty GUI slots, using its named class record.

    The parser checks every intervening sync and bounded record. It skips records
    with GUI payloads rather than assuming their variable legacy layout.
    """
    _, metadata = checksum_fixture(data)
    markers = list(re.finditer(re.escape(b'OQ4Y'), data))
    for candidate in markers:
        position = candidate.start()
        sequence = struct.unpack_from('<i', data, position+4)[0]

        def integer():
            nonlocal position
            value = struct.unpack_from('<i', data, position)[0]
            position += 4
            return value

        def skip(size):
            nonlocal position
            assert 0 <= size < 1048576 and position+size <= len(data)
            position += size

        def string():
            size = integer()
            assert 0 <= size < 65536
            value = data[position:position+size]
            skip(size)
            return value.decode('ascii')

        def sync():
            nonlocal sequence
            assert integer() == int.from_bytes(b'OQ4Y', 'little') and integer() == sequence
            sequence += 1

        try:
            sync()  # idEntity class start
            number, definition, snapshot, bits = integer(), integer(), integer(), integer()
            assert 0 <= number < 4095 and -1 <= definition < 65536
            name = string()
            assert re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', name)
            sync()  # spawnArgs
            count = integer()
            assert 0 < count < 4096
            args = {}
            for _ in range(count):
                key = string()
                args[key] = string()
            assert args.get('name') == name and args.get('classname')
            typename = string()
            if typename:
                skip(integer())  # script object bytes
            skip(4+4+1+4)  # thinkFlags, dormantStart, cinematic, cameraTarget
            targets = integer()
            assert 0 <= targets < 4096
            skip(targets*4)
            skip(4)  # health
            clients = integer()
            assert 0 <= clients < 4096
            skip(clients*4)
            skip(4)  # v4 typed entity flags
            sync()  # ReadRenderEntity
            model = string()
            skip(4+4+24+20+12+36)  # entity/body, bounds, five view flags, origin, axis
            for _ in range(4):
                string()  # custom/reference/overlay shader and skin
            skip(4+12*4)  # sound handle and MAX_ENTITY_SHADER_PARMS
            for _ in range(3):
                sync()
                assert string() == ''  # only empty GUI slots
            skip(4+4+4+4+4)  # depth float, four bools, depth-view int, LOD float/int
            handle_offset = position
            handle = integer()
            assert handle >= -1
            sound_sync = position
            sync()  # immediately following ReadRefSound
            sound_handle = integer()
            assert -1 <= sound_handle < 1048576
            changed = bytearray(data)
            struct.pack_into('<i', changed, handle_offset, 2147483647)
            struct.pack_into('<I', changed, sound_sync, 0)
            struct.pack_into('<I', changed, len(changed)-4, zlib.crc32(changed[:-16]))
            detail = dict(entity=name, entity_number=number, entity_class=args['classname'], model=model,
                          class_offset=candidate.start(), handle_offset=handle_offset, original_handle=handle,
                          replacement_handle=2147483647, broken_sound_sync=sound_sync,
                          expected='marker mismatch while reading ReadRefSound')
            return {'ForeignModelHandle': (bytes(changed), detail)}, metadata
        except (AssertionError, UnicodeError, struct.error):
            continue
    raise AssertionError('No fully decoded v4 entity with empty GUI slots was found.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-save', type=Path, required=True)
    parser.add_argument('--basepath', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ui', choices=('retained', 'classic'), default='retained')
    parser.add_argument('--renderer', choices=('gl', 'vulkan'), default='gl')
    parser.add_argument('--cases', choices=('registrations', 'render-handles'), default='registrations')
    parser.add_argument('--timeout', type=int, default=240)
    args = parser.parse_args()
    if os.name != 'nt':
        parser.error('Runtime probe targets staged Windows x64; native recovery tests also run on Linux.')
    output, source, runtime = args.output.resolve(), args.source_save.resolve(), ROOT/'.install'
    if (ROOT/'.tmp').resolve() not in output.parents:
        parser.error('Output must be a new directory below project .tmp.')
    for relative in ('openQ4-client_x64.exe', 'baseoq4/game-sp_x64.dll', 'baseoq4/game-mp_x64.dll'):
        if sha(ROOT/'builddir'/relative) != sha(runtime/relative):
            parser.error('Stage the current build before running this probe: '+relative)
    original = source.read_bytes()
    fixtures, metadata = (render_handle_fixture(original) if args.cases == 'render-handles' else damaged_fixtures(original))
    output.mkdir(parents=True, exist_ok=False)
    save = output/'save'
    game = save/'baseoq4'
    (game/'savegames').mkdir(parents=True)
    saves = [game/'savegames/Good.save']
    saves[0].write_bytes(original)
    for name, (data, _) in fixtures.items():
        path = game/'savegames'/f'{name}.save'
        path.write_bytes(data)
        saves.append(path)
    markers = ['RESTORE_GOOD_INITIAL']
    script = ['echo RESTORE_GOOD_INITIAL', 'screenshot screenshots/initial.tga',
              'set g_autoExecAfterMapLoad ""']
    for name in fixtures:
        marker = 'RESTORE_REJECTED_'+name
        markers.append(marker)
        script += ['loadGame '+name, 'waitMsec 2000', 'echo '+marker,
                   'openq4_retainedGui report', f'screenshot screenshots/{name}.tga']
    script += ['set g_autoExecAfterMapLoad final.cfg', 'loadGame Good']
    (game/'initial.cfg').write_text('\n'.join(script)+'\n')
    markers.append('RESTORE_GOOD_FINAL')
    (game/'final.cfg').write_text('echo RESTORE_GOOD_FINAL\nscreenshot screenshots/final.tga\nquit\n')
    settings = dict(fs_game='baseoq4', fs_basepath=str(args.basepath.resolve()), fs_savepath=str(save), fs_devpath=str(save),
        com_gameMode='SP', si_gameType='singleplayer', ui_retained='1' if args.ui == 'retained' else '0', ui_autoJoin='0',
        win_allowMultipleInstances='1', sys_consoleWindow='0', in_tty='0', in_mouse='0', in_joystick='0', s_noSound='1',
        r_fullscreen='0', r_fullscreenDesktop='0', r_borderless='0', r_borderlessDefaultMigrated='1', r_hiddenWindow='1',
        r_mode='-1', r_customWidth='1280', r_customHeight='720', r_windowWidth='1280', r_windowHeight='720',
        r_renderApi=args.renderer, r_swapInterval='0', com_maxfps='60', com_skipLoadingContinue='1', com_loadingContinueAutoAdvance='1',
        g_autoSkipCinematics='1', g_autoExecAfterMapLoad='initial.cfg', g_autoExecAfterMapLoadDelayMs='750',
        logFile='2', logFileName='logs/openq4.log', developer='1')
    executable = runtime/'openQ4-client_x64.exe'
    command = [str(executable), *[part for key, value in settings.items() for part in ('+set', key, value)], '+loadGame', 'Good']
    report = dict(source_save=dict(path=str(source), sha256=sha(source)), fixture=metadata,
        cases={name: details for name, (_, details) in fixtures.items()}, command=command,
        harness_sha256=sha(Path(__file__)), ui=args.ui, renderer=args.renderer, fixture_set=args.cases,
        runtime={relative: sha(runtime/relative) for relative in
                 ('openQ4-client_x64.exe', 'baseoq4/game-sp_x64.dll', 'baseoq4/game-mp_x64.dll', 'baseoq4/pak0.pk4', 'baseoq4/pak1.pk4')},
        before={path.name: sha(path) for path in saves},
        scope='Current v4 semantic restore rejection, real recovery UI, good reload. Hidden window, input disabled, engine screenshots.')
    (output/'plan.json').write_text(json.dumps(report, indent=2)+'\n')
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = subprocess.SW_HIDE
    begin = time.monotonic()
    with (output/'stdout.log').open('w') as stream:
        process = subprocess.Popen(command, cwd=runtime, stdout=stream, stderr=subprocess.STDOUT,
                                   stdin=subprocess.DEVNULL, startupinfo=startup)
        try:
            code = process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            process.terminate()
            code = process.wait(timeout=15)
            report['timed_out'] = True
    report.update(exit_code=code, elapsed=time.monotonic()-begin, after={path.name: sha(path) for path in saves})
    log = game/'logs/openq4.log'
    text = log.read_text(errors='replace') if log.is_file() else ''
    report['markers'] = {marker: text.count(marker) for marker in markers}
    report['restore_attempts'] = text.count('Game Map Init SaveGame')
    report['expected_errors'] = {name: details['expected'] in text for name, (_, details) in fixtures.items()}
    report['screenshots'] = {name: sha(game/f'screenshots/{name}.tga')
        for name in ['initial', *fixtures, 'final'] if (game/f'screenshots/{name}.tga').is_file()}
    report['engine_log_sha256'] = sha(log) if log.is_file() else None
    report['recovery_ui'] = dict(retained_pages=text.count('RETAINED_GUI path=guis/menu/loadgame.q4ui'),
                                classic_dialogs=text.count('MessageBox: LOAD FAILED -'))
    ui_passed = (report['recovery_ui']['retained_pages'] == len(fixtures) and report['recovery_ui']['classic_dialogs'] == 0
                 if args.ui == 'retained' else report['recovery_ui']['classic_dialogs'] == len(fixtures))
    positions = [text.find(marker) for marker in markers]
    report['passed'] = (code == 0 and not report.get('timed_out') and all(report['markers'][m] == 1 for m in markers)
        and positions == sorted(positions) and report['restore_attempts'] == len(fixtures)+2
        and all(report['expected_errors'].values()) and report['before'] == report['after']
        and len(report['screenshots']) == len(fixtures)+2 and 'ERROR:' not in text and ui_passed)
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in ('passed', 'exit_code', 'elapsed', 'markers', 'expected_errors', 'recovery_ui')}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
