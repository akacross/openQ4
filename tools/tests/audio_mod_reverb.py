#!/usr/bin/env python3
"""Render real OpenAL loopback audio to qualify nonzero room rolloff units.

No playback endpoint, microphone, input events or installed assets are used.
"""
import argparse
import ctypes as C
import hashlib
import json
import math
import os
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', type=Path, default=ROOT / '.install/OpenAL32.dll')
    parser.add_argument('--output', type=Path, default=ROOT / '.tmp/audio/mod-reverb')
    args = parser.parse_args()
    library = args.library.resolve(strict=True)
    if os.name == 'nt':
        dll_directory = os.add_dll_directory(str(library.parent))
    al = C.CDLL(str(library))

    def fn(name, result, *params):
        call = getattr(al, name)
        call.restype, call.argtypes = result, params
        return call

    ptr, uint, integer, floating = C.c_void_p, C.c_uint, C.c_int, C.c_float
    getproc = fn('alcGetProcAddress', ptr, ptr, C.c_char_p)
    loopopen = C.CFUNCTYPE(ptr, C.c_char_p)(getproc(None, b'alcLoopbackOpenDeviceSOFT'))
    render = C.CFUNCTYPE(None, ptr, ptr, integer)(getproc(None, b'alcRenderSamplesSOFT'))
    create = fn('alcCreateContext', ptr, ptr, C.POINTER(integer))
    current = fn('alcMakeContextCurrent', C.c_char, ptr)
    destroy = fn('alcDestroyContext', None, ptr)
    close = fn('alcCloseDevice', C.c_char, ptr)
    error = fn('alGetError', integer)
    source_i = fn('alSourcei', None, uint, integer, integer)
    source_f = fn('alSourcef', None, uint, integer, floating)
    source_3f = fn('alSource3f', None, uint, integer, floating, floating, floating)
    source_3i = fn('alSource3i', None, uint, integer, integer, integer, integer)
    effect_i = fn('alEffecti', None, uint, integer, integer)
    effect_f = fn('alEffectf', None, uint, integer, floating)
    slot_i = fn('alAuxiliaryEffectSloti', None, uint, integer, integer)
    filter_i = fn('alFilteri', None, uint, integer, integer)
    filter_f = fn('alFilterf', None, uint, integer, floating)
    upload = fn('alBufferData', None, uint, integer, ptr, integer, integer)
    play = fn('alSourcePlay', None, uint)
    rng = random.Random(42)
    pcm = (C.c_short * 24000)(*(rng.randint(-4096, 4096) for _ in range(24000)))

    def measure(reference, distance, rolloff, wet=True):
        device = loopopen(None)
        if not device:
            raise RuntimeError('ALC_SOFT_loopback unavailable')
        attributes = (integer * 9)(0x1990, 0x1501, 0x1991, 0x1406, 0x1007, 48000, 0x1992, 0, 0)
        context = create(device, attributes)
        if not context:
            close(device)
            raise RuntimeError('Stereo float loopback context unavailable')
        current(context)
        objects = []
        try:
            def generate(kind):
                result = uint()
                fn('alGen' + kind, None, integer, C.POINTER(uint))(1, C.byref(result))
                objects.append((kind, result))
                return result.value
            buffer = generate('Buffers')
            source = generate('Sources')
            effect = generate('Effects')
            slot = generate('AuxiliaryEffectSlots')
            filter_ = generate('Filters')
            upload(buffer, 0x1101, pcm, C.sizeof(pcm), 48000)  # mono 16-bit
            effect_i(effect, 0x8001, 1)  # standard EFX reverb
            effect_f(effect, 0x000C, rolloff)
            slot_i(slot, 1, effect)
            source_i(source, 0x1009, buffer)
            source_i(source, 0x1007, 1)
            source_i(source, 0x0202, 1)
            source_f(source, 0x1021, 0)  # engine owns the dry distance curve
            source_f(source, 0x1020, reference)
            source_3f(source, 0x1004, 0, 0, -distance)
            if wet:
                filter_i(filter_, 0x8001, 1)
                filter_f(filter_, 1, 0)
                source_i(source, 0x20005, filter_)
                source_3i(source, 0x20006, slot, 0, 0)
            if error():
                raise RuntimeError('OpenAL rejected fixture settings')
            play(source)
            mix = (floating * (48000 * 2))()
            render(device, mix, 48000)
            if error():
                raise RuntimeError('OpenAL render failed')
            # Exclude the effect's initial rise; compare the same deterministic
            # noise and physical rendering at each distance, not API receipts.
            samples = list(mix)[24000:]
            return math.sqrt(sum(value * value for value in samples) / len(samples))
        finally:
            # Context owns and destroys all objects, including queued sources.
            current(None)
            destroy(context)
            close(device)

    values = {
        'stock_reference_1': measure(1, 200, 0),
        'stock_reference_100': measure(100, 200, 0),
        'mod_near': measure(100, 100, 1),
        'mod_twice_min': measure(100, 200, 1),
        'mod_old_reference': measure(1, 200, 1),
        'mod_scaled_units': measure(1, 2, 1),
        'dry_reference_1': measure(1, 200, 1, False),
        'dry_reference_100': measure(100, 200, 1, False),
    }
    def close_ratio(a, b, expected):
        return values[b] > 1e-8 and abs(values[a] / values[b] - expected) < .005
    checks = {
        'stock_zero_unchanged': close_ratio('stock_reference_100', 'stock_reference_1', 1),
        'mod_half_gain_at_twice_min': close_ratio('mod_twice_min', 'mod_near', .5),
        'unit_scale_invariant': close_ratio('mod_twice_min', 'mod_scaled_units', 1),
        'old_default_reproduces_excess_loss': close_ratio('mod_old_reference', 'mod_twice_min', .01),
        'dry_mix_unchanged': close_ratio('dry_reference_100', 'dry_reference_1', 1),
    }
    # The production setter must send the sanitized authored radius, including
    # when source-radius spatialization is unavailable on an older provider.
    source = (ROOT / 'src/sound/OpenAL/AL_SoundVoice.h').read_text()
    from sound_settings import body
    setter = body(source, 'void\t\tSetInnerRadius(')
    checks['production_reference'] = 'AL_REFERENCE_DISTANCE, Max( innerRadius, 0.001f )' in setter
    result = {'rms': values, 'checks': checks, 'passed': all(checks.values()),
              'provider_sha256': hashlib.sha256(library.read_bytes()).hexdigest(),
              'physical_device': False, 'renderer': 'ALC_SOFT_loopback stereo float 48000 Hz'}
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
