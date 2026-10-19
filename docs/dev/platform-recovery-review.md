# XR and Android recovery review

18 October 2026, current source baseline `8c1a49ca7a033e163e271ef3787a4a9ba73f7479`.
This records the stage-one scope/recovery portion of roadmap VR-01/VR-06 and
AND-01, followed by current stage-two evidence. Archived commits below
exist in this repository; none is replayed wholesale or used as current hardware
evidence. The current in-tree engine/game/renderer contracts take precedence.

## XR selection and dependency review

| Archived change | Reviewed implementation | Selected boundary for later integration |
| --- | --- | --- |
| `0d83c14c4` Vulkan | `XR_KHR_vulkan_enable2`, runtime-created instance/device services, queue identity, eye target format/layout and renderer image release | Recover device ownership and stereo output together against the current module ABI. Historical render API 24 is not a version to restore blindly. Require GL/Vulkan SP, MP, menus, restart and VR-off parity |
| `f98a1d247` desktop-independent submission | `vk_GuiExecutor.cpp` adds a windowless frame, bypasses desktop acquire/present and preserves XR output targets | Headset submission must continue during minimized/out-of-date/absent desktop swapchain; no accidental desktop image/semaphore use |
| `4b5e0c4f9` EGL/Wayland | `gl_VRPresentation.cpp` queries SDL EGL display/context/config and proc lookup; extends binding kinds | Qualify native Wayland EGL independently from GLX fallback; do not introduce a shared-code platform dependency where SDL owns the binding |
| `65aa9bd88` Quest | Android activity/manifest, loader initialization, GLES stereo and optional test runtime; generated headset manifest and payload flags | Optional standalone flavor only after lifecycle safety and variant-specific APK verification. Debug XR runtime must be impossible in published APKs |
| `9dcd121da` hand GUI pointing | `idPlayer::UpdateFocus` starts the focus trace at `GetVRAimOrigin`; debug coordinates aid alignment | Reconcile SP and MP aim/focus with current retained/world GUI ownership; never double-apply physical motion or silently alter authoritative weapon traces |

The active Vulkan VR presentation is still a stub; active PC OpenXR is GL.
Archived happy-path captures do not close current VR-02 or VR-06.

The stage-one `OpenXRSystem.cpp` had the source-derived cycle `Check(SESSION_LOST)` →
`DestroySession()` → `ReleaseImages()` → `Check(xrReleaseSwapchainImage)` before
`frameOpen` and `chain.acquired` are cleared. This confirms the re-entry risk in
source; the reproduction and repair are recorded below. Instance/runtime loss also entered
destruction. VR-06 required taking ownership out of circulation before fallible cleanup,
make destruction idempotent, and stop the caller after session invalidation.
Its fault matrix must cover session/instance loss, each partial acquisition,
wait/release failure, invalid image count/index, create/resize failure and lost
tracking. Require bounded calls, balanced ownership and no stale handles, plus
desktop recovery. Existing call-order tests do not satisfy those conditions.

HF-02 separately replaces millisecond smooth-turn deltas with monotonic host
ticks. XR predicted display time remains the runtime's pose/submission domain;
the [clock contract](presentation-clock.md) does not authorize converting one
clock to the other or claiming lifecycle repair.

## OpenGL XR lifecycle closure, 18 October 2026

