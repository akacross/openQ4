# High-refresh presentation owners

> **Development status:** This document describes the current source tree and its evidence, not the contents of the latest available 0.13.2 package. The 0.14.0 release was withdrawn. See [release status](../user/release-status.md).

Contract for HF-03 through HF-07 in the [roadmap](roadmap.md), 23 October 2026.
It extends the [clock ownership contract](presentation-clock.md) (HF-01/HF-02),
which still owns the clocks themselves. Nothing here changes authoritative
simulation, usercmds, save formats, network timestamps or demo timing. Every
owner below is draw-only: it moves what is drawn between two authoritative
60 Hz samples, or toward input the game has not applied yet, and hands the
authoritative pose back before gameplay can read it.

## Late look (HF-03)

`in_presentationView 1` (default `0`) turns the drawn view with input that has
not reached the game yet. Previous-to-current interpolation deliberately draws
the eye a tick behind; mouse motion then waited for the next usercmd on top of
that. Late look removes both delays for the input-driven part of the view.

**Engine sampler.** `idUsercmdGen::GetPresentationViewAngles` (game API 54
passes the generator through `gameImport_t`) returns the angles the next
usercmd would carry if it were built now: the last built usercmd, plus mouse
and gyro motion drained under the async lock and scaled exactly as `MouseMove`
scales it (CPI, sensitivity, acceleration, zoom), plus the elapsed share of the
coming tick for held look keys and stick deflection
(`openq4::PresentationRateShare`). It writes no usercmd field, never consumes
`mouseDx/mouseDy` and never shifts the build stamp, so the next usercmd still
receives all of the input. The retired `GetPresentationViewDelta` reported only
pending mouse motion and would have dropped usercmds that were built but not
yet run (`com_asyncInput 1`); the game now compares absolute angles with the
usercmd it actually applied, which counts buffered usercmds exactly once.

The sampler returns false, and the view stays on the interpolated authoritative
path, when late look is off, input is inhibited (console, menus, retained UI,
or the native input driver owning the event pump, so the draw never drains it),
a radial selector owns the look input, a command or render demo drives the
game, or a VR headset owns the view. Android touch look arrives as a
per-usercmd delta with no continuous sample and is excluded.

**Filtered versus late look.** `m_smooth` above `1` and `m_filter` above `0`
blend several usercmds of motion. Showing raw motion ahead of that blend would
turn the view one way and then settle it another, so filtered input keeps the
authoritative view. This is a deliberate policy, not a missing feature.

**Game consumer.** `idPlayer::UpdatePresentationLook` runs once per prepared
draw, inside `CalculateRenderView` and only while
`idGameLocal::IsPresentationSceneActive()`. It freezes one correction:
`(current view + unapplied input) − interpolated view` in yaw and pitch, with
pitch clamped exactly as `UpdateViewAngles` clamps it
(`openq4::ComputePresentationLook`). `GetPresentationViewPos` applies that
correction last, in gravity-relative angles, pivoting the eye about the neck
the way `GetViewPos` places it (`g_viewNodalX/Z`). Everything held in front of
the eye follows: the interpolated view model through `GetPresentationViewPos`,
the non-interpolating view model through `ApplyPresentationLookToEyeAttachment`,
and bound effects, attached models, the GUI light, the muzzle-flash light and
the flashlight through the held view-model pose. The scope compass already uses
the drawn render view.

Late look applies only to this client's own first-person eye
(`AllowsPresentationLook`). It stands down while dead, driving a vehicle, in a
cinematic or camera view (unless noclipping), under an influence that locks the
view, during centre-view, in third person or `pm_modelView 1`, during the SP
benchmark view sweep, `g_stopTime`, demo or timedemo playback, VR, a radial
selector, or an MP Arena freeze. Any mode not named there is caught by the
coupling check: each authoritative sample records whether the view's yaw step
matched its usercmds' yaw step (`PresentationLookCoupled`); a held, scripted or
teleported view fails it, and late look stays off for that sample. More than
90° of unapplied input is a discontinuity (angle reset, map change), not motion.

**Displayed aim versus authoritative firing.** A shot uses the usercmd that
carries the input up to its build. Late look draws the input up to the draw,
so the drawn aim never leads the input that the next usercmd will carry.
Without late look the drawn aim trails the shot's aim by up to a tick.

**Same-fire-frame alignment.** Bound muzzle effects, attached models and the
view lights follow the drawn gun. World-space shot visuals stay where the shot
left: hitscan tracers and impacts, and `launchFromBarrel` projectiles, which
spawn at the authoritative barrel and are then drawn by the generic entity
pass. On the first draw after the firing tick, their start can differ from the
drawn barrel by the rotation since that usercmd was built, at most one draw
interval of turning. Interpolation alone shows up to a whole tick of it, in the
other direction. No cosmetic retrace is performed: a draw-frame trace would be
gameplay work, and moving a tracer would misreport where the shot went.

