# Baseline refinements after 0.14.000

## Highlights

- Command-line multiplayer connections now reach the server reliably when a
  long launch command requires the game to switch from single player.

- More precise motion between game ticks: camera, world and material presentation
  share a high-resolution sample for each draw. Pauses, hitches and clock resets
  keep a bounded presentation phase.
- OpenXR smooth turning now measures elapsed host time without rounding each
  frame to whole milliseconds.
- The multiplayer guide correctly identifies enhanced prediction and hitscan
  lag compensation as opt-in settings.

## Upgrade notes

- Replace the complete package, including the engine, matching SP/MP modules,
  renderers and bundled openQ4 data. Save formats, network timestamps,
  authoritative gameplay timing and existing controls are unchanged.
- This increment does not promote a new refresh-rate target, headset/backend,
  Android device or UI migration to supported status. Current known compatibility
  gaps remain tracked in the development roadmap.

## Change log

- Improved damaged-save handling: invalid or duplicate entity registrations no
  longer corrupt the identities needed to clean up a failed load.
- Failed save loads now release remaining restored objects and avoid deleting
  attachments a second time during cleanup.
- A damaged save that fails during restoration now returns to the Load Game page
  with guidance, or a message dialog when using the classic menu. The original
  save remains untouched, and another save can be loaded afterward.
- Creating client effects when their entity table is full now fails safely.
- Interrupted save restores no longer release models or lights using stale
  handles from the saved world.
- Damaged saves with invalid attachment or physics-team links are rejected, and
  partial links are discarded before failed-load cleanup.
- Saved actor and client-effect references now reject incompatible entity types
  before they can be used during restoration or play.
- Invalid saved door and platform activation chains now return to save-load
  recovery, including errors encountered midway through restoring a group.
- Damaged saves with conflicting script-thread ownership now return safely to
  the load screen instead of leaving cleanup or subsequent play with invalid
  thread references.

- The experimental Android app now checks its extracted bundled content and
  repairs missing or damaged files before starting. Interrupted repairs keep
  saves and the previous package intact. Allow free storage for a replacement
  copy of the damaged file; retail game files remain separate.

- Experimental OpenXR mode now returns safely to desktop play after frame or
  session failures and clears held VR controls. A lost session retries after a
  short delay; use `vr_restart` after the runtime itself stops. Screenshots taken
  during VR gameplay now include the world.

- Windows and Linux builds now produce matching bundled content packages, so
  an identical package built on the other platform passes package validation.
- Pausing an Arena match also pauses its game audio clock, while menu sounds stay
  active. Resuming continues from the paused position.
- Retained interfaces can upload generated images with correct transparency and
  bounded resource use, including tall images and renderer restarts.
- Restored game regression coverage and added executable clock/pause checks.
- Refreshed the retail, openQ4 and Awakening GUI inventories, preserving historical
  evidence and identifying changed resources for further validation.
