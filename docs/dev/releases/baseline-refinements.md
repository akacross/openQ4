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

- Replace the engine and matching SP/MP modules together. Saves, network
  timestamps, authoritative gameplay timing and existing controls are unchanged.
- This increment does not promote a new refresh-rate target, headset/backend,
  Android device or UI migration to supported status. Current known compatibility
  gaps remain tracked in the development roadmap.

## Change log

- Retained interfaces can upload generated images with correct transparency and
  bounded resource use, including tall images and renderer restarts.
- Restored game regression coverage and added executable clock/pause checks.
- Refreshed the retail, openQ4 and Awakening GUI inventories, preserving historical
  evidence and identifying changed resources for further validation.
