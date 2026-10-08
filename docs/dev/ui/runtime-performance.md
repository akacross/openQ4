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

## Retained title vertices

7 October 2026. The traced QUAKE 4 wordmark that the title shares with the
initializing screen took the retained title from the 127,000 vertices above to
about 569,500 vertices and 211,800 triangles a frame at 1280x720
(`openq4_retainedGui inspect screen`). At 64 bytes per engine vertex that is
36 MB through the GUI path every frame. It overflowed Vulkan's 32 MB per-frame
geometry ring, which dropped the title's framing bands until the ring doubled.
The wordmark's glow is 24 plain (`antialias: false`) strokes of rising width
around every letter contour, and those strokes alone made 437,000 vertices.

| Title element, native `--screen` benchmark at 1280x720 | Before | After |
| --- | ---: | ---: |
| Wordmark: 24 halo strokes and the letters | 442,122 | 12,815 |
| Framing bands: fill and ten rim strokes each | 64,568 | 53,944 |
| Emblem: multiply shadow and rim | 25,028 | 24,452 |
| Emblem glint rim, under its turning wedge | 16,352 | 8,592 |
| Reticle grid | 12,928 | 12,928 |
| Navigation plates and prompt bar | 2,784 | 1,860 |
| Whole screen | 569,574 | 120,375 |

Each element's count is what hiding it alone removes; the glint's depends on
the wedge's angle. In the engine the title reports 567,900 to 569,300 vertices
before and 116,300 to 116,900 after, with motion on, on OpenGL and Vulkan alike.
The initializing screen falls from 444,100 to 285,300. In the benchmark Join
Game falls from 94,200 to 81,900, Multiplayer from 84,400 to 72,900, Create
Server from 90,700 to 77,700 and the pause menu from 82,300 to 70,000.

- **Region triangulation.** libtess2's polygon output triangulates the planar
  arrangement of all its input contours. A stroke's union is one quad per
  segment and one fan per join, and a wide stroke's quads and fans overlap
  everywhere, so every monotone piece of the arrangement became its own
  triangles, at three unshared vertices each: 35,600 vertices for the widest
  halo stroke. A plain solid path now takes libtess2's boundary contours and
  triangulates only those, in a second pass, with shared vertices: 321 for that
  stroke. The boundary's vertices and edges are the arrangement's own, so the
  same pixel centres are covered. Gradients still clip the arrangement's
  triangles at their stops.
- **45-degree coverage shapes.** Coverage cells merge into spans of equal
  coverage and identical spans into quads. With a solid paint, a span that
  continues one pixel to either side of the span above it, each end moving
  steadily, now joins it as a sheared quad: the quad crosses each row's centre
  line exactly at that row's ends, whole pixels, so it covers the same pixel
  centres. A row joins only when its cells upload the same 8-bit colour at full
  opacity, and a vertical run keeps its first row's coverage as before, so a
  cell on a rounding tie (an exact half pixel) keeps its colour. The plates'
  45-degree chamfers merge this way; the band cuts, traced from the stock art
  at 41 to 45 degrees, only partly.
- **Masked tiles.** The glint is the emblem's whole rim drawn under a wedge
  mask an eighth of a turn wide. Outside the hull of a mask's paths, padded
  for stroke reach and coverage, the mask is transparent and its layer gains
  nothing. Paint under a mask, its element's own or an ancestor's, now uploads
  in 64-pixel tiles, and tiles wholly outside the hull are not submitted. Each
  tile keeps its own host mesh, so the turning wedge converts nothing.

The halo's union is also cheaper to compile: alternating runs of the native
benchmark put the title's cold first frame at 223 ms against 260 ms before.
Warm frames are unchanged within the machine's noise.

Verification:

- `openq4-ui-vector` checks that a wide round-joined zigzag's plain triangles
  share their vertices, cover the antialiased union's area and claim no pixel
  centre twice under a 1/256-pixel top-left rasterizer, and that a 45-degree
  band compiles to three sheared quads on whole pixels (at most sixteen at a
  fractional phase or mirrored) matching the independent per-pixel area
  oracle, while a gradient band keeps whole-pixel rectangles.
- `openq4-retained-ui` puts a ring under a quadrant mask, then turns it half a
  turn: the ring shows wherever the mask does, the masked frame submits under
  half the unmasked ring's vertices, and the check fails with culling disabled.
- A local harness compiled the previous tessellator beside this one and
  rasterized both meshes of every path and mask of the 24 production documents
  and 14 fixtures at nine output transforms (scales 0.75 to 2, sub-pixel phases,
  a 30-degree turn and a pointer lean), at pixel centres on a 1/256-pixel grid
  with the top-left rule and the upload's 8-bit colour. Across 23 production
  documents and 14 fixtures (84,726 cases) every mesh covers the same centres
  in the same colour, except 13 wordmark halo strokes that differ by one or two
  pixels in one faint layer, where the old arrangement's overlapping slivers
  counted a centre two or three times (a finer grid confirms it).
- Engine captures with reduced motion, from a baseline client and this one on
  one runtime, are byte-identical on OpenGL and Vulkan, and OpenGL matches
  Vulkan, for the title (home, depth, focus, exit, depart and settings
  hand-off), the initializing screen, the campaign sub-page, MODS, Multiplayer,
  Create Server, New Campaign, the empty Load Game page and every prompt style:
  51 screenshots on each renderer. The glint, which reduced motion hides, was
  captured with its turn frozen at six angles through a private-mod title, and
  is byte-identical too; there the title submits 115,700 to 120,200 vertices,
  depending on the wedge's angle, against 567,500 to 569,600.

What remains is about 117,000 vertices, nearly all antialiased coverage cells:
two to five per row along every edge of the emblem, bands, grid and letters,
at four vertices each. The initializing screen's turning rings (its teeth and
sweep, about 250,000 vertices at 1280x720) are tessellated at a new angle every
frame.

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

What remains on the Escape card is `ValueControlView::Paint`, which reasserts
every choice option's label, availability and display each frame through
string-keyed lookups and RML readbacks (`GetInnerRML`); a fingerprint of each
entry's readback and view state could skip settled entries the same way.

## Remaining requirements

Fractional motion and cold compilation still need optimized-build profiling,
and long documents need resource/performance stress tests. Geometry preparation
for opacity, retained clipping and engine vertex conversion can be improved
further, and the engine GUI path still copies every retained vertex each
frame. GPU timings, frame pacing at the supported refresh rates, the complete
density/aspect matrix, all GUI families and other platforms remain unqualified.
Composition/masks, complete paints/strokes/fonts, the visual editor and all
current GUI replacements remain separate required work.
