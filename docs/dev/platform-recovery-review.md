# Stage-one XR and Android recovery review

18 October 2026, current source baseline `8c1a49ca7a033e163e271ef3787a4a9ba73f7479`.
This records the scope/recovery portion of roadmap VR-01/VR-06 and AND-01.
Those implementation/qualification items remain open. Archived commits below
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

Current `OpenXRSystem.cpp` has the source-derived cycle `Check(SESSION_LOST)` →
`DestroySession()` → `ReleaseImages()` → `Check(xrReleaseSwapchainImage)` before
`frameOpen` and `chain.acquired` are cleared. This confirms the re-entry risk in
source, not an injected-runtime reproduction. Instance/runtime loss also enters
destruction. VR-06 must take ownership out of circulation before fallible cleanup,
make destruction idempotent, and stop the caller after session invalidation.
Its fault matrix must cover session/instance loss, each partial acquisition,
wait/release failure, invalid image count/index, create/resize failure and lost
tracking. Require bounded calls, balanced ownership and no stale handles, plus
desktop recovery. Existing call-order tests do not satisfy those conditions.

HF-02 separately replaces millisecond smooth-turn deltas with monotonic host
ticks. XR predicted display time remains the runtime's pose/submission domain;
the [clock contract](presentation-clock.md) does not authorize converting one
clock to the other or claiming lifecycle repair.

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
