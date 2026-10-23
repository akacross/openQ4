#!/usr/bin/env python3
"""Verify the production bounded Vorbis reader against full decoding.

Generates original audio with ffmpeg (PATH or imageio_ffmpeg) in .tmp/audio.
No installed game content or host audio/input device is used.
"""
from pathlib import Path
import os
import shutil
import subprocess
from sound_settings import body

ROOT = Path(__file__).resolve().parents[2]


def main():
    scratch = ROOT / '.tmp/audio/stream-decoder'
    scratch.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        from imageio_ffmpeg import get_ffmpeg_exe
        ffmpeg = get_ffmpeg_exe()
    fixtures = []
    for rate, channels, duration in [(22050, 1, 17), (22050, 1, 3.7), (48000, 2, 32), (44100, 2, 0.1), (96000, 1, 3)]:
        path = scratch / f'{rate}-{channels}-{duration}.ogg'
        subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi',
                        '-i', f'aevalsrc=0.3*sin(2*PI*(300+20*t)*t):s={rate}:d={duration}',
                        '-ac', str(channels), '-c:a', 'libvorbis', '-q:a', '5', str(path)], cwd=scratch, check=True)
        fixtures.append(str(path))
    obj = scratch / ('vorbis.obj' if os.name == 'nt' else 'vorbis.o')
    exe = scratch / ('test.exe' if os.name == 'nt' else 'test')
    subprocess.run([os.environ.get('CC', 'clang'), '-O2', '-c', str(ROOT / 'subprojects/stb_vorbis/stb_vorbis.c'), '-o', str(obj)], cwd=scratch, check=True)
    subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror',
                    '-I', str(ROOT), '-I', str(ROOT / 'subprojects/stb_vorbis'),
                    str(ROOT / 'tools/tests/native/SoundVorbisStreamTest.cpp'), str(obj), '-o', str(exe)], cwd=scratch, check=True)
    subprocess.run([str(exe), *fixtures], cwd=scratch, check=True)
    source = (ROOT / 'src/sound/OpenAL/AL_SoundVoice.cpp').read_text()
    production = '\n'.join(body(source, signature) for signature in [
        'void idSoundVoice_OpenAL::ResetQueuedBufferState()', 'void idSoundVoice_OpenAL::AdvanceQueuedBuffer()',
        'bool idSoundVoice_OpenAL::GetPlayableBufferRange(', 'bool idSoundVoice_OpenAL::SetNextQueuedSampleStart(',
        'bool idSoundVoice_OpenAL::QueueNextBuffer(', 'bool idSoundVoice_OpenAL::Update()',
        'bool idSoundVoice_OpenAL::UsesBoundedQueue()', 'int idSoundVoice_OpenAL::SubmitBuffer(',
        'void idSoundVoice_OpenAL::DeleteStreamingBuffers()', 'int idSoundVoice_OpenAL::RoutedQueueFrames('])
    queue_cpp = scratch / 'queue.cpp'
    queue_cpp.write_text((ROOT / 'tools/tests/native/SoundStreamQueueTest.cpp').read_text().replace('// @PRODUCTION@', production))
    queue_exe = scratch / ('queue.exe' if os.name == 'nt' else 'queue')
    subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror',
                    '-I', str(ROOT), '-I', str(ROOT / 'subprojects/stb_vorbis'), str(queue_cpp), str(obj), '-o', str(queue_exe)], cwd=scratch, check=True)
    subprocess.run([str(queue_exe), *fixtures[:2]], cwd=scratch, check=True)


if __name__ == '__main__':
    main()
