# Multiplayer network qualification

Evidence for MP-07 (coupled prediction and rewind) and MP-08 (network
interoperability) gathered on one machine, and the simulated network conditions
that make that possible. Player-facing guidance is in the
[networking guide](../user/multiplayer-networking.md).

## Simulated network conditions

`src/sys/NetworkImpairment.h` is a delay line for UDP datagrams that both socket
layers (`win_net.cpp`, `posix_net.cpp`) use. Each bound `idPort` owns two lines:
received datagrams wait in one before the engine reads them, sent datagrams wait
in the other before they reach the socket.

| CVar | Meaning |
| --- | --- |
| `net_forceLatency` | Fixed milliseconds added to every datagram, each way (0-2000). |
| `net_forceJitter` | Further delay drawn uniformly from 0 to this many milliseconds per copy (0-1000). |
| `net_forceDrop` | Percentage of datagrams lost. |
| `net_forceDuplicate` | Percentage of datagrams delivered twice; each copy has its own jitter. |
| `net_forceSeed` | Seed for the random choices when a port opens; `0` derives one from the clock and port. |
| `net_forceRate` | A bottleneck of this many bytes a second, each way, shared by everything on the port (1,000 to 100,000,000; `0` for none). |
| `net_forceQueue` | Milliseconds of traffic the bottleneck holds before it drops (1-5,000, default 250). |
| `net_forceDropBurst` | Mean number of datagrams lost in a row; `0` or `1` loses them independently (up to 64). |

Datagrams leave in the order they fall due, with ties in arrival order, so jitter
wider than their spacing reorders them as a real link does. Comparisons use the
millisecond clock wrap-safely. Payloads are stored at their real size (up to the
65,535-byte UDP limit); a due datagram larger than the reader's buffer is
discarded and counted, never truncated. A line holds at most 8,192 datagrams or
32 MiB and counts refusals beyond that. Lines keep draining after the settings
return to zero, so turning impairment off never reorders what is still queued.
Due sends are flushed whenever the port is polled, not only when the next send
arrives.

A rate turns a line into a bottleneck. Each datagram, with 28 bytes of IPv4 and
UDP headers, takes its size over the rate to send, and waits behind whatever
the link is still sending. One that would finish later than the queue holds is
dropped, as a full router buffer drops it. An idle link always takes a
datagram, so one larger than the queue still passes. A datagram lost further
along the path still takes its turn on the link. The latency and jitter start
when the datagram leaves the bottleneck. Burst loss is a two-state
(Gilbert-Elliott) chain: it stays in its losing state for `net_forceDropBurst`
datagrams on average and spends `net_forceDrop` percent of the time there. A
loss rate above burst / (burst + 1) cannot be reached and settles at that.
With no rate and a burst length of 0 or 1, the line behaves exactly as before.

`netImpairment` prints the settings and, per open port and direction, the
datagrams offered, dropped, duplicated, released, reordered, refused and
discarded, and the deepest queue so far (`NET_IMPAIR` lines). The line ends
with the payload bytes offered, the loss runs, the datagrams the bottleneck
dropped and its longest wait; these come last so harnesses that read the
leading fields keep working.

The CVars are unarchived and not `CVAR_NOCHEAT`, so like the original two they
count as cheats: hosting or joining a server without `net_allowCheats` or
`sv_cheats` resets them to 0.

