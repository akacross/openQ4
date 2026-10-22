# Audio and voice evidence — 21 October 2026

This is a supporting evidence record for AUD-01 through AUD-07 in the
[roadmap](roadmap.md#audio-and-voice), not a separate work plan. The seven items
remain open until their own acceptance gates are satisfied.

## Tested implementation

Windows x64, MSVC debugoptimized, `builddir`, staged through the project Meson
wrapper into `.install`; base revision `cbe967f2b61935da283a873a731fe975926cf214`
plus the audio changes described here (the engine log reports
`0.14.000-dev+g4085caf9.dirty`, the branch tip before its last test-only and
documentation commits). Every runtime report named below was rerun on
21 October on these final staged binaries:

| Binary | SHA-256 |
| --- | --- |
| `openQ4-client_x64.exe` | `b21f7cd6243a582269d11a60135b45a078891f0af5fabdd750369a278605a1b8` |
| `openQ4-ded_x64.exe` | `dd7e5ef0691b1506be716e55cf8597eac814a6ac3f2d7f44cd51320eaefe3759` |
| `baseoq4/game-mp_x64.dll` | `4cc4c11d3fa510813b2e671d94db9a74d1910e730d3f53814274fd96af3b17fd` |
| `baseoq4/game-sp_x64.dll` | `1773b0729b1701ede1f9db872cc58b248265305d6afde721ec7f5fb4009b96b9` |
| `baseoq4/pak0.pk4` | `de78cd747b9e235e958417a821615d38aa26236514da4136656be45c146a6deb` |
| `OpenAL32.dll` (OpenAL Soft 1.25.2) | `c7905985c3a48cf88b0365879501cbe7b65b3ccf47ff1be3937b0edc079ba6c6` |

Earlier report directories under `.tmp/audio` remain as development history;
only the `final3-*` reports below, and the `final-*` OpenAL loopback reports,
count as evidence for these binaries.

Tests use the installed Steam 1.4.2 PK4s and the user's read-only Awakening
`q4xbase` content under the main checkout's `.home`. Writable profiles, generated
tones, engine screenshots, OpenAL WAV output and logs stay in this worktree's
`.tmp/audio`. No physical microphone, host input injection, desktop capture or fullscreen
launch is used. Another worktree can run concurrently; the harness explicitly
allows multiple instances and never stops a process it did not launch.

## Dialogue volume and pause

`s_dialogueVolume` is archived, defaults to 1 and accepts 0–1. The Audio page has
a slider and numeric value with labels in all twelve shipped language tables.
The player guide describes the setting. The central sound-channel mix applies
it to the sample actually playing, including a leadin/loop transition:

- Explicit `SSF_IS_VO` and `SSF_VO_FOR_PLAYER` speech, including NPC lip-sync.
- Canonical `sound/vo/` and localized `sound/vo_<language>/` samples, independent
  of the calling NPC, script, BSE source or radio channel.
- Music routing has precedence. Neither `SND_CHANNEL_VOICE` (also used by the
  Dark Matter weapon) nor broad `SSF_VO` (also applied to GUI sounds) alone
  classifies an effect as dialogue.

No new sound-save fields are introduced. Master gain, authored distance,
occlusion, reverb and voice priorities keep their existing roles. Mixed speech
and music in a single recording cannot be separated by this control.

`tools/tests/audio_dialogue.py` enters `game/airdefense1` or Awakening's
`game/m01_stranarus_trench1`. Generated 440 Hz speech and 880 Hz effect fixtures
overlap on independent channels. Actual OpenAL source reports show speech gains
1, 0.25, muted, then 0.6 while the effect stays at 1. The 0.6 ratio survives
pause/resume, time scale 0.5 (pitch also 0.5), `s_restart` and save/load. The
shared campaign configuration archives 0.6. English and Turkish text with
English audio fallback pass. OpenAL renders to WAV; the screenshot command
captures the Audio page through its normal semantic menu actions.

Final reports: `.tmp/audio/final3-dialogue-stock/result.json` (28 checks:
compressed fixtures, 5.1 output, 16 MiB decode and 192 MiB aggregate budgets)
and `.tmp/audio/final3-dialogue-awakening/result.json` (25 checks: PCM fixtures,
5.1, the same budgets), plus the Turkish-text/English-audio fallback run
`.tmp/audio/final3-dialogue-turkish/result.json` (23 checks, stereo). The
English Audio-page capture was visually inspected. This proves fixture isolation in running maps, not a
complete listening pass over every authored NPC/BSE/script/cinematic scene.

## Decode admission before streaming

Vorbis admission now bounds compressed input plus pending PCM in bytes, including
synchronous fallback. `s_decodeMemoryMB` defaults to 64 MiB on all platforms;
the existing 48-job cap remains. Admission joins older work before allocating
more. A reservation remains owned until join/cancellation even if its worker
has finished. Failed probes and cancellation release it. Ogg files lacking a
usable length use a fixed 16 KiB counting buffer and rewind before allocating
the final PCM, replacing the unbounded doubling helper.

`listSounds` additionally reports retained CPU sample data, queried OpenAL
buffer sizes, conservatively reserved compressed input, their aggregate and
the admission peak/wait count. At the final gameplay probes:

| Run | Transient peak | Admission limit | CPU PCM | OpenAL PCM |
| --- | ---: | ---: | ---: | ---: |
| Stock map, Turkish text | 30,087 KiB | 64 MiB | 0 KiB | 198,184 KiB |
| Awakening m01 | 47,635 KiB | 64 MiB | 0 KiB | 265,340 KiB |

Both finish with zero outstanding reservation and no budget rejection. A
deliberately lower 16 MiB test exercised backpressure but rejected three long
Awakening tracks; it is not evidence of an intact scene mix. The harness now
requires zero rejections. Header inventory finds no installed Ogg above 64 MiB
input+PCM: the largest stock pair is 40,333,330 bytes and the largest Awakening
pair 47,258,520 bytes. Both exceed 32 MiB, so a 32 MiB mobile default would be a
compatibility regression before streaming exists.

These earlier measurements excluded stb decoder metadata, non-Vorbis loading,
resident CPU/OpenAL data, driver internals and voice queues. The follow-up below
adds fixed decoder arenas and compressed streaming. Android low-memory
qualification remains open. `tools/tests/audio_decode_budget.py` executes production admission,
reservation, join and cancellation methods, including failed decodes and a
runtime budget reduction.

## Compressed streaming

Long Ogg samples now retain their metadata and 60 Hz amplitude envelope, with no
complete compressed file or decoded PCM resident. Above 512 KiB decoded size,
each active voice opens its own VFS/PK4 stream with a 64 KiB read cache, fixed
2 MiB Vorbis arena and three PCM queue buffers (4,096 frames when first
measured; now about a third of a second each, see below). The separate
`s_streamMemoryMB` limit defaults to 32 MiB, reserving 2,304 KiB per voice including
scratch, queued PCM and conservative VFS bookkeeping. Stop and purge release
decoders, file handles and queue buffers. Short-track decode jobs now include
their fixed 2 MiB arenas in `s_decodeMemoryMB` reservations as well.

`tools/tests/audio_streaming.py` generates original mono/stereo Ogg fixtures at
22.05/44.1/48/96 kHz (ffmpeg or `imageio_ffmpeg` required), then compiles the real
bounded reader and production queue transitions. Full and streamed PCM compare
exactly, including sample seeks, independent overlapping cursors, short reads,
EOF, compressed leadin/loop, mixed static/streamed transitions and a self-loop
from a restored offset. Upload failure releases the decoder. A stopped streaming
source requests recovery at the game's sound clock instead of replaying stale
PCM. `audio_stream_budget.py` executes production admission/ownership through
saturation, stop/retry, missing input, decoder failure and a reduced live budget.
`audio_payload_restore.py` also proves compressed streams never restore full PCM.

The final Windows stock and Awakening runs use `audio_dialogue.py --compressed
--decode-memory 16`, enter the same maps as the earlier dialogue tests, and pass
all 24 checks. They exercise mute, pause, time scale 0.5, restart and save/load;
actual rendered 440/880 Hz tone amplitudes exceed 0.05 in each output. The stock
save-game stall also exercises underrun recovery at a nonzero dialogue offset.

| Final run | Decode peak / limit | OpenAL sample PCM | Stream peak / limit | Reported aggregate payload bound |
| --- | ---: | ---: | ---: | ---: |
| Stock airdefense1 | 15,447 / 16,384 KiB | 118,853 KiB | 9,216 / 32,768 KiB | 128,242 KiB |
| Awakening m01 | 16,352 / 16,384 KiB | 148,274 KiB | 4,608 / 32,768 KiB | 153,055 KiB |

Both finish with zero outstanding decode reservation and no rejected streams.
The aggregate includes sample CPU/OpenAL data, envelopes, pending input/arenas
and stream reservations; it excludes driver internals and other engine objects.
Reports: `.tmp/audio/stream-stock-final/result.json` and
`.tmp/audio/stream-awakening-final/result.json`. Client SHA-256:
`01a735014944a4efb233b3b4d57a8de52eabb6d4a36a697f68a16a64b1f7fe81`.
On the final binaries, the compressed stock run
`.tmp/audio/final3-dialogue-stock/result.json` again streams both fixtures with no
rejection (decode peak 14,577 of 16,384 KiB, stream peak 9,792 of 32,768 KiB).
The reports retain runtime and harness identities. The `stream-awakening` run
used a stock map in the expansion game directory; only the final m01 run is
counted as Awakening scene coverage.

The bundled MIT/public-domain stb_vorbis receives a small read/seek/tell callback
extension, with matching canonical/external copies and normal/no-stdio/push-only
compilation checked. No extracted audio is added to Git. Streaming currently
requires usable length metadata and supports tracks up to one hour. Its initial
envelope pass is bounded but synchronous; load-time profiling, mixed-format
leadin/loop behavior, an enforced joint residency limit including WAV/RoQ and
Android/device breadth remain open under AUD-03. The decoder and queue limits
alone are not a total audio-memory guarantee.

### Queue depth across long frames, 22 October 2026

On the merged A+B build (`9255c199c`) `audio_dialogue.py --compressed` failed
4 of 4 runs with about 25 underruns each, and `audio_memory_runtime.py` failed
`retry_and_restarts_play_both`. Earlier passing reports on the same audio code
came from before 23:51 on 21 October. From then on, the laptop sat in Modern
Standby with the display off (Kernel-Power event 506, no 507 afterwards), and
every failing run fell in that period. With `com_speeds 1` the hidden GL window
ran at p50 139 ms with 49 frames over 200 ms and a 2.5 s maximum; the time was
outside the game, front end and back end, in presentation. With
`r_swapInterval 0` the median returned to 17 ms, but periodic ~450 ms present
stalls remained. Vulkan, which renders hidden windows offscreen and never
presents (90ed5029), paced at p50 17 ms with no stalls apart from the first
frame, `s_restart` and save/load, and the same dialogue run passed. CPU load
stayed at 8-30%, with no build processes and over 36 GB of free commit. The
~500 ms CPU p99 in the same day's GL stock baseline has the same cause.

The trigger was environmental, but the failures exposed a real limit. Every
bounded queue (streamed Ogg, CPU-resident PCM without an uploaded buffer,
centre-routed mono) held three 4,096-frame buffers and was refilled once per
main-thread frame. That is 512 ms at 24 kHz and 279 ms at 44.1 kHz. Each
underrun followed a frame of about 450 ms or longer, so a single loading hitch
of that size cut out music or dialogue until the channel restarted it at its
clock. The 64 MiB fallback WAV in `audio_memory_runtime.py` ran dry the same way
before its probe.

Queue buffers are now sized by duration within the bytes the reservations
already count (`src/sound/SoundQueue.h`). A buffer holds about a third of a
second, up to one 4,096-frame 5.1 block (48 KiB). Mono therefore keeps about
1.0 s queued at rates up to 48 kHz, stereo 1.0 s at up to 24 kHz and at least
768 ms at 44.1/48 kHz. Centre-routed mono uploads 5.1 frames, so eight routed
voices at a time take deep slots of up to 16,384 frames per buffer for the
same depth. Further routed voices keep 4,096 frames. The fixed 20 MiB
reservation now also asserts the slots' extra bytes and their routing scratch
(about 19.1 MiB in total). Stream reservations, aggregate admission and the
reported memory numbers are unchanged. The memory runtime still reports
214,246 KiB reserved through both restarts. `audio_streaming.py` now proves the
one-second depth, the per-buffer byte bounds, continuity across multi-read
buffers, and that deep slots are bounded, reused and returned. Against the
previous voice code it fails.

The post-fix runs were made in the same display-off state, with machine load
recorded for each run (`.tmp/mrt/*.jsonl` in that worktree):

| Suite | Before | After |
| --- | --- | --- |
| `audio_dialogue.py --compressed --speakers 6 --decode-memory 16 --audio-memory 192` | 0/2 (25 and 30 underruns) | 3/3 |
| `audio_dialogue.py --compressed` (2 speakers) | 0/4 | 3/3 |
| `audio_memory_runtime.py` | 0/1 | 3/3 |

A frame-timed run of the fixed build had the same stall profile as the failing
one (p50 172 ms, 15 frames over 300 ms, two over 1 s) and logged no underruns,
against 30 before. A hitch longer than the queue still recovers at the channel's
sound clock, as before. Refilling from a worker thread was not attempted: voice
queue state has no locking and is touched only on the main thread.
On the final build (branch tip `ec89ff31c`, client SHA-256 recorded in each
report) the native Meson suite passed 276 of 276, and so did the audio,
sound-settings, recovery, payload-restore, portability and validation-hardening
static tests.

## Mod room rolloff

The voice now sets `AL_REFERENCE_DISTANCE` from the authored minimum distance,
in the same map units as the source. This operates independently of the optional
source-radius extension. A zero/invalid minimum has a small positive reference;
the base setter already sanitizes nonfinite/negative input. The dry path still
uses engine attenuation and `AL_ROLLOFF_FACTOR 0`.

`tools/tests/audio_mod_reverb.py` renders deterministic noise with the staged
OpenAL provider through `ALC_SOFT_loopback`, measuring PCM rather than merely
checking API calls. With minimum 100 and distance 200, room rolloff 1 gives wet
RMS 0.0068158555, exactly half the near-reference RMS 0.0136317110. The old
one-unit reference gives 0.0000681586. Scaling distance and reference together
leaves the result unchanged. Stock room rolloff 0 and dry RMS are unchanged.
Final report: `.tmp/audio/final-mod-reverb/result.json` (6/6).

The [EFX guide](https://openal-soft.org/misc-downloads/EffectsExtensionGuide.pdf)
and the pinned provider's `alc/alu.cpp` define the reference-distance behavior.
The local retail reconstruction also sets the source minimum, but is a
structural reference with known reconstruction errors, not standalone retail
parity evidence. No external implementation was copied. Global distance
defaults, 5.1 centre placement and full retail audible-distance parity were not
changed or qualified by this measurement.

## Aggregate payload admission

`s_audioMemoryMB` now defaults to 256 MiB (range 32–2048). One byte ledger
admits sample CPU data, compressed input, pending decoder arenas, amplitude
envelopes, OpenAL sample uploads and stream reservations together. A fixed
20 MiB conservative allowance covers all 96 hardware voices' three 48 KiB
queue buffers (one 4,096-frame 5.1 block each), the deep centre-routed slots,
voice-chat rings and scratch. Stream reservations also include their
queues; this intentionally overcounts them. This is a managed-payload ceiling,
not a provider-process/RSS limit: driver internals, resource metadata and general
filesystem caches are outside its claim.

Admission joins pending work and may reclaim inactive, unreferenced old-map
samples. Current-map, never-purge and live-channel references remain. Worker
completion can release compressed input; decoder arenas stay reserved until
joined or cancelled. WAV/ADPCM allocations and temporary decode overlap count
before allocation. RoQ now scans chunk headers, then decodes audio directly into
one admitted PCM buffer through 4 KiB input scratch, skipping video data. It no
longer loads the complete video or grows a second PCM container. Envelope
allocations and failed uploads release reservations on all tested exits.

A failed static upload retains CPU PCM for three bounded fallback buffers;
each holds at most one 4,096-frame 5.1 block of bytes (about a third of a second
of mono or stereo PCM since 22 October) for ordinary PCM as well as centre
routing. Failed sample loads stay retryable and never become cached replacement
beeps. Exhaustion can omit new audio when it cannot fit; it does not evict active
sounds. Reducing the budget during playback blocks new admissions without
revoking already admitted data, so existing usage and historical peak can
exceed the newly selected limit until data is released. Restart/map changes
release owned allocations; `listSounds` reports current/peak reservation and
refusal count. Its decoded-size totals now use 64-bit arithmetic.

`audio_memory.py` compiles the production admission/allocator, envelope ownership,
RoQ loader and ADPCM decoder. It checks arithmetic overflow, exact saturation,
concurrent worker release, allocator failure, budget reduction, mono/stereo PCM,
chunk boundaries, truncated/mixed data, failed admission and retry. Existing
production decode-join/cancel, stream lifetime and PCM-queue tests pass, now
including aggregate stream refusal and resident fallback queue continuity.

Loaded-map results at a 192 MiB aggregate budget and a 16 MiB decode budget:

| Scene | Peak managed reservation | Refusals | Scope |
| --- | ---: | ---: | --- |
| Stock `game/airdefense1` | 149,475 KiB | 0 | Compressed dialogue/effect, 5.1, mute, pause, half speed, restart, save/load |
| Awakening `game/m01_stranarus_trench1` | 180,190 KiB | 0 | PCM dialogue/effect, 5.1 and the same lifecycle checks |

Reports: `.tmp/audio/final3-dialogue-stock/result.json` and
`.tmp/audio/final3-dialogue-awakening/result.json` (harness SHA-256
`8fc4b57342564c648d4626e86b4c38326a07f3cdba515c5f0c2fe5167a442b40`); each
identifies its exact engine, modules, staged content and harness. A preceding stock run was interrupted by a
natural campaign radio line and failed its fixture gain checks. The mixer harness
now uses a real saved fixture entity with its own radio channel; the campaign
continues running and cannot replace the fixture on the player's emitter.

`audio_memory_runtime.py` then loads a real map, reduces the budget to 32 MiB and
requests an original 64 MiB WAV. Existing audio keeps playing; the refused sample
remains unloaded. Restoring 256 MiB permits its CPU payload but refuses the extra
full OpenAL copy. Actual rendered output contains both fixture tones through the
bounded fallback. Current reservation is 214,246 KiB before and after two sound
restarts, with no replacement beep or reservation growth. The final report
`.tmp/audio/final3-memory-pressure/result.json` passes all 13 checks, including
that a budget refusal is no longer reported as corrupt ADPCM/PCM media.

These tests do not establish whole-process memory bounds, Android OS low-memory
notification handling, all-map residency, loading-time budgets or physical-device
qualification. AUD-03 remains open for those gates and lengthless streaming.

## Centre-channel placement

`SoundSurround.h` routes eligible mono samples through bounded 5.1 queue
buffers (4,096 frames, or about a third of a second for the eight voices holding
a deep slot since 22 October) only when the provider reports a centre-capable output and supports
multichannel/direct-channel playback. Explicit `SSF_CENTER` uses fraction 1;
global/radio VO uses `s_centerFractionVO` (default 0.75). Centre amplitude is
the fraction; the remaining power is shared equally by FL/FR/SL/SR. LFE stays
silent. Positional NPC speech retains the original mono directional path.
Stereo and active HRTF also retain that path. Streaming reservations now include
the larger 5.1 conversion scratch and queues; the earlier streaming reports
above retain their original binary and reservation measurements.

`tools/tests/audio_center.py` passes 26 checks, including every signed 16-bit
sample at four fractions and real OpenAL loopback PCM on 5.1, 6.1, 7.1, quad,
stereo and HRTF outputs. Its extension gating matches the engine, including
`AL_SOFT_direct_channels_remix`. At fraction 1 on 5.1, centre RMS is 0.08838810
and every other channel is zero. At 0.75, centre RMS is 0.06629362, four
surrounding channels are 0.02923290 and LFE is zero. On 6.1 and 7.1 the centre
stays exclusive for explicit sounds, VO keeps the configured fraction with unit
power and LFE stays silent. Quad (no centre speaker) keeps the original path,
and stereo and active-HRTF comparisons have identical PCM hashes. The production queue
tests cover centre-converted static and streamed leadin/loop combinations,
partial static buffers and underrun recovery.

Loopback report: `.tmp/audio/final-center-layouts/result.json` (26/26). The
gameplay reports `.tmp/audio/final3-dialogue-stock/result.json` (28 checks) and
`.tmp/audio/final3-dialogue-awakening/result.json` (25 checks) pass with six-channel
OpenAL wave output and a 16 MiB decode budget. Both measure stronger 440 Hz
dialogue in FC than the surrounding channels, with an independent 880 Hz effect,
and cover gain/mute, pause, slow motion, restart and save/restore. The harness
compares channels within the windows where the speech fixture is loud: the
median centre-to-surround ratio is 2.27 in Awakening's quiet scene (the
theoretical value at fraction 0.75) and 1.72 in airdefense1, whose own ambience
adds 440 Hz energy to a surround channel. An earlier whole-recording peak
comparison failed a correct mix on a fast run for that reason.

These are rendered-PCM checks, not physical-speaker listening tests. Live output
layout changes, physical devices and explicitly centred positional mod sounds'
wet-send behavior remain unqualified.

## Multiplayer voice

The former disabled voice path is implemented. Engine/game API **53** appends
dedicated voice callbacks; matching SP/MP modules are required. The existing
gameplay protocol stays at 2.41, with explicit `si_voiceProtocol` and
`ui_voiceProtocol` capability opt-in. Unsupported peers do not receive the new
message type. The old reliable VOICEDATA path is discarded.

- **Capture and consent:** SDL's default recording endpoint, native signed
  16-bit mono at 8 kHz. `s_voiceChatCapture` starts off separately from archived
  Send Voice. Only PTT or an explicit local test opens input. Releasing PTT,
  disabling consent, losing the active session, restart and shutdown destroy
  the stream and clear queued capture. One-second retries apply to failures,
  not quick PTT presses; a stream stalled for two seconds is reopened. SDL
  callback draining and main-thread access share the stream lock. Each queue
  holds four 20 ms frames; overflow replaces old audio, never grows a container.
- **Codec:** first-party mu-law companding, 160 samples per independently
  decodable frame, 64 kbit/s speech payload. A version/sequence/capture-time
  header makes each frame 169 bytes. No codec history crosses packet loss;
  gaps remain gaps rather than retransmitted or time-stretched speech.
- **Admission:** exact lengths/version, increasing wrapping sequence numbers,
  a three-frame burst and 50-frame/s sustained limit. Capture older than 120 ms
  is discarded. The server and receiver reject frames more than 120 ms later
  than their learned clock offset; that baseline survives PTT gaps. This is
  an **added-delay bound**, not proof of absolute cross-machine one-way latency.
  The learned offset tracks sender clock drift: the baseline may slew towards a
  later offset by at most 2 ms per second of accepted active traffic, so
  independent monotonic clocks cannot silence a healthy talker after hours,
  while a backlog delayed by a PTT gap is still rejected and rejected frames
  never train the clock. Initial skew and real multi-hour sessions still need
  qualification outside simulation.
- **Transport:** authenticated unreliable messages carry no routing authority
  from the sender. Exact server recipients retain team/arena/spectator and
  managed-match policy, receive preference and mute. No following-spectator
  fan-out, demo or repeater forwarding occurs. A fixed mailbox keeps at most
  one current frame per three talkers per recipient. It is flushed after
  snapshots, expires entries after 100 ms, respects a maximum 20 ms rate burst
  and refuses existing fragments or a reliable backlog that would fragment it.
  Failed sends are discarded; no voice retry queue can block later snapshots.
- **Playback:** three talkers, four OpenAL buffers each, real-time pitch 1 and
  master × receive-volume gain. Speech is independent of dialogue/music gain.
  Generation changes flush the old occupant. Recipient mute/receive changes
  stop already queued speech; connection cleanup clears mute/moderation state.
- **Controls:** both retained Voice and Classic Voice Config expose consent,
  Send/Receive, levels, echo and local-only testing. Localized status reports
  off, ready, recording, input unavailable or session unavailable. Leaving the
  test tab/menu stops testing; revoking access also clears its activation.
  macOS bundles declare microphone usage, and Android declares optional
  microphone hardware plus its recording permission. These declarations are
  implementation coverage, not physical OS-permission qualification.

`tools/tests/voice_chat_runtime.py` launches real hidden clients and either a
listen host or dedicated server on `mp/q4dm1`. It sends a synthetic 400 Hz tone
through the actual codec, net channel, policy and OpenAL playback without
opening microphones. A bounded loopback UDP proxy introduces loss, reorder and
250 ms delay. Both final reports pass all 20 checks:

- `.tmp/audio/final3-voice-listen/result.json`
- `.tmp/audio/final3-voice-dedicated/result.json`

Checks cover both directions, recipient mute/unmute, receive-off, gain 0.125
at master 0.5/receive 0.25, pitch 1 during time scale 0.5, server moderation,
sound restart, packet loss/reorder, late rejection, bandwidth recovery,
reconnect/slot reuse, no spectator leakage, bounded playback and clean exits.
At 2,000 B/s, current voice is dropped while the dedicated server continues
15–25 snapshots/s in steady measurement intervals. Rendered 400 Hz amplitudes
in the dedicated WAVs reach 0.100 (host) and 0.039 (peer), above the harness's
0.02 floor. The proxy reports 74 dropped packets and at most 51 pending
datagrams in its 256-entry bound. Both reports name the final client, dedicated
server and MP module listed above, and harness SHA-256
`ed55dd97f254c26d6f0c7520672e1d8743dba42a400e74e05cca5e55ad9ac950`.

The harness drives each hidden client through a console script it rewrites
between phases. The final listen and dedicated runs passed at the first
attempt, but on the previous build, on this busy shared machine, nine attempts
were needed. Of those, two lost a client when the engine's `exec` of a script failed while Windows was
replacing it (`couldn't exec voice-wait-*.cfg`); an earlier development run
hit the same race once. Two began the reconnect phase during the restarted
match's map restart, which the harness now prevents by waiting for the server
and both talking clients to report a running match after their own restart.
One exceeded the default 360-second budget while a client needed 25 s to load
the map (the final runs pass `--timeout 900`), and one starved the clients of
CPU until too few synthetic frames were captured. The harness also still writes
its report when a child cannot be stopped. These are harness and host-load
limitations, not voice defects; rerun a failed attempt before reading it as a
product failure.

`tools/ui/capture_voice_settings.py` then exercises the real settings adapter,
SDL callbacks and local OpenAL playback using **SDL's explicitly selected
dummy driver**, which supplies silence and never opens a physical microphone.
The vendored SDL Meson build now includes that opt-in driver; SDL never selects
it as a physical-device fallback. The first test captures 59 frames and plays
58, stops on tab exit, then verifies consent revocation. No VOICE_SEND message is
emitted despite echo being enabled. The four English engine-render-target
screenshots were inspected: off, ready, active test and Classic Voice Config.
Reports on the final binaries: `.tmp/audio/final3-voice-ui-english/result.json`
and `.tmp/audio/final3-voice-ui-turkish/result.json` each pass all eleven checks.
The English and Turkish captures were inspected again. In English the retained
"Local microphone test" label wraps onto two lines inside its row, and the
Classic page draws its two new rows without the row plate the older rows use;
both are cosmetic and remain UI-01 polish.

Native `VoicePacketTest` exhaustively tests mu-law error bounds, achieves
37.74 dB fixture SNR and checks malformed packets, wrapping sequence/clock,
idle-delayed backlog, a simulated 24-hour ±1000 ppm clock drift with jitter,
loss and PTT gaps, a rejected backlog that must not train the clock,
burst/flood limits, capture overflow, mailbox freshness and whole-envelope
rejection. `voice_capture_lifecycle.py` compiles production
capture code against fault-injected SDL interfaces; `voice_transport.py`
compiles the production net-channel admission gate. Native retained-settings
tests cover consent, disabled testing, actual peak binding and test shutdown
on tab changes. Focused API, networking, team-policy, macOS packaging and
settings regression checks pass.

These tests qualify Windows process-to-process playback and controlled capture
lifecycle. Physical microphones, default-device migration, permissions/hotplug
on target OSes, real multi-hour sessions (drift is covered only in simulation)
and WAN intelligibility remain AUD-05 qualification work. Narrowband quality
and silence for lost frames are explicit tradeoffs, not an Opus-quality or
voice-processing claim.

## Installed transcript inventory

`tools/tests/audio_asset_inventory.py` reads installed PK4/loose declarations,
with later names overriding earlier ones. It records asset names, hashes,
localization keys and coverage counts, never extracted transcripts. `--sizes`
adds header-based allocation estimates, not a decoder validation.

| Content | Speech shader candidates | Same-name lip-sync/text mappings | Unmapped | Unmapped with a description |
| --- | ---: | ---: | ---: | ---: |
| Retail | 3,672 | 2,268 | 1,404 | 1,298 |
| Awakening | 1,584 | 1,512 | 72 | 8 |

Reports: `.tmp/audio/stock-inventory.json` and
`.tmp/audio/awakening-inventory.json`. Each game directory is inventoried
separately; the expansion report is not a merged runtime filesystem inventory.
Some missing candidates are multiplayer announcer sounds. A description is not
automatically a subtitle; a key existing in any language table does not establish
every locale's coverage. These candidates are broader than the runtime's verified
single-variant/full-path mapping policy below; they are not coverage claims.

## Dialogue subtitles

The shared SP/MP overlay derives cues from actual sound channels and their
integrated sample clock. It uses `lipSync.text` only: a same-name shader mapping
is valid for its single selected entry; otherwise the full sample path without
its extension supplies the mapping. Descriptions, ambiguous random variants,
basename guesses and unresolved localization keys are excluded. Text remains in
installed assets; no extracted transcript or invented alias ships in this repo.
The normal language dictionary supplies English fallback when a selected locale
has no matching text. Quiet exact-key lookup avoids per-frame missing-key spam.

At most the two newest eligible utterances display. Authored volume, fades,
private/anti-private audience and distance still constrain cues; user master and
dialogue mute and hardware voice allocation do not remove captions. The selected
leadin/loop sample owns its text. Stops, replacement, completion and missing text
clear the cue. Speaker labels require a matching live entity/emitter and its
`npc_name`, with a localized radio label where applicable.

The Lowpixel overlay defaults to 17 dp, white text, green speaker labels and a
0.60 black backing. Long text wraps using actual font advances and pages in
proportion to utterance duration; the data does not establish word-aligned times.
It draws through the common HUD path in either UI mode, with persistent localized
size/background/speaker controls in Settings > Audio. Two simultaneous utterances
get one line each. The four controls have labels in all twelve menu languages.

`audio_subtitles.py` executes production cue selection and bounded pagination,
including missing/ambiguous mappings, loops, UTF-8, privacy, distance and overlap.
The `openq4-ui-subtitles` native runtime test validates the document and one/two
line geometry at 1280×720, 1024×768, 3440×1440 and 720×1280. Both pass.

`audio_subtitles_runtime.py` uses original tone/text fixtures plus an existing
installed dialogue shader in actual loaded campaign maps. No microphone or host
input is used. The following reports pass all 16 checks, including selected-text
English fallback, mute, pause, half speed, restart, overlap, interruption,
save/restore, installed transcript selection, archived controls and real Audio
page scrolling. Reports retain executable, module, content and harness hashes.

- `.tmp/audio/final3-subtitles-wide/result.json`: stock, English, 1280×720.
- `.tmp/audio/final3-subtitles-portrait/result.json`: Awakening
  `game/m01_stranarus_trench1`, Turkish, 720×1280.
- `.tmp/audio/final3-subtitles-classic/result.json`: stock, Classic UI, 1024×768.

All three use the final client and harness SHA-256
`fe9a2070f85d66a6339cfb72fb2f8f094cfc945e26c33d8cca5cc40f542176ef`.

Engine-render-target captures were inspected for captions and the new controls.
The final portrait caption is inside the cinematic picture, but Awakening's
existing narrow-layout title card can overlap enlarged captions. The scene also
shows letterbox bands with world pixels outside them. These are retained UI-02/
UI-04 qualification gaps, not a full portrait presentation pass. Arbitrary custom
cinematic HUDs, complete authored scene/locale coverage and physical headset
stereo placement remain unqualified. Missing transcripts stay an explicit AUD-07
gap; this does not provide effect captions or speech recognition for voice chat.

## Long-session voice evidence, 22 October 2026

The interrupted Claude session left a completed dedicated-server/two-client
run in worktree `1388`, `.tmp/soak/soak-2h-final/`. Its `result.json` reports
7,168.9 seconds (1:59:29), not the requested 7,200 seconds. The original harness
accepted a duration one interval short and included shutdown time. Preserve
that report unchanged: its `duration_met: true` is not a strict two-hour pass.
`voice_chat_soak.py` now takes a sample at or beyond the requested endpoint,
stops its duration clock before shutdown, and requires the full live duration.
The user cancelled the repeat long run; no replacement two-hour run is claimed.

All 120 measured intervals pass. Synthetic 400 Hz PCM traverses the real codec,
net channel, server policy and OpenAL wave backend in `mp/q4dm1`; microphone
opens and host input are zero. The server admits 19,390 frames, rejects 1,261
and refuses zero sends. Host/peer playback totals are 8,261/8,983 frames.
Delayed-backlog probes reject 1,168 frames at the peer. Maximum admitted added
delay is 120 ms and the maximum observed playback queue is three frames.
Admission baseline shifts span -48 to +6 ms. A reconnect after interval 60
changes the peer generation from 356 to 359, clears mute/moderation and resumes
admission in 16.8 seconds. No console step runs twice.

Private-memory growth from the warmed first quarter to the final quarter is
-18.2 MiB for the server, -34.3 MiB for the host and +4.1 MiB for the peer
(peer comparison excludes reconnect warmup). The recorded rendered tone remains
present late in the session. Machine CPU load ranges from 27.8% to 100%; free
commit falls from an initial 14.62 GiB to a minimum 1.32 GiB. This is useful
loaded-host stability evidence, not an uncontended performance measurement.
All processes share one machine clock; the native simulated 24-hour drift test
remains the independent-clock drift evidence. Physical capture, WAN peers,
endpoint changes and target-OS breadth remain unqualified.

The saved run binds these SHA-256 identities:

| Artifact | SHA-256 |
| --- | --- |
| Client | `6c3a4dfeaaf5e8e98473d739e1eddc7598de724b2e828d1184bce6fadca724ff` |
| Dedicated server | `14744541d29cc00b6584c89b3fd5080a693b801f3e47f9a34465a6d8d8f4e0d8` |
| MP module | `ea2079fa810e93602757018111c8cfaee012f4447d49e4f43245a21f42e19112` |
| Original harness | `d665d5b8cf3071ce17eba89b1a2f0ea4ef97edda11a7245a4b530a2cf6b89e6f` |

The recovered implementation is in `bf6b50800` (per-sender admission telemetry)
and `c9ca2e315` (session and mixed-release harnesses). Do not transfer the old
runtime result to a newly built executable solely because these commits match.

Worktree `2993` verifies the corrected endpoint with a new 220-second request:
`.tmp/outstanding/voice-short/result.json` records 232.4 seconds, twelve passing
intervals and all thirteen checks passing, including reconnect, delayed backlog,
exactly-once steps and rendered tone. The server admits 2,454 frames and rejects
132; clients play 973/1,043 frames. Maximum admitted added delay is 101 ms and
the queue peaks at four frames. This short run qualifies the harness correction
and current staged runtime, not another long session. The rebuilt native suite
passes 276/276, and transport, capture lifecycle and capability-gating checks pass.

## Mixed-release voice check, 22 October 2026

The saved `.tmp/soak/mixed2/result.json` in worktree `1388` covers published
0.13.0 against the voice-enabled candidate, in both server/client directions,
with `si_pure` both 1 and 0. All fourteen harness checks pass. Pure connections
are explicitly refused for missing packages; non-pure connections are refused
for declaration-checksum mismatch. No unknown unreliable voice messages appear.

No mixed-release peer joins and the talker counters stay at zero. These results
establish explicit refusal for this release pair, not voice interoperability or
runtime capability negotiation with an admitted old peer. The existing
`ui_voiceProtocol`/`si_voiceProtocol` gates and appended message identities are
covered separately by `voice_protocol_gating_contract.py`; production transport
and capture-lifecycle tests pass. The player guide recommends matching releases
and content without asserting that every different release pair is incompatible.

## Other verification and limitations

- `sound_settings.py --no-mutations`: 35,807 checks pass.
- `sound_recovery.py --no-mutations`: 42,348 cumulative checks pass. These are
  counted API tests, not physical endpoint-loss tests.
- Dialogue classification, settings-menu coverage, audio payload restore,
  screen-shake and retail reverb contract tests pass; client and dedicated
  builds and staging pass.
- The full native Meson suite passes on the final build (187 of 187 tests). Its
  imported game regressions caught a voice reset placed above a pinned comment
  in `ClearMap`, fixed before the final runs.
- The audio, voice and subtitle static/native-compile tests, the API pin
  contracts touched by API 53, `build_retained_screens.py --check` and
  `build_subtitles.py --check` pass on Windows.
- The validation script's full Python sweep (`openq4_validate.py push
  --skip-build`, 357 checks) found three test-side gaps, now fixed: unwired
  new tests, a missing subtitle-reset stub in the view-effects harness, and
  the retained gate rejecting the Voice page's deliberate test-off write. The
  three checks and the 84 workflow/contract tests that read the CI files pass
  afterwards. The product-requirements structural audit against
  `cbe967f2b` passes.
- Linux: every changed engine sound, network, menu and language source and the
  touched SP/MP game sources pass `-fsyntax-only` with GCC 13 and Clang 18 in
  WSL Ubuntu, and the production-extraction harnesses (decode, aggregate
  memory, stream budget, payload restore, subtitles, voice transport and
  capture lifecycle) compile with `-Werror` and pass under both. GCC exposed one
  misleading-indentation error in the aggregate-memory harness, now fixed.
  `audio_streaming.py` was not run there (no ffmpeg in that environment), and
  no full Linux, macOS or Android build was made.
- `sound_settings.py` now resolves its own path before recording source hashes,
  fixing a Windows junction/real-path mismatch exposed by this worktree.
- The supplied Awakening scene still reports existing duplicate declarations,
  entities in solid, a missing `engine_righ` effect joint and an unknown
  `walker_trench_unit1_seq_2` script function. These content/gameplay findings
  are outside the current audio repairs and are not counted as clean startup.

Full subtitle coverage, whole-process/mobile memory qualification, physical device
lifecycle and target-OS breadth remain open. Voice and compressed streaming are qualified only
within the automated scope recorded above.
