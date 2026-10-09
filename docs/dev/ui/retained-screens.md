# Retained title, pause and loading screens

This increment extends the retained (RmlUi) interface beyond the SYSTEM page to
the title screen, the single-player pause menu and the stock loading screens,
built from [visual specification 1.9](../ui-visual-design.md) and the design
atlas. It starts from engine `f5503259a5a2f618e5dd1cebab9adc55c2513f79` and
advances screen migration in the [idtech5-ui plan](../plans/idtech5-ui.md). It
adds partial evidence for `FLOW-024`, `FLOW-047`, `FLOW-048`, `ART-030` and
`REN-014` in the [requirement register](product-requirements.md); the
remaining screen migrations and the final gates stay open.

## One gate

`ui_retained` is the only switch for these screens. It is on by default and
archived, so a player who sets it to 0 keeps the stock screens. While it is 0
no menu, pause or loading route creates a retained view, and the stock GUIs
present every screen exactly as before. Developer commands that name a
document explicitly (`testGUI`, `ui_retainedPreview`) remain the runtime's
test and preview tools and load it regardless of the gate.

`ui_retainedSystem` opts into the SYSTEM page, which `ui_retained` includes
only once every setting of the stock SYSTEM page works there, so the default
never loses one. The session lists the stock settings the page has no control
for in `RETAINED_SYSTEM_MISSING_SETTINGS`, now empty, and those it has a control
for that cannot yet do what the stock page did in
`RETAINED_SYSTEM_INCOMPLETE_SETTINGS`: a Performance Preset cannot be applied
([SYSTEM resolution rows](system-resolution-rows.md#the-gate)). The window and
custom size fields take typed digits since committed characters reach
retained fields. The gate test derives both lists from the code.

`ui_retainedMultiplayer` likewise opts into the multiplayer menu card, which
covers the game's in-match menu; `ui_retained` includes it only once none of
its pages hands off to a stock page any more
([multiplayer menus](multiplayer-menus.md#the-gate)). Neither opt-in is
archived, so each lasts until the player quits. Both are `CVAR_NOCHEAT`, so
joining or hosting a game without cheats, which resets every unarchived cheat
CVar, keeps them, and either can change during a match.

`tools/tests/ui_retained_gate.py` holds the gate: it checks the CVar defaults,
that every retained document path in the session is reached only behind the
gate, that the documents are current with their generator and request only
allowlisted session verbs, that no game or legacy content names a retained
document, and it compiles the production session code against counted doubles
to show that nothing retained loads while the gate is 0 and that every
fallback below presents the stock screen.

## Falling back to the stock screens

A retained screen stands in for a stock GUI only while it can. Otherwise that
screen presents its stock GUI, for the rest of the session, and every other
screen keeps its retained form:

- **Not installed.** No search path provides the document. This is quiet: a
  developer message only.
- **Cannot load.** The document is installed but fails to parse, validate or
  load. It is reported once as a warning.
- **The main menu lacks a page.** The title and pause screens cover the legacy
  main menu and hand its pages off to it, so they present only over a menu
  that defines every window they hand off to (`main_b_newgame`,
  `main_b_loadgame`, `main_b_savegame`, `main_b_multiplayer`,
  `main_b_settings`, `main_b_credits`, `main_b_demos`, `main_b_difficulty`,
  `main_b_mods` and `main_b_updates`). A mod's own main menu without them
  presents itself, as the mod made it. The loading screens hand nothing off and
  still present. Under The Awakening the menus come from openQ4's own content,
  so the retained screens present there too.
- **The view stops drawing.** A view that fails to come back after a renderer
  or language change can no longer draw; the stock home screen takes over, with
  one warning.

The SYSTEM page and the campaign selectors follow the same rules. When the
opted-in SYSTEM page cannot load, the click that asked for it opens the stock
SYSTEM page, and the SYSTEM button opens the stock page directly from then on.
Should the session ever refuse an open while the page is still available (no
current state does: a message box or test GUI takes the menu's clicks first),
that request opens the stock page with a developer warning, and the button keeps
the retained page. When the Single Player or campaign selector cannot load, the
stock selector opens.

The multiplayer menu reaches the SYSTEM page through the main menu: the game
returns `main fromMp_toSystem`, and the main menu's `fromMp_toSystem` event
shows the stock SYSTEM sub-page (`desktop::dest` 22). With the retained page
available, the event instead starts `anim_retainedSystemFromMp`, whose
timeline asks the session on the next frame to open the retained page
(`openRetainedSystemFromMp`) over the main menu as it comes up from the match.
The request goes through a timeline because a command set in a named event the
session fires is never collected. The branch runs no page transition, so it
leaves `desktop::active` alone; the stock route raises it for its transition,
which lowers it again. Both routes show the same SYSTEM page. Back returns to
the main menu as the multiplayer menu's Main Menu choice leaves it: its main
page, or the server browser when the match was joined from there. An open the
session refuses sends `fromMp_toSystemStock`, the stock route.
`tools/tests/ui_system_session_route.py` compiles the route against counted
doubles and pins the menu script. The `system-mp-game` capture scenario takes
the real route from a listen server's in-game menu, and `system-mp-route` and
`fallback-system-mp` fire the event at the title; each checks that the main
menu is usable again after Back.

SYSTEM route evidence: `.tmp/ui/system-session-route/validation-evidence.json`,
SHA-256 `f363fcb9d87b3a04aa4ba5617f2fa1982a9909d7d8618a99717eee18c3de2003`.

Pictures fall back as well. CONTINUE shows the newest save's picture only when
its file exists: an autosave names its level's loadscreen, and any other save
keeps its own screenshot beside it (`savegames/<slot>.tga`), as the stock Load
Game page shows it. That screenshot is reread when the title opens, so a newer
save's picture replaces an older one. The pause screen's level block chooses
its levelshot as the loading screen chooses its picture: the map's
`loadimage`, the intro art for a map that loads through the intro screen, then
the map's own levelshot. A candidate that is not installed falls through to
the next, ending at the generic art.

## Screens

The documents are generated by `tools/ui/build_retained_screens.py`, which
cites the specification section behind each measured value. Regenerate them
after editing the script; `--check` fails when an output is stale.

- **Title** (`guis/menu/title.q4ui`, section 9 and 13.7). Framing bands with
  their rim light, the lit field (vignette, additive light band, reticle grid),
  the backdrop levelshot montage, the wordmark (QUAKE 4 traced from `q4text`
  and added as light with the texture's own halo, ART-031) and the multiplied
  Quake emblem with its 0.20 rim light. A glint runs around the emblem every
  9 s: the rim drawn bright under a wedge mask 12% of a turn wide that turns
  about the ring's center, while the rim inside it turns back so the outline
  stays put. Reduced motion (`ui_retainedReducedMotion`) hides the glint and
  keeps the rim. The backdrop, the light and grid, and the framing bands lean
  up to 6 dp away from the pointer, deeper layers further, while the content
  stays fixed (section 13.8 depth). The session publishes the pointer's
  place, or a held look stick's deflection while it leads (menu focus moves
  with the other stick), and reduced motion holds the layers still.
  CONTINUE leads the navigation when a save exists and its
  message line shows the save's levelshot, name and time; the same line explains
  whichever item has focus. SINGLE PLAYER, LOAD GAME, MULTIPLAYER and SETTINGS
  follow, and the secondary links and EXIT stay on the plinth. EXIT asks before
  leaving. Opening the menu focuses its primary action (section 13.4),
  CONTINUE or, without a save, SINGLE PLAYER, so a controller's first Accept
  acts; coming back from a page keeps the focus on the item that led there.
  While the mouse leads, only the item under the pointer is lit
  ([interaction](interaction.md)), so a mouse player never sees two. The prompt bar sits in the bottom band's raised section, its
  glyphs following the active device ([prompt glyphs](#prompt-glyphs)).
- **Pause** (section 13.7, single player). GAME PAUSED replaces the wordmark,
  RESUME leads, followed by SAVE GAME, LOAD GAME, RESTART LEVEL, OBJECTIVES,
  SETTINGS and QUIT TO MENU, the seven actions from 172 u (the plates' art is
  drawn from 172 u, as the title's from 202 u); only EXIT stays on the
  plinth, and both quits ask first. The current level block takes the
  emblem's place: a card with the levelshot, the mission, the difficulty, the
  objectives with their state and the time line. The session asks the game
  with the `retainedPauseState` menu command when the screen opens. Three
  rows list the open objectives, newest first as the stock objective screen
  stacks them, each behind the atlas marker, and then the ones completed on
  this map, newest first, behind a check at 0.5. The time line under a faint
  rule gives the mission's game time (it restarts with each map and is saved
  with it) and how long ago the newest save was written: "0:42:10 in mission
  · saved 4 min ago". A game module that publishes neither leaves the map's
  own objective summary and no time line, and the heading hides when there
  is nothing to list. The paused view
  stays behind the screen, softened and never
  dimmed: the specification gives scene softening no values of its own, so
  it takes `modal.softfocus` (a 7.5 dp blur at 0.80 saturation), ramping in
  over 250 ms with the screen's fade from black. With the opaque-backing
  option, or on a renderer that cannot soften the view, a darkening scrim and
  vignette stand in. Back resumes the game. RESUME closes the screen at once
  (section 8), but the softened view, or the scrim standing in for it,
  releases over 250 ms as the modal backdrop does (section 4): the session
  keeps drawing the closed screen over the running game for those 250 ms,
  with no input and no cursor. Pausing again during the release reopens the
  screen at once, and a disconnect or level load ends the release. Every
  activation after a release shows the screen again and ramps the softened
  view back in, including a return through a page's Back. Every opening, and
  every return after a release, focuses RESUME; a page's Back returns the
  focus to the item that led there.
- **Objectives page** (sections 13.7 and 14.11). OBJECTIVES opens the
  objectives display in its Remastered form as a page of the pause:
  - **Hand-off.** Choosing it docks the bands as a page hand-off does and
    carries OBJECTIVES into the title slot. At 550 ms, when a stock page
    would appear, the stock entry motion plays: the back bar (black 0.80 over
    the leading 45%, under the framing bands so their rim light keeps its
    strength) slides 220 u in over 150 ms, then the heading, plates, text and
    screenshots fade in over 100 ms. The stock frames lead the text at 0.50;
    here they fade in with it, because their 0.40 is baked into their paint.
  - **Plates.** Every open objective is reachable, newest first, as a plate of
    the stock construction on the 143 u pitch: the marker at 0.40, the title
    in Lowpixel 0.20 wrapping to two lines at 308 u, the 134x100 u screenshot in its
    black border and the description in #D0DEB6 wrapping without a limit,
    the plate growing with it. The frames rest at 0.40, baked into their
    paint.
  - **Completed.** Under COMPLETED and its count, the objectives completed on
    this map follow, newest first: the title only, at 0.40 behind a check.
    The stock serial closes the list, at the 13 dp type floor. With no open
    objective one plate shows the stock static screenshot and its line beside
    it, in Lowpixel 0.31 and #D0DEB6.
  - **Scrolling and Back.** The list scrolls under its bar with the wheel, the
    stick, the keys or a drag; the bar holds focus. The pause's prompt bar
    gives way to the page's, Back alone at 532,441 u in the docked bottom
    band ([page prompt bars](#page-prompt-bars)), and Back (or the back input) fades
    the page while the bands come home. The page closes when they arrive; a
    second Back during that leave changes nothing. In the Strogg family
    Back's glyph takes #FFCC00 and its verb R_Strogg. A reopened list starts at its first entry, and a pause that closed
    without Back, as a console load closes it, opens at home without the
    page.
  - **Data.** The game publishes each objective's title, description and
    screenshot, and the completed ones, with `retainedPauseState`. The
    session shows a screenshot only when it is a plain, installed image
    name. Every level load asks the game for all the level's objective
    screenshots (`retainedLevelImages`) after it spawns the map and resolves
    them inside the load, so the page reads no picture mid-frame; they include
    the screenshots of the objectives the player holds, whose entities removed
    themselves when given, so a savegame load resolves them too. The game
    keeps the completed objectives per map, unsaved, so the save format is
    unchanged. The newest save's time is read once in the level load and
    restamped by each save, so opening the pause lists no files.
  - **Strogg.** The Strogg page keeps the construction with #FF9000 frames,
    #FF9900 markers, an R_Strogg heading and the STROGG NET serial. Its
    return plays the translation again.
- **Strogg pause** (`guis/menu/pause_strogg.q4ui`, section 13.7 and the atlas
  Strogg pause). After Kane's stroggification the pause takes the Strogg
  family; it offers the same actions, level block and confirmations.
  - **Frame.** The bands keep their frame but trade the 45-degree notches for
    30-degree shoulders and downward teeth. Their rim light, and the circuit
    traces etched in them, are #F59512, over a warm light band and #FFB060
    crosses.
  - **Plates and labels.** The plates end in a 30-degree shoulder at the end
    of their target (357 u), outlined by their rail. Markers are slanted, as
    the atlas draws them. Labels are R_Strogg in #FCFFC8, turning #FFCC00 on
    focus.
  - **Level block.** The block takes a card chamfered 10 u at every corner,
    with the stock Strogg HUD static added faintly inside it. The levelshot
    sits in a chamfered orange frame.
  - **Translation.** Every label arrives in runes and plays a short form of
    the credits translation (section 8). The rune copy sits on the label's
    baseline at 1.2 times its cap height. It cross-fades into R_Strogg while
    both copies pop 6% larger and settle.
  - **Timing.** GAME PAUSED translates from 60 ms over 500 ms under the scan
    bar, arriving white and settling. The actions follow, 120 ms plus 45 ms
    per row, over 200 ms each, then EXIT. The level block's lines come after
    them, and a map's own objectives summary fades in with its heading. The
    prompt bar and the time line are readable from the start. Returning from
    a page plays the same once the home content shows.
  - **Focus.** A focused plate runs the scan bar under its label. The bar's
    wrapper fits the label, and the bar slides by its right inset, so its
    head sweeps in from the leading edge and rests 12 u past the label in any
    language.
  - **Input and reduced motion.** Input works from the first frame. Reduced
    motion shows the translated labels at once.
  - **Choosing it.** The session asks the game once a level, with the
    `retainedPauseFamily` menu command, whether the player is Strogg (the
    `player_strogg` definition, from game/medlabs on). Every single-player
    level load resolves both pause documents. When the Strogg pause cannot
    present (not installed, unable to load, or stopped drawing), the Marine
    pause stands in for the rest of the session. A game module that does not
    answer keeps the Marine pause.
- **Loading** (section 14.17). Replaces the stock `generic`, `splevel`,
  `mplevel` and `intro` loading GUIs; a map's own loading GUI stays, and so
  does a mod's own copy of a stock one: a stock-named GUI that the mod's own
  game directory (`fs_game` or `fs_game_base`, other than openQ4's, the stock
  game's or the Awakening's) supplies. The
  levelshot, reticle grid, framing bands, brackets and dot matrix frame the
  level name, its message line (the difficulty in single player, the game type
  in multiplayer) and the objectives plate. The levelshot drifts in by 3% over
  the load unless motion is reduced. The Remastered progress sits in the thick
  part of the bottom band: LOADING above a 240 u bar and, under the bar, the
  loader's phase with its place among the four phases (map, world, assets,
  finishing) or the asset queue's count, and the percentage in the value
  color. When the load finishes, the phase line reports the load time and
  LOADING becomes the continue prompt for the last-used device: the desktop
  prompt, or the controller family's south button and CONTINUE
  ([prompt glyphs](#prompt-glyphs)).
  Multiplayer keeps the band low: a card on the leading side holds the
  server's name in its header, then its address in Profont, the mode and the
  limits, the players by team, and the server's message (`si_motd`), and a
  finished multiplayer load reads JOINING, since multiplayer never waits for
  a click; joining by the Welcome card, the screen stays up until the card
  presents ([hand-off](#hand-off-to-the-welcome-card)). The card stands on 384 u, clear of the lower corner bracket, and
  its parts flow, so it grows upward with what it holds. The game module names
  the mode, the limits it enforces (the scoreboard's rule:
  `MPResolveMatchLimitFor`) and whether it has teams from the server info the
  session passes (`retainedLoadingServer`); a game that does not answer leaves
  the session's own strings and one list. In team modes the players stand in
  two columns under MARINES and STROGG in their team colors, otherwise in one
  under PLAYERS, six names a column and then "+N more", over a line of
  spectators and players still connecting. The players are those known as
  the load starts: a listen host's own (bots included) before its map change
  wipes their user info, a client's on a map change before `InitGame` clears
  them, and on a fresh connection those the server names in an optional block
  after its connect response's server info (`ConnectRoster`: a tag, a length,
  then each player's slot, flags, team and name), with this client joining
  them; a server that sends none, or a malformed one, leaves the card without
  players and the connection goes on. Names and the message lose Quake 4's
  color and icon escapes, control bytes and malformed UTF-8, keep whole
  characters within their limits (48 and 256 bytes), and never read as a
  `#str_` key. The message wraps to at most three lines in the notices color;
  the console turns backslashes into slashes, so a cvar can carry no typed
  line break. The arsenal fills the thick band's leading part, from its riser to
  the bar: two rows of ten 16 u icons on a 17 u pitch, one for each kind of
  item as it spawns (the stock row's twenty), each fading in over 150 ms in
  its color code (Appendix B.4). The stock icons are colour-coded materials,
  one stage tinting the icon image; the session reads the image and the tint
  from the material's definition and publishes them with the icon
  (`load_icon_src_N` and `load_icon_r/g/b_N`), then plays its fade
  (`arsenalN`). In single player the same part of the band runs tips while
  the level loads: a TIP tag over one tip of at most two lines of Lowpixel
  14 dp, changing every 6 s with a 250 ms cross-fade between two slots
  (`loading_tip_a`/`_b`, `tipA`/`tipB`, by text alpha). The session starts
  each load at a different tip and moves to the next from the load's redraws
  (`PublishRetainedLoadingTip`); once the level is ready the continue
  prompt, which runs across that part in most languages, takes the band.
  The 18 tips state Quake 4 single-player mechanics checked against the game
  code and stock data (the blaster's charge, the flashlight, medics and
  techs, firing at people and screens instead of a use key, objectives on
  TAB and the pause page, quick save, the machinegun's zoom, headshots,
  armor, barrels, grenades, self damage, pickups that wait, dropped guns,
  vehicle repair, the shotgun's reload and leaving a vehicle), and in every
  shipped language each fits its two lines, which the gate test measures
  from `lowpixel.ttf`. The name strip darkens the message line so it reads
  over any levelshot.
- **Single Player and Campaign** (`guis/menu/singleplayer.q4ui` and
  `campaigns.q4ui`, sections 8 and 9, the sub-page level of 1.10). The Single
  Player page titles itself in the top band's slot at 39,19 u, where the
  title's carry lands. Its Campaign and Arena sections each open a
  sub-page, Arena the [Arena page](#arena-page). The page arrives with the
  focus on CAMPAIGN and the Campaign sub-page on the campaign being played,
  QUAKE 4 unless it is the expansion:
  - **Sub-page state.** The top band stands one notch pitch (97 u) further
    toward the trailing edge while the bottom band stays docked. The parent
    title is the crumb in the band's thin span at 39,12 u and 0.40, cut at
    the step, and the sub-page title starts at the step's foot, 136,19 u.
  - **Crumb fit.** The crumb takes 80 % of the title's size, or less where the
    title would overrun the 83 u span, but never less than the 13 dp type
    floor; past that it is cut. The generator measures each shipped
    language's title in `marine.ttf` as the host lays it out (advances at
    pixels per em, no kerning) and plays that language's crumb timelines,
    chosen by `sys_lang`. English and German shrink to the floor and fit;
    Italian and Polish are cut.
  - **Going deeper.** Accept plays `main_menu_selection` once, and Campaign
    plays the page's half: its plates fade over
    150 ms while it sweeps 640 u toward the trailing edge over 300 ms. Its
    title becomes the crumb over 150 ms. From 50 ms the top band steps
    (`frame.step`, accel(150, 150) over 300 ms) and the CAMPAIGN label
    carries from its row into the slot at the step's foot, scaling to the
    title size. At 350 ms the session presents the sub-page: its plates and
    title show at once and its backing fades in over 150 ms. Back while the
    page goes deeper reverses the change from where it stands, over 150 to
    300 ms by the distance the band has stepped.
  - **Back.** The sub-page title drops at once and the sub-page sweeps 640 u
    toward the leading edge over 300 ms (`screen.return`, linear, as the
    page's sweep going deeper) while its backing fades over 250 ms
    (`content.out`) and the band steps back from the start. The crumb returns
    to the title slot over the last 150 ms. At 300 ms the page returns,
    fading its plates and content in over 150 ms with the focus on Campaign.
  - **Session.** The two levels are two documents. The session
    (`BeginRetainedSubpage`, `UpdateRetainedSubpage`, `RetainedSubpageEvent`)
    plays the leaving document's half and presents the other at the
    hand-over: 350 ms going deeper and 300 ms back. Under reduced motion it
    hands over at once and the arrival's 80 ms fade is the change. Mid-change
    a key's release still reaches the leaving document, so a key held into
    the change retires normally; Back going deeper reverses it, and other
    input and requests wait for the hand-over. Anything else taking the
    screen abandons the change. Leaving the screen places a document at rest
    while it is hidden, so it never presents moved, and every arrival shows
    its plates at once and fades its backing in (`content.in`). When the
    other level cannot present, its stock selector opens at once, as before.
  - **A campaign.** Accepting QUAKE 4 or THE AWAKENING continues to the
    [New Campaign page](#new-campaign-page), Campaign's sibling sub-page.
  - **Arena.** ARENA goes deeper the same way, its own label carrying from
    its row, and Back from Arena returns with the focus on ARENA.
- **MODS** (section 6, the list dialog). MODS on the title's plinth opens the
  title's own dialog instead of the stock pop-up: the modal construction grown
  from 136 u to 280 u, 320 u wide with its centre 17 u above the view's, as the
  modal's is, titled MODIFICATIONS. Its body holds the installed mods (the
  stock list's mods, at most 32) under NAME and VERSION headings and the olive
  rule, on 20 u rows lit as the save lists' are, with a scrollbar, and under
  the list the selected mod's author, release date, required engine and
  directory. LOAD MOD and CANCEL stand where YES and NO do. The session
  publishes the mods as the dialog opens, the current game's selected; the
  dialog opens on CANCEL and moves to the selected mod once its contents show.
  A row's first Accept selects its mod; Accept on the selected mod, or LOAD
  MOD, restarts the engine into it as the stock LOAD MOD does. The wordmark
  dims to 40% gray, as for EXIT. The pause has no MODS.
- **Confirmations** (section 6, the 480 dp confirmation width). EXIT and both
  pause quits ask in the stock confirmation dialog. The screen beneath stays
  in view in soft focus (`modal.softfocus`: a 5 u, 7.5 dp blur at 0.80
  saturation, never dimmed). The glow is cut to the dialog's 320 u
  rectangle: graded only vertically, at half strength at the rectangle's top
  and bottom edges, gone 40 dp beyond them, and fading out over a further
  16 dp past each side. With the opaque-backing option
  (`ui_retainedOpaqueBacking 1`), or on a renderer that cannot soften the
  screen, the stock 0.94 scrim covers it instead, and the glow keeps the stock
  column, exactly the rectangle's width. The stock art's black
  0.70 silhouette sits inside it. The silhouette starts 6.5625 dp in from
  each side, as `popup_top`, `popup_mid` and `popup_btm` do, so a 6 dp lit
  margin and the lit slot outline it. The title starts at the foot of the
  slot's leading flank. Its capitals hang from the raised sections' top line
  into the lit slot, as the stock title's do, with a black outline at 0.85
  extruded 1 dp around the strokes behind the fill. The outline is eight
  opaque copies composited once as a group, so their overlaps never darken it
  past 0.85. The body and the actions sit where the stock ones do: the body's
  first baseline is 87.5 dp down, and the actions start 96 u down. They open
  and close with the stock motion (section 8, `modal.enter` and
  `modal.leave`).
  - Opening brings the soft focus (or the scrim), the glow and the frame in
    over 200 ms, and the title, body and actions appear together at its end,
    when NO takes focus.
  - Closing hides the contents at once. After 50 ms the soft focus (or the
    scrim) and the glow release over 250 ms, and the frame over 200 ms for
    Exit or 250 ms for the pause quit; then the modal closes.
  - The title's Exit modal also dims the wordmark to 40% gray over 200 ms,
    and restores it from 50 ms over 150 ms as it closes.
  - Timeline [completion programs](event-programs.md#completion-programs)
    show the contents and close the modal. A reopen during the leave takes it
    over, so the leave never completes and the modal stays open.

Band motion follows the stock choreography (section 8): opening reveals the
content, choosing a page sends the bands to the page dock (`depart`), a
pop-up only dims the content (`departPopup`), and returning from a page
brings the bands back (`returnHome`). On depart the home plates fade over
250 ms, but the plinth and its secondary links go in 50 ms (`content.out`);
they return together with `content.in`. Control feedback follows the same
section: hover responds at once, focus over 80 ms, a press over 60 ms, and
every return to rest is linear over 300 ms. As the bands dock, the chosen
navigation label travels from its row into the page's title slot at 39,19 u
and settles at the 18 dp screen-title size (`title.carry`, section 13.8),
where the stock page then shows its own title; the session plays it only for
a real page hand-off, and the home state starts without it.

## Hand-off to the stock pages

The title and pause screens cover the legacy main menu while it rests at its
home state; the legacy menu stays active underneath and keeps every page.
Choosing SINGLE PLAYER or SETTINGS runs the legacy home button's own action
(MODS opens the title's own dialog), and the retained screen plays its
departure for the 550 ms (200 ms for a pop-up) the stock page takes to appear.
Back on a legacy page returns to the retained screen as soon as the page starts
to leave. Back on the retained Single Player page runs the legacy menu's own
return from that hand-off (`returnFromSinglePlayer`, as the stock selector
does) unseen, and the menu rests at home at once, so the title comes back
with its bands returning from the page dock
(`idSessionLocal::ReturnRetainedSinglePlayerHome`). UPDATES runs the legacy
button's update check in place: no pop-up opens, so the title keeps its
content and its input until the check's answer arrives as a stock message
box. A stock message box over the home (that answer, a failed connection)
keeps the retained home drawn behind it, still and without input, where the
legacy menu stood, and the home takes the screen back as it was when the box
closes. LOAD GAME, SAVE GAME, RESTART LEVEL, DEMOS, CREDITS and MULTIPLAYER
hand off the same way to their retained pages ([Load Game](#load-game-page),
[Save Game](#save-game-page), [Restart Level](#restart-level-page),
[Demos](#demos-page), [Credits](#credits-page) and
[Multiplayer](#multiplayer-page)), and to the stock pages from the Strogg pause
or when a page cannot present. The departure fades the plinth
and the prompt bar with it, since a page brings its own
([page prompt bars](#page-prompt-bars)). CONTINUE, RESUME, QUIT TO MENU and EXIT are handled by the session
directly.

Documents request these through a typed `session.menu` operation whose
`command` argument must be in the adapter's allowlist; the session drains the
queued requests in `DispatchCommand` and ignores requests from any view other
than the presented home screen.

## Runtime additions

- **Strogg faces.** Documents may name the `r_strogg` and `strogg` (rune)
  faces besides `marine` and `lowpixel`; any other name still draws in
  Chain. The rune face maps the Latin alphabet and leaves most punctuation
  blank, so the host folds what it lacks for the rune copies. Punctuation it
  has no rune for, combining marks and general punctuation become a space.
  Of the letters past ASCII it keeps Latin-1's, with ß, Æ, Ø, Ð, Þ and Ł
  folded to S, E, O, D, P and L; every other letter, in any script, folds
  onto the alphabet. A translated label therefore never shows the face's `?`
  in its runes, which the gate test checks against every shipped string.
- **Image nodes.** An `image` node draws a relative VFS image or material,
  with `image-fit` (fill, contain, cover), `image-align-x/y`, `image-color` and
  `image-blend` (normal or additive light). Sources are validated, can be bound
  to application strings, and are never animated.
- **Path blends.** Vector paths take `blend: additive` (premultiplied light)
  or `blend: multiply`, drawn through the engine's `_retainedMultiply`
  material. Inside a composition layer, or on a host without the material, a
  multiply path darkens by its luminance instead and is counted.
- **View-height canvas.** A document can declare `canvas: {height: 720}`: one
  canvas height of dp spans the view height at every resolution, replacing
  display density and user scale, so stock 640x480 measurements map to 1.5 dp
  per unit and the 4:3 composition stays centered.
- **Overflow under a transform.** RmlUi clips an overflow container inside a
  transformed group with the container's box geometry instead of a scissor.
  The renderer now applies that clip as an exact rectangle for translation and
  scale; a rotated or rounded clip is limited to its bounds and counted in
  `clipMaskFallbacks`. Before this, such content was never clipped (the loading
  bar lit its whole length at any progress).
- **Additive pictures in layers.** An add-blended picture used to write its
  texture alpha. Inside a composition layer (any ancestor fading through
  `opacity`), the layer then composited the picture's whole rectangle as an
  opaque box: the wordmark darkened its rectangle as the title departed.
  Additive pictures now draw with zero coverage, which leaves their light
  unchanged; `ui_retained_layer_pool.py` checks the conversion.
- **Layer row order on Vulkan.** Opacity below 1 and masks composite through
  engine render textures, which keep GL row order on every backend. Since
  2026-09-25 the Vulkan executor has recorded render textures lower-origin and
  marked 2D writes canonical, but the host still sampled Vulkan layers
  top-origin. Every composite therefore read mirrored, empty rows: on these
  screens the navigation and action plates, the markers and the modal
  title's outline vanished on Vulkan, and the SYSTEM page's faded and masked
  parts share the same path. No release shipped it. Composites now sample GL
  row order everywhere. `ui_retained_layer_pool.py` checks the composite
  coordinates and pins the executor's side of the contract.
- **Backdrop soft focus** (REN-016). A node's `backdrop-blur` and
  `backdrop-saturate` soften the frame beneath it (see the
  [document format](document-format.md#typed-values-and-layout)). RmlUi reads
  the backdrop into a pushed layer through its backdrop filters, and the
  runtime hands that layer to `Host::SoftenBackdrop`. The engine binds the
  base surface and copies the window into `_retainedBackdrop`, then runs the
  `glsl/retained_blur.glsl` program twice. The first pass blurs
  horizontally into a scratch target, over every row the second reads (3
  sigma beyond the region). The second blurs vertically and desaturates into
  the backdrop layer. Each pass is opaque and takes up to 49 bilinear taps,
  spaced out for a wide sigma. OpenGL needs GLSL support; Vulkan compiles the
  program at run time; GLES keeps the fallback. The capture and both targets
  keep GL row order, as the layer composites do.
  `ui_retainedSoftFocus` reports whether a frame can be softened, and the
  documents show the scrim when it cannot. `ui_retainedProfile` counts the
  backdrop passes and fallbacks. The SYSTEM page's Apply/Keep/Revert
  confirmation and unapplied-changes dialogs soften the screen beneath them
  too, keeping their 0.6 backing as the fallback
  (`tools/ui/update_system_soft_focus.py`).

## Pictures and precaching

A document's own pictures resolve when it loads. With the gate on at startup,
the title and the pages it reaches load with the stock menus, the Load Game
page with the generic picture a save without one shows, and each
single-player level load resolves the pause documents, the pages only they
reach and the restart screen (each once a session), and the level's
levelshot, so opening a screen reads no file mid-frame
([startup preload](runtime-performance.md#startup-preload)). Every
multiplayer map's levelshot and every Arena match's precache on the front
end's idle frames, and Create Server and the Arena page each read their own
still waiting when they open ([Create Server](#create-server-sub-page),
[Arena page](#arena-page)). `_retainedMultiply` is a generated material and
needs no precache. These preloads and precaches run as a load, so they report
no late loads, and an engine reload (a campaign's game directory, an Arena
match's game module) resolves them again, the levelshots at once. A picture
first drawn outside a load, such as a document opened with `testGUI`, the
gate switched on in the menu, or a save's own screenshot (as on the stock
page), still loads on demand and reports it once.

## Diagnostics

`ui_retainedStatus` prints one `OPENQ4_RETAINED` line: the gate, the SYSTEM
and multiplayer opt-ins, the presented home screen, which home documents are loaded, whether a
hand-off is in progress, whether a closed pause screen or multiplayer card
is releasing the softened view, the multiplayer card covering the game's menu
(`mp=escape`), the number of live retained views (0 while the gate is off)
and, after `stock=`, the documents that fell back to their stock
screens this session (`-` when none). `ui_retainedTrace 1` also logs each
session request with whether the adapter accepted it, and each loading phase as
`RETAINED_LOADING_PHASE`. With `developer 1` the log also names the reason for
each quiet fallback.

## Initializing screen

While the engine starts, before any menu exists, `PrintLoadingMessage` paints
one frame for each step (section 14.17). With `ui_retained` on, that frame
draws `guis/loading/initializing.q4ui` (FLOW-057, ART-031), generated by
`tools/ui/retained_initializing.py`: the stock picture (`splash.tga`) rebuilt
as vector layers on the 640x480 canvas, with the field and rings extended to
any view. Each ring is a run of one measured tone, because the picture is
8-bit and its rings step by single levels; neighbouring rings differ by a
level, so they compile without coverage antialiasing (a path's `antialias`,
[vector paths](vector-paths.md)). The plate band turns counterclockwise once
every 180 s and the teeth clockwise once every 120 s beneath the fixed
clamps, emblem and lettering. QUAKE 4 is traced from `q4text`'s white core by
`tools/ui/trace_wordmark.py` into `tools/ui/wordmark_trace.py`, committed as
data so building the screens never needs the retail asset; its halo is
vector light (the letters dilated 5.5 u, blurred with a 2.25 u sigma, added in
#FF8340 at 0.10), drawn as strokes of rising width whose strengths add up to
the blurred dilation's falloff. The title's wordmark uses the same letters
with the texture's own halo (3.7 u, 4.4 u, #FF8F40 at 0.40) in 24 steps.

The four accents run on the presentation clock with the rings: a warm light
sweeping clockwise once every 10 s with arcs catching its leading edge, a
halo behind the emblem breathing between 0.40 and 1.00, fourteen embers and a
glint crossing the letters in 900 ms every 9 s, clipped to them by a mask of
their contours. The status line is Marine 16 dp on 418 u; each new step
flickers it in from 0.35 over 120 ms, over a 168 u rule of one segment per
step (done 0.55, pending 0.15, the current one pulsing between 0.62 and 0.95).
A timeline starts from the value it finds, so the flicker and the glint step
to their start in their first millisecond. Every loop ends on its
reduced-motion pose, because reduced motion jumps decorative tracks to their
ends: the rings at rest, the light as the upper-left key light, the halo at
0.80, and no embers, glint or pulse.

Every message advances the step, including the five sent before the
renderer can draw, so the rule marks the steps that passed unseen; a later
LOADING... (the render system's own, once its device opens) keeps the current
step. The retained interface manager starts later, so the screen owns its
view in `RetainedUI.cpp` (`RetainedUI_DrawInitializing`), released once
`session->Init` has made the menus or when the game shuts down. During a long
step the session's pacifier repaints it (`Common_InitializingPacifier`) on the
engine thread, at most 30 times a second, never inside another screen update.
A frame the document cannot draw (a mod without it, or `ui_retained 0`)
draws the stock picture and line, which repaint only at a step.
`ui_retainedTrace` logs each frame's step and the rings' angles.

## Weapon wheel

With `ui_retained` on, single player's weapon wheel is
`guis/hud/weaponwheel.q4ui` (WID-033, section 14.6), generated by
`tools/ui/retained_weapon_wheel.py`: the Marine wheel's eleven positions in
strip order, clockwise from the top, around a hub at the view's center. Each
segment is a 0.50 HUD plate between 104 and 232 dp with 6 dp gaps and 2 dp
corners, holding the weapon's glyph, its number (the stock key that selects
it), its reserve in Chain 17 dp and a curved eight-cell gauge in the weapon's
color code; a tick bezel circles the ring. The glyphs are vector silhouettes
traced from the stock `item_<weapon>` masks by `tools/ui/trace_glyphs.py`
into `tools/ui/glyph_trace.py`, committed as data on a 24-unit master, so
building the screens never needs the retail textures. An unowned weapon
keeps its segment as an outline; a weapon without ammunition shows the red
prohibition sign over its dim icon. The selection's backing rises to 0.70
under an additive #616F26 light, its icon turns #FF8000 inside the strip's
#B2CC80 ring and the segment moves 8 dp outward; a notch on the inner edge
marks the previous weapon. The hub is the machinegun scope's double ring and
compass over a signal screen, turned to face the selection, naming the weapon
in Marine 12 dp above its `clip / reserve` in Chain 21 dp.

After Kane's stroggification the HUD, and so the wheel, take the Strogg
family: `guis/hud/weaponwheel_strogg.q4ui`, generated by
`tools/ui/retained_weapon_wheel_strogg.py` on the same state. Its eleven plates
are angular and straight-edged, each with a raised leading tooth on
30-degree shoulders, a chamfered trailing corner and a notched inner edge, on
a ring twisted 4 degrees backward, the polar form of the Strogg shear. Eight
slanted #FF9000 cells along each outer edge hold the reserve, under the stock
Strogg static (`s_static`) masked to the plates and drifting a tile every 8 s.
The core is an octagonal plate with a lower tab, circled by two dashed rings
turning at 0.2 and 0.5 turns a second in opposite directions, and thin circuit
paths join it to every owned plate, brightening for the selection. Icons are
#F59512 at 60%, the selection #FFCC00 inside a #F2AD0B ring, and every label
is R_Strogg over its rune copy. The wheel opens as a translation: the plates
boot in a scrambled order 12 ms apart, each under an additive #FFD06F flash,
the rings spin up, the circuits trace out from the core, the grain settles
from 0.60 to 0.20, and the readouts translate from runes clockwise from the
top, 18 ms apart, before the name. Selecting translates the name and its
ammunition again while the scan bar slides in behind the name; closing drops
the plates out in scrambled order, 8 ms apart, then fades the core, rings
and grain. Reduced motion stops the rings and grain and changes names at
once.

The game (`idPlayer`, `src/game/Player.cpp`) owns the wheel and loads it with
the HUD. It asks the engine for the "weaponwheel" HUD component, or
"weaponwheel_strogg" for a Strogg body (`idCommon::RetainedHudGui`,
`RetainedUI_HudDocument`), which names the document only while `ui_retained`
is on, so no game module names a retained document. A held wheel button opens
it after 180 ms on the current weapon; a
shorter tap swaps to the previous weapon without opening it. While it is
open, either stick past 35% selects the segment under its angle with 4
degrees of hysteresis (`idCommon::GetControllerSelection` reports the more
deflected stick, never inverted like look), and the mouse moves an invisible
selector that selects once it passes 32 dp; inside both the selection holds,
and an unowned weapon cannot be selected. Releasing equips the selection
through `SelectWeapon`, which keeps the current weapon when the selection has
no ammunition; a pause, death, cinematic or vehicle closes the wheel without
switching. The game keeps running at full speed: unlike the classic wheel
there is no slowdown and no blur. The player keeps moving until the wheel
opens, so a tap never stalls a run; while it is open the view holds and the
weapon is lowered, as with the classic wheel. The `open`, `select` and `close`
events play the Marine transmission: the hub powers on from a slit, the
segments deploy clockwise 8 ms apart, each fading in and growing from 90%, a
static burst rises and decays, and on close the segments drop out while the
hub collapses. Reduced motion keeps only short opacity changes.

VR keeps the classic wheel, whose cursor follows the weapon hand, and so does
`ui_retained 0`. The game API is 52: a game module reaches the new `idCommon`
call through its table, so it must match its engine.

Multiplayer has its own wheel (WID-034), `guis/hud/weaponwheel_mp.q4ui`, the
Marine wheel generated with `weapon_wheel_document(multiplayer=True)`: the
gauntlet in the blaster's place, icons in the weapon color code (the pending
weapon at full alpha, the rest at 0.60), the multiplayer gauge's own tints, and
the reserve alone in each segment and the hub, since multiplayer weapons have
no clips. `wheel_team` gives the player's team color to the selection ring,
the selected number, the bezel's ticks, the hub's double ring, the compass's
bright dot and the pointer: #AAE355 for Marines and #FF8E00 for Strogg, whose
selection light is #6B3A08; Deathmatch and Tourney keep the stock olive. The
multiplayer player (`src/mpgame/Player.cpp`) runs it on the local client only,
once per new frame, never in a prediction rerun, and it draws over the HUD and
its multiplayer overlay. The wheel is the client's own: releasing equips
through the weapon impulse the client sends to the server, and a tap sends the
last-weapon impulse. While it is open the engine holds the view, takes the
sticks from movement and keeps fire and zoom out of the usercmd
(`idCommon::SetWeaponWheelCapture`), since the server runs the same usercmds;
keys still move the player, a new map always frees the capture, and the game
is never slowed.
`openq4_weaponWheel hold | aim <x> <y> | release` (cheats) holds and aims the
wheel without its button for headless tests, and `ui_retainedTrace` logs its
opening, selections and release.

## Load Game page

LOAD GAME on the title and on the Marine pause opens
`guis/menu/loadgame.q4ui` (FLOW-004), generated by `tools/ui/retained_saves.py`.
The Strogg pause keeps the stock page, whose family the Marine page would
break.

- **Hand-off.** The home hands off as to a stock page: the bands dock and the
  LOAD GAME label carries into the title slot while the content, the plinth
  and the prompt bar leave. At 550 ms, when the stock page would appear, the
  session presents the page (`BeginRetainedPage`, `UpdateRetainedPage`). A
  stock page lives in the main menu over its home's backdrop and docked bands,
  so this page is the stock page's content alone, and the home keeps drawing
  behind it as the departure left it (`DrawRetainedPageHome`): the title's
  levelshot montage, or the pause over the softened game. The carried label
  is the page's title. The page's plates show at once and its panel and
  backing fade in over 150 ms (content.in). Back returns the home at once with
  the bands, as from a stock page, and the carried title leaves at once, as
  `anim_loadOut` drops the stock page's. The page loads with the stock menus
  at startup, so the click never waits on its 0.1 to 0.2 s load; with the gate
  switched on later, it loads at the first click.
- **Composition** (section 9). The selected save's picture, 183x137 u at
  25,78 u, fitted inside a 1 u #414624 frame on black 0.60, with its date and
  time at 37,215 and 37,230 u (Lowpixel 18 dp). LOAD GAME and DELETE GAME are
  section navigation plates: `b2_dark` at 21,256 and 20,293 u (Appendix B.1),
  208x52 u, with the band rows 13-37.4 u, the lower-leading cut from row 32,
  the #CCCC51 rail and the fill opaque to 57 %, half at 72 % and clear by
  94 %. The list is at 217,78 u, 410x325 u, under SAVE NAME and LOCATION
  (Lowpixel 13 dp at 0.40) and an olive rule at 0.26. Its 20 u rows put the
  name and the level at the stock tabstops, 0 and 180 u, in Lowpixel 15.8 dp
  on `bg_line`'s light: #FF9C00 at 0.01, 0.16 under the pointer or focus and
  0.41 for the selected save, with the white 0.50 rule. The focused row takes
  the home plates' orange inset, and the scrollbar sits in the list's last
  16 u. The prompt bar is in the bottom band, Back at 532,441 u
  ([page prompt bars](#page-prompt-bars)). The stock page's backing (`grad2`: `bg_darkgrad2`
  black at 0.60 across the view, clear to 18.4 % of its width and opaque from
  34 % to 91.8 %) darkens the trailing side.
- **Saves.** The session lists the saves newest first, as LoadGame accepts
  their headers. Each is named from the label it wrote (`^:name\t^0level`,
  colors removed), or by its slot. An autosave shows its level's loadscreen;
  any other save shows its own screenshot, reread when chosen; one with
  neither shows the stock page's generic picture. The list holds 64 rows.
  With more saves, NEWER SAVES and OLDER SAVES rows page by 64, selecting and
  focusing the first save of the older page or the last of the newer one.
- **Choosing.** The page opens with the newest save selected and focused. A
  row's first Accept selects its save; Accept on the selected save, or LOAD
  GAME, loads it. DELETE GAME asks with the stock confirmation, focused on NO;
  YES deletes the save with its picture and label, and the save that takes
  its place is selected. LoadGame refuses a save it cannot use before it
  leaves the current game, and records why (`loadGameFailure`). The page then
  stays, and the reason shows over the foot of the picture in #E46D56 until
  another save is chosen: the level is not installed, the save is damaged or
  comes from an incompatible version, or it cannot be read. A save still
  there after DELETE GAME stays selected and says it could not be deleted.
- **No saves.** The list's place shows the empty state of section 13.13: NO
  SAVED GAMES, one sentence saying where saves come from and, at the title,
  NEW GAME, which opens the Single Player page. The plates rest disabled.
- **CONTINUE.** The title's CONTINUE line showed the save's raw label, color
  codes and tab included. It now shows the save's name, then its level and
  when it was written. A newest save that LoadGame refuses opens this page on
  it with the reason, as LOAD GAME on it would, instead of nothing.
- **Text.** The page adds `#str_231100` to `#str_231107` to all twelve tables.
  The generator measures every language's text in its box and fails
  otherwise: the plates, headings and pager rows on one line, the empty
  sentence on two and a reason on the strip's three. NEW GAME's plate widens
  to its longest translation.

`ui_retainedTrace` logs `RETAINED_PAGE present` when the page presents. The
capture scenarios `loadgame` (three saves made in the level, then the title:
select, delete, Back, load, and the page over the pause),
`loadgame-empty`, `loadgame-failure` (a seeded save the list accepts and
LoadGame refuses) and `loadgame-pages` (70 saves) drive it by console
command. Hyphenated ids such as `row-1` must be quoted there, since the
console tokenizer splits an unquoted `-`. On a shared machine,
`--set win_allowMultipleInstances=1` lets a capture start beside another
openQ4 client; without it, a second client exits at once, leaving no log.

## Save Game page

SAVE GAME on the Marine pause opens `guis/menu/savegame.q4ui` (FLOW-004), also
generated by `tools/ui/retained_saves.py`. The title has no game to save, and
the Strogg pause keeps the stock page.

- **Hand-off.** As the Load Game page's: the pause docks its bands and carries
  SAVE GAME into the title slot, the page presents at 550 ms over the pause,
  which keeps drawing behind it, and Back returns the pause with the bands.
  The page loads with the first single-player level. Each arrival starts with no
  name and no save selected, as the stock page's field did, and focuses the
  name.
- **Composition** (section 9, the stock `p_savegame`). The saves fill the
  content column from 35,78 u, 570x285 u, under SAVE NAME and LOCATION and the
  olive rule, on the Load Game page's 20 u rows, here 550 u wide with the
  scrollbar in the last 20 u. Under them the name plate (`b1_dark` at 4,370 u,
  484x52 u, at 0.40: the band rows 13-37.4 u starting 33 of its 512 texels in,
  the rail up the leading edge, down the cut and along the foot, the fill
  opaque to 44 %, half at 62 % and clear by 88 %) holds the name field at
  49,382 u, 344x20 u, in Lowpixel 20 dp (textscale 0.28). SAVE GAME is the
  section plate at 397,370 u; its label may run past the plate's faded end
  toward the canvas edge, as the stock one did in French. The prompt bar is
  in the bottom band, Back at 532,441 u ([page prompt bars](#page-prompt-bars)), over
  the stock page's backing.
- **The name.** A [text field](numeric-fields.md#text-fields) of up to 32
  bytes. Typing into it opens it, as Accept does; an empty field shows "Name
  this save" in white 0.35, and while it is edited empty the line above the
  plate asks for a name in #E46D56. Enter writes the name into the page's
  `save.name` (`ui.state.set`) and saves under it, as the stock field's
  onEnter did.
- **Choosing.** A row's first Accept selects its save and puts the save's name
  in the field, unless a name is being typed there, which a selection never
  replaces. Accept on the selected save, or SAVE GAME, saves under the name.
  With a name typed but not yet entered, SAVE GAME returns the focus to the
  field, where Enter saves. SAVE GAME rests disabled without a name.
- **Saving.** A name no save holds saves at once; the new save becomes the
  newest, selected, and the name stays. A name a save already holds asks
  first with the stock OVERWRITE SAVE? dialog, focused on NO, its body naming
  the save in orange; YES saves over that save even if the field has changed
  since. An autosave is refused with the stock WARNING notice, "You cannot
  save over an autosave.", and CLOSE alone. A save the session refuses says
  why in the same notice instead of the stock message box: the player must be
  alive, the drive must have space, a failed mission cannot be saved, and
  anything else reads "The game could not be saved." The stock page's own
  overwrite check now shares the page's (`Session_MenuSaveSlotState`).
- **Text.** The page adds `#str_231108` to `#str_231113` to all twelve tables;
  the last three carry the stock code table's reasons, which the Polish and
  Russian tables lack. The generator checks every language's text in its box.
  The overwrite title runs on over the dialog's raised trailing section, as the
  stock title ran past its rectangle, because Italian and Spanish overrun the
  lit slot; the notice's lone CLOSE is 210 dp wide for German.

## Restart Level page

RESTART LEVEL on the Marine pause opens `guis/menu/restartlevel.q4ui`,
generated by `tools/ui/retained_difficulty.py`. The Strogg pause keeps the
stock page, and the title has no level to restart.

- **Hand-off.** As the Load Game page's: the pause docks its bands and carries
  RESTART LEVEL into the title slot, and the page presents at 550 ms over the
  pause. It loads with the first single-player level and opens at the level's
  difficulty (`g_skill`), focused.
- **Composition** (section 9 "New game", the stock `p_newgame`, which openQ4's
  in-game Difficulty page retitled). Five section plates (`b2_dark`) on a
  30 u pitch from 21,172 u: PRIVATE, CORPORAL, LIEUTENANT, GENERAL and
  WARLORD. The chosen one is lit at full strength with an orange label,
  whatever its feedback, as the stock `skillCheck` lit it. Its description
  stands at 239,181 u in Lowpixel 18 dp (textscale 0.25) at 0.60. RESTART
  LEVEL is the enlarged primary plate (`b6_light` at 237,222 u, 356x43 u: the
  band rows 4-27 of 32, a 45-degree cut from row 14, the olive rail and fill
  at 0.49 fading out by 95 %, at 0.40 and full strength under the pointer or
  focus) with its 18 u corner marker and the Marine label (textscale 0.33).
  The prompt bar is in the bottom band, Back at 532,441 u
  ([page prompt bars](#page-prompt-bars)), over the stock page's backing.
- **Choosing.** A plate chooses its difficulty on the page; nothing reaches
  the session. RESTART LEVEL restarts the level at the choice
  (`RestartLevelAtSkill`, with the autosave's loadout), and Back leaves the
  level's difficulty as it was. The in-game page offers no turbo mode, as the
  stock one hid it.

## New Campaign page

Accepting QUAKE 4 or THE AWAKENING on the Campaign sub-page opens
`guis/menu/newcampaign.q4ui`, generated by `tools/ui/retained_difficulty.py`:
the difficulty choice for that campaign (section 9 "New game", FLOW-050).
Arena opens its own sub-page, the [Arena page](#arena-page).

- **Sibling sub-page.** New Campaign is Campaign's sibling and holds the same
  sub-page state: the top band one notch on, the bottom band docked, SINGLE
  PLAYER as the crumb, and the campaign's name as the title at the step's
  foot. Between the two only the pages move (`page.leave` and `page.enter`,
  section 8). Accepting a campaign plays `main_menu_selection` and
  Campaign's departure, 8 dp toward the leading edge and out over 140 ms
  (cubic 0.4, 0, 1, 1) with its title and prompt bar. At 140 ms New Campaign
  presents and arrives from 12 dp toward the trailing edge over 220 ms (cubic
  0.16, 1, 0.3, 1) with its title, backing and BACK. Back mirrors it: New
  Campaign leaves toward the trailing edge, and Campaign comes back from the
  leading edge with the focus on the campaign that led there.
- **No first-frame flash.** An arrival starts from nothing, so each page waits
  hidden after it leaves: New Campaign always, Campaign when it left for New
  Campaign. Any other arrival shows Campaign at once, as before.
- **Composition.** The Restart Level page's (openQ4's stock `p_newgame`): the
  five difficulty plates with the chosen one lit, its description, and START
  GAME as the enlarged primary plate. TURBO MODE stands under it at 237,272 u
  (the same plate, its Marine label at textscale 0.27) with its value at
  489,280 u, ON in orange or OFF, as the stock `turboCheck` showed it. The
  prompt bar is in the bottom band, Back at 532,441 u
  ([page prompt bars](#page-prompt-bars)), over the stock page's backing.
- **Choosing and starting.** Each arrival starts at CORPORAL with turbo mode
  off, as the stock page did. A plate chooses and TURBO MODE toggles on the
  page; nothing reaches the session until START GAME, which sets `g_skill`
  and `g_turboMode` and starts the active campaign's first map (airdefense1,
  or the Awakening's first map in `q4xbase`).
- **Session.** `OpenRetainedNewCampaign` resets the page and begins the change
  from Campaign (`BeginRetainedSibling`, then `PresentRetainedSibling` at the
  hand-over). Input waits for the hand-over, as in a sub-page change; the
  change is too short to reverse. After the engine reloads into the
  Awakening's game directory the page presents at once. Campaign learns at
  its activation whether it arrives back from New Campaign (`sibling_back`)
  and on which campaign (`awakening_chosen`). Under reduced motion the
  session hands over at once and the arrival fades in within 80 ms. When the
  page cannot present, the stock difficulty page opens as before.

## Arena page

ARENA on the Single Player page opens `guis/menu/arena.q4ui`, generated by
`tools/ui/retained_arena.py`: the Arena campaign's browser as Single Player's
second sub-page (section 9 "Arena Campaign", FLOW-011), in the sub-page state
Campaign holds, titled ARENA under the SINGLE PLAYER crumb, over the stock
page's backing.

- **Change.** ARENA plays Campaign's change with the ARENA label carrying
  from its row, and the browser presents at 350 ms; Back plays the page's
  half and Single Player returns at 300 ms with the focus on ARENA (the
  session sets `from_arena` first). Back while the page goes deeper reverses
  the change as for Campaign. Where the campaign must first reload the engine
  into its game directory or game module (after an Arena match, say), ARENA
  selects it as before and the page presents once the engine is back.
- **Authority.** `idArenaCampaign` publishes the browser's state into the
  stock browser and, while it is loaded, this page (`PublishGui`), its words
  already in the player's language, and opens this page where it can
  (`OpenBrowser`, through `idSessionLocal::RetainedArenaPage`). The page's
  verbs reach the campaign's own commands (`RETAINED_ARENA_VERBS`), which
  check each again, and the campaign's events (the entrance, the result, the
  reset question) reach whichever browser presents. With the gate off, or
  when the page is not installed, cannot load or stops drawing, the stock
  browser presents as before.
- **Ladder.** The five tiers form a vertical ladder of plates in the section
  navigation at 16,72 u (170x40 u on a 44 u pitch), and the chosen tier's
  matches a column beside it at 196,72 u: three qualifiers (36 u), then the
  boss match on a larger 50 u plate whose orange edge shows while it waits.
  Each plate is the section plate's dark band, rail, corner marker and Marine
  label (QUALIFIER 18 dp, TIER 20 dp, the boss 22 dp across the plate) with
  the published status under it: LOCKED, AVAILABLE, BOSS READY or COMPLETE. A
  locked one is dimmed with the lock and cannot be chosen; a completed one
  carries the check and a green edge; the chosen one is lit over an orange
  wash. A plate's first Accept chooses it; Accept on the chosen tier moves to
  its chosen match, and Accept on the chosen match starts it. The bumpers (and
  Q and E) step to the next open tier either way, unless a modal or the
  entrance holds the page (`arenaStepTier`).
- **Briefing and detail.** Under the matches the chosen tier's briefing: its
  name, description, the path to the next tier and the rule. The detail column
  at 404 u shows the match's levelshot, name, description, map, game type,
  roster, limits and skill, then DIFFICULTY between its - and + steps (each
  out at its end of the range) and START MATCH, the enlarged primary plate,
  live only while the campaign can start the match. Under the ladder,
  CAMPAIGN PROGRESS with its count and a bar filling by a twentieth a match,
  CAMPAIGN COMPLETE once the last boss falls, and RESET PROGRESS.
- **Reset.** RESET PROGRESS, live while there is progress, asks the
  campaign, which raises `arenaResetReveal`; the stock modal, grown 14 u and
  titled RESET PROGRESS, says what it clears and asks on CANCEL. RESET clears
  the progress; CANCEL or Back keeps it.
- **Entrance.** START MATCH (the campaign's `arenaMatchLaunch`) plays the
  stock entrance on the page: the screen darkens to 0.72 over 320 ms as a
  section 6 card (12 and 3 dp cuts, the stock panel's orange rail) scales in
  from 94 % with the match's levelshot dimmed under it, ENTERING THE ARENA, the
  match, an orange rule, its game type and map and PREPARE FOR COMBAT; from
  760 ms the card fades and the screen goes to black for the campaign's
  hand-over at 1250 ms. While the campaign holds the entrance
  (`arena_transitioning`) every control is out and the session takes no
  request, Back included.
- **Result.** Back from a match the campaign opens the page and raises
  `arenaResultReveal`: the stock ledger as the modal grown to the stock
  report's 396 u, titled MATCH REVIEW and revealed in the stock phases from
  the black the match ended on, which lifts over 720 ms. The result shows over
  its green, red or amber accent with the match from 260 ms, the message and
  score from 610 ms, what it unlocked and the awards (or CAMPAIGN COMPLETE)
  from 930 ms, and at 1260 ms the actions, with the focus on the second:
  RETRY after a defeat or REPLAY after a win or a draw, where the match can be
  played again, then NEXT after a win short of the last, RETURN, or CONTINUE
  after an aborted match. Back dismisses it.
- **Pictures.** As it loads with the menus, the campaign queues every
  match's levelshot for the front end's idle frames, which precache a few a
  frame once a menu has presented for a second, and the page reads any still
  waiting when it opens, so choosing a match never loads one. The session's
  retained preloads and those precaches run as a load
  (`declManager->SetInsideLoad`), so they report no late loads, and an engine
  reload (an Arena match's game module, a campaign's game directory)
  precaches the levelshots at once, inside its load.
- **Captures.** `arena` drives the page from Single Player with progress
  set, `arenamatch` starts a real match and disconnects from it, and
  `arenafail` holds the server's port (on the loopback interface, which
  `net_ip` names for it) so the launch fails and the page reports MATCH
  ABORTED. The campaign appends its launch behind the capture script, so a
  match stage continues through the after-load hook (`@aftermap`) or through
  appended `vstr` steps (`exec` would insert ahead of the launch), and the
  reloaded game module logs to `logs/openq4-match.log`.

## Demos page

DEMOS on the title opens `guis/menu/demos.q4ui` (FLOW-013), generated by
`tools/ui/retained_demos.py`: the Load Game page's construction for the demo
library that openQ4's legacy browser (`guis/demo_menu.gui`) shows. In game,
during playback, or when the page cannot present, the legacy browser opens
as before; playback keeps its legacy controls.

- **Hand-off.** As the Load Game page's, from the title: the bands dock and the
  page presents at 550 ms over the title's montage. Nothing carried DEMOS from
  the plinth, so the page's own title fades in with its panel and backing
  (content.in), as a stock page's does. The page loads with the stock menus at
  startup.
- **Composition** (sections 9 and 13.13). The selected demo's map in the stock
  preview, 183x137 u at 25,78 u (its levelshot as the pause's level block
  finds it; render demos have no map and show the generic picture), with its
  kind, status and details below it in Lowpixel 18 dp; a status this build
  cannot play is in #E46D56. PLAY, DELETE and REFRESH are section plates on
  the stock 37 u pitch from 256 u. The list is at 217,78 u under NAME, MAP,
  DATE and DURATION and the olive rule, its rows on the stock 20 u pitch.
  Above the headings the filter tags (section 13.13) stand at 43 u: small
  header-band plates with a 45-degree cut and an olive rail, 0.28 unset and
  0.60 with a close cross when set, lit under the pointer or focus. The
  prompt bar is in the bottom band, Back at 532,441 u
  ([page prompt bars](#page-prompt-bars)), over the stock page's backing.
- **Library.** The session rescans `demos/` for every publication and lists
  the recordings newest first, filtered: MULTI-VIEW, RENDER, LEGACY or
  INCOMPLETE, the legacy browser's filters, or every recording with no tag
  set. A tag sets its filter, and Accept on the set tag clears it. The list
  holds 64 rows and pages through more with NEWER DEMOS and OLDER DEMOS rows,
  as the Load Game page does. Each row and detail line is capped as the legacy
  browser caps it.
- **Choosing.** The page opens with the newest demo selected and focused. A
  row's first Accept selects its demo; Accept on the selected demo, or PLAY,
  plays it where it can play, through the legacy browser's own player. A demo
  that could not start leaves the page here, saying so over the foot of the
  picture. DELETE asks with the stock confirmation, which names the demo;
  YES deletes the recording, which must lie in the save path's demo
  directory, and the demo that takes its place is selected; one that could not
  be deleted stays selected and says so. REFRESH rescans and keeps the
  selected demo wherever it now stands.
- **No demos.** The list's place shows the empty state: NO DEMOS and one
  sentence saying where demos come from, or that the filter hides them all.
  The plates rest disabled, and REFRESH takes the focus.
- **Text.** The page adds `#str_231114` to `#str_231120` to all twelve tables;
  the generator measures every language's text in its box and fails
  otherwise.

## Restart screen

When the player dies in single player and the respawn wait runs out, the game
reports the death (`died`), the level unloads, and `guis/menu/restartmenu.q4ui`
(FLOW-005, generated by `tools/ui/retained_death.py`) presents in place of the
stock `guis/restart.gui`.

- **Composition.** The stock screen's: black at 0.94; the QUAKE 4 wordmark as
  the title draws it (ART-031), in q4text's 258x63 u box at 145,91 u with its
  halo shrunk to the box; the popup art 360 u wide at 140,129 u to 341 u, lit
  by its glow column and with no title in its slot; and four enlarged primary
  plates (`b6_light`, 324x38 u from 159,162 u on a 40 u pitch, their Marine
  labels at textscale 0.33 and 14 u corner markers): RESTART, LOAD GAME, MAIN
  MENU and EXIT GAME. The plate under the pointer or focus explains itself in
  the line at 362 u (Lowpixel textscale 0.20, centred), each with the stock
  screen's sentence; the line belongs to its plate, since a control's feedback
  reaches only its own subtree.
- **Choosing.** RESTART has the focus on arrival. RESTART, LOAD GAME and MAIN
  MENU run the stock screen's own commands (`HandleRestartMenuCommands`):
  restart from the last checkpoint or autosave, else the map; the main menu at
  its Load Game page; or the main menu. EXIT GAME asks with the stock exit
  confirmation, focused on NO.
- **Session.** `OpenRestartMenu` presents it, loaded with the pause so a death
  never waits on its load. With the gate off, without the file, or after its
  view stopped drawing (then for good), the stock screen presents instead.

## Credits page

CREDITS on the title opens `guis/menu/credits.q4ui`, generated by
`tools/ui/retained_credits.py`, as LOAD GAME opens its page.

- **Source.** The generator reads openQ4's stock `p_credits` for its layout and
  choreography, never its words: the Raven logo's light-up (`anim_credits`),
  then thirteen screens of headings and names, each line twice, in the rune
  face and in Lowpixel, with an orange scan bar behind each heading. It
  compiles each screen's `onTime` script (its sets, and its colour,
  `textscale` and rect transitions, a later transition retargeting an earlier
  one from where it stands, the stock rule) into tracks, and lays the logo and
  the screens end to end in the stock order (1-8, 11, 12, 10, 9, 13) in one
  timeline of about 111 s that repeats. A chain of completion programs back to
  the logo would be a cycle, which documents may not hold.
- **Words.** Every line shows `credits.<window>`, which the session fills from
  the legacy main menu's credits window of the same name when the page opens
  (`PublishRetainedCredits`, which finds the lines through
  `UI_RetainedStateNames`), so the generated page carries none of the names.
- **The credits translation** (section 8). The runes fade in over 2000 ms; then
  each heading translates from runes to Latin over 1000 ms as its scan bar
  slides in from the leading edge and dims, each name follows 50 ms later over
  500 ms, settling from white to #D5FFA7, both copies popping 0.02 textscale and
  settling, and the screen leaves 640 u toward the trailing edge over 500 ms.
  The scan bar is an additive #FF8000 ramp brightening to its head, with soft
  edges. The logo is the stock picture, tinted from black to #D6FFA8 and back
  as additive light.
- **Page.** The page stands on the stock backing at full strength (section 8:
  opaque for Credits) under its own CREDITS title, which fades in with the
  panel (content.in) since nothing carried it from the plinth; the prompt
  bar's Back, alone, is at 532,441 u ([page prompt bars](#page-prompt-bars)). Every arrival starts the loop over from the logo, and leaving
  stops it with every screen out. In game, or when the page cannot present,
  the stock page opens as before.

## Multiplayer page

MULTIPLAYER on the title opens `guis/menu/multiplayer.q4ui`, generated by
`tools/ui/retained_mp_page.py`, as LOAD GAME opens its page: the stock
Multiplayer page's level (section 9 "Menu levels", FLOW-050).

- **Page.** It holds the page state Single Player holds: the bands docked,
  MULTIPLAYER in the top band's title slot at 39,19 u, where the title's carry
  lands, the sections on the home navigation plates from 181 u (the stock
  page's first button) with BACK under them, and the page's description in
  the content column at 395,190 u. The sections are the stock page's GAME
  BROWSER as JOIN GAME, CREATE SERVER, and SETTINGS as PLAYER SETUP (section
  13.7's name, which keeps it apart from the title's SETTINGS). The stock
  FRIENDS LIST, which the stock menu hides and nothing handles, is gone. The
  generator fails when a language's label or description would not fit.
  Arriving from the title focuses JOIN GAME, the primary action.
- **Sections.** CREATE SERVER goes one level deeper to the retained
  [Create Server sub-page](#create-server-sub-page), and JOIN GAME to the
  retained [Join Game sub-page](#join-game-sub-page) where the session offers
  it; otherwise, and for PLAYER SETUP, a section opens its stock page. The
  page leaves as
  the stock Multiplayer page leaves for one: its plates fade over 150 ms while
  it sweeps 640 u toward the trailing edge over 300 ms, the title and prompts
  going with them. At 500 ms the legacy menu takes the screen in its
  Multiplayer page state. The session first runs the menu's timelines up to
  now, then writes `desktop::curr` 3 (which keeps the menu's `onActivate` from
  resetting it home), `desktop::active` 1 and the page (`desktop::dest` 14,
  17 or 18); the menu's `openMultiplayerPage` then places that page and plays
  its arrival with the bands docked. The session writes these as the menu's
  own `set` does, taking each variable off its declared expression: a value
  written without that is restored to the declared 0 by the menu's next
  evaluation, and the title would come back.
- **Back.** A stock page's BACK, Escape or video-warning path leaves as
  before. Where its out-animation used to bring the stock Multiplayer page
  back, it asks the session (`multiplayerOpen`), which presents the retained
  page at once with the focus on the section that led there, or, where the
  page cannot present, sends `openMultiplayerStock` for the stock page. BACK on
  the page returns the title: as from any page before a stock page has opened,
  and after one the legacy menu leaves its Multiplayer page for home
  (`leaveMultiplayerPage`) while the title returns from the page dock.
- **Fallback.** In game the stock menu keeps its pages. Where the page is not
  installed, cannot load or stops drawing, MULTIPLAYER runs the stock button
  and the stock pages return to the stock Multiplayer page. A main menu
  without the three events the page's routes run (a mod's copy of an older
  one, say) keeps its own Multiplayer page the same way, quietly, as a home
  screen keeps a main menu that lacks one of its pages.
- **Captures.** `multiplayer` opens the page, CREATE SERVER and its BACK, JOIN
  GAME's retained browser on the LAN source (`openq4_browser source lan`, so
  no master server is asked) and its BACK, PLAYER SETUP and its BACK, then
  BACK to the title; the stock pages' BACK runs through `openq4_guiAction`.

## Create Server sub-page

CREATE SERVER on the Multiplayer page goes one level deeper to
`guis/menu/createserver.q4ui`, generated by `tools/ui/retained_create_server.py`,
as Single Player's CAMPAIGN goes to Campaign (section 9 "Menu levels",
FLOW-050). It offers everything the stock page does, so it is the default
under `ui_retained`: the session's list of what it lacks
(`RETAINED_CREATE_SERVER_MISSING`) is empty, and while anything is listed
there only `ui_retainedMultiplayer 1` offers the page.

- **Change.** The Multiplayer page plays `subpageEnterCreate`: its plates fade
  over 150 ms while it sweeps 640 u toward the trailing edge, MULTIPLAYER
  becomes the crumb, and from 50 ms the top band steps one notch while the
  CREATE SERVER label carries from its row to the step's foot. The sub-page
  presents at 350 ms, its content and backing fading in over 150 ms with the
  focus on CREATE SERVER. BACK plays the sub-page's `subpageLeave` and the
  Multiplayer page returns at 300 ms onto CREATE SERVER (`from_create`); Back
  while going deeper reverses the change from where it stands, and reduced
  motion changes at once. The session's change of level now takes a sub-page
  kind (`retainedSubpage_t`) where it took Arena's flag.
- **Content.** The stock `p_mp_create` over the stock page backing: MAP
  SELECTION over the chosen map's levelshot (183x137 u at 45,75 u) and the
  maps the chosen game type plays (42,219 u, 20 u rows, 64 a page with pager
  rows past them); SERVER OPTIONS from 228,73 u as section 7 setting rows on
  the stock 24 u pitch, the value column 180 u in; ADVANCED OPTIONS under
  them; the enlarged CREATE SERVER plate at 244,397 u; the prompt bar in the
  bottom band, Back at 532,441 u ([page prompt bars](#page-prompt-bars)). The rows are the stock page's: Server Name (a text field),
  Server Type, Dedicated, Gametype (the stock twelve), Auto Balance, the limit
  (Frag Limit, Capture Limit for the CTF families or Control Time for
  DeadZone), Time Limit, Max Players, Min Players, Allow Voting, and Team
  Damage, or Tourney Round Limit for Tourney. Auto Balance and Team Damage
  lock outside team modes, as the stock rows dimmed. ADVANCED OPTIONS opens the
  stock popup's options in the modal construction grown to the popup's size:
  Use Password, Set Password, Remote Console Password, Allow Server Side
  Mods, Weapon Stay, Pure Server, Server Upstream Rate, Ready Mode, Allow
  Spectators, Do Warmup, Allow Voice Chat, Allow Buying, Fill With Bots, Bot
  Skill, the map cycle's text field and VIEW LOCAL SERVER BAN LIST. The two
  passwords are masked text fields
  ([text fields](numeric-fields.md#text-fields)) that may be empty; Set
  Password dims and hides its text while Use Password is off, as the stock
  popup hid its field. Its value column starts 220 u in, where every
  language's label and choice fit; the stock one ran past its rows. The
  dialog's height follows its rows, and it rises from 23 u to stay centered
  once it outgrows that.
- **Ban list.** VIEW LOCAL SERVER BAN LIST, a row with a chevron at the
  dialog's foot as the stock link sat on its pitch, asks the session for the
  list and opens PLAYER BAN LIST over the dialog, nested in its modal scope as
  the stock popup opened over its own: the MODS list dialog's construction,
  as wide as ADVANCED OPTIONS or wider where a language's REMOVE BAN or CLOSE
  needs it, the bans under NAME and GUID on 20 u rows (the first 32; removing
  one brings up the next), or a line saying nobody is banned. A row's first
  Accept chooses its ban; REMOVE BAN, enabled once one is chosen, removes it
  and the list stays open; CLOSE and Back return the focus to VIEW LOCAL
  SERVER BAN LIST. The session reads the bans as the stock popup does (the
  game's `PopulateBanList` rows, `N:  name<tab>guid`), keeps their GUIDs, and
  removes the chosen one through `RemoveGuidFromBanList`; the game writes
  `banlist.txt` at its shutdown.
- **Settings.** The session owns them. It publishes each one as its CVar holds
  it (`create.*`), and each control asks for a change through its own verb
  (`RETAINED_CREATE_SETTINGS`), which the session checks against the CVar's
  range before it writes it. The player counts keep their order: a lower
  maximum lowers the minimum, a higher minimum raises the maximum, as
  retail's session kept the stock page's `checkMinPlayers` and
  `checkMaxPlayers`; openQ4's session now handles those again, and the stock
  popup's `populateBanList` and `handleServerAdminRemoveBan`, so the stock
  page's ban list lists and removes bans as retail's did.
  The game type lists its maps again as the stock MAPScan does: the maps whose
  decls play it, else every multiplayer map, `si_map`'s own chosen where the
  list has it, each named without the color codes the stock list drew.
  Choosing a map writes `si_map`. The text fields hand over their text when
  entered (`RETAINED_CREATE_TEXTS`), at most the stock fields' 25 bytes for
  the name, 200 for the map cycle and 16 for each password, never cut inside
  a character; the map cycle and the passwords may be empty. Every
  multiplayer map's levelshot precaches on the front end's idle frames, a
  few a frame once a menu has presented for a second, and the page reads
  any still waiting when it opens, so browsing the maps never loads one.
- **CREATE SERVER** starts the server through `StartMenuServer`, which the
  stock page's `startMultiplayer` now calls too: the upstream rate's client
  limit and the listen-server warning ask first, then the menu closes and the
  server spawns.
- **Fallback.** In game, or where the page is not installed, cannot load or
  stops drawing, CREATE SERVER opens the stock page.
- **Captures.** `createserver` goes deeper, chooses CTF, opens ADVANCED
  OPTIONS, turns Use Password on and types a password, which shows as its
  mask while editing and once the session has taken it, opens the seeded
  ban list, removes the second ban and closes it, closes the dialog and
  climbs back; `createserverstart` chooses Team DM and starts a listen server
  on the loopback, following the reloaded module.

## Join Game sub-page

JOIN GAME on the Multiplayer page goes one level deeper to
`guis/menu/joingame.q4ui`, generated by `tools/ui/retained_join_game.py`, as
CREATE SERVER goes to Create Server (section 9 "Menu levels" and "Lists",
FLOW-050). It is the stock browser (`p_mp_browse`) on the sub-page frame the
two share (`tools/ui/retained_subpage.py`). It offers every control the
stock page does, so it is the default under `ui_retained`: the session's
list of what it lacks (`RETAINED_JOIN_GAME_MISSING`) is empty, and while
anything is listed there only `ui_retainedMultiplayer 1` offers the page.
`ui_retained_gate.py` maps each of the stock browser's buttons to the page's
verb or node, or to that list; the stock PunkBuster column's sort is exempt
(section 9's symbol table: a discontinued service, no replacement column).

- **Change.** The Multiplayer page plays `subpageEnterJoin`, CREATE SERVER's
  change with the JOIN GAME label carrying from its row to the step's foot;
  the sub-page presents at 350 ms with the focus on GET NEW LIST. BACK plays
  its `subpageLeave` and the Multiplayer page returns at 300 ms onto JOIN GAME
  (`from_join`); Back while going deeper reverses the change, and reduced
  motion changes at once.
- **Content.** MOD (the mod filter) with its spinner at 27,46 u and SOURCE
  with its INTERNET and LAN tags (section 7's cut tags, the list's source lit
  at 0.60 and the other at 0.28, each as wide as its longest translation) at
  324,46 u; the server list at 23,83 u under its column headings, on the
  stock 18 u rows (64 a page, with pager rows past them): the favorite, the
  password and the dedicated server's symbols at the stock symbol stops, then
  SERVER NAME from the stop the stock PunkBuster column held, PING, the
  repeater's symbol, PLAYERS, GAMETYPE and MAP. The symbols sit on their
  16 dp tiles with the cut upper-leading corner as section 9's symbol table
  draws them: a gold star, a padlock, a server case with its green power
  light, a television with its antennas and color bars. Each ping follows
  its network quality (section 13.13), drawn as four bars rising like slider
  ticks from PING's stop:
  - four bars to 60 ms, three to 120 ms, two to 200 ms and one above
    (`Session_NetworkQualityBars`, which takes a bar off per 2% of packet loss
    where loss is known; the browser hears none);
  - lit in `status.success` at three and four bars, `status.warning` at two
    and `status.error` at one, the rest faint;
  - 1.6 u wide, 0.9 u apart, rising from 2.4 to 7.2 u on the row text's
    baseline, with the ping's text following at 292 u.

  The columns after the
  name are wider than the stock ones, so every language's heading fits beside
  the sort's chevron, which follows the heading's longest translation. The
  scan's status line at 41,291 u (175 u, which every language's status fits),
  a player search's tag after it and CLEAR SORTING; the scan's progress bar
  across the list's width at 21,312 u with its notice over it from 41 u (the
  stock load bar); REFRESH LIST, GET NEW
  LIST, JOIN IP ADDRESS and FIND PLAYER/CLAN down the leading column from
  19,330 u on a 26 u pitch, so the fourth clears the bottom band, each as
  wide as the longest label of any (Italian's FIND PLAYER/CLAN); the chosen
  server's levelshot in the stock frame, at 240,337 u so the favorite toggle
  clears it; JOIN SERVER, enabled once a server is chosen, at 385,330 u, and
  under it the favorite toggle (ADD TO FAVORITES, or REMOVE FAVORITE while
  the chosen server is one); the prompt bar in the bottom band
  ([page prompt bars](#page-prompt-bars)). An empty list says so,
  unless a scan is still running: that no server was found, or, when the
  scan holds servers that the filters or a search all hide (`join.listed`,
  how many it holds), that none matches the current filters. A join from the
  page, by JOIN SERVER or JOIN IP ADDRESS, that fails or is aborted comes
  back to this list, as the stock browser kept it: when the menu next rests
  at home without a level, Join Game presents instead of the title, once
  (`retainedJoinReturn`); a join that loads its map forgets it.
- **List.** The session owns it. While the page presents it lists the
  servers the scan found and the filter passes, in the sort's order, a page
  at a time (`join.row<i>.*`, the ping's bars as `join.row<i>.quality`),
  with their count and how many the scan holds,
  the scan's status line (the stock page's `sortNotice`), whether a scan
  runs, its progress (`join.progress` and `join.notice`, the stock page's
  `loadPct` and `loadNotice`), the source, the mod filter (`filterMod`,
  which the scan writes on the legacy menu), the player search and the sort,
  and publishes again whenever the scan's revision moves (a server answered,
  a sort, filter or search changed, the status or the progress changed). The
  scan's read view
  (`idServerScan::VisibleServers`, `IsFavoriteServer`, `GetSorting`,
  `GetRevision`) lists exactly what the stock list shows. The servers' names,
  game types and maps are read as players' text (`Session_RetainedPlayerText`):
  escapes and controls dropped, never read as a `#str_` key; a nameless
  server shows its address. The chosen server's levelshot is the loading
  screen's choice for its map (`RetainedPauseShot`), looked up again only
  when the map changes and precached; a map path the browser may not look up
  (`idServerScan::ValidMapPath`: no parent references or absolute paths)
  shows the generic art.
- **Verbs.** INTERNET and LAN choose the source on the legacy menu
  (`gui::lanSet`, which the stock browser's scans read) and get a new list
  from it; GET NEW LIST gets a new list (the master server and the favorites
  on the Internet, the LAN otherwise) and REFRESH LIST asks again
  (`Session_ScanServers`, the stock `UpdateServers` and `RefreshServers`). A
  heading sorts by its column, and again the other way; CLEAR SORTING lists
  the servers as they answered. On a controller, west asks for the list
  again, as REFRESH LIST does, and north sorts it by the next text column
  (`joinSortNext`: PING, SERVER NAME, PLAYERS, GAMETYPE, MAP and round again,
  ascending, from PING while the list is unsorted or sorted by a symbol):
  section 13.5's secondary and tertiary actions, through the document's
  `onSecondary` and `onTertiary`, neither of which acts while a dialog is
  open. MOD's spinner shows the previous or next mod
  the list holds (`UpdateFilterByMod`, the stock arrows'). A row's first
  Accept chooses its server and Accept on the chosen one moves on to JOIN
  SERVER, which connects to the chosen server by the address the session
  kept. The favorite toggle adds the chosen server to the favorites or takes
  it off (`idServerScan::ToggleFavoriteServer`, the stock toggle's work for a
  server the page names). The choice follows its server through new orders
  and stays while a scan may list it again.
- **Progress.** The bar is the stock `load_bar3` tube in `marine.progress`:
  its alpha profile down the 14 u tube (a bright top edge, dim under the
  notice, a lighter foot), the track at 0.30 and the fill at 0.50, the fill's
  width the scan's fraction. Retail's scan published that fraction and its
  notice to the stock browser (`loadPct`, `loadNotice`); openQ4's had
  dropped both, so the stock bar stayed empty, and publishes them again
  (`idServerScan::GetLoadNotice` and `GetLoadProgress` for a menu that draws
  its own): "Getting list of servers..." while a new list waits on the master
  server, "Scanning for LAN servers..." as the LAN sweep starts, then the
  server that answered last with the count of listed servers heard from or
  given up on ("Scanning %d/%d: %s"; on the LAN "Scanning - Found: %s",
  across its one-second reply window), and once the scan completes the
  count it covered ("Scanned %d openQ4 Servers") on a full bar, which stays
  until the next scan or a clear. A refresh says nothing until a server
  answers, as retail's did. The fraction moves in whole percents, so a LAN
  sweep republishes the list at most a hundred times. The notice can name a
  server, so the page reads it as a player's text. Polish and Russian gained
  the three scan strings their tables lacked.
- **Server details.** The scan describes a server as the stock browser's
  tooltip shows it (`idServerScan::GetServerDetails`): its address, its
  players' names, and its settings as "label: value" lines (the map, the time
  limit, the limit its game type ends on, team damage, team autobalance, pure
  and spectators), its text read as the browser reads a server's. The limit
  follows the game's descriptor table (`mp/GameTypes.cpp`): the capture limit
  for the flag modes, the round limit for Clan Arena, Freeze Tag and Red
  Rover, DeadZone's control time, and the frag limit otherwise;
  `server_browser_contract.py` holds the scan's table to the game's. Retail's
  scan kept the stock tooltip for the row the pointer was over each frame the
  classic menu ran; openQ4's had published the selected server's players
  there and kept the tooltip hidden. The session keeps it again
  (`UpdateBrowserTooltip`, `idServerScan::GUIUpdateHover`, reading the
  list's `serverList_hover`). Polish and Russian gained the tooltip's labels,
  which their tables lacked, and French and Italian DeadZone's control time.
- **Details card.** The retained page shows those details in the stock
  tooltip's card as section 7's hover card, through the runtime's detail
  card ([interaction](interaction.md#detail-cards)). Each row names its row as
  the subject (`join.detail`). The pointer's row is the subject while the
  pointer moved last, and otherwise the focused row. The session publishes the
  row's server (`PublishRetainedJoinDetail`: `join.detail.address`,
  `join.detail.player0`-`10`, `join.detail.setting0`-`6`, read as players'
  text) and the row it describes (`join.detail.row`), and the card shows only
  while that matches the subject, so it never shows another server's details
  for a frame. The card is the stock 270x186 u: a black body at 0.9 with an
  olive border, cut at its lower-leading corner and bevelled at its
  upper-trailing one; the address in Lowpixel 14 dp; PLAYERS and SERVER
  SETTINGS at 0.4 over 11 player and 7 setting lines in Profont 13 dp on the
  stock 12 u pitch; and olive dividers at 0.32 as the stock draws them. It
  sits under the focused row (over it near the view's edge), or beside the
  pointer.
- **JOIN IP ADDRESS** opens section 6's entry dialog on the stock popup's
  pieces: the address field (99 bytes, as the stock field took), which Enter
  commits into `join.address` and connects with; CONNECT, while there is an
  address; CANCEL; and "your ip address:" with this machine's
  (`join.clientip`). The session connects through
  `Session_ConnectToTypedAddress`, which the stock popup's `inetConnect` now
  shares: no control, quote, semicolon or backslash, resolved, IPv4, IPv6 or
  loopback, the default port added. An address it cannot join keeps the
  dialog with the reason (`join.addressError`, the stock popup's message
  box text); one it can closes the dialog as the connect begins. Retail's
  session published "your ip address:" for the stock popup too
  (`getClientIP`, the first interface's address), which openQ4 had dropped:
  it is back, on `Sys_GetLocalIPAddress` (the first non-loopback IPv4
  interface, on both net backends).
- **FIND PLAYER/CLAN** opens an entry dialog with SEARCH FOR: and a name
  field (31 bytes, a player name's), which Enter or SEARCH applies:
  the scan hides every server without a player whose name holds the text,
  colors removed and in any case (`idServerScan::SetPlayerSearch`), and the
  search's tag shows it until its Accept ends it. Retail asked the master
  server for a player's or a clan's servers, which no master answers now, and
  openQ4's stock FIND PLAYER/CLAN did nothing; both pages search the list
  instead, and a clan tag is part of a player's name, so the stock PLAYER and
  CLAN choice is gone. GET NEW LIST ends a search, as retail's search was a
  list of its own.
- **Favorites.** A favorite on this machine (a loopback endpoint) now lists
  from the Internet source: the scan kept it as `localhost:port`, which only a
  DNS lookup parses, so it was never asked. Favorites are kept in numeric form,
  and a `localhost:` line saved before reads as `127.0.0.1`.
- **Fallback.** In game, or where the page is not offered, not installed,
  cannot load or stops drawing, JOIN GAME opens the stock browser.
- **Checks.** `ui_retained_gate.py` compiles the session's Join Game code
  against a scan double: the opt-in, the change and its reverse, the rows
  and their text, the choice following its server, the sorts and north's
  next column, each source's scans, the paging, the symbols, MOD's spinner, the favorite toggle, the
  levelshot (and the generic art for an unsafe map path), JOIN SERVER's
  address and the fallback; it also maps each stock browser button to the
  page or to `RETAINED_JOIN_GAME_MISSING`. The native screens check lays the
  page out at 1280x720 and drives its states, west and north (neither under
  a dialog), the two dialogs and the search's tag and the progress bar, and `server_browser_contract.py` runs the
  scan's read view, the per-server favorite toggle, the map-path check, the
  player search, the scan's progress (a LAN sweep, a new Internet list, a
  refresh, a clear, and what the stock browser receives) and the loopback
  favorites against the production `ServerScan.cpp`.
- **Captures.** `joingame` (opted in) goes deeper, gets a new Internet list in
  which the seeded favorite, a dedicated server the capture starts on the
  loopback (`SCENARIO_SERVERS`), answers (the master server cannot be reached
  from the loopback the client binds), sorts by name and clears the sort,
  sorts by PING and asks for the list again as north and west do
  (`openq4_retainedGui event onTertiary` and `onSecondary`), climbs back and
  returns, chooses the server (its levelshot and dedicated
  symbol shown), takes it off the favorites and puts it back, steps MOD to
  the next mod and back, searches for a player nobody is (the list empties
  under the search's tag until its Accept), and joins it, the game module
  reloading into game_mp; the progress bar is full once the scan completes,
  and the focused first row's details card shows under it.
  `joingameaddress` opens JOIN IP ADDRESS, enters an address it cannot join
  (the reason shows), then the server's, which joins it. `stockbrowser` runs
  the classic menu (`ui_retained 0`): its browser's GET NEW LIST fills the
  stock load bar again and names the count (`openq4_browser report` prints
  `loadNotice` and `loadPct`), and the server's row, treated as hovered
  without a pointer (`openq4_browser hover`), shows the stock tooltip with
  its address and settings, which no row hides again (the report prints the
  tooltip's state and items).

## Loading phase line

The session publishes the loader's phases to the retained loading screen
only while that screen presents the load: MAP before the render world loads,
WORLD before the game builds the level, ASSETS while the renderer works
through its model and image queues (their own loaded and total counts replace
the phase's place), FINISHING after the renderer's level load, and the load
time once the level is ready. The continue prompt follows `prompt.glyphs`
like every prompt ([prompt glyphs](#prompt-glyphs)). The wait for continue
redraws the screen each frame, so touching a controller or the mouse switches
it. The session no longer publishes its own `loading_controller`.

## Page prompt bars

Every page in the docked state carries section 13.4's prompt bar in the
bottom band's raised trailing section, which spans 375.1-717.9 u of the
canvas at every aspect. Back keeps the stock Back position: its 45 dp target
starts where the stock BACK plate's did, at 532,441 u, with its glyph 8 dp in
and its verb, BACK, 6 dp after the glyph. SELECT, the focused control's
Accept, ends 22 dp before Back's glyph. Each prompt is the title's
construction: the active device's glyph ([prompt glyphs](#prompt-glyphs))
and a Marine 14 dp verb at 0.80.

- **Pages.** Load Game, Save Game, Restart Level, New Campaign, Demos,
  Credits, Create Server, Join Game and the pause's Objectives page carry the
  bar in place of the stock BACK plate. Back is a button with the plate's
  control ID (`load_back`, `credits_back` and so on) and the page's Back.
  With the pointer anywhere in its target, its verb turns orange and its
  glyph lights from 0.85 to full; focus also underlines it, and a press
  insets it 1 dp. SELECT is a legend for Enter or the south button and never
  takes the pointer: a click would act on a focus that the pointer
  presentation hides. Credits and the Objectives page show Back alone, since
  Accept has nothing else to do there. The Strogg Objectives page tints its
  glyph #FFCC00 and sets BACK in R_Strogg #FCFFC8, turning #FFCC00.
- **Single Player, Campaign and Multiplayer** show the same bar in the same
  place, as legends, since their own BACK is in the content. The bar keeps
  its place between Multiplayer and Create Server or Join Game, and between
  Campaign and New Campaign. At 21:9 it stays on the raised section, where
  the view-anchored bar hung past it.
- **Fit.** `check_page_prompts` fails generation unless every shipped
  language's prompts fit, with the wider of each keycap and a controller
  button: Back's verb ends at least 8 dp inside the 4:3 view, and SELECT
  starts inside the bar, 5 u past the riser. Spanish is the tightest: 17 dp
  clear in Marine and 13 dp in R_Strogg.
- **Pointer.** The bar's box runs from 380 u to the 4:3 view's trailing edge
  and covers no control of the page's own. Legend bars, the title's and the
  pauses' included, never take the pointer, so the pause's faded bar cannot
  cover the Objectives page's Back.

Checks:

- The native screens test lays out each page's bar at 16:9 and 21:9 in the
  same canvas place, Back's glyph at every `prompt.glyphs` value and SELECT
  where it shows. The pointer over SELECT lights nothing and a click there
  does nothing; anywhere in Back's target the pointer lights Back, and a
  click runs the page's Back. Single Player's, Campaign's and Multiplayer's
  legends take no input.
- `ui_retained_gate.py` checks every page's glyph groups with the others'
  ([prompt glyphs](#prompt-glyphs)).

## Prompt glyphs

Every prompt shows the active device's glyph (section 13.5). This covers:

- the prompt bars of the title, Single Player, Campaign, the Marine and
  Strogg pause menus and the Multiplayer page, and the pages' own
  ([page prompt bars](#page-prompt-bars));
- the loading screen's continue prompt;
- the multiplayer cards' prompt bars and the Escape card's tab-strip keys
  ([multiplayer menus](multiplayer-menus.md)).

While the adapter-owned `prompt.glyphs` is 0, a prompt shows the keyboard's
keycap. At 1–5 it shows the controller family's button that does the same in
menus ([input routing](input-routing.md)): south for Enter's Accept, east for
Escape's Back, and the left and right shoulders for the cards' Q and E.

The glyphs are vector symbols in the family text color, whose shape and
letter carry the identity:

- **Xbox and Nintendo** print letters on a disc. Nintendo's A and B swap
  places: B on the south, A on the east.
- **PlayStation** prints its cross, circle, square and triangle on a disc.
- **Steam Deck** prints its letters inside a ring.
- **Generic** draws the four positions as a diamond, with the button's one
  filled.

Shoulders draw the bumper as a 13 dp plate rounded on its top corners with
the family's label in strokes:

- LB and RB on Xbox.
- L1 and R1 on PlayStation, and in an outlined plate on Steam Deck.
- L and R on Nintendo.
- A generic controller's plate is outlined, with a chevron pointing to its
  side.

On the Escape card's tab strip, the shoulder takes the keycap's 20x22 dp and
answers the tab key's states.

Accept and Back prompts follow Swap Confirm and Back
([input routing](input-routing.md)). Each also carries every family's button
at the other of the two positions (`<prompt>-<family>-swapped`), shown while
the adapter-owned `prompt.swapped` is set. So a Nintendo pad's SELECT shows
its east A and EXIT its south B, and a forced swap on an Xbox pad shows B and
A.

The letters and symbols are strokes in a 22 dp box, so no font or string
stands in for them. The prompt bar's glyph is 22 dp square and centered on
its verb. The title's and the pauses' bars still end where they did
whichever glyph shows, because they are anchored at their trailing edge; a
page's bar is anchored at Back's target instead. The Strogg pause tints
its glyphs as it tints its keycaps. The loading screen draws its south button
at 18 dp, beside CONTINUE.

Checks:

- `ui_retained_gate.py` compiles the backend's family mapping,
  `RetainedUI_PromptGlyphs` and the swap (`in_swapConfirmBack` and
  `idKeyInput::MenuControllerKey`) against stand-ins, pins every menu input
  path's translation, and checks that the 35 Accept and Back glyph groups
  carry both positions. It pins where the backend sets
  and clears the family, and checks that the adapter publishes before the
  frame draws. It also checks that each of the 17 documents with prompts
  binds every glyph to its family's index, and that both cards give the
  shoulders to their tab keys and Tabs prompt.
- The adapter harness checks the publication: once per change, in the
  session's state pushes, and never to a document without the state.
- The native screens test lays out the title's bar at every value, the
  pages' bars ([page prompt bars](#page-prompt-bars)), and the Escape card's strip
  keys and prompt bar at every value.
- The `prompts` capture forces each style through `ui_promptStyle`, then
  Xbox and Nintendo with `in_swapConfirmBack 2`, and touches no device. The `loading` capture shows the Xbox continue prompt.
  `mpcard-prompts` does the same on the Escape card over a listen server.

## Hand-off to the Welcome card

A multiplayer load that ends at the Welcome card, with `ui_autoJoin` off and
the card on, keeps the loading screen up, reading JOINING, until the card
presents (`BeginRetainedLoadingHold`), in place of the load's wipe: the join
never shows the bare match or the stock menu in between. The session draws
the held screen above the game and its menu, under any wipe and the console,
and user commands wait while it holds. On the frame after the card first
presents, the screen fades out over 250 ms (the runtime's 80 ms under reduced
motion; the document's `handoff`) over the card and its softened match, so
the card's first frame, the slowest, draws under the screen. Another screen
taking over (the stock menu in the card's place, another GUI, a retained
dialog) ends the hold with the same fade, and so does its ceiling, 5 s; a new
load or a stop drops it at once. Each load presents the screen whole again
(`present`).

The presentation clock stands still through the load and the rest of its
frame, then catches up at once, so the hold counts its 5 s, and may fade,
only from the first frame the clock moves. A listen server's card presented
in the load's own frame; a remote client's came 2 to 4 s after it, the menu's
first opening among that time.

## Validation

- `openq4-ui-retained-screens` (native) loads the four production documents,
  lays them out at 1280x720 (the title also at 1920x1080) and drives their
  state. It checks the schema additions, the additive and multiplied draws,
  the transformed clip, the emblem glint and its reduced-motion rule, the
  levelshot drift, the phase line, the percentage and the controller prompt,
  the multiplayer server card and JOINING, the hand-off's fade over 250 ms
  (80 ms under reduced motion) and `present` making the screen whole again,
  the arsenal's fade, tint and two rows, the tips (hidden until published, the slot cross-fade, the tag and
  two-line box inside the band, and the band given to the continue prompt
  when the level is ready, or to the arsenal in multiplayer), the title
  carry on both menus, the
  depth lean and its reduced-motion hold, the exit confirmation's lit margin,
  title placement, body placement and single 0.85 outline composite, its
  enter and leave timing with the contents and focus waiting for the
  entrance, a completion due before an event running before its program and
  a reopen during the leave, and that every action is an allowlisted session
  verb. For the Strogg pause it checks the faces, the rune copies of the
  published lines, the grain, the label wrapper that the scan bar spans, the
  translation's order and timing (RESUME by 320 ms, QUIT TO MENU and the
  level block still waiting, GAME PAUSED white and settling to #FCFFC8 at
  0.80), the focus scan bar, reduced motion and the soft focus. For the
  Objectives page it checks the hand-off and the entry motion, a plate per
  open objective with its description and screenshot, the title's 308 u
  wrap, a long description growing its plate, the completed rows, the
  scrollbar's focus and the down input scrolling the list, a snapshot
  restored with the page open keeping its scroll, Back closing the page with
  the bands home and a second Back ignored, a reopened list at its top, a
  pause opening without the page, the empty state's static and line, the
  level block's rows with their state, and the Strogg page's heading, serial,
  BACK prompt and return. It checks that the back bar lies under the bands.
- `openq4-retained-ui` and `openq4-ui-document` cover timeline completion
  programs: firing once at the end, cancellation, replay, pause, reduced
  motion and a snapshot taken while a completion is due, and the rejected
  schemas (unknown event, endless timeline, actions and completion cycles).
- `tools/tests/ui_retained_layer_pool.py` runs the host's layer allocation
  and its opacity and mask composites against a counted renderer, and pins
  the Vulkan executor's render-texture row order that the composites sample.
- `tools/tests/ui_retained_gate.py` qualifies the gate as described above,
  including the startup preload, the level-load precache, the loading phase
  line and the published pointer, and pins the frame pump order that lets
  RESUME retire the pause screen. It covers the release after RESUME: the
  closed screen kept for 250 ms and then let go, a new pause, a disconnect
  or a level load ending it, and nothing released when the pause hands over
  to another screen or the title closes; it pins the release's draw over the
  game and its 250 ms against the documents' timeline. It covers the Strogg pause's selection: the
  game asked once a level and again after each level load, the title never
  asking, and the Marine pause standing in for a Strogg pause that is not
  installed or stopped drawing. It pins the game's `retainedPauseFamily`
  answer, and compiles the host's face names and rune fold to check that
  every code point of the shipped string tables, and every other one below
  U+FFFF, folds onto a rune the face has or onto a space. It covers the
  Objectives page's data: the level's screenshots resolved inside the load
  (after the game spawns the map, before the media finish), only installed
  plain image names shown, the held objectives' screenshots among them, and
  the time line's last save: read once in the level load, not when the pause
  opens, absent with the gate off, and restamped by a save.
- The screens test also lays out the Single Player page and its Campaign
  sub-page: the page title in the slot, the sub-page's band one notch on with
  the bottom band docked, the crumb's rise, fit, floor (in Italian) and cut,
  the sub-page title at the step's foot, both changes' timing (the plates
  half gone, the band stepping and the page a quarter swept at 75 ms, the
  crumb by 150 ms, the step, sweep and carry at 350 ms, the backing fading
  in, the title dropping at once on Back, the crumb returning over the last
  150 ms, the backing out and the sub-page swept by 300 ms, the page's first
  frame already docked and fading back in place), the rest each document
  takes when hidden, the French crumb at 80 %, Back reversing a change from
  where the band stands, and the reduced-motion arrival. The gate test covers
  the hand-over: each half's event, the 350 ms and 300 ms waits, the
  immediate hand-over under reduced motion, a press held and a release
  forwarded mid-change, no second request, Back reversing over 150 or 250 ms
  by the step's distance (and not reversing a Back), the change abandoned
  when another screen takes over, and the stock selector at once when the
  sub-page cannot present. It pins the frame pump and input hold, the halves'
  durations against the session's waits, the four reversal lengths and that
  rest returns everything a change moves. It covers the loading tips: the
  first as the screen presents, the next every 6 s in the other slot, a new
  load starting elsewhere in the list, none in multiplayer or while another
  screen presents the load, the calls from the load's redraws, and that every
  tip in every shipped language fits its two lines.
- The gate test also compiles the server card's production sanitizer, roster
  store and publish with idlib's own escape parser: escapes, control bytes,
  malformed and cut UTF-8, line limits and `#str_` names; players by team,
  six names and "+N more", spectators and players connecting, a game that does
  not answer, a load that knows no players, the store's 32 slots, and the
  roster cleared after each publish. It pins where the network code captures
  the roster (before `InitClient` and the listen host's map load, before a
  client's `InitGame`, and the connect response's block between the server
  info and the send, read behind its tag and length and never ending the
  connection), game_mp's answer, `si_motd` in both game modules, and that
  every language's roster lines carry one count and fit the card.
  `openq4-connect-roster-test` covers the block's codec: a round trip, every
  truncation, another version, counts, slots, teams and flags out of range,
  the longest name and one byte more, a full roster and capacity. The screens
  test lays the card out from its foot: its base height with no players and
  no message, the address in Profont, the team columns under their heads in
  the team colors, a list's line breaks drawing no glyph, the spectators line
  beneath, a one-line message and a long one clipped at three lines, the
  card clear of the top band, one list outside team modes and the line alone
  without names.
- `tools/ui/capture_retained_screens.py` captures the screens in the engine
  from a hidden window with engine screenshots and semantic
  `openq4_retainedGui` operations, never OS input (`lines` sets a multi-line
  state, one argument per line, as the console turns backslashes into
  slashes). With `--gate 0` the title
  and pause scenarios, including the pause scenario's real map load, check
  that nothing retained loads; the loading scenario drives its document through
  `testGUI` and is not a gate check. Its default, `--gate default`, leaves
  `ui_retained` unset, as a player has it. The `fallback-*` scenarios run as
  a private mod in the savepath, whose files take precedence over openQ4's
  packs as any mod's do (loose files in the savepath alone cannot, because
  the savepath is searched last): a title, SYSTEM or Single Player document
  that cannot load, a main menu without its Demos page, and
  (`fallback-loading`) a mod's own `splevel` and `generic` loading GUIs, under
  which game/airdefense2 loads without the retained loading screen. `system-default`
  and `system-optin` press the SYSTEM button with the page off and opted into.
  `pause-strogg` pauses game/recomp, where Kane is Strogg, mid-translation
  and at rest, then focuses a plate, opens the quit confirmation and resumes.
  The pause scenarios wait for the confirmation's 300 ms leave before they
  focus RESUME, because the modal keeps focus until it closes.
  `pause-objectives-page` gives airdefense1's first objective, completes it
  and gives two more, then opens the Objectives page, scrolls and closes it.
  `subpage` opens the Single Player page, goes deeper to Campaign and comes
  back, with shots mid-change and at rest; `subpage-reduced` does the same
  under reduced motion. `newcampaign` goes on from Campaign to New Campaign,
  chooses, toggles TURBO MODE, comes back, reopens the page reset and starts
  the campaign, reading `g_skill` and `g_turboMode` back. Back during a change reaches the session only as
  real input, so the gate and screens tests cover the reversal.
- `tools/tests/ui_retained_gate.py` compiles the session's loading hold
  against a stand-in session and drives it: who it holds for (each refusal:
  the stock screen, single player, a demo, `ui_autoJoin`, the card off or
  fallen back, a mod's menu), a listen server's join on the clock the load
  left standing, a remote client's card coming seconds later and fading on
  the next frame, the ceiling counted from the first moving frame, the
  screens that end it and the drops. It pins where the session begins it in
  place of the wipe, draws it under the wipe, updates it before the card and
  holds user commands, and the loading document's `handoff` and `present`.
- Live probes with `ui_autoJoin 0` traced the hold and captured it: a listen
  server on OpenGL in English, its card in the load's own frame and the
  fade over the next 60 and 120 ms; a remote client on OpenGL whose card came
  2 to 4 s after the load, JOINING held until then; Vulkan in German under
  reduced motion; and no hold with `ui_autoJoin 1` or `ui_retained 0`.

The initializing screen adds:

- gate cases (`check_initializing`): the document's state and events, one
  rule segment per step, the step keys and the later LOADING..., the step
  advancing before the renderer can draw, the stock picture for a frame the
  document cannot draw, the pacifier's guards and 33 ms floor, and the view's
  release after `session->Init` and first in `ShutdownGame`;
- native checks: the picture's placement at 16:9, the status text and its
  flicker, the rule's segments and pulse, the glint crossing, the rings and
  the light turning on the clock, the halo breathing, and reduced motion's
  poses; and a vector check that a path opting out of antialiasing compiles
  plain triangles;
- live captures on OpenGL at 4:3, 16:9 and 21:9 and on Vulkan at 16:9, with
  the flicker, the glint across two letters and reduced motion, and a traced
  start on OpenGL: the first frame at the render step, then each step and
  repaints during the long ones every 80 to 300 ms, the rings' angles
  following the clock (3 and 2 degrees a second).
- the layers alone (no accents, rings at rest) against the stock picture on a
  4:3 view at 100%: the field within 0.44 levels on average (95% within 2),
  and the letters' halo within 2 levels just outside the letters. The letter
  cores differ by 10 to 16 levels: the specification's #F2F0EC is `q4text`'s
  own core, while the stock picture's letters measure about #FCFCFC. The
  rings' center measures 319.4, 214.2 u (a circle fitted to the inner ring's
  edge) and the emblem keeps its box centered on the canvas, so the emblem's
  own ring sits 20 u above the rings' center, as in the stock picture.
- the title's wordmark against its `q4text` bitmap: the halo within a level
  on average, the letters crisper.

The weapon wheel adds:

- gate cases (`check_weapon_wheel`): the document's state, events and slot
  count agreeing with the game's, the 180 ms tap, 35% stick, 4-degree
  hysteresis and 32 dp pointer constants, the engine naming the document
  only behind the gate, the classic wheel kept for VR, multiplayer and
  `ui_retained 0`, a tap swapping before a release equips,
  no time scale or blur, the open, select and close events, unowned weapons
  that cannot be selected, the retained wheel taking a hold before the
  classic one and drawing before its blend, and the engine's stick selection
  never inverted like look;
- native checks: the wheel centered on the view, the selection's 8 dp
  extension along its direction, backing, light, ring and orange icon, an
  unowned weapon's outline, the prohibition sign, the gauge filling in
  proportion to the reserve, each slot's key and reserve, the compass,
  pointer and previous notch, the hub's name and ammunition, the open from a
  slit, the clockwise deploy, plates readable by 150 ms under the static
  burst, the settle and the close;
- live captures driven by `openq4_weaponWheel` on OpenGL at 4:3, 16:9 and
  21:9 and on Vulkan at 16:9, with reduced motion on both: the wheel opening
  on the current weapon after its 180 ms hold, a stick vector selecting the
  shotgun and then the lightning gun, release equipping it, and a tap
  swapping back to the previous weapon, each traced by `ui_retainedTrace`;
  and with `ui_retained 0` the classic wheel, its slowdown and blur.

The Strogg wheel adds a native check (the same state, the selection's ring and
extension, an unowned plate's rim, the slanted cells' fill, the circuits'
three levels, every readout's rune copy, the grain at rest, the rings' 0.2 and
0.5 turns a second, the scrambled boot under its flash, the rings spinning up,
the name translating from runes, the scan bar lighting and dimming, the close
and reduced motion stopping the rings), gate cases (the Strogg body's
component, both families' shared state and events, a boot order covering
every slot once, and the wheel drawing through the Strogg close), and live
captures on `game/recomp` on OpenGL at 4:3, 16:9 and 21:9 and on Vulkan at
16:9, with reduced motion on both.

The multiplayer wheel adds a native check (Deathmatch's olive on the ring,
bezel, hub rings, compass dot, pointer and light; a Marine's and a Strogg's
team colors on them, the #6B3A08 light and the selected number's color; the
reserve alone in the hub), gate cases (the engine's "weaponwheel_mp" entry, the
open capturing input and the close freeing it, equipping and the tap by
impulse, no time scale, the update only in a new frame, and the capture
holding the view, sticks, fire and zoom and clearing on a new map), and live
captures on a `q4dm1` listen server in Deathmatch and Team Deathmatch on
OpenGL and Vulkan at 16:9.

## Evidence

Built as a debug engine and staged into `.install`; the six expensive layout
tests ran from an optimized build with assertions enabled. On Windows 11 with
an NVIDIA GeForce RTX 4060 Laptop GPU, twelve scenario runs captured the
screens on OpenGL and Vulkan (1.4.325) at 1280x720, on OpenGL at 1024x768, and
with the gate off. All exited cleanly with no errors. The gate-on runs
presented all three screens, and RESUME retired the pause screen. The gate-off
title and pause runs, including a real map load, loaded no retained document.
The reviewed images include the title and its glint, the exit modal at 4:3,
the pause screen before and after RESUME, the loading bar clipped at 62%, the
Vulkan title and loading screens, and the stock title with the gate off. All
106 other Meson tests, the optimized layout tests and the commit-validation
Python list pass. Evidence: `.tmp/ui/retained-screens/validation-evidence.json`,
SHA-256 `e645a25b3daae42e1b4cc5a6301fc67cfc8c31c85895759f92fb4a179697d5b9`.

The Remastered loading progress was captured the same way. Real single-player
loads traced MAP 1/4, WORLD 2/4, ASSETS 3/4, FINISHING 4/4 and the load time,
in that order, on OpenGL and Vulkan at 1280x720 and on OpenGL at 1024x768.
The loading scenario rendered the phase with its asset count, the percentage,
the load time and the controller prompt on both backends; the gate-off runs
loaded no retained document. Evidence:
`.tmp/ui/retained-loading/validation-evidence.json`, SHA-256
`9961bf8402d8897d4d95be20ab20f780ccd371c674c0b7371b676c4bdcce2fc8`.

The Remastered multiplayer composition was captured on OpenGL and Vulkan at
1280x720 and on OpenGL at 1024x768: the band stays low, the server card stands
clear of the lower corner bracket, the message line reads over a bright
levelshot, and a finished multiplayer load reads JOINING. Evidence:
`.tmp/ui/retained-loading-mp/validation-evidence.json`, SHA-256
`238cca71ae82b18ded323317822f1e770b3db55f4ebeea9afc58753cb73994db`.

The title carry was captured on OpenGL and Vulkan at 1280x720 and on OpenGL
at 1024x768: SETTINGS travels toward the title slot as the bands dock, and
the stock Settings page then shows its own title in that slot. The gate-off
title and pause runs loaded no retained document. Evidence:
`.tmp/ui/retained-title-carry/validation-evidence.json`, SHA-256
`36aa73558fb395d333351f52102d070871fc69352136a168137f07cd57785b69`.

The title's depth lean was captured on OpenGL and Vulkan at 1280x720 and on
OpenGL at 1024x768: with the pointer at the top-trailing corner the bands
and backdrop lean while the wordmark and navigation stay in place. Evidence:
`.tmp/ui/retained-title-depth/validation-evidence.json`, SHA-256
`938294a3434fcd14513e9c5b54fa3efa7c53913a7544700e62a0f4d4d9f835ce`.

The confirmations were captured on OpenGL and Vulkan at 1280x720 and on
OpenGL at 1024x768, beside an engine capture of the stock exit dialog. These
match the stock to within a pixel at 1280x720: the silhouette edges, the
raised top line, the slot floor, the bottom edge, the title's cap line, the
body's baseline and the action row. The retained faces' side bearings start
the title's ink 3 px before the stock's. With the layer fix, the Vulkan
dialogs match OpenGL. Before it, their outline, plates and markers were
missing there, as were the title menu's navigation plates. Evidence:
`.tmp/ui/retained-modal/validation-evidence.json`, SHA-256
`32b9bbf8b67cf36b59dca317274579f637bb2eda2bc7c3000b7122160b9f8945`.

Timeline completion programs and the confirmations' stock motion were
qualified by native tests in an optimized build of a clean worktree. All 107
Meson tests pass, among them the completion schema and timing tests, a
snapshot taken while a completion is due, and the exit confirmation's enter
and leave. Without the completion run that precedes an event's program, the
screens test fails. There are no engine captures of the transitions: the
only client path with firewall rules, `.install`, was in use by another
session. Evidence: `.tmp/ui/retained-modal-motion/validation-evidence.json`,
SHA-256 `a23a96a22a4abd67ded93a9a00624ffa6dba93d4d4275170346aafc0c2ba5b70`.

The retained title and pause screens' section 8 tokens were qualified by the
native screens test. On depart, the plinth and its links are gone at 50 ms
while the home plates are at 0.8. The wordmark sits at 40% while the Exit
modal is open and is restored 200 ms into its leave. Evidence:
`.tmp/ui/retained-motion-tokens/validation-evidence.json`, SHA-256
`0d139aa4bd795cece9cf6e7ebda88883b0b52bd53c1ce8ab9544a9ca3b082218`.

The motion was then captured in the engine, on OpenGL and Vulkan at
1280x720, from a candidate runtime built from the pushed code. The exit
confirmation appeared half way in, open, holding, releasing and closed,
and the plinth was gone 30 ms into a depart. The captures exposed the
additive-picture layer fault above. Fixed, the wordmark's rectangle reads
69 on OpenGL and 68.7 on Vulkan instead of a dark 26. Evidence:
`.tmp/ui/retained-motion-engine/validation-evidence.json`, SHA-256
`b915a8889da4535c7b4a19fc6c9af500ad8bc1dccd5608dafe6057221189cbf9`.

Soft focus was captured in the engine on OpenGL and Vulkan at 1280x720 and
on OpenGL at 1920x1080, from a candidate runtime of this build. Over the
title, the screen beneath the open exit dialog is blurred and desaturated
but not dimmed: away from the dialog its luminance holds, while its
saturation falls to about 0.8. The glow spreads past the dialog, and
Vulkan matches OpenGL. The blur keeps the same look at both sizes, and the
quit dialog softens the paused view. With `ui_retainedOpaqueBacking 1`
the stock scrim and column return, and the blur program never loads.
Native tests pin the ramp, the hold and the release, and a host harness
pins the capture and passes. Evidence:
`.tmp/ui/retained-softfocus/validation-evidence.json`, SHA-256
`ae57a44a9b1ddf3d582d1caa7d8565e82582b76a3c63f09717a7f8e5efec6eaf`.

The softened paused view was captured the same way on OpenGL and Vulkan at
1280x720, over airdefense1. The view is blurred and desaturated, the HUD
crosshair blurs away, and the frame is not darkened. The darkening fallback
keeps the crosshair sharp, and the quit confirmation softens the pause
screen above the softened view. The screens test pins the ramp, a page's
return and the next pause; without the ramp's restart key it fails.
Evidence: `.tmp/ui/retained-pause-softfocus/validation-evidence.json`,
SHA-256 `1443f7b6398db734e30c564d03a831f0aa401f3c3940d726a31bcb0ca9e4268d`.

The SYSTEM page's dialogs were qualified by native tests against the real
document: without soft focus the 0.6 backing shows and no backdrop pass
runs; with it the backing hides and one pass softens the screen beneath.
All SYSTEM tests and updater checks pass; there is no engine capture of
these dialogs yet. Evidence:
`.tmp/ui/system-dialog-softfocus/validation-evidence.json`, SHA-256
`4e33e60981080475ab3a66f6098b885008ebb2dd657a7211c570cc8de342a6c5`.

The default and the fallbacks were captured on OpenGL at 1280x720 and
1024x768 and on Vulkan at 1280x720, from a candidate runtime of this build,
with `ui_retained` unset. The title, pause and loading screens presented in
their retained form. Run as a private mod:

- a title document that cannot load left the stock title, with one warning,
  while the pause screen stayed retained;
- a main menu without its Demos page presented itself, with no warning, and
  nothing retained loaded;
- an opted-in SYSTEM page that cannot load opened the stock SYSTEM page from
  the same click;
- a Single Player selector that cannot load opened the stock selector.

By default the SYSTEM button opened the stock SYSTEM page, and the retained
page when it was opted into. With `ui_retained 0` the title, a real map load
and the SYSTEM button loaded nothing retained. All 18 runs exited cleanly with
no errors. Evidence: `.tmp/ui/retained-default/validation-evidence.json`,
SHA-256 `4aae5c75825a2036a9569bc19496bca79d567c3cf7ce682ca28dd576c19cf7f7`.

The pause screen's level block was captured over airdefense1 on OpenGL and
Vulkan at 1280x720: it shows the intro art the level's loading screen uses,
where it showed the generic loadscreen. Evidence:
`.tmp/ui/retained-pause-shot/validation-evidence.json`, SHA-256
`d3b289962528acd575ddf5fc17033f8ece7e2e159d89d3724d2e10d36ffa6a06`.

The live level block was captured over airdefense1 on OpenGL and Vulkan at
1280x720. With the level's first two objectives given, it lists Retrieve
Medic above Regroup with Rhino Squad and the time in the mission under the
rule; without them it shows the time line alone. Evidence:
`.tmp/ui/retained-pause-objectives/validation-evidence.json`, SHA-256
`43f7a4867c20868c828296b1faf46a1bd64c1282538da0d113b0e58e7df2074b`.

The Strogg pause was captured over game/recomp, where Kane is Strogg, on
OpenGL and Vulkan at 1280x720 and on OpenGL at 1024x768: mid-translation,
with the actions still in runes, then at rest, with a focused plate's scan
bar, the quit confirmation and RESUME. airdefense1 still pauses in the
Marine family. Vulkan matches OpenGL within two levels at rest, and with
`ui_retained 0` the Strogg level loaded nothing retained. All runs exited
cleanly with no errors, and all 109 Meson tests pass. Evidence:
`.tmp/ui/retained-pause-strogg/validation-evidence.json`, SHA-256
`2180c19336bea8e678a54440b5eacb20ab01d31a4a5121893dcbc9e725886894`.

The Objectives page was captured over airdefense1, with its first objective
given and completed and two more given, on OpenGL and Vulkan at 1280x720 and
on OpenGL at 1024x768: docking, the page with both plates and the completed
row, scrolled, and closed, the level block then listing the two open
objectives above the completed one and "saved just now" after the level's
start autosave. Over game/recomp the Strogg page shows its plate, serial and
Strogg BACK. No run loaded a picture outside the level load, the Strogg
page matches across renderers within two levels (the Marine page differs
only in the moving sky behind the plates), and with `ui_retained 0` nothing
retained loaded. All runs exited cleanly with no errors, and all 109 Meson
tests pass. Evidence:
`.tmp/ui/retained-pause-objectives-page/validation-evidence.json`, SHA-256
`f700445cf82cb8e6e7e01ba64b30bdbe8e55adcb22fbb0237e23d9976f0577c6`.

The release after RESUME was captured over airdefense1 and game/recomp on
OpenGL and Vulkan at 1280x720: about 100 ms after RESUME the screen is gone
and the running game, HUD included, is still softened (a quarter of the
resumed view's sharpness on both renderers), and the status line reports
the release; 800 ms after it the view is sharp and the release has ended.
With `ui_retained 0` nothing retained loaded and nothing was released. All
runs exited cleanly with no errors, and all 109 Meson tests pass. Evidence:
`.tmp/ui/retained-pause-release/validation-evidence.json`, SHA-256
`f7e0da538649ac0ccb7f21133ffd74133909e3bf25dc342bad0d57a48ef8f957`.

A private mod supplying its own `splevel` and `generic` loading GUIs loaded
game/airdefense2 on OpenGL and Vulkan at 1280x720 under its own `generic`
screen: the retained loading screen never loaded, and the developer log
names the mod's file. The same sets load airdefense1 under the retained
loading screen without the mod. Evidence:
`.tmp/ui/retained-mod-loading/validation-evidence.json`, SHA-256
`a5bf27df44fef680527d2358f64eac706d3bbac6a0f2f1a97a9a1ddaa11bf874`.

A listen server loading mp/q4dm1 published its eleven kinds of item to the
arsenal, each with the image and tint read from its colour-coded material
(the lightning gun 1, 1, 0.73, the railgun 0, 1, 0, the large armor red),
and the loading scenario's arsenal, published the same way, draws tinted in
the thick band on OpenGL and Vulkan at 1280x720, identically on both.
Evidence: `.tmp/ui/retained-loading-arsenal/validation-evidence.json`,
SHA-256 `a2bd70225491d8ea1ff802bcb3b046b68ac7ca17136e49d46680faf92ceee094`.

The Single Player page went deeper to Campaign and back on OpenGL and Vulkan
at 1280x720 (identical to within one level) and on OpenGL at 1024x768: the
session handed over at 350 ms and 300 ms, the band stepped one notch, the
crumb read SINGLE PLAYER in the band's thin span, and Back returned the focus
to Campaign. Under reduced motion each level presented at once, and with
`ui_retained 0` the stock selectors opened and nothing retained loaded.
Evidence: `.tmp/ui/retained-subpage/validation-evidence.json`, SHA-256
`eca04d36298751db3331776e99e4fde0e3c123a6bb06570d0eed62c1935b44b5`.

Single player tips were captured on OpenGL and Vulkan at 1280x720, on OpenGL at
1024x768 and in German, Polish and Russian: the TIP tag over a two-line tip in
the band's leading part while the level loads, the next one cross-fading in the
other slot, and the band given to the continue prompt once the level is ready.
A real airdefense1 load showed the tips changing every 6 s. Evidence:
`.tmp/ui/retained-loading-tips/validation-evidence.json`, SHA-256
`4f0f69638a05f185f8018379dd746d6cd804d2eef97d7b66d3206dc090dea4b4`.

The server card's players and message were captured on OpenGL and Vulkan at
1280x720, on OpenGL at 1024x768 and in German, Polish and Russian: the team
columns under MARINES and STROGG over the spectators line and a three-line
message, and one list with "+3 more" outside team modes, the card growing up
from its foot. A listen host's map change and a second client's fresh
connection traced the players they published. Evidence:
`.tmp/ui/retained-server-card/validation-evidence.json`, SHA-256
`dc352d1c28dfe32f9057dcb7d8ee69d17ad11ba1712b42cb1472c236b617c113`.

The hand-off to the Welcome card was traced and captured on listen servers and a remote client with `ui_autoJoin 0`: JOINING held until the card presented and then faded out over it, on OpenGL in English and on Vulkan in German under reduced motion, and no hold with automatic joining or the stock screens. Evidence: `.tmp/ui/retained-loading-handoff/validation-evidence.json`, SHA-256
`ed845b87064b11dea753eab7d7f27b70ad79d07e649d400d0c43325619e02c1e`.

The initializing screen: `.tmp/ui/retained-initializing-evidence/validation-evidence.json`, SHA-256
`97391702528b95a50bd2f946e18c3f5dabc608e5dd1f052374cbb71ee1de39bd`.

The weapon wheel: `.tmp/ui/retained-weaponwheel-evidence/validation-evidence.json`, SHA-256
`5e2922f97851b9cca3b43d542bd7af93ed09e514f34512f85f27dbbc439694ba`.

The Strogg weapon wheel: `.tmp/ui/retained-weaponwheel-strogg-evidence/validation-evidence.json`, SHA-256
`fc816eb3b1ddcd26054d7f9cfe0d858ae0d41a682f1d723063600362a8db6bd0`.

The multiplayer weapon wheel: `.tmp/ui/retained-weaponwheel-mp-evidence/validation-evidence.json`, SHA-256
`21695827676d2113d77f3326db45576d9f9458eb5817279bfc52971681f71a6b`.

The Load Game page: `.tmp/ui/retained-loadgame-evidence/validation-evidence.json`, SHA-256
`0ca1295e613bac04ccb9625f73af37b3bafe0311b1dc7d0b75f4f3eda9ffed49`.

The Save Game page and typed characters: `.tmp/ui/retained-savegame-evidence/validation-evidence.json`,
SHA-256 `a19668e3ec74f32813923274778912d3dadfe6f682bc0867a75f259f61966b9a`.

The Restart Level page: `.tmp/ui/retained-restartlevel-evidence/validation-evidence.json`,
SHA-256 `c59bf89c0bccdfa9615b95eacd3b215bd181b71c5c755769df3d530b9f21d3d9`.

The New Campaign page: `.tmp/ui/retained-newcampaign-evidence/validation-evidence.json`,
SHA-256 `5ef64a6421c78346292a3e2ac037659cd23f554802638b963e330b426b42b92e`.

The Demos page: `.tmp/ui/retained-demos-evidence/validation-evidence.json`,
SHA-256 `6af050d9337ba49f1906fc18bfc799af9adde4b8c2aa4b70dee997d98747ae9f`.

The MODS dialog: `.tmp/ui/retained-mods-evidence/validation-evidence.json`,
SHA-256 `6be45e12dadc8a14882242127fc431e54e54504b23ceb43a71a91b6cb329339d`.

The restart screen: `.tmp/ui/retained-restartmenu-evidence/validation-evidence.json`,
SHA-256 `c0efdf55a7abe4f8ac14bd3239fd2fdbae555b9cded737973c565211f2eb8fdf`.

The Credits page: `.tmp/ui/retained-credits-evidence/validation-evidence.json`,
SHA-256 `d6ac5ccd40691bbd7b368514a72dbc9278374db007fab76b14be34e98efc1045`.

The Arena page: `.tmp/ui/retained-arena-evidence/validation-evidence.json`,
SHA-256 `d47a2a28292827e6f85d91cbfef10f21fe7c8aa8c2f010c0883756cc3254360f`.

The Multiplayer page: `.tmp/ui/retained-multiplayer-evidence/validation-evidence.json`,
SHA-256 `f07ddc497858aca4c9c94abb64cb3bd966a53f7078c018c51f882c0f63c40393`.

The Create Server sub-page: `.tmp/ui/retained-createserver-evidence/validation-evidence.json`,
SHA-256 `a307268c17d9e94836bbd26d8f4684825f8787e11c35d2cf89f5a48ded4b0b33`.

Create Server's password rows on masked text fields: `.tmp/ui/retained-createserver-passwords-evidence/validation-evidence.json`,
SHA-256 `608164c9a749f0cd13f931057fb9bc6c3ebe406bd2d89c89c9f470285c7cdbd0`.

Create Server's ban list and the page as the default: `.tmp/ui/retained-createserver-banlist-evidence/validation-evidence.json`,
SHA-256 `aaaeed1f5512c93c181d1fb2895122bc30dcea5437f35b660bd4a2bf057951d8`.

The Join Game sub-page (opt-in) and loopback favorites: `.tmp/ui/retained-joingame-evidence/validation-evidence.json`,
SHA-256 `79aa239d2f10627940727d4a0c5c7306dee0a571ddee62d5dc149ad95b5c7e86`.

Join Game's symbols, mod filter, favorite toggle and levelshot: `.tmp/ui/retained-joingame-symbols-evidence/validation-evidence.json`,
SHA-256 `fc9c671fb6fe43184528d0613b8bdbe4c44794efca2598295c47d0e5a8e538bc`.

Join Game by default, with JOIN IP ADDRESS and FIND PLAYER/CLAN: `.tmp/ui/retained-joingame-default-evidence/validation-evidence.json`,
SHA-256 `4d2c6a2f86f0f1c3fa141acba00768cdbe5783344740d6d0071d74163d51ba4c`.

The server browsers' scan progress: `.tmp/ui/retained-joingame-progress-evidence/validation-evidence.json`,
SHA-256 `86ad58e9f0cb2e487b06fa2e253b38711cb750ecee629ff6b72f3acb43b5cf7f`.

A server's details and the classic browser's server tooltip: `.tmp/ui/retained-joingame-details-evidence/validation-evidence.json`,
SHA-256 `5b7857f09bfd8f65fd8cfa22264375b890b55387090450c5ca5010fd6b034e46`.

The runtime's detail card and Join Game's server details: `.tmp/ui/retained-detail-card-evidence/validation-evidence.json`,
SHA-256 `f756cd836ed5469f16f0f60658c9568d31f35bff637eb694493c464dc0f58854`.

Join Game's network quality bars: `.tmp/ui/retained-network-quality-evidence/validation-evidence.json`,
SHA-256 `05402c1366af7555381f7142104d346e7e019382670c6b9801977120db398e28`.

## Known limitations

The [menu audit](menu-audit.md) of 8 October 2026 records what it fixed and
what remains across every retained menu.

- The initializing screen's first frame loads, lays out and compiles its
  document: about 0.9 s on a loaded machine, part of it the Marine font and
  RmlUi's first use, which the title would otherwise pay. A 300% capture is
  not possible in a window larger than the desktop, and the GLES fallback
  has not been captured.
- The weapon wheels are single player's Marine and Strogg wheels and the
  multiplayer wheel. Quick chat and The Awakening's thirteen positions are
  not built; touch does not start a drag at the weapon button; a refused
  release has no controller pulse (the sound system's rumble would cancel it
  each frame); names do not wrap to a second line; the Marine open's ring
  flash and the name's tune-in from a line, with its color settling from
  white, are not drawn; and the Strogg circuits grow out from the core rather
  than tracing along their paths.
- The Load Game page lists the saves newest first only. It has none of
  section 13.7's list sorting, filter tags or refresh, and it pages by 64 rows
  rather than virtualizing. The Strogg pause's LOAD GAME, SAVE GAME and
  RESTART LEVEL keep the stock pages. A save's own screenshot loads when first shown,
  outside a level load, as on the stock page. The title's CONTINUE detail
  joins the level and the date with an unlocalized hyphen.

- The completed objectives are kept per map and not saved, so after loading a
  save the page and the level block list only those completed since. The
  time line has no total time: nothing tracks play time across missions. A
  failed objective is not marked (failure ends the mission at once). The
  objectives display held on the scores button in play, its hold or toggle
  setting and the notices keep the stock screens.
- The Strogg pause keeps the stock confirmation dialogs, and its grain does
  not drift. Its translation is the menu's short form: the full credits
  translation, with its 2000 ms rune fade-in and 250 ms line stagger, is not
  built.
- Only RESUME releases the softened view over 250 ms: a disconnect, a level
  load or a hand-over to another screen drops it at once, as each replaces
  the view behind it. The HUD's crosshair still shows through the darkening
  fallback.
- Soft focus covers the confirmations, the pause screen and the SYSTEM
  page's two dialogs. The SYSTEM dialogs have no enter or leave motion, so
  their soft focus switches with their visibility. The opaque-backing option
  has no Settings row yet (`ui_retainedOpaqueBacking` is a CVar). A node
  inside a composition layer gets no soft focus, because only the base
  surface is read. Only the confirmation width exists.
- The multiplayer Escape card is opt-in (`ui_retainedMultiplayer`) while its
  Admin page hands off to the stock menu; the Welcome card presents
  by default ([multiplayer menus](multiplayer-menus.md#known-limitations)).
  The retained home screen is never presented in a multiplayer game.
- The Welcome card's own opening runs on the clock the load left standing
  and ends at once, so the hand-off reveals the card already softened. A
  first card frame slower than the fade still cuts it short.
- The sub-page level covers Single Player's Campaign and Arena, and
  Multiplayer's Create Server and Join Game. The Multiplayer page opens the
  stock Settings page through the stock within-a-screen change instead of a
  sub-page. The retained Join Game shows a server's players and rules in the
  stock tooltip's card rather than a docked detail column, and has no prompt
  bar yet (Join, Spectate and Favorite). Player Setup
  does not yet edit in place,
  Demos is not yet among its sections, and
  Campaign's Chapters is not yet a level of its own; New Campaign is
  Campaign's sibling. The Single Player page keeps the home navigation plates and the
  BACK row instead of the section layout (navigation from 14 u, content from
  228 u) and the Back action in the bottom band; Classic is not built. A
  change going back cannot be reversed, and the crumb of a title too long for
  the 13 dp floor (Italian, Polish) is cut at the step.
- The Arena page's result ledger has been captured live only for a launch
  that could not open its server (MATCH ABORTED). A played match's win,
  defeat or draw reaches it through the same campaign path, which the native
  screens check and the gate cover; the in-match ceremony stays game_mp's.
  In the hidden capture window a reloaded game module presents its first
  frame at a screenshot, which reads black.
- The SYSTEM page stays opt-in until every stock setting works there:
  presets cannot be applied from it. Its Display Device list offers the
  first eight displays only
  ([SYSTEM display rows](system-display-rows.md#known-limitations)). Like
  every retained dropdown it steps its value with left and right, so a list
  that cannot open can still be changed.
- The loading screen has no touch prompt (touch counts as desktop input).
  The arsenal fills in only
  where the map spawns its items: a listen server's own load, not a client
  joining another server. The server card lists a joining client under the
  team it asks for, which the server may balance differently, and a
  multi-view demo's load shows no players.
