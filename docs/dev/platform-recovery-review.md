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

VR-06 is complete for the active desktop OpenGL implementation. `Check` records
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
| `819846f5d` background tic sleep | Recover bounded background scheduling only after checking multiplayer/server and resumed clock semantics; retain no-background-busy-loop and no-catch-up-storm tests |
| `20766e8d1` cutouts | Recover insets/orientation behavior through the current safe-area/density model, including portrait and controller/touch ownership |
| `ba6d3af2e`, `c5845ca2d`, `2f1d2d681` launcher/preflight | Recover localized missing-data flow; archived `RetailData.isPresent` tests only for a regular `pak001.pk4`, not complete integrity. Preserve usable installed data on interrupted extraction; AND-03 owns full validation and recovery |
| `023f0eeee`, `1484195c4` emulator | Recover ABI metadata, module names and ELF checks together; archived artifact-verifier changes alone miss the current exact APK allowlist. Keep diagnostic payloads out of production |

Current `OpenQ4Activity` still trusts `.ready` after extraction; this is the
known AND-03 integrity/recovery gap, not a newly fixed feature. Signed release
verification and dependency licensing added after the archived branch must be
preserved. Each recovered feature needs an independently reviewable change and
its stated failure/recovery tests under the existing roadmap IDs.
