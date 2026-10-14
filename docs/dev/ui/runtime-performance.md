# Retained UI measurements and vector caching

8 September 2026. This checkpoint adds runtime CPU measurements and removes
redundant path compilation during fades and whole-pixel movement. It advances
the [replacement plan](../plans/idtech5-ui.md); full performance qualification,
composition, production artwork, editor and GUI migration gates remain open.

The later [composition checkpoint](composition.md) supersedes the per-primitive
opacity path described below: canonical fades now use isolated layers and reuse
both geometry and vertex tint. Measurements here remain the historical baseline.

## Cache behavior

Vector elements retain compiled, premultiplied path geometry independently of
opacity. A fade updates the submitted vertex colors without repeating curve
subdivision, stroke union, coverage integration or gradient subdivision.
Opacity still uses the existing per-primitive contract; isolated group fades
require the planned composition renderer.

Whole output pixels of translation are applied when submitting cached geometry.
Only the fractional translation phase participates in path compilation. The
viewport/scissor region is transformed into that coordinate space and expanded
to a 256-pixel grid for the cache key. Small movements can reuse the region;
crossing a cache-region boundary recompiles it. The render manager always clips
to the exact current viewport/scissor, including after movement or resize.

Changes to fractional position, scale, rotation, shear, layout dimensions or
the cached coverage region rebuild paths. Source reload clears both geometry
and tint caches. Density/video changes use the existing regeneration path.
This is a bounded cache per element, not an accumulating history of positions.

The native retained test compares animated cached geometry against a newly
loaded document at the same final position and opacity. It also checks live
clipping during translation, zero path compilation for opacity-only changes,
no geometry upload during whole-pixel movement, fractional-phase invalidation
and zero retained geometry allocations after shutdown.

## Tessellation precision regression

The moving 200% fixture exposed a single-precision tessellation failure at a
thin chamfered rail. A boundary returned two nominally coincident points at
`791.79998779296875` and `791.7999267578125`, creating a tiny extra loop. Its
calculated coverage at pixel `(791,0)` was `1.000010482367812`. The invariant
check rejected the path; static captures had not exercised that phase.

The pinned libtess2 subproject now uses a small
[double-precision patch](../../../subprojects/packagefiles/libtess2/double-precision.patch).
The patch changes `TESSreal` and the corresponding subnormal assertions; the
archive pin, allocator bounds and upstream license/credits are retained.
The compiler checks the expected scalar size, preventing a stale unpatched
header from silently using an incompatible ABI. No system libtess2 is used.

The boundary integrator also evaluates clamped linear trapezoids directly,
avoiding subtraction of nearly equal antiderivatives. The coverage invariant
remains intact. The failing rail is now exercised over ten fractional phases
with independent clipped-triangle area checks, and the 60-frame 200% motion
benchmark completes without path errors.