**Never altered.** Traces, damage, projectile spawns, network events, RNG,
`viewAngles`, `deltaViewAngles`, `firstPersonViewOrigin/Axis` and the usercmd.
[`presentation_hf_contract.py`](https://github.com/themuffinator/openQ4/blob/master/tools/tests/presentation_hf_contract.py)
rejects writes to each of them from the late-look path, confines the correction
to the presentation functions and checks the SP/MP bodies are identical;
`--mutations` proves representative regressions fail it.

## Visual ownership inventory (HF-04)

| Visual | Disposition |
| --- | --- |
| View weapon, its bound effects and attached models, the GUI light, the lightning beam's near end | Existing owners (`UpdatePresentationWeapon`, `UpdatePresentationClientEntities`, `UpdatePresentationEffects`), now also turned by late look. |
| View muzzle-flash light and flashlight | **Implemented.** Re-placed from the drawn eye and gun when the light is already live. Think still creates, re-times and frees them; the flashlight carries Think's wall back-off instead of tracing on a draw frame. A VR hand keeps its tracked placement. |
| World muzzle-flash and flashlight lights (`_WORLD`) | Suppressed in the owner's own view. Other views see them on the owner's world-model joint: an SP subview may show the authoritative tick; MP remote owners are remote actors (HF-05/MP-07). Recorded exclusion. |
| Classic muzzle-flash dynamic light | A short world light at the fire position, intentionally fixed where the shot happened. |
| Unbound client debris, brass, BSE debris and MP client gibs (`rvClientMoveable`) and their trail effects | **Implemented.** Sampled after Think's authoritative push; drawn between the two tick samples with the scale envelope; the trail is pushed with the authoritative effect clock (`rvClientEffect::PresentAt`). Physics, bounce sounds and lifetime stay in Think. |
| Projectiles, movers, actors, bound client entities and lights | Existing generic entity pass and projectile replay fixes; terminal projectile states and restore reseeding unchanged. |
| Active articulated figures (ragdolls) | **Implemented.** The animator keeps the AF pose it replaces each tick; a draw blends the previous and current authoritative model-space poses (quaternion blend) over the root's interval. The AF bodies are never re-evaluated. |
| Angular-velocity joint modifiers | Exclusion: they integrate state from their last sample and cannot be evaluated at an earlier time; the authoritative pose is copied. |
| `idBrittleFracture` shards | Exclusion: the model callback rebuilds every shard from its own physics body each tick; a per-shard history would be a new owner for a rare, short-lived effect. |
| `idMultiModelAF` (one def per body) | Exclusion: bodies own separate render defs outside the entity pass; used by few props. |
| Unbound effects an owner repositions per tick: Makron bolt and gauntlet impact, the lightning gun's world beam (third person/other players), the vehicle lock-on guide and Awakening cockpit markers | Exclusion: their endpoints are trace or target positions chosen by gameplay each tick; interpolating them would draw beams to points the game never chose. The lock-on guide can trail an interpolated target by up to a tick of its motion. |

## Alternate views (HF-05)

Cinematic and private (security) cameras, third person, third person in a
vehicle and the death camera used to put the whole scene back on the 60 Hz tick.
`idPlayer::PresentAlternateView` now samples each such view once per tick,
exactly as the authoritative path built it, and draws it between its last two
samples on the scene's clock; `IsPresentationViewInterpolated` then admits the
scene to the same clock. Camera frame commands, cuts and third-person traces
stay in the authoritative call, which is idempotent within a tick; the draw pass
never calls `GetViewParms` at another time.

A view starts again from its current sample instead of blending when it
publishes an authored cut (`renderView.forceUpdate` from `idCameraAnim`),
changes kind or camera entity (spawn identity), skips a tick, runs at an altered
tic rate, jumps further than the motion already in flight (32 units plus four
times the last step, or 90°), when `g_presentationInterpolation 0`, during demo
or timedemo playback, when third person rides a carrier that cannot be drawn
interpolated, or when third person or the death camera follows a body held on
the tick (a remote player followed in multiplayer). A static private camera samples the same pose twice, so it costs
nothing and lets the world it shows move smoothly.

Not changed: a free-flying MP spectator already uses the first-person path; a
followed player is a remote actor, and remote-player poses stay authoritative
until MP-07 defines prediction, rewind and displayed aim together. The local
body's admission to the entity pass (SP actor, MP local player) keeps its
contract coverage (`actor_policy`). The MP Arena tableau camera is unchanged.
Vehicle cockpit eyes interpolate as before; their joint-composed eye against the
presentation-evaluated cockpit skeleton still needs human qualification.

## Cross-system behaviour (HF-06)

| System | Behaviour |
| --- | --- |
| Game/network demo playback, timedemo | Bypass presentation (`PreparePlayerSceneForRender` returns early); late look and alternate views also refuse. Deterministic playback and benchmark meaning are preserved. |
| Render demo playback | Draws recorded views; the late-look sampler refuses while `readDemo` is open. |
| Command demos | The sampler refuses while `cmdDemoFile` drives the game. |
| AVI capture | Keeps the fixed-rate tic path (presentation-clock contract). |
| TAA history and motion vectors | Camera motion, including late look, is per-frame view reprojection. Authored cuts reach the renderer through `forceUpdate`; interpolated alternate views give continuous history. |
| BSE | Draw-only pushes repeat the authoritative game time, so particles move without respawning or ageing; the renderer de-duplicates servicing per frame. |
| Audio | Not advanced by presentation; AUD-02 owns audible lifecycle. |
| VR | Late look refuses; alternate views play flat as before. |
| Save, restore, map reset | All new state is transient and reseeded: player look/alternate-view samples, debris samples, the animator's AF history; none is serialized. |
| Repeated draws, subviews | Draw owners run no Think, physics, scripts, sound or effect creation (contract tests). Input is consumed once: live authoritative turn rates match the configured input in both late-look modes (below). |

Remaining HF-06 qualification: repeated stereo/subview draws in VR, TAA
appearance under late look by eye, and long sessions with mixed demo/capture use.

## Supported frame-rate behaviour (HF-07)

Declared targets, pending physical qualification:

| Target | Frame interval | Budgets on the Windows x64 desktop reference (visible foreground window, `r_swapInterval 0`) |
| --- | --- | --- |
| 240 Hz, supported target | 4.17 ms | p95 ≤ 4.6 ms, p99 ≤ 6.3 ms frame interval; engine input-to-draw ≤ 1 ms with late look; no missed tick at p99 |
| 360 Hz, experimental | 2.78 ms | Reported only; not a release promise |

Cases to qualify: caps 30/60/120/144/165/240/360 and `0`, vsync and VRR where
available, low-FPS catch-up (fewer draws than ticks), menus and loading (the
loading pacifier follows `com_maxfps`), hidden windows (capped at 60), and the
`performance` (60), `ultra` (240) and Steam Deck automatic caps. Use
[`presentation_look_runtime.py`](https://github.com/themuffinator/openQ4/blob/master/tools/tests/presentation_look_runtime.py)
for engine-side latency and smoothness, `com_showFramePacing 2` for p50/p95/p99
intervals and the gameplay benchmark for frame times, all in a visible
foreground window. Physical display latency (scan-out, compositor, panel)
needs external measurement and is not claimed by these tools.

An occluded window on Windows does not qualify: on 23 October 2026 the same
client capped at 240 presented at 57 Hz on OpenGL (p99 232 ms) and 15 Hz on
Vulkan (p99 725 ms) behind other windows on a loaded machine. HF-07 remains open
until physical runs on the reference hardware meet the budgets above.

## Evidence

Native: `openq4-presentation-look` executes the production policy header in a
model of the usercmd pipeline at 30–997 Hz with jitter, buffered and direct
usercmds, steady and flick-speed turns through the wrap and both pitch clamps:
the drawn view equals the input sampled at the draw within 0.02°, interpolation
alone always trails by a tick, no draw turns further than the input did, and
held rates draw without a staircase. Static: `presentation_hf_contract.py`
(engine sampler, SP/MP owners, alternate views, AF history, mutations) and the
updated `presentation_interpolation_contract.py`.

Live single player, `game/airdefense1`, OpenGL, synthetic probe at 2000
counts/s (220°/s), 512 draws per case, `com_maxfps 240` on an occluded window
that presented at about 62 Hz (draw interval p50 16.2 ms, p95 25.6 ms). Retained
under `.tmp/hf/look-run3` and `.tmp/hf/scen-run1`:

| Measure | Late look off | Late look on |
| --- | --- | --- |
| Authoritative turn rate (expected −220.00°/s) | −220.00°/s | −219.95°/s |
| Drawn yaw against the sampled input | — | p95 0.003°, max 0.007° (command quantization) |
| Delay behind the input (line fitted at usercmd build, 3.9 ms build-to-draw bias removed) | about 16 ms | about 0 ms |
| Frame-to-frame residual of the drawn yaw, p95 | 2.15° | 0.09° |

Third person with `g_presentationInterpolation 1` recorded 512 interpolated
draws (residual p95 2.06°, the same as interpolated first person); with `0` the
scene correctly stayed on the authoritative tick and recorded none.

Owner activity, from the capture's per-draw counters (`.tmp/hf/scen-run4`), on
airdefense1's posed `env_ragdoll_marine` figures plus a spawned Strogg marine
killed by `damage`, the player's own death (`testDeath`, death camera) and a
`launching_barrel_small` thrown by `damage`:

| Scenario | AF poses requested on draws | Blended | Client debris drawn |
| --- | --- | --- | --- |
| Ragdoll | 2,764 | 2,747 | — |
| Player death | 2,589 | 2,571 | — |
| Exploding barrel | 1,869 | 1,860 | up to 2 at once |

The unblended remainder are draws at the end of a tick, which show the
authoritative pose. A first build blended nothing: the AF calls `ForceUpdate()`
every tick, clearing `lastTransformTime`, so the history now keeps the time of
the pose held in `joints[]` itself, and the contract rejects the old condition.
No run logged an error. These runs measure engine-side behaviour on one Windows
machine; they are not physical input or display qualification, nor a visual
review of the drawn motion, and the occluded window did not reach the requested
rate.
