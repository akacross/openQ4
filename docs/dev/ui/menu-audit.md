# Retained menu audit

8 October 2026. A review of the retained (idtech5-ui) menus as they ship with
`ui_retained 1`: the title, the Marine and Strogg pause screens, Single Player
and its Campaign, New Campaign and Arena sub-pages, the Load, Save, Restart
Level, Demos and Credits pages, the MODS dialog, the death screen, the
Multiplayer page with Create Server and Join Game, the SYSTEM page and the
multiplayer Welcome and Escape cards. The HUD, scopes and weapon wheels were
out of scope. It extends the [retained screens](retained-screens.md),
[multiplayer menus](multiplayer-menus.md) and
[runtime performance](runtime-performance.md) records.

## Method

- **Read-only code review** of the session glue (`Session_menu.cpp`,
  `Session.cpp`), the runtime's input and focus (`Interaction.cpp`,
  `Runtime.cpp`, the adapters), the generators and the shipped string tables,
  and a map of every front-end page against its stock route.
- **Engine captures** with `tools/ui/capture_retained_screens.py` of every
  menu scenario at 1280x720, 4:3 and 21:9, in German, French, Hungarian and
  Polish, plus probe scenarios for routes no capture covered: Back on the
  Single Player page reached from the title, Back and LOAD GAME on the death
  screen, and UPDATES. No OS input was sent; every step is a console verb.
  The harness keeps those routes as scenarios: `singleplayer-back`,
  `death` (now with Back), `death-load`, `updates` and
  `createserver-stepping`.
- **CPU measurements** with `openq4-retained-ui-benchmark --screen` and
  main-thread stack samples taken by attaching cdb to it.

## Fixed