This replaced the inherited Windows-only lag queue (POSIX had none). That queue
stored at most 1,400 bytes per datagram and silently dropped anything larger,
so with `net_forceLatency` set before connecting the handshake looped ("packet
exceeds latency queue capacity", "Bad challenge"). It released queued sends only
when another send came along, and had no jitter, reordering or duplication.

Tests: `tools/tests/native/NetworkImpairmentCases.h` drives the header
directly: fixed delay and order, jitter bounds and reordering, loss and
duplication rates, seed repeatability, oversize discards, a 9,000-byte
datagram, clock wrap and capacity. It also covers the bottleneck's pacing to
the millisecond, its tail drop, an idle link taking a large datagram, draining,
pacing across the clock wrap, the byte count, burst loss (rate and mean run
length) and the new settings changing nothing while off. The native core
safety test runs the cases, and `tools/tests/network_impairment_state.py` also
runs them against 14 single-reversal copies of the header, each of which must
fail. `tools/tests/network_impairment_contract.py` checks that both platforms
define the same CVars, open and release the lines with the port, queue
receives and sends, flush due sends while polling and report, with the
report's leading fields unchanged; it carries eight single-reversal controls
of its own.

## Prediction and lag compensation under impairment (24 October 2026)

`.tmp/mp-round2/impair_probe.py` runs a loopback listen server with three bots
and one remote client on the candidate build of this round. The client steps
through six phases, settling 4 s before each 6 s measurement with `net_verbose 2`
(controller state per snapshot) and `net_mpPredictDebug 1` (remote pose ages);
the server samples `lagCompStatus` every 3 s. Impairment is set on the client's
port, so both directions of its link are affected. `net_forceSeed 4242` makes the
runs repeatable. Reports: `.tmp/mp-round2/runtime/{legacy,enhanced,handshake}/report.json`.

| Phase | Settings (client port) | Resyncs | Client lead median | Server lead / RTT | Duplicated-command reports |
| --- | --- | ---: | ---: | --- | ---: |
| clean | none | 0 | 48 ms | 40 / 16 ms | 0 |
| latency50 | 50 ms | 0 | 144 ms | 140-144 / 117 ms | 0 |
| jitter50x40 | 50 ms + 0-40 ms | 0 | 192 ms | 181-188 / 117-150 ms | 2 |
| loss10 | 50 ms, 10% loss | 0 | 144 ms | 140-151 / 117-150 ms | 4 |
| duplicate20 | 50 ms, 20% duplication | 0 | 144 ms | 146-153 / 117-136 ms | 0 |
| combined | 60 ms + 0-40 ms, 5% loss, 5% duplication | 0 | 208 ms | 199-214 / 150-201 ms | 6 |

Legacy prediction (`net_mpPredictMode 0`), from the `legacy` run; the server
columns are the `lagCompStatus` samples taken during each phase. The
`enhanced` run (`net_mpPredictMode 1`) matches it phase for phase: no resyncs,
the same leads, and at most four duplicated-command reports in a phase.

- The delay lines did what was asked: in `loss10` the client's receive line
  dropped 35 of 361 datagrams (9.7%); in `duplicate20` it duplicated 66 of 362
  (18%); jitter reordered 13 received and 133 sent datagrams in its phase.
- The prediction controller held through every phase. The lead follows the
  round trip plus about one frame, the target settles within the 4 s, and
  commands arrive early (median 5-20 ms ahead). Duplicated commands appear
  only in a handful of snapshots under jitter and loss, where a late datagram
  arrives after the server needed it.
- The channel discards the reordered and duplicated datagrams
  (`net_channelShowDrop` "out of order packet"); usercmd redundancy covers the
  lost ones. No malformed, truncated or overflowing messages were logged.
- Lag compensation follows the real lead. Legacy rewinds rise from 56 ms clean
  to 156-169 ms at 50 ms and reach the 200 ms cap with jitter or the combined
  conditions. Enhanced prediction's advertised 16-tic extrapolation covers the
  whole lead, so its pose age is 0 and its rewinds stay at 0-16 ms (the frame
  bias), and its remote pose error is the deliberate forward extrapolation.
- A client that connected with 80 ms + 0-40 ms, 10% loss and 5% duplication
  already set (`handshake` run) joined on its first challenge, with no "Bad
  challenge" and no capacity refusals, then behaved as above.

## High player count (24 October 2026)

`impair_probe.py --dedicated --bots 20 --max-players 24 --quiet-client` hosts 20
bots on `openQ4-ded_x64.exe` with one remote client. The client records frame
times (`com_speeds`) instead of verbose logs, and the server runs `net_verbose 1`,
which reports a snapshot deferred behind a reliable backlog. Reports:
`.tmp/mp-round2/runtime/crowd-quiet/` and, with three bots for comparison,
`few-quiet/`.

| Phase | Client frame median | Prediction target the server sees | Round trip |
| --- | ---: | ---: | ---: |
| clean | 16 ms | 34-39 ms | 2-5 ms |
| latency50 | 17 ms | 142-146 ms | 104-122 ms |
| loss10 | 17 ms | 140-143 ms | 103-136 ms |
| duplicate20 | 16 ms | 142-148 ms | 103-121 ms |

No snapshot was deferred and no message overflowed; the three-bot run matches.

Earlier 20-bot runs had bursts of resyncs and commands up to 1.6 s late. Each
time the client process was starved of CPU, not the network path. The first
hosted the 20 bots on a listen server that also rendered, on the same machine
as the client. The second logged `net_verbose 2` and `net_mpPredictDebug` with
a flush per line, about 900 lines a second with 20 remote players. A third
overlapped another session's full-core build, which reproduced the symptom on
demand: client frames rose to a 38-57 ms median and the prediction target
climbed steadily toward its 1 s cap (`crowd-quiet-overlapped-build/`). A client
that cannot hold the 60 Hz tic rate falls behind the server in the same way;
this was measured, not changed. The one reliable-message overflow logged came
at server shutdown, after the client had already quit.

## Congestion, rate control and burst loss (24 October 2026)

`.tmp/mp-round3/congest_probe.py` (derived from `impair_probe.py`) hosts three
bots on `openQ4-ded_x64.exe` with one remote client in legacy prediction. It
steps through 14-second phases, measures the last 8 s of each with
`net_verbose 2`, and diffs the client's cumulative `NET_IMPAIR` counters per
phase. The bottleneck is on the client's port, so it limits the download
(server to client) and the upload alike. `net_forceSeed 4242`. Reports:
`.tmp/mp-round3/runtime/{congest-quiet,congest-matched}/` (`phases.json`).

| Phase | Settings (client port) | Download offered | Bottleneck drops | Longest wait | Snapshots | Lead median | Duplicated-command reports |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | - | - | - | 183 | 48 ms | 0 |
| rate64k | 30 ms, 64,000 B/s | 5,706 B/s | 0 | 2 ms | 182 | 112 ms | 1 |
| rate24k | 30 ms, 24,000 B/s | 6,071 B/s | 0 | 40 ms | 180 | 128 ms | 0 |
| rate12k | 30 ms, 12,000 B/s | 6,352 B/s | 0 | 159 ms | 183 | 144 ms | 43 |
| rate12kdeep | as rate12k, 1,000 ms queue | 6,921 B/s | 0 | 175 ms | 181 | 144 ms | 48 |
| rate6k | 30 ms, 6,000 B/s | 10,622 B/s | 56 | 199 ms | 132 | 224 ms | 105 |
| burst10x4 | 50 ms, 10% loss in runs of 4 | 5,956 B/s | - | - | 144 | 176 ms | 15 |
| burst10x1 | 50 ms, 10% independent loss | 6,199 B/s | - | - | 158 | 144 ms | 7 |

No phase resynced. The upload stayed at about 2.7 KB/s throughout.

- A three-bot match needs about 6 KB/s downstream. A link with spare capacity
  adds only the time to send a snapshot burst: the lead rises by the latency
  plus up to 160 ms of queueing, and a deeper queue changes nothing while the
  link keeps up.
- A link below that demand congests and then feeds itself. At 6 KB/s the
  bottleneck dropped 56 datagrams in 8 s, and the server offered 10.6 KB/s, 1.7
  times the demand, because lost acknowledgements make it resend reliable data
  and delta snapshots against older bases. Snapshots fell by 28%, the lead
  reached 224 ms with the prediction target climbing (194 to 295 ms), and the
  server duplicated late commands in 105 snapshots.
- Rate control prevents it. The `congest-matched` run connects with
  `net_clientMaxRate 5000`, so the server keeps under the 6 KB/s link. It then
  sent 4.2 KB/s with no bottleneck drops and a 15 ms longest wait. The lead was
  160 ms with a steady target (167 to 169 ms), and 16 snapshots reported
  duplicated commands. The price is snapshot rate: 133 in the window, against
  151 with the same limit on a 12 KB/s link and 182 unlimited.
- Losses in runs of about 5.4 datagrams (38 lost in 7 runs) cost more than the
  same rate of single losses (19 lost, runs of 1.06): 14 fewer snapshots and a
  lead 32 ms higher. Neither resynced.

An earlier run of the same phases while another session built with every core
and two other clients ran (`congest-ded`) resynced 15 times on the clean
connection alone, and the target climbed toward its 1 s cap. As in the
high-player-count runs, that is CPU starvation, not the network. The rates and
drops above come from the quiet run; one other session's client was still
running at 24% total CPU.

## Still open

Real remote peers (WAN routes, NAT, other operating systems and architectures)
and the defaults decision for enhanced prediction and lag compensation remain
open under MP-07/MP-08. The server does not adapt its rate to a congested link
on its own: a player whose connection is slower than the match needs has to
lower `net_clientMaxRate`. Whether to adapt automatically is a design decision.
Simulated conditions do not model route changes, cross-traffic sharing a
bottleneck, or asymmetric links (the rate applies both ways).
