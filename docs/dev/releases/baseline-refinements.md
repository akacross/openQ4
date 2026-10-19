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
- An unavailable optional menu now falls back to the stock screen during save
  loading. Missing GUI definitions required by the save still stop the load
  safely and identify the missing file.
- Creating client effects when their entity table is full now fails safely.
- Interrupted save restores no longer release models or lights using stale
  handles from the saved world.
- Damaged saves with invalid attachment or physics-team links are rejected, and
  partial links are discarded before failed-load cleanup.
- Saved actor and client-effect references now reject incompatible entity types
  before they can be used during restoration or play.
- Invalid saved door and platform activation chains now return to save-load
  recovery, including errors encountered midway through restoring a group.
- Damaged saves containing invalid standalone object classes are rejected before
  construction and return to the load menu. Supported older saves retain their
  existing readers.
- Damaged saves with conflicting script-thread ownership now return safely to
  the load screen instead of leaving cleanup or subsequent play with invalid
  thread references.

- The experimental Android app now checks its extracted bundled content and
  repairs missing or damaged files before starting. Interrupted repairs keep
  saves and the previous package intact. Allow free storage for a replacement
  copy of the damaged file; retail game files remain separate.
- The experimental Android app no longer blocks game-window creation behind
  its startup splash. Fatal errors can replace a still-open game window.
- Missing retail files no longer send Android startup diagnostics to the wrong
  folder; the app keeps its selected game-data location.
- Android's optional new interface now initializes on the game's thread,
  fixing rejected menu creation during startup and save-load preparation.
- The experimental Android app silences audio and releases held controls when
  backgrounded. Returning to a live single-player game opens its pause menu
  before combat resumes, while existing menus and loading screens keep their
  current flow. Android device qualification remains in progress.
- Android's timer wakes less often in the background and avoids prolonged
  catch-up after the system freezes the app, including with accelerated time.
- Android native error reports now stay beside the normal game log, making
  startup failures easier to diagnose.
- Android Back now follows menu and pause navigation. Error screens have larger
  touch controls and can be dismissed with Back, without opening the on-screen
  keyboard over the report. Dragging away from a button cancels the tap.
- On Android 11 and later, the game renders beside camera cutouts so they do
  not cover HUD controls. The surrounding strip stays black.

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
