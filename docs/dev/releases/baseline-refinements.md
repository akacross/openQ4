# Baseline refinements (unreleased)

> **Unreleased development notes.** 0.13.2 is the latest available release; 0.14.0 was withdrawn. These changes are not a new download. See [release status](../../user/release-status.md).

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

- After Kane's stroggification, the pause menu's quit and exit questions and
  the Save and Load pages' delete and overwrite questions match the Strogg
  menus around them, their text translating from Strogg runes as they open.

- Save and Load Game now offer date, name and location sorting, manual-save and
  autosave filters, and Refresh List. Your selection follows the same save as the
  list changes, and refreshing preserves a name you are typing.

- Multiplayer friend and mute marks now clear when another player takes over
  a vacated slot. The Players menu returns to your statistics if the selected
  player leaves, and pending menu actions cannot follow their replacement.

- Multiplayer player lists now scroll at a readable row height, with column
  headings kept in view. Crowded rosters remain reachable in Welcome, Players
  and the match summary, and kick-vote choices no longer stop after 16 entries.

- The opt-in SYSTEM page now follows performance presets and settings changed
  from the console while it is open. Unfinished edits are preserved with a
  conflict message, and queued controls cannot overwrite newly changed values
  or select an option that has become unavailable.

- Fresh profiles keep Quake 4's stock crosshair hit feedback. Optional hit
  markers remain available in Game settings, and existing saved choices are kept.

- Installing a Windows development build no longer closes openQ4 games running
  from other worktrees or installations.

- Bots can correct jump-pad flights that would overshoot the platform after a
  hit, and brake dangerous momentum when their route ends.
- Bots allow room to slow down after a dodge jump, avoiding hops that land at
  a platform's edge and immediately slide off.
- Bots brake earlier when another player is already using a jump-pad corridor.
- Bots account for repeated jump-pad pushes when checking landing damage and
  reconsider dangerous routes earlier after losing health.
- Bots check their actual takeoff position before jumping onto raised ledges,
  preventing a mistaken wall-slide prediction from approving an overshoot.
- Bots can traverse valid slopes without mistaking the lower support probe for
  an obstructed player position, including under low ceilings. Their checks for
  unsupported edges and hazardous landings remain in place.
- Android touch buttons now respond across their full visible plates. Default
  Pause and Reload placement leaves the multiplayer rank and status readouts clear.
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
- Developers can build a separate x86_64 Android emulator app for diagnosis.
  It keeps its own saves and data and cannot replace the ARM64 phone app.
  This diagnostic build is not offered as a release APK.
- Android's timer wakes less often in the background and avoids prolonged
  catch-up after the system freezes the app, including with accelerated time.
- Android native error reports now stay beside the normal game log, making
  startup failures easier to diagnose.
- Android Back now follows menu and pause navigation. Error screens have larger
  touch controls and can be dismissed with Back, without opening the on-screen
  keyboard over the report. Dragging away from a button cancels the tap.
- On Android 11 and later, the game renders beside camera cutouts so they do
  not cover HUD controls. The surrounding strip stays black.
- The experimental Android app now opens a language and game-data setup screen.
  Choose your own Quake 4 folder with the system picker, follow copy/check
  progress and retry interrupted work without losing completed archives or
  saves. Setup includes English, German, Spanish and French recovery messages;
  select Single player or Multiplayer once the files are ready. Physical device
  testing is still in progress.
- Android setup can now back up saved games, including descriptions and previews,
  or export diagnostic logs to a ZIP through the system file picker. Setup
  failures are included in the logs. Cancelled or failed exports keep the
  original files; retry uses a new destination. See the
  [Android setup guide](../../user/android-setup.md) for backup limits and
  upgrade guidance. Physical device/provider qualification remains in progress.
- Open **Android setup** from the game's Settings and use **Return to game**
  to keep playing the same session. Quit the game before importing files or
  exporting saves and logs.
- Android setup now offers Default, Compact and Left-handed touch layouts,
  button size and look sensitivity with a drag test. Apply your choices before
  launching or returning to the game. Unapplied drafts leave your active
  controls unchanged.
- Android setup now has an **Interface** page. Choose a viewing profile such as
  Phone, Tablet or Couch, or set the menu and text size yourself, with a live
  preview. Applied sizes reach the game at its next launch or return from
  setup; size changes you make later in the game are kept. See the
  [Android setup guide](../../user/android-setup.md#adjust-menu-and-text-size).
- The standalone Android app now provides experimental touch gameplay controls:
  move, look and fire together, tap to cycle weapons or hold for the selector,
  and pause without a controller. Reload and zoom appear for supported weapons.
  Layout editing and portrait presentation are still in development; see the
  [touch controls guide](../../user/android-setup.md#play-with-touch-controls).

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
