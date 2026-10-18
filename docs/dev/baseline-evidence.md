# Stage-one baseline evidence

18 October 2026; starting source `8c1a49ca7a033e163e271ef3787a4a9ba73f7479`.
This is the evidence and ownership record for stage 1 of the
[roadmap](roadmap.md), not another development plan. Stage 1 establishes an
honest baseline, including reproduced failures; it does not require the later
product, renderer, device or release gates to pass. The runtime report index
below identifies the tested binaries and limits each observation.

## Current defaults and accountable workstreams

The source audit covers the current in-tree engine, SP/MP modules, renderer
selection, package metadata and UI inventory. Existing domain evidence retains
its recorded package/platform scope. A first-class platform target does not
mean every renderer, optional feature or current package is qualified.

| Configuration or default | Current source and disposition | Evidence owner / remaining gate |
| --- | --- | --- |
| Windows x64, desktop OpenGL / `best` | Default `gl` in `RendererModule.cpp`; current gameplay captures available | Desktop/platform workstream, [platform matrix](platform-support.md), REL-01 |
| Windows x64 Vulkan | Supported opt-in retains October NVIDIA/Intel evidence; no automatic promotion to default | Vulkan workstream, [capability matrix](engine-capability-matrix.md), VK-01/VK-02 |
| Linux x64 / Steam Deck, GL | First-class target; existing native Wayland/X11 evidence is historical, not rerun by this Windows audit | Linux/platform workstream, platform matrix and PLAT-01 |
| Linux Vulkan and macOS Vulkan | Experimental; software/CI evidence does not qualify physical GPUs | Vulkan/platform workstream, VK-01 and PLAT-01/PLAT-04 |
| macOS arm64 | Preview; unsigned packages and OS-floor signoff remain explicit | Apple/platform workstream, [macOS signoff](macos-signoff-evidence.md), PLAT-04 |
| Linux arm64 | Preview; current physical release signoff pending | ARM/platform workstream, [ARM64 evidence](linux-arm64-signoff-evidence.md), PLAT-02 |
| Windows arm64 | Experimental; no current client hardware qualification | ARM/platform workstream, platform matrix, PLAT-03 |
| Android arm64/API 24+/GLES3 | Experimental; source/package support exists, device qualification pending | Android workstream, [build contract](android-build.md), AND-01/AND-02/AND-03 |
| PC OpenXR GL, VR off by default | Implemented opt-in; Vulkan/EGL/Quest recovery is not active implementation | XR workstream, [recovery review](platform-recovery-review.md), VR-01/VR-02/VR-06 |
| MP prediction / lag compensation | `src/mpgame/gamesys/SysCvar.cpp`: both `0`; enhanced modes remain optional | Multiplayer workstream, MP-01/MP-07; corrected [player guide](../user/multiplayer-networking.md) |
| Pure assets, dual-stack network, rcon2 | Existing bounded implementations; proprietary game DLL and retail protocol 2.85 interoperability intentionally unsupported | Network/security workstream, capability matrix, MP-08 / REL-01 |
| Retained interface | `ui_retained 1` in `Session_menu.cpp`; stock fallback remains `0`. Published 0.14.000 notes describe that release's earlier default | UI workstream, [register](ui/product-requirements.md), UI-01 through UI-11 |
| TAA / GPU skinning / dynamic resolution | `r_temporalAA 2`; GPU skinning and dynamic resolution remain opt-in. VR/crop/nearest exclusions remain | Rendering workstream, [temporal contract](temporal-presentation.md), REN-04/REN-05 |
| Authored PBR and shared classic domains | Native authored PBR default-on does not promote shared classic domains; `r_rendererShared*` domains remain `0`; aggregate modern-lighting proven domains remains zero | Rendering workstream, capability matrix, REN-01/REN-02 |
| Room reverb / audio distance | `s_useEAXReverb 1`; `DOOM_TO_METERS` and `METERS_TO_DOOM` both `1.0f`. The old metre-conversion diagnosis is withdrawn | Audio workstream, [audio contract](audio-modernization.md), AUD-01 through AUD-03 |
| Exact scheduling / game time | 60 Hz scheduler and 16 ms ordinary game/snapshot time remain separate | Game/presentation workstream, [clock contract](presentation-clock.md), HF-01/HF-02 |
| Retail SP, MP and additive Awakening SP | In-tree canonical modules; no expansion multiplayer module | Compatibility/game workstream, [retail ledger](retail-baseline-ledger.md), Q4-02 through Q4-07 |
| Save readers, BSE, jobs, caches, native tools | Existing implementation is preserved. Full progression, effect, memory and tool qualification remain separate | Game/core/tools workstreams; capability matrix's linked evidence, Q4-03/Q4-05/Q4-07/CORE-01 through CORE-06; paused TOOL scope |

