# Current retail compatibility ledger

Stage-one Q4-01 investigation, 18 October 2026. Starting source
`8c1a49ca7a033e163e271ef3787a4a9ba73f7479`; current evidence is indexed in
[baseline evidence](baseline-evidence.md). This ledger classifies observed gaps;
it does not reopen resolved decl/BSE reconstruction or certify full campaigns.
Final controls use clean implementation `7674acef91c2653e8c6153ae11e7b158c05e52ff`;
earlier failed reports retain their own package/source identities.

## Current reported symptoms

The [roadmap report register](roadmap.md#report-and-contribution-traceability)
retains the complete issue/PR ownership map. The following retail gameplay reports
were checked against their current issue text and discussion on 18 October:

| Report | Baseline disposition and remaining evidence |
| --- | --- |
| [Weapon effects, sound and reload, #170](https://github.com/themuffinator/openQ4/issues/170) | Reported on 0.13.2. The merged BSE sound-diversity fix stays closed; individual particle/reload symptoms remain qualification pending under Q4-03/AUD-01/HF-04. Current weapon, effect, build/backend and timestamped reproduction are not yet supplied; the four lighting maps do not qualify these symptoms. |
| [Machinegun transparency, #183](https://github.com/themuffinator/openQ4/issues/183) | Report names Windows 10/RTX 3060 but no exact build, backend, map/save or asset set. Qualification pending under VK-04/REN-08; generic current weapon captures cannot reproduce or clear the reporter's firing/view conditions. The existing request for those details remains open. |
| [Tech Li at the Hangar Perimeter lift, #184](https://github.com/themuffinator/openQ4/issues/184) | Report identifies hangar1/Windows 10 and a progression stall. The #189 medic watchdog addresses an unreachable-patient case, but the exact reporter save and normal heal/progression regression remain Q4-02 qualification; map startup does not close it. |

These entries classify available evidence and preserve outstanding reports. They
do not treat absent reproduction data as a resolution or invent a root cause.

## Lighting findings rechecked

The existing map runner entered Network2, Recomp, Storage1 and Q4DM9 on both
GL and Vulkan, then wrote mapped, stencil and shadows-disabled engine captures.
All eight processes completed with the requested API, 960x540 bordered window
and capture sequence. A further two runs exercised Recomp's steady diagnostic
point light and the material/shadow planner self-tests. These are visual
investigations, not performance comparisons. Images were decoded and inspected;
successful capture is not a claim of pixel parity.

Host: Windows x64, NVIDIA GeForce RTX 4060 Laptop GPU; GL reports NVIDIA 591.74,
OpenGL 4.6.0; Vulkan reports API 1.4.325. Each launch/config and `gfxInfo` log owns
its precise settings/device record. SP freezes after settling, but separate
processes do not share identical particle/light/actor time. MP remains live.

| Report | Current observation and classification | Owner / remaining evidence |
| --- | --- | --- |
| Network2 GL/Vulkan lighting difference | **Reproduced differences** around the opening's upper/left illumination across control modes. Initial shadows-off captures also differ; the final mapped/stencil contrast remains conspicuous. Effects occur at different phases, so this is not an isolated shadow-map root cause | Q4-03 / VK-04: isolate light/material/effect and synchronize time before assigning root cause |
| Recomp dark opening and decal wall silhouette | Opening remains dark on both APIs. The lit fixture shows receiving walls and floor on both and the historical solid decal-wall failure is **not reproduced**. Residual lit/shadows-off differences remain | Keep the explicit `noShadows`/`DECAL_MACRO` repair closed; Q4-03/VK-04 own remaining non-shadow parity |
| Storage1 corpse/fire difference | Both APIs draw corridor, corpse, fire and smoke; actor/effect phases differ. No missing-corpse verdict is supported by these controls: **qualification pending** for synchronized effect comparison | Q4-03. This corridor fixture uses the explicitly recorded pod-intro bypass; it does not qualify the original opening or campaign progression |
| Q4DM9 darker Vulkan ambient/wall | Fixed camera `(1528,-384,452.25)`, yaw 180; matched structure and visible wall/pipe lighting, with no obvious former broad dark-wall failure. **Not reproduced in this view**; moving pickups/effects remain uncontrolled | Q4-02/VK-04; retain the old failing package, qualify additional views separately |

Historical [September shadow evidence](shadowmapping-final-audit-2026-09-05.md)
is unchanged. Authored `noShadows`, ambient lights and unsupported caster types
are reported separately from API/resource failures. Stock warnings remain in
the logs; no asset edits were made to silence them.

## Runtime baseline and failures

The bound original-media view contains 40 unmodified installed PK4s and zero
loose files. Its expected-manifest SHA-256 is
`5250429197dd4083cf464f4cb83cd02fdbbd28be52d35c0c6688e6ca898bd67e`.
The ordinary staged package adds pak0/pak1 and supersedes **165 retail virtual
paths**. It is therefore a retail-PK4 compatibility baseline with declared
overlays, not an original-asset-only baseline.

Two complete harness runs (`.tmp/stage-one/stock-baseline-run/`, `.tmp/s1/`)
passed SP Storage1 save/restore, render-demo playback and the Q4DM1 listen-server
role. Each profiled successful role supplied 256 CPU/GPU samples and passed its
unchanged existing per-map budget. Both **failed the connecting MP client**:
startup timed out before active gameplay/display/capture completion. The shorter
save path did not resolve it. This is a reproduced failure of this workload,
not a qualified pure-client result or a proven path-length diagnosis. MP-08 and
Q4-02 own the remaining client-startup investigation; the full failed reports
and logs remain alongside reruns.

An initial overlay-free probe incorrectly selected `fs_game baseoq4` without
its required package metadata/paks. Its pre-log timeout was traced with a
non-invasive debugger stack to `idFileSystemLocal::Startup` â†’ `FatalError` â†’
`Sys_Error`'s Windows message loop. This is an invalid package setup, not evidence
of broken retail rendering. The supported original-content control must select
`fs_game q4base`, stock UI and the same openQ4 binaries, with an isolated writable
q4base. `capture_legacy_baseline.py --stock-assets-only` now makes that distinction
explicit. The failed setup reports remain under `.tmp/s1os*` and `.tmp/s1ov`.

The corrected controls reached Air Defense 1 SP/GL and Q4DM1 MP/Vulkan gameplay
using original content only (initial `.tmp/s1oa/`, `.tmp/s1om/`; final clean-build
`.tmp/s1oaf/`, `.tmp/s1omf/`). Both final engine images were
visually inspected: world geometry, weapon and stock HUD are present; MP is an
active joined player. Logs confirm loading the matching in-tree game modules
from the fixed comparison runtime's baseoq4 binary directory, with no content
packs mounted from it. These hidden-window captures are compatibility controls,
not pacing or full progression evidence. The final controls report 21 SP and
622 MP warnings and zero ERROR records; the initial MP run reported 616 warnings.
Repeated runtime warnings vary with the sampled gameplay interval. Missing openQ4 Arena/demo
menus, SMAA/postprocess/soft-particle resources and custom declarations are
expected omissions in this control. Undefined stock `r_aspectRatio` binding,
missing MP AAS/sound and non-precached stock decl warnings remain explicit
UI-03/Q4-02/MP-02/MP-03 investigation inputs; capture success does not clear them.

The installed Steam directory also contained unrelated loose/generated content
and an extra baseoq4 overlay. The baseline preflight rejected that directory;
the audit uses independent PK4 copies instead. No installed assets or user
configuration were changed. Missing-media, authored-content warnings, package
configuration errors and renderer defects must not be merged into one verdict.

## File-by-file overlay disposition

[retail-overlay-audit.csv](retail-overlay-audit.csv) lists every one of the 165
colliding files, its repository source SHA-256 (LF-normalized text, raw binary), original archive locations,
classification and workstream owner. It is the source counterpart of the runtime
harness's `retailPathCollisions`, not a new acceptance schema.

| Collisions | Disposition |
| --- | --- |
| 128 `gfx/` files | Intentional loading/reticle imagery; UI-04/UI-05 own replacement/exception evidence. They are not fixes for the four maps' world lighting |
| 24 `guis/` files | Intentional menus/HUD behavior and layout; UI-03/UI-04 own migration, with save readers under Q4-05/Q4-07 |
| 8 `strings/` files | Intentional localization and openQ4 text; no missing retail media is inferred from these overrides |
| 2 `glprogs/glsl/SniperStretch2` files | Intentional scope presentation, owned by UI-04/REN-08 |
| `default.cfg` | Intentional bindings/defaults, including wheel/quick-chat controls |
| `scripts/maps/storage1.script` | Compared against pak010: adds only the opt-in `g_openQ4Storage1NoDropPodState` branch/helper; default still calls retail `inFlightSetup`. Retain the named diagnostic fixture until Q4-02 replaces it with a validated engine/game facility |
| `scripts/maps/convoy2b.script` | Compared against pak010: adds only opt-in no-actor/unlocked-hovertank guards. Default retains retail driver/vehicle actions; Q4-02 owns eventual fixture retirement |

Virtual-path collisions alone miss declaration-level overrides. The additional
source review records these separately:

| Source under content/baseoq4/pak0 | Purpose and disposition |
| --- | --- |
| `def/weapons/00_napalmgun_openq4.def` | Deliberate residue balance change (smaller hazard, longer lifetime), including stock-named impact declaration; retain as an intentional gameplay difference, never describe a run using it as stock gameplay |
| `def/vehicles/awakening_turret_openq4.def`, `materials/00_awakening_turret_openq4.mtr`, three `effects/openq4_awakening_turret_*` files | Additive Awakening turret implementation; Q4-04 owns campaign-scoped behavior |
| `def/openq4_m01_cinematic.def`, `scripts/openq4/awakening/m01_dropship.script` | Original Awakening scene helpers referencing installed media; Q4-04 |
| `def/liquids_openq4.def`, `materials/liquids_openq4.mtr`, `materials/types/liquids_openq4.mtt`, two `effects/openq4_liquids_surface_bubbles_*` files | Intentional liquid feature resources; retain separately from retail compatibility claims |
| `def/maps_openq4.def`, `def/bot_support.def` | New laboratory map and bot declarations; intentional new content |
| `materials/hardwareshaders_openq4.mtr`, `materials/hud_openq4.mtr`, `materials/weaponwheel_openq4.mtr` | Scope/HUD/wheel presentation resources; UI-04/REN-08, not world-lighting workarounds |
| `materials/postprocess_openq4.mtr` and remaining `glprogs/` | Existing renderer feature resources. Original-content controls omit them; shared/generated engine resources remain the preferred direction for future changes |

Retained Q4UI documents, bot profiles, the new map, light grids and new language
tables are intentional features, not candidates for automatic deletion merely
because retail lacks them. No blanket source/bitmap acceptance is granted.
This audit found no safe compatibility-only override to remove without changing
an intentional feature or a named diagnostic fixture. Their retirement or
replacement requires the owning roadmap item's gameplay evidence.