Meson applies the patch through its documented
[wrap diff mechanism](https://mesonbuild.com/Wrap-dependency-system-manual.html#diff-files).
Existing checkouts with an already-extracted unpatched dependency must refresh
that generated subproject before rebuilding:

```powershell
& tools/build/meson_setup.ps1 subprojects update --reset libtess2
```

This refresh replaces the generated libtess2 source directory. Keep any local
dependency changes as reviewed patches before refreshing it. Clean checkouts
apply the patch automatically when the pinned archive is extracted.

## Measurement interfaces

`Runtime::Statistics()` returns the most recent frame's CPU update/render time,
path compilation and geometry preparation time, compilation/cache/upload counts,
host draw counts and submitted vertex/index totals. Resident compiled-geometry
counts/bytes follow resource lifetime, including hidden elements. Vector cache
bytes describe the elements visited during that frame. These are tracked CPU
buffers, not total process memory, RmlUi's entire allocation graph or GPU memory.

The developer command `ui_retainedProfile <1..3600 frames>` records a bounded
sequence of rendered frames. Its final log line is JSON prefixed by
`Retained UI profile: `. Engine CPU timing includes retained evaluation,
submission and the surrounding GUI flushes. GPU execution, presentation and
the rest of gameplay are outside this measurement. Profile data does not change
the presentation clock or inject any input.

Without a preview document, the same command profiles the session-owned root
views (the title, pause, SYSTEM and loading screens) by submitted frame. Its
line is prefixed by `Retained UI root profile: ` and reports the views drawn per
frame, their summed retained CPU time, the wall interval from each frame's first
root draw to the next frame's, and their layer composites, backdrop passes and
backdrop fallbacks. A hidden window on Windows is capped at 60 fps, so its
frame interval measures CPU-bound frames, not GPU cost.

The capture harness accepts `--profile-frames N`, waits for the requested frames
before taking its engine screenshot and requires completed profile records.
With video restart, it checks both the original and recreated preview. The
report retains profile records alongside launch arguments and binary/log hashes.

## Native benchmark

`openq4-retained-ui-benchmark` loads the real vector fixture and uses the real
canonical evaluator, RmlUi layout and retained renderer. It exercises stationary,
opacity-only, whole-pixel and fractional translation scenarios, reporting JSON
lines with CPU percentiles, compilation/upload counts and tracked buffer peaks.
It uses synthetic font metrics and an empty draw host; it excludes the game's
font backend, engine vertex conversion, actual graphics APIs and GPU execution.
It is a diagnostic executable, not a timing threshold in the normal test suite.

```powershell
& tools/build/meson_setup.ps1 compile -C builddir openq4-retained-ui-benchmark
& builddir/openq4-retained-ui-benchmark.exe tools/ui/fixtures/vector-smoke.q4ui 1.25 60
& builddir/openq4-retained-ui-benchmark.exe tools/ui/fixtures/vector-smoke.q4ui 2 60
```

The baseline was `d096cc9f` with measurement instrumentation, before cache
changes, using the same fixture and scenarios. Its preserved benchmark binary
SHA-256 is `957e5c207fa893ec9f8bc83afc312d4f58bf5a93cdf24e67236b4385ef41b27d`.
Both comparisons use the existing Windows **debug, optimization 0** build.
They demonstrate work avoided in this fixture; they are not shipping-build
frame-rate results or cross-platform performance claims.

The 60-frame baseline compiled 780 paths during both opacity and whole-pixel
movement. The new cache compiles zero in either scenario. Opacity still rebuilds
780 tint submissions; whole-pixel movement also eliminates those uploads.
Fractional motion continues to compile the changing coverage. Additional cached
geometry increases tracked resident CPU memory and is included in the reports.

The final native benchmark binary SHA-256 is
`d5edcaa4dc38662c4d1307578b1013e027cdea4b11b034357e17b0828b94e200`.
Reports are under `.tmp/ui/ui-profile-baseline-{125,200}.jsonl` and
`.tmp/ui/ui-profile-final-{125,200}.jsonl`. Median CPU times in milliseconds:

| Scenario | 125% before | 125% after | 200% before | 200% after |
| --- | ---: | ---: | ---: | ---: |
| Stationary | 0.85 | 0.57 | 1.39 | 0.81 |
| Opacity | 15.96 | 1.13 | 20.34 | 1.52 |
| Whole-pixel movement | 14.96 | 0.62 | 16.14 | 0.88 |
| Fractional movement | 17.38 | 13.12 | 39.64 | 22.32 |

These are individual local runs and include measurement variability. The final
implementation also has more precise tessellation, which removes numerical
fragmentation as well as fixing the rejected rail. The stationary fixture's
tracked buffer peak rises from 407,696 to 807,224 bytes at 125%, and from
480,600 to 1,470,080 bytes at 200%. Cold first-frame evaluation remains about
24 ms and 36 ms respectively in this unoptimized benchmark. Fractional movement
and cold compilation therefore remain explicit optimization/qualification work.

All three native test targets pass after the precision patch. Client, dedicated
and both renderer modules were built/staged before the final gameplay profiles.

`--screen` runs a production root document as the session presents it:
`onInit`, the `open` timeline and a four-second settle, then timed 60 Hz frames
on its view-height canvas, with each declared CVar source at its type's default.
It reports frame, update, render and tessellation times, paths compiled, draw
calls, submitted vertices, and layers pushed and elided:

```powershell
& builddir/openq4-retained-ui-benchmark.exe --screen content/baseoq4/pak0/guis/menu/title.q4ui 240 1280 720
```

An optional sixth argument names a document event that runs after the settle,
so the timed frames show what it opens; `first_ms` is the frame that opens
it. Create Server's ADVANCED OPTIONS, with PLAYER BAN LIST nested in it,
opens in a 2.8-3.4 ms first frame against 2.5-2.7 ms without the list
(debugoptimized, two runs each, 30 frames at 1280x720):

```powershell
& builddir/openq4-retained-ui-benchmark.exe --screen content/baseoq4/pak0/guis/menu/createserver.q4ui 30 1280 720 advancedModalShow
```

## Gameplay evidence

The final hidden, windowed runs used the registered engine screenshot command
after active SP/MP gameplay, with mouse/controller input disabled and no host
input injection. The unchanged vector fixture's frames, thin rails, gradients,
ring/hole, check stroke and localized labels were reviewed from render-target
TGA files. Each profile contains 180 actual rendered frames, including entry
motion. SP repeats the profile after full video restart and timeline replay.

| Profile under `.tmp/ui/performance/` | CPU p50 / p95 / max (ms) | Path compilations | Outcome |
| --- | --- | ---: | --- |
| `sp-gl-125-restart`, original preview | 1.47 / 2.10 / 28.31 | 57 | SP `airdefense1`, OpenGL, 125%; exit 0, no warnings/errors/retained diagnostics |
| Same run, recreated preview | 1.48 / 12.37 / 13.80 | 130 | Second 180-frame profile and timeline replay confirmed |
| `mp-vulkan-200` | 2.23 / 7.72 / 45.48 | 109 | MP `q4dm1`, Vulkan, 200%, auto-join; exit 0, no errors/retained diagnostics |

The high maxima and motion percentiles remain visible here because cold and
fractional-motion work are not yet fully qualified. These unoptimized CPU
profiles include GUI flushes but do not measure GPU completion or frame pacing.

Both runs used client SHA-256
`c3ce0146e2c7b1466210728450ca454d5ed1dfa039e93cb7493ea53b72ff0df3`,
fixture SHA-256
`78dc7bc86a65d6983ac23646f5534f205ec670bb85ade94cffecb4c8da921bbe`.
The final rebuilt OpenGL module SHA-256 is
`95ff9ca571526cc7668756552d91334093ecb472a1a227bba155962a5d354118`;
the Vulkan module SHA-256 is
`0c858cd74c859d9bacab961bd52cbcfbea1169bf7f5a1398a9d8936fc9707f41`.
SP screenshot SHA-256:
`68fd1b33c134e3d7d049d6bc696f7f24752a567e85fd92c2a4d5b612b12fb48a`.
MP screenshot SHA-256:
`120bd3c469282c0b23ce221f7f34f88556620633665bfa9a1de51f84180f8921`.

The MP log retains 93 existing content warnings; comparison with the preceding
MP capture found no new warning messages. The capture reports retain full
launch arguments, hashes, profile records and `replacement_acceptance: false`.
Windowed gameplay and these fixture screenshots do not qualify other platforms
or the complete 271-resource GUI corpus.

```powershell
$assets = 'C:\Program Files (x86)\Steam\steamapps\common\Quake 4'
python tools/ui/capture_legacy_baseline.py --assets $assets --mode sp --renderer gl --retained-document tools/ui/fixtures/vector-smoke.q4ui --density 1.25 --timeline enter --video-restart --profile-frames 180 --output .tmp/ui/performance/sp-gl-review
python tools/ui/capture_legacy_baseline.py --assets $assets --mode mp --renderer vulkan --retained-document tools/ui/fixtures/vector-smoke.q4ui --density 2 --timeline enter --profile-frames 180 --output .tmp/ui/performance/mp-vulkan-review
```

## Retained title screen CPU

1 October 2026. With `ui_retained 1` the title screen took 9.5 ms of retained
CPU a frame on a debugoptimized build, and 15-19 ms when the GPU fell behind
the hidden window's 60 fps cap: graphics calls inside the timed region then
block. The title is mostly static, so nearly all of that was work repeated
every frame. A temporary per-phase probe on the 1280x720 home screen split it:

| Work per frame (debugoptimized, 60 fps cap) | Before | After |
| --- | ---: | ---: |
| Path tessellation | 3.1 ms, 2 paths | 0.4 ms, 1 path |
| Host vertex conversion | 2.4 ms, 192,000 indices | none for unchanged meshes |
| Composition layers | 33 | 15 |
| Runtime update | 1.1 ms | 0.7 ms |

The changes keep the presentation:

- **Zero-opacity layers.** Any opacity below 1 is an isolated `filter`
  layer, and the hidden focus rails, hot markers and message lines sit at 0.
  A pushed layer now stays pending, recording its draws, until something
  needs its target: a nested layer, a mask snapshot, a backdrop or a visible
  composite. Composited at zero opacity, or into an empty clip, it is dropped
  without a target, a clear or a composite, which is exact: a premultiplied
  composite at zero opacity leaves its destination unchanged. The new
  `layerElisions` statistic counts them, and `layerPushes` now counts the
  layers that received a target.
- **Sub-pixel jitter.** The glint's rim turns back under its turning parent,
  so it stays put, but single-precision composition moves its sub-pixel phase
  by about 1e-4 px between frames, and the exact-match cache key compiled it
  almost every frame. A phase change below 1/1024 px now keeps the compiled
  mesh. Coverage moves no further than the phase, a quarter of one 8-bit step;
  every other key term must still match exactly.
- **Tessellation.** The coverage emitter extends rows through sorted vectors
  instead of a map per row, gradient stop planes clip only the cells they
  cross, and scratch buffers are reused. The turning wedge mask, which must be
  tessellated every frame, falls from 0.9 to 0.3 ms natively. A local harness compiled
  the committed tessellator beside this one and compared 264,984 cases, every
  path and mask of the six production screens and three fixtures across
  sizes, densities, sub-pixel phases, rotations, mirroring, bounds and both
  antialiasing modes: every mesh is byte-identical.
- **Retained meshes.** `RenderGeometry` keeps each geometry's transformed and
  clipped submission and reuses it while its translation, transform, clip,
  texture and multiply resolution are unchanged. Hosts receive a stable mesh
  identity and a revision through the optional `Host::DrawMesh` and
  `ReleaseMesh`, whose defaults draw immediately. The engine host converts
  a mesh once per revision, material and view size. Each chunk passes the
  contiguous vertex range its whole triangles use, so vertices are no longer
  duplicated per index, and the material is classified once per mesh rather
  than once per vertex.
- **Update.** `ApplyMotion` holds every authored property, nearly all static,
  and formatted all of them each frame. A value already applied under the same
  state revision and text ratio is now skipped; text and backdrop pairs are
  still reapplied. Input eligibility looked up each canonical node with its own
  search of the element tree, and now resolves all of them with one
  breadth-first walk in `GetElementById`'s order.

Each pair alternated a baseline client (origin/main `c5119c41`) with this
change on one machine (Windows 11, RTX 4060 Laptop GPU): a hidden 1280x720
window, the title at home for 4 s, then `ui_retainedProfile 120`. Medians of
`retained_cpu_p50_ms`, with the median frame interval:

| Build and renderer | Before | After |
| --- | ---: | ---: |
| debugoptimized, OpenGL, 60 fps cap | 9.59 ms | 3.59 ms |
| debugoptimized, OpenGL, uncapped | 9.43 ms | 3.51 ms |
| debugoptimized, Vulkan, 60 fps cap | 9.72 ms (19.8 ms frames) | 3.77 ms (16.7 ms frames) |
| release (`b_ndebug=true`), OpenGL, 60 fps cap | 10.21 ms | 3.89 ms |
| release, OpenGL, uncapped | 9.53 ms | 4.77 ms |
| release, Vulkan, 60 fps cap | 9.69 ms (20.1 ms frames) | 3.55 ms (16.7 ms frames) |

Baseline runs also fell into a slower, GPU-bound mode at times: Vulkan at
25-27 ms with 38 ms frames, OpenGL at 15.6 ms with 19.7 ms frames. The native
`--screen` benchmark of the title, with an empty draw host, falls from 5.3 to
1.0-1.3 ms on debugoptimized and 0.96 ms on release.

Engine captures of the title scenario in
`tools/ui/capture_retained_screens.py`, with reduced motion so that every frame
settles, are byte-identical before and after on OpenGL and Vulkan for the home,
depth, focus, exit-confirmation (over soft focus), and depart screenshots. The
hand-off to the stock settings page differs between two baseline runs as well,
because of its own animation. A motion-on capture shows the glint, rim and
montage unchanged.

What remains per frame: the engine's GUI path still copies every retained
vertex, into the GUI model and then into frame memory and the vertex cache at
each flush. That is about 2 ms for the title's 127,000 vertices, and static GPU
buffers for retained meshes would remove it. The wedge mask turns and is
tessellated every frame. Fifteen layers remain, for the 0.4-opacity rails and
markers and for the glint and its mask. A cold first frame takes 45-50 ms,
most of it stroke unions, the reticle grid alone 28 ms.

## Gameplay HUD state updates

The game writes HUD state every frame, and the multiplayer document carries
about 1,700 bindings with the Competitive preset. Each changed batch used to
copy the whole state, evaluate every binding and then reapply every bound
property. With dependency-tracked evaluation (see
[bindings](bindings.md#updates-ownership-and-lifetime)) a batch evaluates and
applies only what it reaches. The native benchmark
(`openq4-ui-retained-screens-test --hud-bench`, debugoptimized, one variable
changed per batch) on `remastered_mp.q4ui`:

| Document | State update | Frame after a change |
| --- | ---: | ---: |
| Remastered bindings, every binding evaluated | 0.71 ms | 3.1 ms |
| With Competitive, every binding evaluated | 1.53 ms | 5.3 ms |
| With Competitive, dependency-tracked | 0.01 ms | 0.38 ms |

## Gameplay instrument performance

The October 2026 gameplay investigation found that the Remastered ECG's
repeated core/glow vector strokes remained expensive after tessellation:
each moving frame still transformed and submitted their geometry. With the
user-approved bitmap exception, the ECG uses two adjacent copies of each
installed stock texture through the existing vector mask. Full texture periods,
Marine/Strogg rates, low-health tint and essential motion are preserved. No
extracted proprietary texture is added to the repository. The native Marine
HUD diagnostic drops from 64,272 vertices / 51 draws to 22,180 / 25, with warm
frame CPU time falling from 2.896 to 0.585 ms on this machine.

The radio graph's bar transforms used the full HUD canvas as their reference
box, moving the visible ink outside its mask. Correcting that revealed a
second cost: forty changing audio columns added about 1.4–1.6 ms per frame in
the native fixture; two multiplayer talker graphs added about 3.6 ms. The
approved fallback scrolls a fixed repeated waveform, keeps existing masks,
colours, speaker labels and show/hide events, and freezes under Reduced Motion.
These graphs indicate activity rather than measured loudness. Documents no
longer declare audio peak fields, so the HUD peer skips their unused history
reads and state writes. Warm preset graphs compile no vector paths and add
about 0.01 ms (Marine), 0.02 ms (Strogg), or 0.05 ms (both MP talkers) in the
same native diagnostic. These timings exclude GPU execution and use synthetic
fonts; the optional `--hud-audio-bench` mode records all phases.

The original four gameplay scenes were repeated on an i7-13700H / RTX 4060
Laptop GPU, NVIDIA 591.74, Windows, using the optimized staged client. Each
1280x720 window used MSAA 8, SMP off, VSync off and uncapped rendering, with
25 seconds warmup followed by alternating UI-off/on windows of 10 seconds.
Multiplayer used a solo listen server without bots and explicitly enabled
auto-join. Recorded camera poses match the original runs, allowing 0.125
world units for ground settling; Storage 2 excludes its moving-lift samples.

| Scene | UI on before (FPS) | UI on after (FPS) | Gain | UI off after (FPS) | UI-on P95 before / after |
| --- | ---: | ---: | ---: | ---: | ---: |
| Storage 2 / Vulkan | 86.5 | 216.2 | +150.1% | 170.8 | 19 / 6 ms |
| Air Defense 1 / Vulkan | 121.0 | 204.5 | +69.0% | 354.0 | 15 / 7 ms |
| Q4DM1 / Vulkan | 112.9 | 158.5 | +40.4% | 366.8 | 13 / 9 ms |
| Q4DM1 / OpenGL | 104.6 | 139.7 | +33.6% | 232.7 | 16 / 10 ms |

FPS values are medians of smoothed end-of-window snapshots, not averages
over each entire window. P95 uses the full sample histogram in millisecond
bins. CPU load varied substantially: the stock UI controls varied as well,
and a separate unchanged-baseline Air Defense repeat fell from 121 to 84.4
FPS. Treat gains as local observations. In particular, Storage 2's faster
UI-on result does not establish that retained UI is cheaper than stock UI.
Multiplayer retains measurable UI overhead after this instrument fix. The
comparison isolates the task's changes against the original working-tree
build; it is not a checkout comparison with the previous release.

Separate 300-frame retained CPU profiles fall from 2.7091 to 0.949 ms at p50
in Air Defense, from 4.623 to 1.602 ms in Vulkan Q4DM1, and from 3.25 to
1.4934 ms in OpenGL Q4DM1. Storage 2 measures 1.199 ms after the fix; its
original CPU profile is excluded because its setup changed after FPS sampling.

Qualification includes all three native retained UI/screen suites, generated
document consistency, SP decoder/playback-history checks, and engine render
target captures on OpenGL and Vulkan. Six moving graph pairs change pixels;
all six Reduced Motion pairs remain identical. In sixteen paired HUD captures,
all changed pixels are confined to the approved ECG area. Live microphone and
network voice were not exercised. Logs, runtime identities, per-window results,
captures and the method are retained in
`.tmp/ui-perf-fix-20261011/REPORT.md`; original UI on/off evidence is in
`.tmp/ui-ab-20261011/`.

## Initialization animation (11 October 2026)

The initialization view now advances between stage changes at cooperative
startup checkpoints: existing print/read progress offers, completed GUI loads
and menu-image preloads. A scoped main-thread owner ends before normal session
presentation, including on exception. The pump does no work on worker threads,
inside its own draw or during retained document loading/resource callbacks.
It never starts a rendering thread, sleeps, waits for animation to finish or
invents progress. The retained clock already measures monotonic elapsed time;
the defect was the lack of frames during synchronous initialization.

Redraws target at most 30 Hz, respect lower presentation caps, and reserve nine
times the previous completed frame cost for loading before another optional
frame. Slow drawing or a blocking present therefore reduces animation frequency.
The first cold compilation is paid once and does not poison the warm budget.
Stage changes still present immediately. Reduced Motion skips optional redraws
and preserves the existing still poses. Normal gameplay does not run this pump.

The dim rotating plate band, teeth and soft light sweep use the existing
`antialias: false` authoring option. Fill-only paths without analytic coverage
now retain local triangles across motion; the render manager applies their
current transform and clip. Curve precision uses a conservative output-scale
bucket, invalidated on density/size changes. Lettering, bright details, masks
and strokes retain their original output-space coverage. No raster assets are
introduced. Unchanged startup messages also avoid state publication and binding
updates on every animated frame.

Matched 120-frame native benchmarks in the existing Windows `debugoptimized`
preset, after the same 240-frame warmup:

| View | Previous CPU p50 / p95 | Updated CPU p50 / p95 | Updated paths compiled / uploads per median frame |
| --- | ---: | ---: | ---: |
| 1280 × 720 | 13.530 / 21.496 ms | 0.532 / 0.892 ms | 0 / 0 |
| 3840 × 2160 | 28.229 / 35.964 ms | 0.482 / 0.942 ms | 0 / 0 |

These measure retained CPU work with a native test host, not GPU time or total
game frame cost. An actual OpenGL screen profile measured 3.128 ms median
retained submission and a 16.661 ms median frame interval. Real startup runs
presented 14–19 frames, including 11–16 optional updates, with about 60–75 ms
total drawing time. Reduced Motion presented only the three remaining startup
stages (12.7 ms drawing in the measured Vulkan run). Work that has no safe
checkpoint still produces gaps: observed maxima were 329–412 ms. This is a
bounded improvement, not a guarantee of uninterrupted 30 fps or zero startup
cost on every device. Earlier startup, before the graphics device exists,
cannot show the initialization view.

Validation covers the native pacing and transform-cache checks, retained
screens through 4K, vector/mask tests, client and dedicated loading-pacifier
reentry tests, and generated-document consistency. Staged engine tests enter
Air Defense 1 in SP/OpenGL and Q4DM1 in MP/Vulkan with host input disabled.
Engine `screenshot` pairs change under animation on both renderers; Vulkan
Reduced Motion pairs are pixel-identical. There were no retained UI warnings
or runtime errors. The MP smoke still reports missing stock AAS variants and
late material/skin precaches; these are unrelated to initialization animation.
The native benchmark's existing JSON output also requires forward-slash input
paths on Windows because backslashes are emitted without JSON escaping.
Other platforms and visible-window GPU timings remain unqualified.

Logs, command lines, captures, runtime identities and measurements are retained
under `.tmp/initialization-animation/`. `ui_retainedTrace 1` now reports optional
`INITIALIZATION_UPDATE` frames and an `INITIALIZATION_PRESENTATION` summary of
frame count, total draw cost and largest gap without collecting host input.

## Legacy instruments and HUD submission (11 October 2026)

The radio and voice trace now samples the installed legacy waveform bitmap,
with the stock material's 21-interval vertical scale table and 0.6-width/second
horizontal scroll. It uses one stationary image quad with repeating UVs. The
ECG uses the same UV path for its installed Marine/Strogg textures. These are
runtime asset references; proprietary bitmap data is not included in Git.
Reduced Motion freezes the decorative radio/voice trace; the essential ECG
keeps its existing motion policy.

Icons already originate in editable SVG paths and become cached native meshes.
Loading those same shapes through another SVG renderer would not eliminate
tessellation, vertex submission or mask composition. Keep SVG as the authoring
format and reuse compiled geometry. Raster atlases remain a possible measured
tradeoff for especially expensive artwork, with density, memory and invalidation
costs; a blanket icon format replacement is not justified by current evidence.

A native isolation probe with full health/armor hides the two visible gauge
symbols while leaving the surrounding HUD intact. That removes three draws
and 1,672 Marine / 1,596 Strogg vertices; both versions compile zero paths per
warm frame. Three alternating repeats did not show a stable total CPU gain
beyond timing variation. This bounds these particular symbols' cost, not every
icon, GPU work, weapon selection, flashing or all density settings.

The runtime now reuses immutable mesh submissions and cached bounds. Stationary
masked vector panels can reuse their rendered pixels, with revisions, clips and
viewport changes invalidating the cache. Textured content is excluded from that
cache so time-varying materials cannot freeze. An additive image fully covering
one non-overlapping coverage mask can instead texture the mask's triangles
directly; other masks and alpha images retain the general compositor. Cached
target allowances account for every view sharing the host. Allocation pressure
can evict another view's idle cached pixels; references in the current frame
still prevent resizing their target. Native checks cover shared target pressure
and three 4K contexts sharing two cached targets while reserving scratch space.
Pending layers composite only their artwork's pixel bounds. The engine avoids redundant
target binds, preserving GUI batching and explicit backdrop flushes.

The adapter publishes changed application values while preserving atomic event
batches, case-insensitive state names, pending values and save/restore behavior.
Presentation-only documents skip unchanged layout work; controls, scrollbars,
modals and pointer interaction continue to update normally. CVar sampling visits
only CVar declarations, and animated UV changes avoid layout invalidation.
Empty focus no longer looks up the unnamed document and scans its canonical
tree. Hidden branches retain their current inline animation values without
invalidating visible layout; showing a branch resolves them before drawing.
The bundled RmlUi presentation update similarly defers `display:none`
descendants. This is an explicit opt-in limited to canonical presentation
documents; ordinary RmlUi, CSS animations and interactive widgets keep full
updates. The complete patch stack is checked against the original archive.

Qualification includes the complete native retained/screen/HUD suites and the
compiled production adapter tests, including failed publication retries and
pending state across events and saves. Native checks cover exact waveform
samples, wrapping, Reduced Motion restarts, masked holes/edges, opacity, resize,
partial-image fallback and cache invalidation. Gameplay timing and engine
render-target captures on OpenGL and Vulkan also qualify the installed bitmap:
six graph animation pairs change and six Reduced Motion graph regions remain
pixel-identical. The Air Defense 1 gauge capture preserves the centered layout
and the previous one-step 8-bit background-color tolerance against legacy.
Evidence is retained in `.tmp/ui-legacy-fidelity-perf/REPORT.md`; gameplay timing
is recorded there separately from these rendering checks.

The final Windows `debugoptimized` native benchmark reduced Marine frame work
from 0.644 to 0.147 ms, Strogg from 0.815 to 0.258 ms, and the MP overlay from
0.285 to 0.064 ms. These measurements exclude the engine and GPU; they describe
the combined working-tree candidate, including the concurrent transform-cache
improvement. A new SVG loader would not address the remaining engine cost.

The isolated, uncapped 1280×720 gameplay comparison used 8× MSAA, SMP disabled,
three ten-second windows per condition and one warmed process per scene:

| Scene / renderer | Legacy frame ms | New UI frame ms | Difference | New UI root CPU p50 ms |
| --- | ---: | ---: | ---: | ---: |
| Air Defense 1 SP / Vulkan | 2.98 | 3.58 | +0.60 | 0.380 |
| Q4DM1 MP / OpenGL | 3.80 | 5.05 | +1.25 | 0.474 |

Frame columns are medians of the three window means, not per-frame medians.
These results **do not meet negligible-overhead acceptance**. Root CPU excludes
later renderer/backend execution; the gap cannot be assigned wholly to icons
or layout. The final trace recorded zero SP layout updates per warmed frame
and 0.63 MP updates. Further profiling must separate remaining state/motion,
submission, backend and GPU work before choosing another rendering method.
The final OpenGL captures are 1280×720 and Vulkan captures are 2538×1312:
the requested 3840×2160 window was clamped, so this is not a 4K GPU qualification.
SP gameplay logged no warnings; MP retained the stock missing AAS variants,
`mp_buying_givecash` and late-precache warnings. Test-GUI documents also log
late precaches when loaded outside the level-loading path.

## Coverage atlases and presentation replay (11 October 2026)

The follow-up keeps the centered legacy gauge dimensions, saturation and installed
bitmap instruments. SVG-derived artwork still supplies the editable source. At
runtime, unchanged solid, whole-pixel coverage cells can share a nearest-filtered
RGBA8 atlas. This removes repeated vertex conversion/submission without changing
the cells' premultiplied colours or resampling their edges. Gradients, overlapping
cells, fractional coordinates, unsupported topology and oversized shapes keep
the original meshes. Overlap retains the GPU's original destination blending.
The atlas has at most 32 pages of 512×512 pixels (32 MiB each of CPU and GPU
storage). Live allocations never move; completely unused pages wait four host
frames before reuse. Rasterization also bounds visited-cell work. Named image
uploads preserve their sampler; the cinematic upload helper's linear/repeat
defaults must not replace the atlas's nearest/clamp sampling.

Canonical presentation documents record a bounded draw list after their layout
settles. Static meshes and valid cached layer composites replay directly. Bitmap
offset and scale values remain live: a scrolling ECG or radio waveform updates
the recorded sampling coordinates every frame. Geometry/style changes, document
replacement, resize, resource retirement and target eviction invalidate the
recording. Clipped/perspective image sampling, transient composition, backdrops,
live binding text and interactive documents keep the full rendering path. The
diagnostic CVars `ui_retainedAtlas` and `ui_retainedReplay` independently disable
these optimizations; neither is archived.

Hidden branches defer CSS writes while their canonical animation clocks continue.
Revealing a branch flushes the deferred values before layout. Fully transparent
canonical stacking contexts skip painting, and unchanged vector paint reuses its
last geometry and transform. Plain legacy text reuses glyph layout and batches
adjacent glyphs from the same material; live escapes still consult the host.

The GUI-root boundary now preserves batching when the target and actual viewport
are unchanged. The renderer API advances to 24 for the appended `BeginGuiRoot`
slot. Explicit `BindRenderTexture` calls retain their original flush/barrier
semantics, and cropped/editor/different-aspect paths retain required viewport
flushes. Stage matching renderer modules with the engine.

The implementation review also repairs same-frame legacy fallback when retained
rendering fails and reclaims obsolete, unleased target allocations under memory
pressure. Unuploaded atlas entries draw their original geometry until upload
succeeds. Isolated images and non-overlapping glyph runs apply opacity directly;
overlapping glyphs retain the compositor. CVar sampling allocates state changes
only for changed values, and the legacy HUD bridge caches normalization while
still publishing every application write. Its declared-key lookup now follows
the legacy dictionary's case-insensitive names. Native tests cover failed allocations, shared-view leases, resize,
hidden animation/reveal, replacement readbacks, static replay and live sampling.
The visible-window follow-up retains crosshair coverage quads through clipping
and replays unchanged captured HUD packets. Changed packets, failed preparation,
resizing and resource replacement invalidate that replay. Isolated opacity in
noninteractive presentations resolves only the affected element's filter.
Leaf text and images retain live opacity values in their recorded commands;
fades within (0,1) need neither style updates nor a document repaint. Disjoint
quads multiply their original premultiplied colours, avoiding cumulative rounding.
Overlapping text retains its completed composition target in the existing bounded
layer cache, after the same geometry has painted in an earlier host frame.
That admission delay allows a font's first GPU upload to finish; freezing its
first draw produced missing text on Vulkan. Images do not enter that text cache, so material animation stays
live. Zero/full-opacity transitions repaint, and changes to text, clipping,
geometry, resources or target leases invalidate reuse. Other isolated opacity
changes repaint without relaying out the document. Interactive/layout changes retain
the full update. Engine captures compare cached text against ordinary group
composition at six opacity levels with zero changed pixels on both OpenGL and
Vulkan. HUD geometry readbacks run after layout changes; hidden
animations retain resolved element handles. The legacy peer advances its
scripts, expressions and transitions through `RunTimeEvents`, with normal
layout restored immediately whenever Classic renders. Per-document CPU work is
now included in the root profiler.
Unchanged motion defaults avoid CSS formatting and use a hashed property index.
Forwarded HUD state also uses a transparent ASCII-case-insensitive hash lookup,
retaining the legacy dictionary's naming and event-write semantics.
Detailed runtime and per-draw stopwatches run only while `ui_retainedProfile`
requests timing. Ordinary gameplay retains work counters without querying the
clock for every draw. Native/tool hosts keep timing enabled by default, and the
runtime test verifies that disabling timing preserves the submitted geometry.
Prompt labels and glyphs refresh on binding/program writes, controller appearance
changes and resource/language reloads; older non-SDL input backends retain polling
because they do not publish keyboard-layout changes. The adapter tests cover
paired glyph updates, case-insensitive writes, deletion and controller changes.
Timing CSVs now append `frameBuildUs` and `frameSubmitUs`, splitting `cpuUs`
immediately before command submission. In serial mode submission includes backend
execution/presentation; in SMP mode it measures submission and waiting, not a
separate backend-thread interval.
Evidence and the final timing assessment belong in
`.tmp/ui-negligible-overhead/REPORT.md`. The earlier acceptance failure above is
historical evidence, not a claim that this follow-up has met the performance goal.

Final Windows captures show zero changed gauge pixels outside the live ECG
between the original meshes and optimized rendering, including MP over gray.
Decorative Strogg grain is held still for this comparison; unfrozen grain
changes between captures even with optimizations disabled. Radio/voice motion
and Reduced Motion pass on OpenGL/Vulkan for Marine, Strogg and MP.
The first atlas build removed 5,100 submitted vertices per MP frame and 3,240
per SP frame in the measured scenes. Earlier diagnostic medians were distorted
by shared 500 ms presentation stalls. A coordinated visible-window retry
removed those stalls and measured snapshot-average increases of 0.343 ms
SP/Vulkan and 0.570 ms MP/OpenGL. The logged `present` field was subsequently
confirmed to be a smoothed recent average, not a whole-window mean; earlier
whole-window labels were incorrect. These remain diagnostics, not acceptance.
`framePacingSnapshot` now also prints `Frame timing window` with sample count,
summed interval milliseconds and their arithmetic mean since `framePacingReset`.
The gameplay harness exports these separately as `pacingWindowSamples`,
`pacingWindowSpanMs` and `pacingWindowMeanMs`, without changing the live pacing
display or its existing fields. The old presentation stalls are no longer an
acceptance blocker. Final measured acceptance belongs in the evidence report.
The subsequent true-window checks still do not establish negligible overhead.
After the user paused background jobs, default-settings whole-window comparisons
add 0.049 ms in SP/Vulkan and 0.358 ms in MP/OpenGL. A further leaf-opacity
optimization avoids formatting CSS when the recorded filter already reads the
live value; the last installed CSS remains the comparison baseline for later
topology changes. Eight native suites pass. A sequential engine test revisits
an earlier alpha and crosses zero/full opacity without reloading the view:
all seven reference/optimized pairs match exactly on each graphics API (28
captures). This qualifies correctness, not a measured frame-time improvement.

The updated build's MP aggregate of +0.011 ms hides opposing ABBA block
differences (+0.364/-0.605 ms), so it is not accepted as negligible overhead.
Twelve shorter pairs add 0.683 ms, with all six blocks slower. Since switching
off destroys the retained HUD, a further check allows six seconds of settling
after each switch: MP still adds 0.218 ms (+4.93%), with block differences of
+0.035/+0.420 ms. No samples or stalls are discarded. The target remains open;
the user requested a pause after this validation pass. Test reservations are
released at the checkpoint. CPU frontend work remains the main investigation
direction; changing already-cached SVG icon sources does not remove that work.

## Hidden animation input reuse (13 October 2026)

Hidden presentation branches now retain their deferred-input status. Their
timelines keep advancing, while repeated state/value lookups and ancestor
visibility walks wait until a display or presentation change. Revealing a
branch applies its current values before layout; visible animation, input and
the installed legacy ECG/radio/voice bitmaps keep their existing behavior.
Native regression checks cover zero repeated hidden-property scans, current
and completed-value reveal, and document replacement. Eight optimized UI
suites pass.

The coordinated 1280x720, 8x MSAA, uncapped gameplay repeat uses four five-second
windows per condition, six seconds of settling and ABBA ordering. Whole-window
means include every interval. Q4DM1/OpenGL measures 3.371 ms legacy versus
3.459 ms retained (+2.60%); Air Defense 1/Vulkan measures 2.565 versus 2.640 ms
(+2.93%). MP root CPU p50 falls from 0.091 to 0.070 ms and actual animation
input scans from about 12 to 2 per frame. The baseline had substantial host
variation, so this does not isolate the whole-frame benefit of the small
runtime change. Reversing the condition order confirms 3.438 versus 3.587 ms
on MP/OpenGL (+4.32%) and 2.524 versus 2.569 ms on SP/Vulkan (+1.79%). Both
balanced orders therefore place the new UI within 1.8-4.3% of legacy in these
two scenes. This qualifies near-legacy performance on the tested Windows
machine, not zero overhead or other-platform performance. Each completed
candidate verifies that its runtime hashes remain unchanged throughout the run.

Fresh engine captures qualify the Marine, Strogg and multiplayer bitmap graphs
on OpenGL and Vulkan: all six animated pairs change and all six Reduced Motion
pairs remain identical. Native audio fixtures compile no paths after warm-up;
both visible MP voice displays add about 0.0032 ms of host CPU work. Live
microphone/network voice is outside this capture fixture. The coordinated scope
fix also preserves Vulkan dialog text with atlas caching and replay enabled.
Evidence and full settings are in `.tmp/ui-near-legacy-20261013/REPORT.md`.
This follow-up preserves the shipping legacy-UI default; the broader negligible
overhead requirement below remains open.

## Complementary renderer checks (13 October 2026)

The same staged build was then tested in single-player/OpenGL and
multiplayer/Vulkan, with the same 1280x720, MSAA 8, uncapped settings, 25-second
warm-up, six-second settling and four five-second windows per condition. Each
scene was repeated with the condition order reversed. Every interval contributes
to the means; no slow windows were discarded.

| Scene and condition order | Legacy ms | New UI ms | Difference |
| --- | ---: | ---: | ---: |
| Air Defense 1 SP / OpenGL, ABBA twice | 3.552 | 3.634 | +2.31% |
| Air Defense 1 SP / OpenGL, BAAB twice | 3.971 | 3.787 | -4.63% |
| Q4DM1 MP / Vulkan, ABBA twice | 2.480 | 2.521 | +1.66% |
| Q4DM1 MP / Vulkan, BAAB twice | 2.515 | 2.519 | +0.13% |

The reverse OpenGL run contains a pronounced legacy-side slowdown; the negative
difference is not evidence that the new UI is intrinsically faster. Vulkan's
individual balanced blocks also vary. These measurements support near parity in
the sampled gameplay, but cannot resolve an exact small overhead under this host
variation. The MP fixture is a solo listen server, not a populated match.

Retained root CPU p50 is 0.0567-0.0639 ms in SP and 0.0681-0.0858 ms in MP.
All four 300-frame profiles report zero layout rebuilds; actual animated-property
scans remain about one per SP frame and two per MP frame. Source polling,
property application and draw submission account for the remaining bounded work.
There is no additional dominant UI bottleneck demonstrated by these profiles,
so this follow-up makes no runtime or content changes. Engine screenshots confirm
the expected HUD gauges and crosshair in both combinations. All four runs use
identical runtime hashes, unchanged during sampling and matching the staged build.
Logs, full settings, per-window results and captures are recorded in
`.tmp/ui-cross-api-20261013/REPORT.md`.

## Menu and gameplay optimization (13 October 2026)

Interactive screens now retain separate trees containing controls, modals and
their ancestors. Eligibility and modal visibility no longer scan decorative
artwork or rebuild the full element index every frame. Ancestor visibility,
pointer eligibility, mask bounds and modal ordering keep their existing rules;
document replacement and shutdown retire the cached handles.

The coverage atlas now splits wide or tall stationary vector meshes into tiles.
It keeps the existing 32 pages of 512x512 RGBA8 storage (32 MiB each of CPU and
GPU pixel storage), nearest sampling and identity padding. Empty tiles and
unused tile borders are omitted, including a check that preserves additive RGB
with zero alpha. Multiply artwork uses white RGBA for empty pixels and padding,
with its original destination-colour blend. Both blend modes share the same
bounded pages. A mesh
uses the original geometry until every required page upload succeeds; partial
allocation failure releases all of its tile references. Fractional motion,
gradients, overlap and oversized bounds retain the geometry path. Temporary
rasterization is independently capped at four million pixels, so widely
separated small shapes cannot allocate an unbounded bitmap.

Single cached coverage meshes can apply live isolated opacity directly. Stable
compound plates retain their completed target so an overlapping fill and rail
still receive group opacity once. New cache entries must have survived an
earlier presentation frame; animated masks cannot evict the current working set.

Changing analytic masks can also sample unchanged source artwork from that
bounded layer pool. The source is immutable while the mask and group opacity
remain live; `ui_retainedSourceCache 0` selects the original composition path.
Same-frame animated-mask comparisons on OpenGL and Vulkan at MSAA 8 differ
by at most one RGBA8 code value. Exact identity transforms share the null
transform's geometry key. Affine basis vectors are transformed as directions,
avoiding precision loss from subtracting translated float positions. Compilation
reuse across small transform noise is limited to less than 1/1024 pixel over
the complete compiled region, including artwork outside its authored box.

Quiet canonical menus skip layout when no visible value editor or scrollbar
needs a native update. Interaction, focus reveal and owned-widget settling still
run. Hidden widgets resume ordinary updates when shown. Dense analytic coverage
uses row bins and small per-row sorts; sparse, widely separated contours retain
the bounded comparison sort. The same coverage integration and paint rules
remain in use.

Single-player pause screens retain the unchanged 3D scene after two consecutive
stable presentation frames. The HUD, view effects and menu timelines continue
to render. Resuming, a changed view or simulation time, a presentation gap,
resize, video restart and special vision paths invalidate the scene. The
unarchived `ui_retainedPauseCache 0` diagnostic restores ordinary scene drawing.
Engine and game modules must be rebuilt and staged together (game API 52).
Reused pause scenes also skip redundant entity and weapon pose preparation.
The separable soft-focus shader pairs adjacent Gaussian taps where possible
and computes successive weights by recurrence. Wider kernels retain their
original sample spacing.

The root profiler includes CPU and frame-interval p99/maximum values and vector
compile/upload times. `ui_retainedGeometry` lists active meshes, revisions and
atlas residency. Native coverage and production-adapter checks cover tile
boundaries, padding for both blends, sparse/additive tiles, upload failure/retry,
revision retirement and exhaustion of the page limit. Native tests also cover
compound alpha, quiet-button feedback and pause-scene invalidation.

On this Windows host, the 1,200-frame native title benchmark's median falls
from 0.508 to 0.384 ms after row binning and button-layout changes; median path
compilation falls from 0.275 to 0.188 ms. Trimming atlas tiles lets the paused
HUD and menu retain about 83,000 of 86,000 submitted vertices, up from about
54,000, within the same page limit. In 300-frame OpenGL and Vulkan profiles,
retained pause-root CPU p50 falls from about 0.5 to 0.26 ms. Whole-frame timing
varies substantially between runs, so these are diagnostic checkpoints rather
than final parity acceptance.

Engine captures on both APIs at 1280x720 qualify title/pause, focus and modal
composition with caches disabled, enabled and disabled again. Vulkan title
captures match exactly; other differences are isolated one-code-value rounding.
Pause-cache checks also cover cold startup, video restart, resume and reopening.
Shader-source A/B/A captures qualify the blur against its original kernel.
Evidence is under `.tmp/ui-runtime-optimization/`. Gameplay was within about
8% of legacy before these menu changes; final gameplay repeats and title/pause
whole-window parity remain open. The user explicitly included both menus in
the acceptance scope.

The subsequent balanced four-window menu comparison keeps all frame intervals
and stalls, with six seconds of settling and five seconds per window. Staged
runtime hashes match the optimized build and remain unchanged during each run:

| Scene / renderer | Legacy ms | Retained ms |
| --- | ---: | ---: |
| Title / OpenGL | 0.676 | 1.453 |
| Pause / OpenGL | 0.670 | 1.355 |
| Title / Vulkan | 0.405 | 1.179 |
| Pause / Vulkan | 0.400 | 0.798 |

The remaining menu gap is substantial. A separate source-cache toggle comparison
reduces title time by about 8% on OpenGL; Vulkan differs by about +2%, within
the variation of this run, so no Vulkan whole-frame gain is established.
Settled interactive screens now replay their paint commands, including fresh
backdrop capture. Transient targets are reserved and cached leases validated
before replay draws to the destination. Atlas opacity draws have a read-only
residency check, so a disabled, resized or dirty atlas returns to traversal
before any partial frame is painted. Visible native value widgets continue
their ordinary update path. Unchanged button geometry also avoids repeated
focus/hit-bound walks; input, bound state, layout and visibility changes refresh
it. Native tests cover stationary hover, moving/disabled controls, a changing
background under replayed blur, resize and unsupported-host fallback. Eight
UI suites pass, including focus, popup, scrollbar, number, HUD and view effects.

This combined change reduces pause-root CPU p50 to 0.080 ms on OpenGL and
0.069 ms on Vulkan. Balanced pause whole-window means are 1.095 versus 0.697 ms
legacy on OpenGL, and 0.684 versus 0.409 ms legacy on Vulkan. The animated title
still adds substantial work (1.519 versus 0.666 ms OpenGL; 1.266 versus 0.479 ms
Vulkan). The latter run includes pronounced host variation; all intervals
remain included. Menu parity is still unqualified. Engine capture A/B/A checks
pass on both APIs at 1280x720, and the preceding replay change also passes at
720x1280, with exact or isolated one-code-value differences.

The matching pre-replay gameplay repeat places Air Defense 1 within 3.04%
(OpenGL) and 1.35% (Vulkan) of legacy, and solo Q4DM1 within 3.09% and 1.51%.
Each uses four five-second windows per condition and six seconds of settling,
with staged build hashes unchanged throughout. The shorter replay/interaction
recheck measures +3.58%/+3.79% for Air Defense 1 and +7.82%/+1.41% for Q4DM1
(OpenGL/Vulkan). A slower OpenGL MP window remains included. The experiment
with eight 1024-square atlas pages is rejected: within the same 32 MiB budget,
page fragmentation leaves substantially more pause geometry uncached. The
qualified atlas remains 32 pages of 512 square pixels.

Moving convex three/four-sided linear-alpha masks now have a material shader
path. It intersects the shape with each physical pixel and samples cached
artwork through that coverage, eliminating the title glint's per-frame vector
compilation and upload. Stationary masks retain their caches; unsupported
geometry, strokes, stop values and hosts use ordinary coverage. Mask snapshots
remain immutable, clipping stays in physical pixels, and source targets are
never modified. `ui_retainedLinearMasks 0` disables this path for comparison.
Native checks exercise reflected/sheared transforms, source-cache on/off,
overlapping artwork, live opacity, resize and feature fallback. Nine UI suites
pass. Engine captures compare CPU and shader masks at the same animation time
on both APIs, including four-sided masks and video restart; all differ by at
most one colour code value.

A balanced feature-only title comparison measures 1.539 to 1.000 ms on OpenGL
and 1.255 to 0.574 ms on Vulkan. Root CPU p50 falls to 0.174/0.183 ms, and vector
compilation/upload counts are zero during the profile. These compare the
retained path with its optimization off/on; they do not establish parity with
legacy. The next comparison must again include legacy title and pause screens.

Decorative transforms outside control/modal ancestry now resolve their paint
properties without a full layout update. Moving controls still update layout
and hit bounds. The focused native fixture and all nine UI suites pass.
Sharp four-pixel mask ramps revealed two additional correctness requirements:
subdivided CPU masks must keep their single-sample target under window MSAA,
and Vulkan GUI uploads must ignore pointer-only memos whose cache headers may
have been recycled during an in-progress presentation. World depth/light-pass
and GPU-skinning reuse remain intact. Production-function adapter tests cover
that distinction. Clean SMP 1 / MSAA 8 captures of CPU/shader mask transitions
and video restart pass on both APIs with at most one colour-value difference.

The subsequent `linear-transform-menu-ab` comparison includes legacy again:

| Scene / renderer | Legacy ms | Retained ms |
| --- | ---: | ---: |
| Title / OpenGL | 0.724 | 0.938 |
| Pause / OpenGL | 0.680 | 1.083 |
| Title / Vulkan | 0.409 | 0.525 |
| Pause / Vulkan | 0.405 | 0.640 |

All runtime hashes stay unchanged. Title vector compilation/upload remains
zero; root CPU p50 is 0.143/0.161 ms for title and 0.077/0.066 ms for pause
(OpenGL/Vulkan). These are improvements, but menu parity remains open.

A subsequent atlas change groups sixteen independent 512-square pages into
each 2048-square image. Allocation and four-frame retirement still use 32
separate page slots, and the GPU cap stays 32 MiB; a dirty upload temporarily
assembles 16 MiB. Failure/retry and recycling preserve live neighbouring pages.
API draw counts drop from 73 to 40 for title and 96 to 59 for pause with the
same atlas residency. Both APIs pass cached/uncached title, pause, focus and
modal captures at SMP 1 / MSAA 8, and exercise video restart. The timings vary
too much to establish a stable cross-renderer gain from this change alone.

Decorative transforms now use RmlUi's typed primitives directly. Native tests
compare them with independently parsed CSS at densities 1, 1.5 and 2, with
DP/PX translation, reflected/nonuniform scaling, rotation and snapshot restore.
Sharp mask captures also pass on both APIs. With the shipped metric settings
(renderer metrics 0, whole-frame GPU timing 1) during balanced windows, the
combined candidate measures:

| Scene / renderer | Legacy ms | Retained ms |
| --- | ---: | ---: |
| Title / OpenGL | 0.601 | 0.732 |
| Pause / OpenGL | 0.652 | 0.997 |
| Title / Vulkan | 0.359 | 0.431 |
| Pause / Vulkan | 0.363 | 0.620 |

Detailed profiling runs separately after those windows. Title root CPU p50 is
0.106/0.091 ms. Earlier runs enabled per-pass metrics throughout; their timing
overhead accounts for only part of the gap. Both menus remain above legacy.

A settled opaque blur covering the complete viewport now finishes its second
pass on the base surface, avoiding a temporary destination and final composite.
The live backdrop is still captured every frame. Partial, translucent, streak
and unsupported cases retain their layered path; `ui_retainedDirectBackdrop 0`
selects that reference. Native tests and production-adapter checks cover those
guards. Engine captures pass on both APIs at 1280x720 and 720x1280, including
focus, modal and video restart with SMP 1 / MSAA 8. Portrait comparisons are
exact; wide differences are isolated one-value pixels. Default-metric pause
means are 0.544/0.684 ms for legacy/retained on OpenGL and 0.344/0.552 ms on
Vulkan, so menu parity remains open.

Decorative-only projection now also avoids refreshing unrelated control hit
bounds; native coverage keeps moving controls and modal ancestry live. The
convex-mask shader skips pixel clipping for wholly contained/outside pixels,
with CPU/shader sharp-mask comparisons still within one colour value on both
APIs. Moving blur weights to vertices and grouping disjoint host draws were
tested and rejected because neither established a useful frame-time gain.

`ui_retainedHalfBlur` filters each axis before reducing that axis for opaque,
direct full-view 6–8 pixel kernels. Its horizontal target keeps every source
row; the vertical pass then halves height, followed by a linear resolve. A
half-centred kernel averages two original Gaussian kernels before pairing
samples, avoiding the high-frequency aliasing of integer-centred pairs at this
sampling phase. Other kernel widths, odd sizes, offsets and partial/layered
effects retain the full-resolution path. Every frame still captures live
content. Resource, resize and fallback guards are covered by the host adapter.

The upsample is a spatial approximation. Wide production title, pause, focus
and modal comparisons differ by at most one colour value; portrait fallback
comparisons are exact. Both APIs exercise SMP 1, MSAA 8 and video restart.
Full-view stripe, step and colour-grid fixtures at widths 6, 7.5 and 8 produce
identical reference-return captures; candidate differences reach 4–5 values at
edges with mean absolute error below 0.3/255. Separate GPU diagnostic medians
fall from 277 to 173 microseconds on Vulkan and 434 to 365 on OpenGL. Default
whole-frame feature comparisons improve only about 3%, with retained variation;
this is not menu parity. Evidence is under
`.tmp/ui-runtime-optimization/reduced-blur-{filtered,patterns,portrait}` and
`reduced-blur-feature-default`.

Ordinary single-player pause now holds the presentation scene clock at the
authoritative game time. Previously its drift correction periodically restarted
interpolation despite a stopped simulation, moving the camera back toward the
previous pose and invalidating the scene cache. HUD/menu animation keeps its
independent clock. Native tests cover a long pause, resume, multiplayer and demo
behavior. Cache/reference engine captures without `g_stopTime` pass on both
APIs with SMP 1 / MSAA 8, video restart and resume/reopen; differences are
isolated one-value HUD pixels. The eleven UI/material suites pass.

The `menu-live-clock` comparison uses ordinary pause, rather than a diagnostic
simulation stop. Vulkan title means are 0.346/0.367 ms (legacy/retained), but
pause remains 0.348/0.563 ms. OpenGL title is 0.690/0.849 ms with large window
variation, and pause is 0.621/0.952 ms. These runs do not establish menu parity.

`ui_retainedHudStateCache` skips an identical stock HUD expression walk at the
same simulation time while a working Remastered peer owns drawing. It compares
the complete dictionary's pooled immutable entries, including direct dictionary
writes, and invalidates for timed scripts, input/named events, activation,
presentation writes, reload/restore and Classic fallback. Explicit redraw and
GUI editing/script diagnostics bypass it. The cached dictionary is never saved.
HUD drawing and animation continue on their original clocks. Production-method
tests cover repeated publications, mutations, clock changes and bypasses.
Both APIs pass ordinary pause, restart and resume/reopen captures within one
value in isolated HUD pixels. Feature-only pause means improve from
0.553 to 0.486 ms on Vulkan and 0.940 to 0.873 ms on OpenGL. Whole-menu parity
still needs to be established against legacy with the final candidate.

## Final candidate checks (14 October 2026)

The final candidate also reduces repeated GUI number publication. Integral
floats keep their original six-decimal dictionary representation, including
negative zero; fractional, large and exceptional values retain the original
formatter. Integer publication uses a locale-independent integer conversion.
Fixed cinematic rectangle keys no longer need formatting each frame. Unchanged
stock dictionary values keep their pooled storage, but every application write
still reaches the replacement so it can override an intervening UI event.
Debug logging retains its old-value checks only while that logging is enabled.
The native fixture compares 65,536 float bit patterns with the original
formatter; the production-method adapter covers publication, direct dictionary
mutation and event overrides. All eleven UI/material suites and the five
renderer/HUD adapters pass after the final source changes.

Classic presentation lights now receive the same held scene clock as the
camera and entity poses during an ordinary single-player pause. This avoids
retiring or fading lights behind the reused view. Multiplayer retains its
original presentation path.

A separate flattened-menu surface experiment was removed. Its final isolated
pause comparison improved Vulkan by about 5% and OpenGL by about 1.5%, while
adding a render target, invalidation machinery and up to five colour values of
composition rounding. The existing bounded artwork caches and command replay
remain. Prototype measurements with `ui_retainedFrameCache 1` do not describe
the final candidate, and that experimental CVar is no longer registered.

The refreshed `menu-qualified-final` comparison uses normal animation, ordinary
pause, default GPU timers, detailed renderer metrics off, MSAA 8 and SMP 0 at
1280x720. Each uncapped condition has four five-second windows in ABBAABBA
order; 144/240 Hz each have two per condition. No slow windows were discarded.
The staged binary hashes match the optimized build and remain unchanged.

| Scene | Legacy uncapped mean ms | Retained uncapped mean ms | Difference |
| --- | ---: | ---: | ---: |
| Vulkan title | 0.367735 | 0.378361 | +2.89% |
| Vulkan pause | 0.346451 | 0.483137 | +39.45% |
| OpenGL title | 0.602364 | 0.708452 | +17.61% |
| OpenGL pause | 0.600295 | 0.867025 | +44.43% |

At 144 Hz, all four mean comparisons differ by at most 0.021%; at the default
240 Hz, at most 0.293%. Both conditions' p99 is 8–9 ms at 144 Hz and 6 ms at
240 Hz. One retained OpenGL title window includes a 22 ms maximum; it is kept
in the result. These caps give comparable observed pacing on this hardware,
but do not erase the uncapped overhead. **The requested title/pause parity gate
remains open.** Final engine title/pause captures were inspected on both APIs.

Separate diagnostics, with detailed renderer metrics enabled, put title GPU
medians below legacy on both APIs (OpenGL 219/252 us; Vulkan 101/119 us,
retained/legacy). Pause remains higher (353/243 us; 173/113 us). Title therefore
still warrants CPU/submission investigation, particularly on OpenGL; pause has
both additional HUD/front-end work and soft-focus GPU work. These diagnostic
samples must not be substituted for the whole-window frame-time measurements.

The refreshed uncapped gameplay windows (`gameplay-final-numbers`) give:

| Scene | Legacy mean ms | Retained mean ms | Difference |
| --- | ---: | ---: | ---: |
| OpenGL Air Defense 1 | 4.098225 | 3.936005 | -3.96% |
| Vulkan Air Defense 1 | 2.421579 | 2.532122 | +4.56% |
| OpenGL Q4DM1 | 3.345477 | 3.449113 | +3.10% |
| Vulkan Q4DM1 | 2.265403 | 2.674543 | +18.06% |
| Vulkan Q4DM1, reverse order | 2.280696 | 2.265670 | -0.66% |

The apparent OpenGL SP gain is within substantial window variation. Vulkan MP
had one retained window at 3.323 ms while all legacy windows stayed around
2.27 ms; the reverse-order repeat stayed close throughout. Both runs remain
in the evidence. Three cases support the earlier near-legacy gameplay finding;
Vulkan MP's variation prevents a precise new overhead claim from this sample.
These are warmed static cameras and a solo MP fixture, not a loaded server or
other-hardware qualification.

Final ordinary-pause, video restart and resume/reopen captures with SMP 1 and
MSAA 8 pass on both APIs (`pause-final-numbers`): at most one colour value in
246 HUD pixels, also present in reference-return comparisons. After the timing
runs, review removed an extra dictionary lookup that could read a freed key
when that key was supplied by the overwritten value. The production adapter
now models separate key/value pools and covers that alias. The rebuilt HUD and
screen suites pass; this narrow correctness fix is subsequent to the timed
binary identities recorded above. The final staged SP/Classic-switch smoke
also passes on both renderers with matching build/stage hashes and no retained
warnings or errors (`publication-review-smoke`).

## Moving mask and crossfade replay (14 October 2026)

The title's counter-rotating glint can now replay its stationary source while
refreshing the analytic mask. Replay first validates the complete projected
artwork, clip and source-cache lease; geometry changes, unsupported paint or
lost resources use the ordinary traversal. This stays under the existing
`ui_retainedReplay` switch. Eight live mask poses, reference returns and video
restart produce identical RGB pixels on both APIs with SMP 1 / MSAA 8
(`mask-replay-visual`). Native coverage also exercises changing opacity,
resizing and disabling the analytic-mask host path.

Four-window feature comparisons (`mask-replay-feature`) give 0.737702 versus
0.663832 ms on OpenGL and 0.380998 versus 0.367069 ms on Vulkan with replay
off/on. Both include their slower windows; these are feature comparisons,
not a fresh legacy-parity result. A separate recorded-draw ordering experiment
was removed: OpenGL gains were inconsistent and a Vulkan candidate window
slowed substantially. Its results remain in `record-order-feature`.

Fitted leaf images now support the same isolated-opacity replay as scrolling
images. The title montage uses opacity for its white-tinted fades, preserving
the authored timings. Decorative leaves beside buttons avoid a menu layout
walk; interactive ancestry, owned widgets and compound groups retain normal
style preparation. Native tests compare replayed and normal draws through
zero/full-opacity crossings and verify that hover and control updates remain
correct. Twelve same-frame reference/candidate captures per API are RGB-exact,
including video restart (`menu-fade-qualified`). Two expected late-preload
notices belong to the private preview's stock materials and are retained in
the reports; there are no other retained warnings or runtime errors.

All eleven UI/material suites pass in `test-menu-fades-relink.log`. Earlier
widget crashes in this increment were traced to stale Host-interface objects:
restoring a rejected experiment also restored old header timestamps. Rebuilding
all interface dependents resolves those failures; they are not waived. The
updated combined candidate is staged and compared in `menu-fades-comparison`.
Each uncapped condition has four five-second windows with four-second settling,
normal motion, MSAA 8 and SMP 0. The affected uncertain cases also have four
windows per condition in the opposite order (`menu-fades-reverse`).

| Scene/order | Legacy mean ms | Retained mean ms | Difference |
| --- | ---: | ---: | ---: |
| Vulkan title, ABBAABBA | 0.348621 | 0.352338 | +1.07% |
| OpenGL title, ABBAABBA | 0.587101 | 0.686237 | +16.89% |
| OpenGL title, BAABBAAB | 0.602469 | 0.662329 | +9.94% |
| OpenGL pause, ABBAABBA | 0.614057 | 0.917462 | +49.41% |
| Vulkan pause, ABBAABBA | 0.518419 | 0.511126 | -1.41% |
| Vulkan pause, BAABBAAB | 0.344365 | 0.481389 | +39.79% |

Vulkan pause's first order includes a 0.926770 ms legacy window, versus its
other legacy windows at 0.363564–0.413072 ms. It is retained in the mean, but
that run cannot establish parity. The opposite order is stable and confirms
the remaining pause overhead. No cause for the isolated slow window has been
established. OpenGL title's retained root p50 is now 0.0506 ms, with zero layout
updates and one replay per frame in the sampled 300 frames; whole-frame
OpenGL title remains 10–17% above legacy across these two orders. **The menu
parity gate remains open.**

A shader-only constant Gaussian-weight experiment was also rejected. Its
OpenGL original/candidate means were 0.908385/0.901855 ms, and Vulkan
0.476746/0.505918 ms. Separate GPU medians did not improve consistently. The
experiment changed only private test-profile shader overrides and was never
incorporated in the staged package (`constant-blur-feature`).

The combined candidate also passes ordinary pause, video restart, resume and
reopen on both renderers with SMP 1 / MSAA 8 (`pause-menu-fades`). Compared
captures differ by at most one colour value in 244 OpenGL / 210 Vulkan HUD
pixels, including reference-return variation. Current paused and resumed
engine captures were visually inspected.

A subsequent dirty-backdrop cache was rejected. Exact queued-2D comparisons
localized the live ECG and allowed partial blur updates. Cropping its source
draws reduced Vulkan diagnostic GPU duration to about 85 microseconds from
173, but whole-window means worsened from 0.486059 to 0.521626 ms (+7.32%).
OpenGL's apparent 3.44% gain depended on a slow baseline window, and its
candidate GPU medians were higher. Its native admission/cropping adapter and
OpenGL pause/resize/restart/resume captures passed; Vulkan pixel qualification
was not run after the timing rejection. All prototype changes are removed;
`backdrop-cache-rejection.json` and `rejected-backdrop-cache/` preserve the
results and implementation. This does not change the accepted parity findings.

## Large documents

5 October 2026. The multiplayer Escape card (`mp_escape.q4ui`) is the largest
retained document: 7.6 MB, 4,499 nodes, 366 controls, 2,173 bindings, 1,925
timelines with 5,240 tracks and 34,395 authored properties. The game loads it
with every multiplayer map, and on a debugoptimized build its load took
8-12 s and each frame half a second, because several steps did work
proportional to the whole document once per node, binding, track or changed
property:

- **Node and element lookup.** `DocumentModel::FindNode` searched the tree and
  RmlUi's `GetElementById` searches the whole document breadth-first. A load
  configured each node with two searches and the value view resolved every
  node with one; each frame resolved every changed property, every control's
  bounds and every focus query the same way. A validated document's model now
  indexes its node IDs (a copy starts unindexed and searches), and the runtime
  resolves each canonical node's element once per load into a map that lives
  as long as the document. Canonical elements never change while it is open:
  text nodes own no canonical children, and a choice popup moves under the
  document but lives on. The value view and number fields take the same
  lookup.
- **Validation.** Each binding was checked against every timeline track, and
  each widget control against every binding and track. Both now look the
  owned (node, property) pairs up in sets built once.
- **Applied properties.** A new state revision made `ApplyMotion` format all
  34,395 properties again. Only the properties bindings own can change with
  the state, so the rest keep their fast path.
- **Modals and eligibility.** The modal check visited every node on every
  state read and binding pass; it now visits only the nodes on a path from the
  root to an authored modal. Input eligibility records only controls and skips
  the subtree under an ineligible node, whose controls read as ineligible.
- **State reads.** Each frame's read of the CVar sources copied the whole
  state; it now copies it only when a source has changed.
- **Transactional copies.** Events and completion programs evaluate on copies
  of the state and motion. The document's timelines, authored values,
  declarations and bindings never change after a load, so copies share them
  and duplicate only live values.
- **Playing tracks.** Every play first advanced every playing track, so the
  hundreds of control feedback timelines started at load sampled one another
  quadratically. Sampling again at the same clock reproduces the same values,
  so a burst of plays at one clock samples once; a presentation write or a
  restore still forces a fresh sample.

`openq4-retained-ui-benchmark --screen` now also reports `load_ms`, the
runtime's document load. One machine (Windows 11, debugoptimized), the
committed runtime (`dde802ef`) against this change, three runs each, 240
frames at 1280x720 after the four-second settle; medians:

| Document | Load before | Load after | Frame p50 before | Frame p50 after | Frame p95 before | Frame p95 after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `mp_escape.q4ui` | 9,484 ms | 624 ms | 504.0 ms | 13.4 ms | 764.3 ms | 61.0 ms |
| `mp_welcome.q4ui` | 231 ms | 117 ms | 4.50 ms | 0.73 ms | 5.25 ms | 0.85 ms |
| `title.q4ui` | 80 ms | 78 ms | 0.96 ms | 0.67 ms | 1.12 ms | 0.88 ms |
| `pause.q4ui` | 70 ms | 63 ms | 1.12 ms | 0.29 ms | 1.23 ms | 0.36 ms |

The native screens test, which loads the Escape card four times, fell from
104-187 s to 42 s. The canvas suite (`ui_document_canvas.py`) and its 30
mutations, the native suite and the script tests that read these sources pass.

What remains: parsing the 7.6 MB source and reading its nodes take most of the
load, the Escape card's frame was mostly the presentation pass over its values
(see [Settled frames](#settled-frames)), and
each event or completion program still copies the motion and state's live
values: up to 100 ms on the Escape card's page and modal changes in the
native screens test.

## Settled frames

8 October 2026. Main-thread stack samples of the screen benchmark on the
Escape card (cdb, 30 samples) put about two thirds of a settled frame in
`Runtime::Impl::ApplyMotion` and most of the rest in `ValueControlView::Paint`,
not in RmlUi's layout. Every frame the presentation pass walked all 34,395
authored values, comparing each against the input it last applied: two string
compares per key, and the 1,269 text values translated and looked up again.

`Motion` now stamps every write that can change its values (a sample, a play,
a cancel, a reduced-motion jump, an external write, a restore, a reset) from a
counter shared by all copies, so an unchanged stamp means unchanged values.
`ApplyMotion` returns at once while the stamp, the state revision and the text
ratio are those of its last complete pass; a language change reloads the
document. A pass that finds an element missing leaves the next pass complete.
`RuntimeStatistics::motionInputsScanned` counts the values a frame's passes
walk, and the native screens test pins it at zero on a settled Load Game page
and above zero after a state change. Documents with a looping timeline, such
as the title's montage and glint, still walk their values each frame.

Same machine and build type as above, 60 frames at 1280x720 after the settle:

| Document | Frame p50 before | Frame p50 after | Update p50 before | Update p50 after |
| --- | ---: | ---: | ---: | ---: |
| `mp_escape.q4ui` | 14.21 ms | 5.85 ms | 13.44 ms | 5.07 ms |
| `mp_welcome.q4ui` | 0.82 ms | 0.28 ms | 0.71 ms | 0.18 ms |
| `joingame.q4ui` | 1.89 ms | 0.50 ms | – | 0.25 ms |
| `createserver.q4ui` | 1.66 ms | 0.89 ms | – | 0.61 ms |
| `loadgame.q4ui` | 0.41 ms | 0.17 ms | – | 0.08 ms |
| `pause.q4ui` | 0.39 ms | 0.16 ms | – | 0.07 ms |
| `title.q4ui` | 1.09 ms | 1.02 ms | – | 0.37 ms |

What remained on the Escape card was `ValueControlView::Paint`, which
reasserted every choice option's label, availability and display each frame
through string-keyed lookups and RML readbacks (`GetInnerRML`).

### Settled lists

The runtime now counts `ApplyMotion`'s passes that can write presentation
and hands the count to `ValueControlView::Paint`. A closed list whose
readback (value, labels, availability and option count) equals the one its
last paint applied in the same pass is left as painted: nothing else writes
its rows. An open list, a changed readback or a new pass paints in full, and
a count of 0 keeps the old behaviour. A document whose timelines loop, such
as the title, starts a pass every frame, so its lists would still paint in
full; Join Game and the title have none.

Interleaved A/B, the same build with and without the skip, alternating runs,
median frame p50 of five runs of 60 frames at 1280x720 (debugoptimized). The
machine ran lighter than for the table above, where the Escape card measured
5.85 ms:

| Document | Without | With |
| --- | ---: | ---: |
| `mp_escape.q4ui` | 2.13 ms | 0.67 ms |
| `createserver.q4ui` | 0.91 ms | 0.62 ms |
| `mp_welcome.q4ui` | 0.26 ms | 0.18 ms |
| `joingame.q4ui` | 0.52 ms | 0.51 ms |
| `title.q4ui` | 1.10 ms | 1.00 ms |

## Startup preload

9 October 2026. With `ui_retained 1` the title waited while the session
loaded every retained page it might hand off to and precached every
multiplayer map's levelshot (`idSessionLocal::PreloadRetainedScreens`, inside
`idSessionLocal::Init`), then every Arena match's (`idArenaCampaign::Init`).
Timestamped startups (`com_timestampPrints 2`) of a build with temporary laps
around each step split the twelve pages' loads; medians of three, on a
debugoptimized build, where the laps add some cost of their own:

| Step, over the twelve pages | Time |
| --- | ---: |
| The GUI's parse and validation of the document | 1,989 ms |
| The view's load: the runtime parsed and validated the same document again, then built its markup, elements and bindings | 2,691 ms |
| The GUI's application values and first state | 1,307 ms |
| The 50 multiplayer levelshots | 338 ms |

Join Game (1,390 ms), Create Server (794 ms) and Demos (630 ms) were the
largest pages. The levelshots had cost 1.7 s while community maps' were
extracted again on every launch, which `a82b13ab` stopped. The Arena's 20
match levelshots, largely the multiplayer maps' pictures, took another
0.3 s after those, or 0.65 s once they no longer loaded first.

What changed:

- **One parse per load.** A `Document` copy now shares its parsed source and
  model: a load or an edit replaces the parsed document and never changes
  it. The GUI hands its validated document to its view
  (`RetainedUI_LoadParsedView`, `Runtime::LoadDocument( const Document& )`),
  so each page is parsed once. Every later load gains too: the pages a level
  loads, and the reload of every GUI at each map change.
- **Cheaper validation.** A check builds its pointer and message only when it
  fails (`Require` became a macro over `Fail`). The finiteness walk builds no
  pointers and finds the failing value's pointer only on failure; field
  checks read member names in place instead of copying them; the
  per-command and per-control lookup tables are built once. Diagnostics are
  unchanged: the native document tests compare pointers and messages. The
  runtime's own load of the twelve pages, which includes its parse, fell
  from 1,882 to 1,228 ms (`openq4-retained-ui-benchmark --screen`
  `load_ms`, interleaved, five runs each).
- **Parsing on the job system's workers.** Before the stock main menu loads,
  the session reads the startup documents and queues one parse each on the
  job system (`PrefetchRetainedScreens`, `UI_RetainedPrefetchDocuments`). A
  page's load takes its parse when the source is unchanged, waiting for it
  if it is still running, and keeps only the markup, element and binding
  work on the main thread. Parses no load took are dropped after the
  preload. A synchronous job system (`jobs_enable 0`, `jobs_deterministic 1`)
  or a full job queue leaves the load to parse inline, as before.
- **Only what the title reaches.** Startup loads the title, Load Game,
  Credits, Demos, Arena, Multiplayer, Create Server and Join Game. The pause
  screens, the pages only they reach (Save Game, Restart Level) and the
  death screen load with the first single-player level
  (`PrepareRetainedLevel`), once a session, as the Strogg pause already did.
- **Levelshots on idle frames.** Startup lists the multiplayer maps and the
  Arena matches (`QueueRetainedLevelshot`). Once a front-end menu has
  presented for a second, each frame precaches as many of their levelshots
  as fit 4 ms, at least one, as precaches rather than late loads
  (`PrecacheRetainedLevelshots`). Create Server reads any map levelshot
  still waiting when it opens, and the Arena page any match levelshot, so
  browsing either never loads one. A level in play holds the queue until the
  front end returns, and an engine reload, already a load, reads it at once.
  `ui_retainedTrace 1` logs each step (`RETAINED_LEVELSHOTS`).

Two interleaved A/Bs against the build before this work (`03ddba97`), each of
eight rounds: hidden 1280x720 OpenGL window, `s_noSound 1`, debugoptimized,
each side with its own warm save path, every launch quitting from its
autoexec. All sides read the same `pak0.pk4` (the older copies' embedded
checksum was patched to it), so they load identical documents. The first
rotated the order of three builds to separate the steps; the second
alternated the final build with the baseline. The first title frame is timed
from the log's opening at process start. Medians:

| Build | First title frame | Session initialization | Pages loaded at startup |
| --- | ---: | ---: | ---: |
| Before | 14.2 s | 6.9 s | 12 |
| One parse, cheaper validation, level pages and multiplayer levelshots deferred | 9.5 s | 3.3 s | 8 |
| The same, parsing on workers | 9.2 s | 2.7 s | 8 |

| Build | First title frame | Session initialization |
| --- | ---: | ---: |
| Before | 13.6 s | 6.8 s |
| After: the above, and the Arena levelshots on idle frames | 8.8 s | 2.1 s |

Paired by round, the title came 4.7 s sooner (median; 3.6 to 4.9 s in seven
rounds, and 13.4 s in one where the machine stalled the baseline's launch).
Two traced startups (`ui_retainedTrace 1`) read all 70 levelshots in 66
and 68 idle frames, from 0.6-0.8 s to 2.1-2.3 s after the first title frame:
0.6-0.75 s of reading in all, at most 38 ms of it in one frame.

Hand-offs, engine probes with console verbs only (the menu audit's capture
harness with the probe scenarios `probe-preload-settled`,
`probe-preload-rush` and `probe-preload-arena-rush`), longest frame over each
step. The settled probe waits six seconds at the title first; the rush
probes go to their page as soon as they reach the title, within its first
two seconds:

| Probe | Step | Before | After |
| --- | --- | ---: | ---: |
| Settled | The title's first six seconds | 422 ms | 410 ms |
| Settled | LOAD GAME | 35 ms | 50 ms |
| Settled | MULTIPLAYER | 99 ms | 93 ms |
| Settled | CREATE SERVER | 122 ms | 118 ms |
| Settled | Browsing 12 maps | 43 ms | 57 ms |
| Rush | MULTIPLAYER | 84 ms | 52 ms |
| Rush | CREATE SERVER | 108 ms | 708 ms |
| Rush | Browsing 12 maps | 46 ms | 41 ms |
| Arena rush | SINGLE PLAYER | 72 ms | 62 ms |
| Arena rush | ARENA | 109 ms | 278 ms |

One run of each probe varies by tens of milliseconds: the first A/B's
probes, without the Arena change, measured the settled LOAD GAME at 76 and
31 ms, MULTIPLAYER at 121 and 77 ms, CREATE SERVER at 147 and 92 ms and the
browsing at 67 and 53 ms. The title's longest frame is its first. In the
settled probe the idle frames read all 70 levelshots, at most 33 ms of a
frame; in the rush probe Create Server opened with 35 of the 50 map
levelshots still waiting and read them in 575 ms, and the Arena page read
its 20 in 181 ms. Browsing stays smooth either way.

What remains:

- **A page opened at once.** Opening Create Server or the Arena page in the
  title's first two seconds, before the idle frames have finished, reads the
  levelshots still waiting in one frame (708 ms in the rush probe). Decoding
  levelshots on the job system's workers would remove it.
- **Map changes.** Every map change re-initialized every loaded GUI
  (`uiManager->Reload( true )` in `ExecuteMapChange`), the retained pages
  included: the startup's document work again, now one parse per page, on
  the main thread. The retained pages now keep their views
  ([map changes](#map-changes)).
- **Outside the menus.** Of the remaining wait before the title, hashing
  `pak0.pk4` and `pak1.pk4` (800 MB) against the executable's checksums takes
  about 1.4 s on every launch, and compiling the game's scripts about 1.2 s.

## Map changes

9 October 2026. Every map change re-initialized every loaded GUI
(`uiManager->Reload( true )` in `idSessionLocal::ExecuteMapChange`). With
`ui_retained 1` that took in every retained page: the eight the title reaches
at the first map change, and from the second on also both pause screens, Save
Game, Restart Level, the death screen, the loading screen and the weapon
wheel. Each read and parsed its document again, built a new view (markup,
elements, bindings) and restored the old view's snapshot into it: the
startup's document work again, on the main thread, inside the load. A restart
of the same map did it too.

The reload comes from Doom 3. The level load's purge
(`idDeclManagerLocal::BeginLevelLoad`) defaults every declaration not parsed
outside a level load, and the image manager frees every image a level load
read. A stock GUI's windows hold material pointers, and parsing it again finds
them inside the load, so their images load with the level instead of on the
first draw after it. A retained page needs less. The materials its view holds
survive a purge as objects, and its text and layers draw from generated
resources. What it needs is for the pictures it names to resolve again inside
the load: the preload and the level loads parse them as load media
(`SetInsideLoad`), so every map change purges them, and a purged picture drawn
later is parsed again mid-frame ("Loading non pre-cached material decl"), its
image read then too where a level load had read it. A language or renderer
change already rebuilds every retained view on its own (`RefreshResources`).

The first change made map changes call `UI_ReloadForLevelLoad`, initially
leaving stock GUI re-initialization intact (the follow-up below removes it).
A retained page whose document reads back byte for
byte unchanged keeps its view (`idUserInterfaceRetained::KeepForLevelLoad`):
the pictures it names resolve again inside the load, as its reload had them
do, and its pending input, programs and session requests are dropped, as a new
view would drop them. A changed document, or a view that cannot be prepared,
re-initializes as before; `reloadGuis all` still re-initializes everything;
pictures bound to state still resolve where their publishers precache them.
Each kept page logs `RETAINED_GUI_KEPT`.

Interleaved chains of map changes, the build before (`5d378666`) against this
one, in ABBA order: six rounds of each in single player and five in
multiplayer. Debugoptimized, hidden 1280x720 OpenGL window, `s_noSound 1`,
each side with its own warm save path and the same `pak0.pk4` (the older
client's embedded checksum patched to it), console verbs only. Single player
starts at the title and runs `map game/airdefense1`, then `game/airdefense2`
and `game/airdefense1` again; multiplayer runs a listen server's
`spawnServer mp/q4dm1` from the title, then `mp/q4dm2`. Timestamps
(`com_timestampPrints 2`) give the GUIs' share of each change, from the
level-load purge to the loading screen's first state, and `com_speeds` the
frame that held the whole change, from the wipe to the autosave. Medians, and
the median of each round's difference:

| Map change | Retained pages | GUIs, before | GUIs, after | Whole change, before | Whole change, after | Difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Title to airdefense1 | 8 | 2.18 s | 0.65 s | 11.1 s | 9.6 s | -1.8 s |
| airdefense1 to airdefense2 | 15 | 2.53 s | 0.57 s | 6.3 s | 4.4 s | -2.1 s |
| airdefense2 to airdefense1 | 16 | 2.76 s | 0.66 s | 11.1 s | 9.6 s | -2.2 s |
| Title to mp/q4dm1 | 8 | 2.12 s | 0.59 s | 5.3 s | 3.8 s | -1.5 s |
| mp/q4dm1 to mp/q4dm2 | 11 | 2.77 s | 0.65 s | 5.5 s | 3.3 s | -2.2 s |

Re-initialized, the retained pages took 1.5 to 2.1 s of each change; kept,
47 to 85 ms, mostly reading each document back to compare it (Join Game's
4.3 MB the most, 12 to 19 ms). With the Escape card opted in
(`ui_retainedMultiplayer 1`, three rounds) the second multiplayer change
re-initialized 12 pages, the 7.8 MB card among them, in 3.4 s and kept them
in 127 ms: the whole change went from 7.0 to 3.5 s. The 120 frames after
each load were as smooth in both builds (longest 20 to 32 ms), and no
"Loading non pre-cached" warning named a retained picture in either; the
other warnings, player models and tables, were the same in both.

Hand-offs after the second single-player map change, two runs of each build
alternating (the kit's `probe-mapchange-sp`: a save on airdefense1, a map
change to airdefense2, then the pause, SAVE GAME, LOAD GAME and RESTART LEVEL
and back, a death and the death screen's LOAD GAME), longest frame over each
step:

| Step | Before | After |
| --- | ---: | ---: |
| The pause | 119, 107 ms | 101, 101 ms |
| SAVE GAME | 62, 54 ms | 42, 46 ms |
| LOAD GAME | 54, 55 ms | 38, 38 ms |
| RESTART LEVEL | 41, 31 ms | 31, 31 ms |
| The death screen | 148, 154 ms | 128, 145 ms |
| Its LOAD GAME | 228, 162 ms | 230, 220 ms |

Single runs vary by tens of milliseconds. With `fs_debug 1` over the steps
both builds opened the same files: the saves, the soft focus's shader and the
levelshots the front end's idle frames precache once the level is over (the
probe starts in the level, so the title never read them); no picture was read
late.

### Stock GUI reuse

9 October 2026, follow-up to the retained-page change. `GUI_LEVEL_PURGE_DONE`
(with `com_showLevelLoadTimes 1` and `com_timestampPrints 2`) now separates
level-load setup and the declaration/renderer/sound/BSE purge from the first
stock GUI. The earlier table's stock estimate included that preceding work.

An unchanged stock GUI now implements the same `KeepForLevelLoad` hook. It
keeps its parsed window tree, compares the root and every included source
byte for byte, and resolves its media inside the load. The parser observation
also remembers failed include candidates: adding a file that takes precedence
invalidates the cache even if the previously selected include is unchanged.
Explicit `reloadGuis all`, language reloads, changed/missing sources, failed
parses, incremental editor parses and GUIs restored from a save or demo use the full
reload. Custom game/editor widgets and native chat surfaces retain their
existing reload path.

A background-only walk is insufficient. During the original parse a scoped
declaration observer records materials, script-only background alternatives,
script sounds, expression tables and widget resources. Re-finding those
references after the purge restores their contents and level-use marks;
GUI material sorting is reapplied. The live window walk also references
current backgrounds, including simple windows and directly assigned scroller
backgrounds, and expression tables. Slider thumbs refresh their dimensions.
Previously displayed model previews rebuild their render-world references
inside the load so the model purge cannot leave a stale preview behind.

Window identities survive; their authored presentation/script values are
restored from an in-memory snapshot taken immediately after parsing. This
resets a previously open Load/Save subpage, timeline flags, transitions and
focus just as a fresh parse did. Constructor-assigned scroller backgrounds
are retained separately because they have no authored background name in
the snapshot. The backend repeats initialization/activation and drops
pending commands and bind handling.
The `text` and `name` dictionary defaults reset as in `InitFromFile`; other
game-published values stay live. GUI state publishers continue to update
bound pictures normally. The cache
is engine-private, counted in `listGuis`, and does not change game-module or
save-file formats. The source/media observation scopes are thread-local and
inactive outside parsing; no replacement game assets are added.

Four interleaved pairs per mode (AB, BA, AB, BA), after a separate warm-up
for each side, measured 40 map changes. Windows x64 debugoptimized, OpenGL,
1280x720 hidden/windowed, 60 fps, sound disabled, stock installed assets and
`ui_retained 1`; no device input. The client was the only runtime difference:
before was `37f1d1d5` plus the purge marker, SHA-256 prefix
`2be75b8952b9177d`; after was `c442b13083dd6903`. Renderer/game modules and
both staged packages matched. Peer clients and CPU tests were paused; free
commit checks were 25–29 GB. Timings below are milliseconds; before/after
columns are medians, and savings are medians of paired differences.

| Map change | Stock before → after | Stock saved | Setup/purge before → after | Whole change saved |
| --- | ---: | ---: | ---: | ---: |
| Title → `game/airdefense1` | 176.0 → 13.5 | 162.5 | 1.0 → 2.0 | 222.5 |
| → `game/airdefense2` | 327.5 → 62.5 | 266.5 | 57.0 → 58.5 | 385.0 |
| → `game/airdefense1` | 355.5 → 61.5 | 294.0 | 33.5 → 36.5 | 432.5 |
| Title → `mp/q4dm1` | 173.0 → 17.5 | 156.0 | 1.5 → 2.0 | 169.5 |
| → `mp/q4dm2` | 325.5 → 62.5 | 262.0 | 19.5 → 20.5 | 329.5 |

The stock share falls 81–92%. The candidate keeps 8 stock GUIs from the
title, 49 then 46 in the SP chain, and 29 on the second MP change. Setup/purge
paired differences are only 0–2 ms. Whole-change savings use the frame that
contains the change, including the wipe and autosave. For the longest of the
first 120 post-load frames, paired median differences range from −0.5 to
+2.5 ms; the first MP map moves from a 20 ms median to 22 ms. Every SP change
and each second MP change has zero non-precached warnings. Both clients emit
the same 68 existing warnings on the first MP map (player/entity/effect
definitions and menu/weapon media); names and multiplicities match in every
pair.

Two interleaved pairs of hand-offs after the second SP map change, longest
frame over each step:

| Step | Before | After |
| --- | ---: | ---: |
| Pause | 87, 81 ms | 76, 80 ms |
| SAVE GAME | 38, 32 ms | 28, 29 ms |
| LOAD GAME | 29, 27 ms | 29, 26 ms |
| RESTART LEVEL | 22, 25 ms | 23, 19 ms |
| Resume | 18, 18 ms | 18, 18 ms |
| Death | 104, 105 ms | 104, 104 ms |
| Death screen's LOAD GAME | 152, 151 ms | 147, 143 ms |

All steps complete and the engine screenshots show the expected pages.
`fs_debug 1` records identical file-read counters in every pair: no new late
image reads. These direct-to-map probes skip title warm-up, so both builds
still open 300 images (123 distinct paths) during the hand-offs, including
existing deferred levelshots, objective and player-preview textures. Both
also produce the same 27 precache warnings after the first load. Those
baseline reads/warnings remain; this change does not claim to remove them.

A separate stock-only pair (`ui_retained 0`) saves on airdefense1, changes to
airdefense2, displays reused monitor GUIs, opens Pause/Save/Load, and restores
the saved airdefense1 while Load Game is open. Pause and Save then reopen
correctly, with no unreachable actions or errors and identical precache
warnings. Engine captures confirm the menu defaults and reused monitor bank.
This caught an earlier prototype retaining its open Load subpage; restoring
the authored window snapshot fixes it without rebuilding the tree.

The fast menu gate, all 51 related script checks (including the new compiled
stock-cache regression), and all 160 native checks pass. The full suites
passed after the authored-state reset fix; the final dictionary-default
adjustment also passed its targeted script checks and the full native suite.
The regression exercises byte changes, failed include candidates, scoped
observation, authored-state reset, purge re-referencing and the real
window/scroller traversal.
Evidence is under `.tmp/mapchange/`: `stock-defaults-{sp,mp}-report.txt`,
`stock-defaults-warning-check.json`, `stock-defaults-handoff-comparison.json`,
`stock-defaults-identity.log`, `stock-defaults-before-identity.log`,
`stock-defaults-screen-comparison.json`, `stock-defaults-gate.log`,
`stock-defaults-scripts.log`, `stock-final-native.log`, `test-summary.json`,
and `runs/stock-defaults-*` (logs and engine captures).
The fixed independent runtimes are `.tmp/runtime/mc-stock-{before,after}/`.

## Remaining requirements

Fractional motion and cold compilation still need optimized-build profiling,
and long documents need resource/performance stress tests. Geometry preparation
for opacity, retained clipping and engine vertex conversion can be improved
further, and the engine GUI path still copies every retained vertex each
frame. GPU timings, frame pacing at the supported refresh rates, the complete
density/aspect matrix, all GUI families and other platforms remain unqualified.
Composition/masks, complete paints/strokes/fonts, the visual editor and all
current GUI replacements remain separate required work.