No default or support tier was changed to match stale prose. Historical resolved
decl/BSE fixes remain closed. Missing physical/device evidence is classified as
qualification pending; optional rendering/VR/Android work is not an implicit
prerequisite for unrelated supported configurations. Each capability row in the
capability matrix retains its more specific source/evidence owner.

## Executable coverage and clock ownership

The [coverage map](game-test-coverage.json) accounts for all 83 tests/probes from
the imported game history. The unified suite runs 74 relevant Python contracts
and compiled fixtures against this repository; obsolete companion-layout checks
map to current checks. Meson registers the native probes and production clock
test, and the push-validation profile runs Meson tests. See
[coverage and provenance](game-test-coverage.md) for the SDK-EULA boundary.

The clock test executes the shared production policy, including submillisecond
reads, 16/17 ms scheduling, one million ticks, non-divisor caps, jitter, catch-up,
stalls, pause, slow steps, resets, signed timestamp wrap and XR host deltas.
The pause fixture executes extracted production SP/MP methods and proves
scene/material reads stay frozen during a draw. Clock inputs are values, not
authoritative state references; deterministic event/state fixtures remain equal
across presentation caps. This proves clock-policy invariants, not a complete
game command replay or physical 240/360 Hz pacing qualification (HF-03/HF-06/HF-07).

## Workload and timing policy

Use existing `stock_asset_baseline.py`, renderer map harnesses and their evidence
schemas. Keep the full launch/config, `logFileName` log, engine screenshot,
source revision/dirty state, staged executable/module hashes, retail PK4 manifest,
overlay collision list, backend/GPU/driver and camera together. Raw reports and
failures stay in their original directories. Do not turn a failed report into a
pass by omitting its failed role or broadening thresholds.

The retail baseline uses its existing `stock-baseline-targets-v1` contract and
256 CPU/GPU samples per profiled map. Those results are absolute checks of that
contract, not before/after performance claims. The lighting comparisons use
ordered mapped/stencil/shadows-off engine captures; animation is not synchronized
between separate processes, so full-image differences do not isolate shading.

For any subsequent timing comparison, declare this protocol before collection:
30 seconds of loaded gameplay warmup, 2,048 measured frames per run, three
interleaved A/B then B/A pairs at identical camera/cvars/package/driver/power
state, engine CPU plus asynchronous GPU timing, no screenshot/log flush in the
sample window, and no simultaneous build/test workload. Retain all per-frame
samples and p50/p95/p99 for each run. A result is inconclusive if between-repeat
p95 spread exceeds 5%; otherwise require a change larger than both 5% and the
observed repeat spread before claiming an improvement. Frame-budget gates remain
their declared absolute budgets. Record timer/logging overhead with a paired
instrumentation-off run; absent that measurement, label overhead unmeasured.
This protocol is policy for comparisons, not a claim that this stage performed
such a benchmark or set final HF-07 hardware budgets.

Visible bordered-window GPU captures, hidden/offscreen capture, software rendering
and physical display/input testing are separate evidence classes. This stage
uses engine render-target screenshots only and sends no device input. None of
its image or synthetic-clock evidence certifies physical motion, input latency,
headset comfort, Android devices, macOS or a final release package.

## Retained local evidence

All paths below are repository-relative and deliberately outside the release
package. The [retail ledger](retail-baseline-ledger.md) records observed results;
the UI [inventory report](ui/inventory-report.md) records source reconciliation.

| Evidence | Location |
| --- | --- |
| Configuration, build, stage and native-suite logs | `.tmp/stage-one/` |
| First complete recovered game suite | `.tmp/stage-one/game-suite/results.json` |
| Meson-discovered recovered suite | `builddir/game-regression-logs/results.json` |
| UI raw inventories and governed revision audit | `.tmp/stage-one/ui-*-inventory*.json`, `.tmp/stage-one/ui-register-audit.json` |
| First retail baseline and shorter-path retry, including failures | `.tmp/stage-one/stock-baseline-run/`, `.tmp/s1/` |
| Four-map GL/Vulkan controls | `.tmp/s1m/` |
| Recomp lit decal controls | `.tmp/s1r/` |
| Independent original-PK4 asset view and bound expected manifest | `.tmp/stage-one/paks/`, `.tmp/stage-one/stock-baseline-paks/stock_pk4_manifest.json` |

The asset view contains independent copies of the installed 40 PK4s, with no
loose retail files. It avoids importing unrelated user mods/generated caches
from the installed game. No proprietary source or screenshots are added to Git.
