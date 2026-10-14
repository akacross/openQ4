# Arena Campaign match ceremony — implementation notes

The single-player Arena Campaign (`src/framework/ArenaCampaign.*`) runs each
match as an offline listen server hosted by `game_mp`. Player-facing behaviour
is described in [the player guide](../user/arena-campaign.md); this note records
how the match ceremony is built, the contracts between the framework and the
game module, and the 2026-10 audit that reworked it.

## Shape of a match

`idMultiplayerGame::IsArenaCampaignMatch()` is true only for the framework's own
listen server carrying `si_arenaCampaign`. An Arena match always has exactly one
human and no remote clients, so every ceremony phase is **host-local** state on
`idMultiplayerGame` (`arenaCeremonyPhase_t`), never an `mpGameState_t` value
(those are replicated wire bytes) and never an `mpMatchSession` pause kind.

| Phase | Game state | Driven by |
| --- | --- | --- |
| `INTRO` | WARMUP | `ArenaCampaignIntroBlocksCountdown` arms it from the WARMUP case of `rvGameState::Run`; one 1.8 s beat per combatant |
| (entrance) | COUNTDOWN | `BeginArenaCampaignEntrancePresentation`, from the COUNTDOWN edge of `GameStateChanged` |
| `SPAWN_IN` | GAMEON | armed by `OnMatchStarted` inside `NewState( GAMEON )`; 3 s, then "Fight" |
| `TABLEAU`, `SCOREBOARD`, `STATS`, `DONE` | GAMEREVIEW | `BeginArenaCampaignResult` / `AdvanceArenaCampaignCeremony` |

On the listen server `GameStateChanged` runs *after* `Run` in the same frame
(`SendState` → `ReceiveState`). It must never reset the ceremony: doing so wiped
the spawn-in that `OnMatchStarted` had just armed, and the introduction the
WARMUP case had just armed. The presentation is reset on the authoritative
`NewState( WARMUP )` edge instead, before `Run` arms the introduction.

## Cameras

`TraceArenaCampaignCamera` places the eye at `focus + radial * range`, so an
authored orbit angle of 0° is in front of the subject's face and 180° is behind
the head. Every shot is authored that way: the introduction drifts across the
front of the combatant (latching the clearest of six sides on its first frame
and pulling in rather than cutting away), the countdown sweeps from behind
around to the player's front three-quarter, the spawn-in starts in front and
ends behind the head before converging on `firstPersonViewOrigin/Axis`, and the
tableau opens on the victor's front three-quarter. The tableau latches both the
yaw and the pitch on its first frame and orbits relative to them;
`idPlayer::UpdateViewAngles` skips its death-view branch while
`ArenaCampaignAllowsFreeLook()` holds, so a player killed by the final frag can
still steer the orbit.

`ArenaCampaignPresentationActive()` hides the crosshair, weapon zoom and status
bar (`idPlayer::DrawHUD`) for every presentation shot; the match HUD still draws
because it carries the letterbox and cards.

## HUD presentation contract

The game drives both the stock `mphud.gui` and its Remastered peer
(`tools/ui/remastered_hud_mp.py` → `guis/hud/remastered_mp.q4ui`) with the same
named events and `arena_present*` state:

| Event | Mode | Copy |
| --- | --- | --- |
| `arenaCampaignIntroduce` | 3 | `arena_presentKicker` ("OPPONENT 2 OF 3"), title = name, subtitle = side or CHALLENGER |
| `arenaCampaignEntrance` | 1 | kicker = `#str_42156` (tier / role), title = match, subtitle = presented game type |
| `arenaCampaignVictory` | 2 | title, score, victor |
| `arenaCampaignPresentationClear` | → 0 | |

The first introduction opens the letterbox; later introductions and the
entrance take over the open frame instead of collapsing and reopening it
(`arena_presentHold` in the stock GUI, `arena-intro-open` / `arena-entrance-held-run`
in the Remastered document). A clear that is still fading must not hide a card
armed after it: the stock GUI's clear only hides the frame while
`arena_presentClearing` is still set, the Remastered events cancel the clear
timelines after playing their own, and `ClearArenaCampaignPresentation` only
sends a clear while `arenaHudPresentation` says a card is visible.