| Severity | Finding | Fix |
| --- | --- | --- |
| High | Back on Single Player, reached from the title's SINGLE PLAYER, left a blank stock menu: the legacy menu stayed off its home after the hand-off, so the retained title never came back and the stock page had no buttons. | Back runs the legacy menu's own return from Single Player unseen and rests it at home, and the title returns with its bands from the page dock (`ReturnRetainedSinglePlayerHome`). |
| High | Back (Escape, B, Start) on the death screen closed it: the map was gone, so the player saw a loading screen and then the title. | The death screen's Back keeps it and returns focus to RESTART, and the session ignores close requests from it. |
| High | A deflected stick on the multiplayer Welcome card, which presents by default, sent presses with no release, so the card repeated the move until another key ended it. | The menu pump pairs the stick's steps on the card, as it does on every other retained screen. |
| Medium | Left and right could not change a dropdown: they moved focus, unlike a stock choiceDef and against section 13.5. | Left and right step a closed choice through its eligible options and wrap (`Interaction::ChoiceKey`). |
| Medium | Create Server's ADVANCED OPTIONS button sat in the header over the page title: a second `ADVANCED_TOP` (the dialog's top) shadowed the button's. | The button has its own constant and sits under the server options. |
| Medium | UPDATES faded the title's content for a pop-up that never opens, and its answer, a stock message box, showed the stock title behind it. Any message box at the title did. | UPDATES runs in place; a message box keeps the retained home behind it and gives the screen back as it was. |
| Medium | The death screen's LOAD GAME opened the stock Load Game page. | It opens the retained Load Game page over the title. |
| Medium | On Single Player, Campaign, New Campaign, Arena, Create Server and Join Game a focus change or video restart switched to the game's sound world, silencing the menu. | Every retained front-end screen without a level plays the menu's sounds. |
| Medium | Back from Create Server or Join Game did nothing when the Multiplayer page could not present. | Back finds the stock Multiplayer page. |
| Medium | A join from Join Game that failed or was aborted came back to the title, not to the server list: the legacy menu never left its home on that route. | The session remembers the join's origin, and the menu's next return home presents Join Game once. |
| Medium | The Escape card spent about 14 ms of CPU on every settled frame (debugoptimized), two thirds of it re-walking its 34,395 authored values. | `ApplyMotion` returns at once while nothing it reads has changed: 5.9 ms on the Escape card, 0.5 ms on Join Game ([settled frames](runtime-performance.md#settled-frames)). |
| Low | CONTINUE did nothing when the newest save could not be loaded. | It opens the Load Game page on that save, saying why. |
| Low | The pause and loading screens named difficulty 4 NIGHTMARE, the Arena's name, instead of WARLORD. | They name it WARLORD. |
| Low | The loading screen showed Duel, Clan Arena, Freeze Tag and Red Rover untranslated. | They take their localized names. |
| Low | The prompt bars' SELECT read "modo" in Spanish and "selezionata" in Italian (`#str_200747` is a monitor label). | The prompt uses the localized `#str_231042`. |
| Low | The title's link bar ran past its plinth in German, Turkish, Hungarian, Polish, Czech, Brazilian, Spanish and Russian. | The plinth runs on for each language that needs it. |
| Low | The pause's QUIT CURRENT GAME title was clipped in French. | It runs over the raised trailing section, and the generator fails any dialog title that does not fit in some language. |
| Low | The MODS dialog clipped LOAD MOD in nine languages and its detail labels in five. | The dialog and its plates are as wide as the longest language, and the values start after the longest label. |
| Low | The Create Server, Join Game and Multiplayer crumbs never shrank: their fit read only openQ4's own string tables. | The fit reads the stock tables too, so they shrink like the others, down to the 13 dp floor. |

The [retained screens](retained-screens.md#known-limitations) and
[multiplayer menus](multiplayer-menus.md#known-limitations) known limitations
dropped four stale entries: the Escape card's Match page, the Save Game page,
Join Game's controller sorting and Match Control's team join are all built or
fixed.

## Remaining

Highest impact first.

- **Settings.** GAME, CONTROLS and AUDIO, the Load Defaults dialog and Player
  Setup are the stock pages, and the retained SYSTEM page stays opt-in until
  presets can be applied ([effect execution](settings-effect-execution.md)).
  Going to them from the retained title swaps the whole backdrop.
- **Startup preload.** The title waits while every retained page loads and
  every multiplayer map's levelshot is precached, about 6 s on a
  debugoptimized build, 1.7 s of it the levelshots. The levelshots of
  community maps are also extracted into the save path on every launch
  (`FindMapScreenshot`).
- **Prompt bars.** Pages (Load, Save, Restart Level, New Campaign, Demos,
  Credits, Create Server, Join Game) keep the stock BACK plate, so controller
  players see device glyphs only on the title, pause, Single Player, Campaign
  and Multiplayer screens (section 13.4 asks for the bar on every screen).
- **Focus.** The title, both pause screens and the SYSTEM page open with
  nothing focused (section 13.4 puts initial focus on
  the primary action), so the first press of Enter does nothing. At page
  level a focused control that turns disabled or hidden loses focus without
  a replacement (SYSTEM's Apply), and Back can be swallowed once by a
  detached, clean number editor.
- **Strings.** Separators are joined in C++ (the CONTINUE detail's " - ", the
  pause time line's order and " · ", "%.1f s"); Polish and Russian lack the
  stock code strings, so ENTER and ESCAPE keycaps and save labels stay
  English; Demos and the Match page mix case where the stock is all caps;
  BACK uses two keys (`#str_230045` and `#str_200018`), which differ in
  Spanish. The Italian and Polish crumbs of long titles are cut at the 13 dp
  floor.
- **The Escape card's frame** is still about 5.9 ms on a settled screen
  (debugoptimized): `ValueControlView::Paint` reasserts every choice option
  each frame.
- **Join Game** republishes all 64 rows on every scan change, and its MAP
  column cuts long names mid-letter.
- **The "stopped drawing" fallback** is checked for home screens each frame,
  but not inside `FindRetainedGui`, so Single Player, Campaign and New
  Campaign keep reusing a failed view.