VR-06 is complete for the active desktop OpenGL implementation in
`284af3f9`. `Check` records
session/instance retirement without destroying the caller's temporary resources;
frame boundaries consume that request once. A failed frame call stops subsequent
pose, action, image and submission work. Teardown invalidates published frame and
input state, releases owned held keys and pointer state once, and abandons pending
frames/images through session destruction. It never retries a failed release or
releases an image whose wait timed out. This follows the
[OpenXR image ownership contract](https://registry.khronos.org/OpenXR/specs/1.0-khr/html/xrspec.html)
and [session destruction rules](https://registry.khronos.org/OpenXR/specs/1.0/man/html/xrDestroySession.html).

Image counts are bounded before allocation, filled counts must match capacity,
and unsigned image indices are checked before access. Failed screen replacement
preserves its old swapchain unless the session itself was lost. Session failures
return to desktop rendering and retry after three seconds; instance/runtime loss
stays on desktop until `vr_restart`. Screenshot draws whose renderer declines
stereo now draw the world in both SP and MP instead of capturing only the HUD.

`tools/tests/openxr_lifecycle.py` compiles the actual production ownership methods
against a hostile handle/image implementation. All 19 cases pass on Windows and
Linux, including 1,000 acquisition cycles, each of three partial acquisition
positions under four failure results, wait/release failures, malformed counts and
indices, failed create/resize, idempotent teardown and held input retirement.
Original recursive teardown, timeout-as-success and retained pointer/movement
failures remain in `.tmp/stage-two/xr-{teardown,timeout,input-teardown}-repro.log`.
The old engine also fails the actual-runtime timeout control in
`.tmp/s2xr-old-timeout/report.json` (SHA-256
`18a6fa188d3cae8a6138a9da74cefa7d4ee21363ba0c1ed50f49640dd6497a30`).
That negative control intentionally used the pre-XR-repair engine, identified by
its report's executable hash; its source hashes describe the newer fixture tree.

The final staged package passes 28 hidden-window gameplay runs using the
process-local test runtime: SP Storage 1 with its documented pod diagnostic and
MP Q4DM1 listen-server warmup. The matrix covers acquire/wait/release, frame
wait/begin/end, view/space/action calls, partial session creation, malformed image
enumeration, loss-pending and invalid tracking. It checks bounded recovery,
balanced session/instance ownership, no stale handles or calls after loss, desktop
fallback and manual restart. All controller actions are inactive; physical input
is disabled. Engine `screenshot` captures include the desktop scene, both eye
render targets and continued stereo after a screenshot. Final SP timeout and MP
acquisition-loss captures were visually inspected. This is simulated-runtime
evidence, without physical input, headset or comfort qualification.

The exact 28 reports and source/binary hashes are bound by
`.tmp/stage-two/xr-final-evidence.json` (SHA-256
`da1e581e88550a8ed0c517cafd750af65fd5facf8ba873f83f2f1bd6c11cfc83`);
the 27-case batch is `.tmp/stage-two/xr-final-matrix.json` and the separate wait
timeout is `.tmp/s2xr-final-wait/`. Tested engine SHA-256:
`f66cfcae8c48801d37c78eb30526a8e87a9a9100befa36e37c0894b3d5d58afb`;
SP module `a70276783ab66977b1c398a0b5c92a3a4869914a1b4142478331f606e5415225`;
MP module `999a8dedb3b17bcd449c17f78ea984a4c6c377826e25d639543bc6d4741e7895`;
test runtime `1aff033fd54019a246b21a143a4c5f8f311c038b3af42c0e9b7183ba4e24c1b3`.
The full Windows native suite passes 207/207
(`.tmp/stage-two/xr-final-native-suite.log`, SHA-256
`f5fed293932114ec59d2d057e84c12a88cc7aedb6782f44d8af7e028cc44449e`), the XR
source contract passes, and the complete XR source compiles with the Linux client
flags in a GCC 13 syntax check. Earlier fixture build errors and an input-driver
source-drift rejection are retained; the stable-source full suite passes.

VR-01 must carry these guarantees into any later Vulkan/EGL/Quest integration;
none is promoted by this GL result. VR-02 still owns real headset/controller,
focus, comfort and pacing evidence. The Linux syntax/native checks do not establish
Linux GL runtime or headset support. No frame-time or audible-device claim is made.

## Android selection and package matrix

| Variant | Selected ABI/API/render scope | Distribution and prerequisite |
| --- | --- | --- |
| Phone/tablet production | arm64-v8a, minimum API 24, target/compile SDK 35, GLES3 | Existing signed experimental package; preserve certificate identity, matching SDL/native version, 16 KiB ELF/package alignment, notices and exact verifier allowlist |
| Emulator diagnostic | x86_64, API 24 floor plus current emulator image, GLES3 | Debug-only recovery candidate; separate module suffix/ELF metadata/allowlist, no release publication until separately selected and qualified |
| Quest | arm64-v8a, GLES3/OpenXR, explicit headset manifest | Optional experimental flavor; API floor/device claims need Quest-specific verification. Depends on VR-01/VR-06 and flavor-aware stage/APK checks; no debug runtime in distributable artifacts |

Current Meson/Gradle and `verify_android_apk.py` admit the ARM64 package only.
The matrix selects the scope for integration; it does not make the two candidate
variants implemented or supported. No NDK, SDL or API bump is bundled into recovery.

| Archived change | Recovery decision and current conflict |
| --- | --- |
| `486ecf735` touch gameplay | Recover touch-owner state/controls and executable input contracts; merge with current retained UI ownership and editable layout policy, never enable duplicate SDL/usercmd consumers |
| `3ce244cda` diagnostics/lifecycle | Recover accessible logs and lifecycle reset boundaries with localized strings; qualify pause/resume, rotation, process death and input cancellation against current SDLActivity |
| `5c8693456`, `91fc0bad4` background audio/input and SP resume | Integrated with paired OpenAL pause/resume functions, persistent fallback mute and session-owned resume before audio/gameplay. Native recovery checks pass; physical Android qualification remains open |
| `819846f5d` background tic sleep | Integrated with an atomic lifecycle query, 100 ms background waits and a ten-current-tic Android catch-up budget at every timescale. Production-method clock/wake/shutdown tests pass; physical suspension and resumed network sessions remain unqualified |
| `20766e8d1` cutouts | Recover insets/orientation behavior through the current safe-area/density model, including portrait and controller/touch ownership |
| `ba6d3af2e`, `c5845ca2d`, `2f1d2d681` launcher/preflight | Recover localized missing-data flow; archived `RetailData.isPresent` tests only for a regular `pak001.pk4`, not complete integrity. Preserve usable installed data on interrupted extraction; AND-03 owns full validation and recovery |
| `023f0eeee`, `1484195c4` emulator | Recover ABI metadata, module names and ELF checks together; archived artifact-verifier changes alone miss the current exact APK allowlist. Keep diagnostic payloads out of production |

The stage-one `OpenQ4Activity` trusted `.ready` after extraction. The repair below
addresses that part of AND-03. Signed release verification and dependency
licensing added after the archived branch remain required. Each recovered feature
needs an independently reviewable change and its stated failure/recovery tests
under the existing roadmap IDs.

## Android extracted-package repair, 18 October 2026

`OpenQ4Activity` delegates APK-owned extraction to `PackageStorage`. Gradle now
produces a canonical ASCII manifest of normalized paths, byte lengths and SHA-256
digests; the package revision is the SHA-256 of that manifest. The signed-APK
verifier requires both exact metadata files and still compares every asset and
native library with the validated stage. ABI/API, certificate, alignment, license
and native-library allowlists are unchanged.

Before launching the engine, the host reads the bounded manifest and verifies
every extracted file, even when `.ready` exists. Missing, truncated and mismatched
files are copied into a separate temporary outside the mounted `baseoq4` tree,
checked against the declared size/hash, synced and renamed over the destination.
Healthy files are read for verification but never recopied. Failure invalidates
readiness and leaves the previous package and saves/configuration untouched.
Only after complete verification and readiness publication are old generated
revisions removed. Unexpected content and links below the normalized app-private
root fail closed without deleting that content. Android's
[file-space estimate](https://developer.android.com/reference/java/io/File#getUsableSpace())
is an early preflight; write/sync/rename failures still stop startup because the
estimate does not reserve space. Atomic replacement uses
[Android's existing rename API](https://developer.android.com/reference/android/system/Os).
An already valid readiness record is preserved, so verified healthy content does
not depend on a new metadata write when storage is exhausted.

The original real-Activity corruption control fails with an existing `.ready`
marker (`.tmp/stage-two/android-ready-repro.log`). The expanded
`tools/tests/android_host_storage.py` executes the production Java host/storage
classes with small Android/SDL stand-ins. Windows JDK 21 and Linux JDK 17 runs pass
healthy reuse, missing/truncated/same-size corruption, interrupted partial reads,
failed replacement, poisoned APK source length/hash, malformed/oversized metadata,
low-space preflight, upgrade cleanup and save preservation. Linux also rejects
active-file, nested-directory, temporary-file and package-parent links and
preserves an outside sentinel. Windows explicitly skips Android-style link
canonicalization instead of counting it as a pass.

The optional `--package-source .install/baseoq4` run uses independent copies of
the actual 810 MB staged package, performs two verified reuses without recopying,
corrupts a PK4 byte without changing its length, repairs only that pack and verifies
the result again. The log records exact package sizes and hashes. This is host
storage validation with warm filesystem caches, not Android startup timing.
The actual Gradle manifest closure matches Python's canonical bytes, including a
path ordering boundary and an empty file, and rejects an invalid path. All seven
APK-verifier/build test groups pass. The complete Java host plus the matching
SDL 3.4.16 sources compile against configured Android SDK 35.

Local evidence is `.tmp/stage-two/android-repair-evidence.json` (SHA-256
`b787b2bbb980d07132b34c2a1a08a2a9d28a406faf50b3b20c6b8521a3a1bc9c`), with
per-source and per-log identities. Logs include `android-repair-full-package.log`,
`android-repair-linux-final.log`, `android-package-tests-r1.log`,
`android-manifest-probe.log` and `android-sdk-java-compile.log`. No Android device,
power-loss test, new signed APK installation or certificate migration is claimed.
The existing signed release pipeline checks the new exact manifest after packaging.
Localized onboarding/retry UI, retail-data preflight, accessible release logs and
save export remain AND-01/AND-03 work; the broader items stay open.

## Android window ownership, 19 October 2026

The startup-window portion of archived `81d29509b` is adapted to the current
SDL/native-window lifetime contract. SDL 3.4.16's Android driver permits one
window. The engine splash previously occupied it until after graphics startup,
preventing creation of the game window. Android now keeps the Activity's launch
screen and skips the engine splash. Desktop splash behavior is unchanged.

On the fatal-error path, hiding the game window did not free that slot either.
Android now stops its text input, unbinds the GL context, retires the published
native-window identity and destroys the game window before the error console
creates its replacement. Repeated release is harmless. This changes window
ownership only; fatal-screen touch/back handling and broader lifecycle recovery
remain separate AND-01 work.

`tools/tests/android_window_lifecycle.py` compiles the actual production methods
against an in-memory SDL API enforcing the one-window rule. Before the change,
Android fails because its splash consumes the slot; the desktop control passes.
Afterward, Windows and Linux runs pass the Android startup/game/fatal sequence,
retirement ordering, repeated release and unchanged desktop behavior. These
fixtures neither inject device input nor replace a real Android runtime check.

The NDK r27d ARM64/API 24 build and stage pass with matching SDL 3.4.16 and
OpenAL Soft 1.24.3 dependencies. The Windows build/stage and all 254 native tests
pass. The first suite's existing durable-file test failed a post-rename assertion;
its unchanged isolated rerun passed. Its assertion now requires the intended
injected fault before a read clears the original error, so a native rename
failure cannot masquerade as the post-rename case. No production file-I/O change
was made. Linux passes its 343 checks and explicitly skips DrvFS FIFO support.
The original transient failure's OS error was not retained by the old assertion;
its exact external cause is unproven.

Source, dependency, build, test and staged-library/package identities are bound
by `.tmp/stage-two/android-window-evidence.json` (SHA-256
`794f400eeb26fd98f81e284cf902a771a2ab447eed23cf45121acb0d7c7ee0ff`).
The interrupted builds were resumed after the requested pause; their original
logs are retained. The debug APK also passes exact staged payload/manifest,
seven-library allowlist, API/ABI, native extraction, 16 KiB ELF/ZIP alignment and
v2 signature checks. Its SHA-256 is
`1a2c65f4e50f39d8f68ad8ad6f557e7071a3335aa80d34ef03461c080f050231`;
`.tmp/stage-two/android-apk-verification.json` records the checks (SHA-256
`b2815612ffe96fcdbad60a9d3f9bfb1b5a31d4c2883885bd031fb9de5c3de3ce`).
This local debug signature does not establish release certificate continuity.
The subsequent S25 check below qualifies startup for that device/package only.

## S25 startup, data path and upgrade check, 19 October 2026

Dan's Galaxy S25 (SM-S931B, Android 16/API 36, ARM64, 4 KiB pages) installs
the debug APK above. All 40 copied retail files match the independent source
fixture's SHA-256 manifest. Storage 1 reaches its first active draw, the engine
`screenshot` command captures the opening scene at 2340 by 1080, and
`Stage2AndroidSmoke` saves successfully. Final engine/app logs show renderer
shutdown and process exit without a reported crash. This is opening-scene
startup evidence, not campaign progression; audio is disabled and no device
input or OS screenshot is used.

The initial missing-data launch exposed a path bug: the engine discarded the
Android host's external data directory and fell through desktop discovery to
`/`. Android now preserves the host's explicit directory even when retail files
are absent. Required-PK4 integrity checks remain unchanged. The production
selection-block fixture fails before the change and passes afterward on Windows
and Linux, including unchanged desktop discovery and unset-path controls.
Android/Windows builds and staging pass; all 256 Windows native tests pass.
The corrected missing-data path still needs a physical-device retry.

The updated debug APK, SHA-256
`de949e3f506d75c12bae162129ea442bb8961b7982e2d300d07486f30caea64e`,
passes exact staged payload, seven-library, manifest, API/ABI, 16 KiB ELF/ZIP
alignment and v2-signature checks. An in-place update with the same debug
certificate preserves the original save, metadata and preview byte-for-byte.
Its restore attempt fails safely because `guis/menu/pause.q4ui` cannot be
created; the game displays its load-failed dialog and is then force-stopped.
The original save and failure logs are retained. Inspection identifies a UI
thread binding captured during library loading instead of engine initialization;
the repair below passes native checks, while successful device restore remains
required. This is not a release
certificate-continuity qualification.

Evidence is `.tmp/stage-two/android-basepath-evidence.json` (SHA-256
`7c8f08eb0179c70cb7ad44841d679a3731457a12d0acafd728961d88af12f0d8`),
including source/build/test identities and the `android-s25-baseline/` and
`android-s25-upgrade/` logs, engine capture, asset manifest and save hashes.
Remaining observed warnings include unsupported mobile window placement/MSAA,
unavailable SMAA resources and existing Storage 1 script/content diagnostics.
Onboarding, retained UI recovery, touch, audio and lifecycle checks remain open
under AND-01/AND-03; this check does not close broad device qualification.

## Android UI engine-thread binding, 19 October 2026

SDLActivity loads native libraries on its Java thread and invokes the engine
later on SDLThread. The retained-view coordinator and global GUI manager captured
their owning thread during library construction. Consequently, actual engine
calls could neither create retained views nor resolve native GUI allocations.
Both owners now bind during UI initialization, preserving rejection of calls
from other threads and allowing serial engine reinitialization.

The S25 restore failure above occurs in optional pause-menu preparation before
the game reads saved state. The original save contains no `pause.q4ui` reference;
`FindGui`'s broad loading-session guard produced the serialized-GUI diagnostic.
The subsequent [serialized-GUI boundary repair](savegame-reliability.md#serialized-gui-admission-and-optional-menu-fallback)
preserves optional fallback while rejecting missing definitions required by the
save. Native and Windows GL/Vulkan checks pass; physical retry remains pending.

`tools/tests/ui_engine_thread.py` runs the production manager/retained
initialization, view creation and allocation query methods with counted command
and Runtime stand-ins. Construction happens on one thread and engine startup on
another. Before the fix, both engine operations fail and the library-loading
thread incorrectly remains authorized. Afterward, Windows and Linux pass that
sequence, foreign-thread rejection and serial reinitialization on the desktop
thread. The retained resource-lifecycle fixture and all 257 Windows native tests
also pass. These checks do not activate a real SDL window or inject input.

Android ARM64/API 24 and Windows builds/stages pass. The updated debug APK,
SHA-256 `905cad2bccf62a55aa1aaff176f4d704b99cd237773fd5582b0f0b7393add668`,
passes exact payload, API/ABI, alignment, native extraction and v2-signature
verification. Its in-place installation preserves all three original save files.
The Android debugging interface disconnected before the physical retry; no
successful device restore or UI visual/input acceptance is claimed yet.

Evidence is `.tmp/stage-two/android-ui-thread-evidence.json` (SHA-256
`4f8d698f484efbb6ebd7e79bf0522a6f3b3fd90412ac717dc22fba74133e5ebe`),
with source identities, original failure analysis, native logs and package/update
records. AND-01/AND-03 and Q4-05 remain open.

## Android background audio and single-player resume, 19 October 2026

SDL 3.4.16's Android pump sends background lifecycle events on the engine thread
and then blocks before returning them to the game. The old deferred handler
therefore released held input and changed the sound world only after the app
returned. OpenAL's mixer could continue running while the game loop was parked.

The Android main-thread watch now performs the existing background transition
before that block. Foreign-thread callbacks still publish pending work for the
engine thread. The sound hardware immediately flushes a silent listener and uses
`ALC_SOFT_pause_device` only when both pause and resume functions exist. It retains
the matching resume pointer for that device. Missing extensions fall back to a
mute that normal updates preserve, and a device retry retains the requested
suspension. A player's explicit mute remains independent.

Foreground events leave audio suspended until the session handles the return.
A live SP map opens its pause menu before sound rendering or game tics; an
existing menu, map load, demo, editor or network session keeps its current flow.
A suspension during loading is consumed at the map handoff. Early/late input
cleanup also tolerates an uninitialized key table while a fatal console pumps
events. Desktop lifecycle dispatch remains deferred.

`android_lifecycle.py` compiles the production watch, transitions, input cleanup
and session resume method with counted API stand-ins. Windows and Linux pass
Android/desktop branches, foreign-thread deferral, repeated cycles, one-time
consumption and the SP/menu/load/network controls. Substituting the old watch
fails before queued events are processed. `openal_device_pause.py` runs the
production pause, deferred-flush and update methods against counted OpenAL,
covering absent/partial extensions, a changed later function lookup, duplicate
events, player mute, device retry and a foreign current context. Removing the
paired-function guard, persistent mute or deferred flush independently fails.
Device creation/retry API calls are stand-ins; this is not a real-device test.

Windows and Android ARM64/API 24 builds/stages and all **262 Windows native
tests** pass. The new debug APK passes the existing exact-payload, ABI/API,
16 KiB alignment, native extraction and v2-signature verification. Physical
installation, save restoration and Android suspend/listening checks remain
pending the disconnected phone. Background tic scheduling, process-death
recovery and the other AND-01/AND-03 items remain open.

The matched desktop package passes an input-disabled, hidden-window Arena run
with OpenAL's null output: two pauses freeze the gameplay sound world's clock,
both resumes retain its 14 active channels, and the results menu/ledger and
normal shutdown complete. Engine captures show the pause and result screens.
This checks desktop regression without a physical listening claim.

Evidence is `.tmp/stage-two/android-pause-evidence.json`, SHA-256
`cf789c484de5729b9512c58b39ba15f1a1fa021be3e23011085f6f237c0155b0`.
It binds sources, native/negative-control logs, the two builds/stages, SDL/OpenAL
implementation identities, the desktop runtime and debug APK SHA-256
`4e9b8c1ad27e802e9ef1b78eb3f00f87f35203b253dcc7e997ee26175ab90e98`.

## Android background timer recovery, 19 October 2026

The asynchronous worker previously woke every millisecond even while SDL parked
the game loop. The recovered background sleep uses an atomic lifecycle snapshot
and waits 100 ms in the background, retaining 1 ms foreground waits. It checks
shutdown again after sleeping before advancing time or emitting wake events.

The archived sleep alone did not bound accelerated-time catch-up. Android now
limits each scheduler call to ten current, scaled tics, including the first call
after an OS freeze when foreground has already been announced. The clock still
advances and wake events correspond to emitted tics; a long suspension does not
leave a backlog. The 60 Hz base command clock and desktop policy are unchanged.
This does not establish that a suspended multiplayer connection survives.

`android_async.py` compiles the production scheduler, Android worker and atomic
query with controlled clocks, sleep and event APIs. Windows and Linux pass
foreground cadence at five scales, combined game-time scales, one-hour freezes,
smooth slow time, the ten-tic limit, wake counts, shutdown during a background
wait, initialization and imprecise-timer controls. Substituting the old scheduler
fails on unbounded catch-up; the old worker independently fails its sleep check.
The production lifecycle fixtures and million-tic clock-ownership check pass.
All **264 Windows native tests** pass, alongside Windows and Android ARM64/API 24
builds and staging.

The debug APK passes exact staged payload, seven-library, manifest, API/ABI,
16 KiB ELF/ZIP alignment, native extraction and v2-signature checks. SHA-256:
`ba6b01cf8c96d791a353c9ba2f435d832d053c6d3fc51f999127a6ed7e94d242`.
It has not yet been installed: Windows enumerates the S25's file-transfer and
modem interfaces, but not its debugging interface. No measured power, thermal,
device suspension, network-resume or release-certificate claim is made.
AND-01/AND-03 remain open.

Evidence is `.tmp/stage-two/android-async-evidence.json`, SHA-256
`fb0c1779500bb4df0a732db00a3850be12a7889e65a29b45f4bb790e63b7438a`.
It binds the source and staged identities, native/negative-control logs, full
suite, builds and verified package. Initial fixture compilation failures from
a misspelled stand-in helper remain beside the corrected passing logs.