## Framework ↔ game contracts

- **Match card.** `PrepareServer` publishes localization keys in
  `ui_arenaMatchTitle`, `ui_arenaMatchTier`, `ui_arenaMatchRole` and
  `ui_arenaMatchGameType`. The game reads them for the entrance card, the
  scoreboard header (which also drops the server address) and the retained
  loading screen. A campaign Duel runs as deathmatch, so only the framework
  knows to call it a Duel.
- **Pause.** The game cannot see the engine's menus, so `idArenaCampaign::Frame`
  publishes `ui_arenaMenuOpen` (a session GUI other than the chat box, or a
  retained application, over a live match). `ArenaCampaignPausesWorld()` turns
  it into a world freeze: `idGameLocal::RunFrame` rebases every match deadline
  through `RebaseArenaCampaignPauseFrame` (the competitive pause's
  `RebaseCompetitivePauseFrame` plus the ceremony's own times) and runs the
  paused entity think; `idMultiplayerGame::Run` returns before the rules.
- **Result.** `arenaComplete <token> <outcome> <player> <opponent> [awards]`,
  outcome 0 loss, 1 win, 2 draw, **3 aborted**. A match whose opponents are all
  gone, an emptied team, or a GAMEREVIEW reached by a forfeit or abort
  transition reports *aborted*: nothing is recorded and the browser offers the
  match again. These used to be recorded as wins, so removing the bots cleared
  the ladder. `RejectManagedLegacyMutation` also refuses the multiplayer menu's
  Admin actions during an Arena match.
- **Abandoned.** `Session_Disconnect_f` reads `ActiveMatchToken()` before
  `AbortMatch` and then calls `ReportAbandoned`, which reopens the browser on a
  "Match abandoned" ledger with Retry.
- **Start failures.** `ReturnToBrowserAfterStartFailure` also reads the token
  before `AbortMatch`, so the "Match aborted" ledger names the match it could
  not start. A launch lost to a game-module reload (`Com_ReloadGameModule_f`)
  reports through `ReportStartFailure()` instead of reopening the browser as if
  the button had been ignored.

## Skipping

Escape is owned by the ceremony once a result is pending
(`idGameLocal::HandleESC` → `ArenaCampaignOwnsEscape`): it skips the remaining
tableau, scoreboard and stats with the usual hand-over fade and reports at once.
A fresh fire press does the same, and also skips the rest of the
introductions, but only after `ARENA_SKIP_GRACE_MSEC` on the beat so a trigger
held as the match ends cannot skip it.

## Driving it without input

`openq4_arenaCeremony <win|loss|draw|skip|status>` (cheat) ends the live local
Arena match with a chosen result through the normal scoring path, skips the
current beat, or prints the ceremony state and match clock. With
`net_allowCheats 1`, an Arena match can be launched from the command line
(`+set ui_arenaCampaignActive 1 +set ui_arenaActiveMatch <n> +spawnServer <map>`)
and driven end to end through `g_autoExecAfterMapLoad` and a command pump; this
is how the audit below was validated. `campaignMenu` opens a menu over a running
match, which exercises the pause.

## 2026-10 audit

Runtime checks on the staged build (Remastered HUD, GL, 1280×720, hidden
window) before the fixes showed:

- the spawn-in never ran — the GAMEON edge cleared it — so control returned at
  once with no camera move and no "Fight";
- the introduction card never appeared (a clear sent on the WARMUP edge
  completed after the card and hid the layer), and the camera filmed each
  opponent from behind;
- the Remastered victor card was an empty box (its label and name were authored
  transparent inside a group that was the only thing faded in);
- the crosshair and status bar drew over every cinematic shot, the entrance and
  scoreboard called a Duel "Deathmatch", and the scoreboard showed
  "Quake 4 Server" with a localhost address;
- the stats beat offered a chat entry and "Press Escape to return to the game".

Code review found the rest: no pause; leaving went to the title screen;
removing the bots (console, Admin page, Match Control) recorded a win; a draw
was announced as "You lose"; the tableau orbit ignored look input for a dead
player; the countdown's 3-2-1 ended 3.6 s before "Fight"; the introductions
dipped through a 700 ms fade at both ends of every 1.8 s beat; and in the
browser, `arenaBlockInput` dropped the timeline command coalesced with it
(stranding a black curtain), keyboard and controller focus could operate the
controls behind an open report, tier briefings named locked bosses, awards
vanished after the campaign was complete, and NEXT after a replayed win pointed
at an already-beaten boss.

After the fixes the same runs show the face-on introduction cards (team
matches: teammates first), a held frame into the countdown card
("BOOT CAMP / QUALIFIER 1 — FIRST BLOOD — Duel"), the spawn-in orbit ending in
first person with "control returned", the champion card with the victor's
name, a scoreboard headed by the match, a stats board without chat entry or
cursor, the victory report, a paused match clock (5:53 before and after a 5 s hold while
it ran live 5:56 → 5:54), the "Match abandoned" and "opponents left" reports
with Retry and unchanged progress, the skip path reporting straight away, and
a launch refused its UDP port reporting "Match aborted" under the match's name.
Not verified at runtime: the tableau orbit under real mouse input, and
keyboard/controller navigation of the browser (both need device input).

## Best results

Each match keeps its best result in the archived `ui_arenaBest`, beside
`ui_arenaProgress`: space-separated `<match>:<outcome>:<player>:<opponent>:<difficulty>`
entries, the match a zero-based index (tier × 4 + match), the outcome 0 loss,
1 win or 2 draw, the scores as `arenaComplete` handed them over (both
`ARENA_SCORE_UNAVAILABLE`, -9999, when the player never took a side) and the
difficulty `PopulateBots` used.

- **Ordering** (`ArenaBestResultBeats`): win > draw > loss, then the wider
  margin, then the harder difficulty, then the higher score; a tie keeps the
  older record. A match completed before the record existed carries an implicit
  scoreless win (`ArenaEffectiveBest`), so only a win replaces it.
- **Updates.** `FinishPendingCompletion` reads the record against the progress
  from before the match and writes the new entry when it beats it. Outcome 3
  (aborted) never competes, and an abandoned match never reaches it. The ledger's
  **NEW BEST** tag (`arena_resultNewBest`, `#str_42165`) appears only when a
  stored entry was beaten, not for a first result.
- **Repair.** `ArenaRepairPersistedProgress` always runs `ArenaRepairPersistedBest`
  after repairing the mask. It drops entries that are malformed or out of range,
  duplicated, for a locked match, whose outcome disagrees with its scores, or
  whose win/no-win disagrees with the match's completion bit. It then rewrites
  the cvar in canonical form with a warning. A new campaign version clears it.
- **Reset.** `arenaResetConfirm` clears it with the progress, and Reset Progress
  is offered while either is non-empty (`arena_canReset`), because a lost first
  match leaves a record but no win.
- **Browser.** The stock browser draws the record across the foot of the
  levelshot (`arena_selectedBestVisible`, `arena_selectedHasBest`,
  `arena_selectedBest`; "No result yet" for an open match without one, no band
  for a locked match).

Runtime check on the staged build (hidden GL window, Qualifier 1, matches ended
with `openq4_arenaCeremony`, the browser driven with `openq4_guiAction`, one
savepath across launches): a first win recorded `0:1:1:0:3` and the band read
"VICTORY 1 - 0 VETERAN" with no NEW BEST tag. After a restart the record was
still there, and a loss left it alone ("did not beat its best result"). An
equal win on the same difficulty also kept it. Reset Progress cleared it to
"No result yet" and disabled the button. A config seeded with seven entries
repaired on load to `0:1:1:0:3 1:0:0:2:3 2:0:-9999:-9999:3` (five dropped:
malformed, duplicate, locked tier, locked boss, and a win with a losing score).
The same 1-0 win on NIGHTMARE then replaced it, and the ledger showed
**NEW BEST** beside the score.

## Known gaps

- The in-game menu during an Arena match is still the stock multiplayer menu;
  Join Team, Server Info, Admin and Match Control remain visible although
  their actions are refused or inert. An Arena-specific pause menu (Resume,
  Restart match, Leave) is the natural next step.
