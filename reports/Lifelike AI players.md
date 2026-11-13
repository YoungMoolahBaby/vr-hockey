# Lifelike AI players: the change list

*2026-11-13. Research round "Lifelike AI players". Why the 3v3 AI reads as robots to a hockey player, what elite players do instead, and what to change, in order. No code was changed to write this.*

**Sources:**
- The four research notes and their fact-checks in [`research_notes/Lifelike AI players/`](../research_notes/Lifelike%20AI%20players/): elite skating and body motion; puck skills and deception; hockey IQ on and off the puck; believable AI and presence in VR.
- Earlier rounds: [`reports/VR hockey sense training.md`](VR%20hockey%20sense%20training.md) ("Believable opponents need honest kinematics…"), `research_notes/VR hockey sense training/simulation_and_scoring.md`, [`reports/Hockey physics feel.md`](Hockey%20physics%20feel.md) (change 11, AI skaters on Jon's model), `research_notes/Hockey physics feel/skating kinematics.md`, and [`reports/Shot release.md`](Shot%20release.md) (the held stick's effective mass).
- The code on main at 7d9ad8c: `threes.py` (`Game`, `Player`), `figures.py`, `goalie.py`, `game.py`, `rig.py` (`Drive`), `retrieval.py` (`Skater`), `puck.py` and `physics_core.py` (`sim_step`, `collide_blade`), and `sandbox.py` (`Physics._tick`, which runs the AI inside the 1 kHz physics tick).
- A baseline measured for this report: four 600 s self-play games (seeds 0-3), six AI skaters, the real 1 kHz puck, the AI capped as in the headset (Jon's skate setting 3.0, so the AI's top is 2.85 m/s and a carrier's 2.42 m/s), level 1. That is 37.5 live game-minutes and 225 skater-minutes. Rates use the true tick times (the AI ticks about every 20.5 ms), so they are not 3% high like some of the notes' rates. One scratch experiment tried change 3. The scripts (`synth_probe.py`, `synth_analyze.py`, `synth_timing.py`), their summaries (`baseline.json`, `delay.json`) and the AI-blade prototype (`ai_blade_proto.py`, `ai_blade_kin.py`, `ai_sweep.py`) are in [`research_notes/Lifelike AI players/scripts/`](../research_notes/Lifelike%20AI%20players/scripts/); run them from `prototype/`.
- The primary sources, with URLs, are listed at the end. The researchers read them and the fact-checkers checked them; this report cites them through the notes.

Only claims the fact-checkers confirmed are used as evidence. Where a note was corrected, the corrected value is used (section 5). Every target marked [E] is a design choice, not a measurement.

Tags: **[M]** measured in the cited study. **[D]** derived: arithmetic shown, or our own measurement of the sim or of Jon's recordings (this report's baseline included). **[E]** estimate or design proposal, assumptions stated, including scratch models of a proposed change. **[V]** vendor claim, developer talk, coaching text, scouting or anecdote. **[S]** secondary: read in a source that cites the primary. Statements about the code are read from the code and carry no tag.

## 1. The short version

**Why it reads as robots.** Six tells. The numbers are this report's baseline [D] unless marked.

1. **Everybody knows at once.**
   - 95% of the skaters' new roles start on the same AI tick as a change of possession. The median reaction is 0 s.
   - Possession changes hands (or goes loose) 41.5 times a game-minute, and 29% of those spells last under 0.3 s. So the targets the skaters steer for jump more than 2 m 48 times per skater-minute, and 81% of those jumps come at a change of possession.
   - People need about 0.2 s to react to an expected signal and about 0.4 s to choose between two [S]. Expert defenders wait *longer* than novices and get fooled less: 268 against 193 ms, and 14% against 42% wrong-way moves on fakes (VR rugby) [M].
2. **Everybody skates flat out, and bang-bang.**
   - The AI's mean speed is 0.84 of its top. It spends 64% of the time at 90% of top or more and 1.8% standing. It skates backward 0.4% of the time.
   - Its acceleration sits on the 5 m/s² cap 40% of the time and reverses direction at the cap 36 times per skater-minute.
   - Kucherov averaged 0.42 of his top speed while on the ice [D]. University forwards averaged 0.34-0.37 of their peak [D]. Elite national-team players stood or glided 38-44% of play and skated backward about 12% [M].
3. **The puck is glued, and turnovers are dice.**
   - The puck is put 0.75 m straight ahead of the carrier every 20 ms, about 0.4 m from where his blade is drawn. A light poke from Jon is undone the next tick unless it moves the puck 0.5 m or 3 m/s.
   - 34% of AI touches end in a random poke: 0.34 losses per second of carrying. Finnish league carriers kept the puck through 95.4% of one-second carries, about 0.05 losses a second [D from M; the definitions differ].
4. **Passes no player would make.**
   - 50% of AI passes leave more than 90° from where the passer faces. 66% are made with an opponent within 1 m, because a pressed carrier passes on a coin flip. All leave at 10 m/s.
   - 45% reach the intended teammate. The Liiga's tracked passes succeeded 79.9% of the time [M]; elite women's games 73.5% [D].
   - Of the 213 passes the other team ended up with, 91 had already reached the receiver's stick and failed the flat 45% catch roll.
5. **Defenders glued on, and swapping.**
   - The nearest defender sits a median 1.17 m from the carrier, with his stick in poke reach 58% of the carrier's time.
   - Marks change 2.1 times per skater per game-minute even when possession is settled.
   - The loose-puck chaser changes 4.3 times per loose-puck minute, and 39% of the changes flip back within 1 s.
6. **Nobody looks, talks or differs.** Facing is the travel direction. Every decision uses everyone's true position, though the puck is behind a skater (more than 90° off his facing) 16% of his time off the puck. No teammate speaks. All five AI skaters share one set of constants and one look.

**What a Kucherov is.** Not speed.
- In 2025-26 he scored 130 points with a top speed at the 61st percentile [M]. In 2023-24 he averaged 0.42 of his top speed on the ice and went over 20 mph about twice a game [D].
- He touches the puck more: 41.5 possessions per 20 minutes at 5v5 (2023-24), against 31.3 for the average forward [M]. His average possession is under the top-10 cut-off of 1.67 s [M]; its exact length is not published.
- He passes across the slot and through the middle [S], and scored on 19.1% of his shots in 2025-26, against 13.0% for forwards [M].
- Scouts describe a slow, gliding pace, curved "inside-out" routes, and waiting "just long enough" [V].
- So "a team of Kucherovs" means earlier and better reads, an honest puck, patient pace with real bursts, and bodies that show what they mean. It does not mean faster legs.

**The changes that do the most** (all 17, in order, in section 2):
- **Staggered, committed roles** (changes 3-4). Each skater reacts to a turnover after his own 0.2-0.45 s, keeps his role and his man, and steers for a target that moves smoothly. In a scratch test the delay alone cut same-tick reactions from 95% to 23% and lifted pass completion from 45% to 51% [E].
- **Jon's skating model, with cruise and burst** (changes 5-7). Push 6, glide 1.5, stop 8, carve 6 m/s²; cruising at about half of top and bursting on a read; steering round people instead of being shoved.
- **Honest catches, and passes picked by time-to-intercept and value** (changes 8-9). No catch dice, no coin-flip passes under pressure, passes at 7-19 m/s through lanes a player would use.
- **Defence that holds a gap and commits on cues,** with pokes you can see coming (change 10).
- **Bodies that show intent:** backward skating, pivots, hockey stops, and a head that looks before it goes (changes 11-12).
- **A real AI blade** in the 1 kHz contact model (change 17). It is the end goal: Jon plays against a puck that is really on a stick. It is cheap once compiled, but its controller is not ready.

**Keep:**
- the real 1 kHz puck for passes and shots;
- `goalie.py`'s model, which already rewards a quick cross-slot shot (xG 0.78 against a set goalie, 0.95 straight after a 4 m lateral pass) [D];
- an average touch close to the NHL's (1.0 s against 1.29 s [M]; the medians differ);
- AI that never pushes Jon (but change 5 should make it steer round him instead of snapping).

**Cost.** One AI tick takes 0.90 ms on average (p99 1.96 ms), 4.5% of a core [D]. It runs inside the 1 kHz physics tick and holds the GIL. Changes 1-16 add roughly 10-15 ms per second of game (1-1.5% of a core), if the heavy parts run at 4-10 Hz and are spread over ticks [E: the per-change costs in section 2, added up]. A vectorised skating step (change 6) could win back about as much, since the six `_skate` calls are about 0.4 ms of each tick [D/E]. The AI blade adds about 0.26% of a core per blade, outside the GIL, once its controller is compiled [D/E].

**Comfort.** None of this moves Jon's view. The risks are things filling it close by [E]: an AI figure snapped sideways next to his head (today's `_separate`), bursts and pivots within 1-2 m, and a defender closing fast on his face. Changes 5 and 10 lower these, and changes 7 and 11 carry rules that keep bursts and fast pivots away from his head. Change 1 logs what is needed to check a sickening session against AI motion.

---

## 2. The ranked change list

**How it fits together.** The notes point to a layered AI [E]:
1. **Perception:** what each skater has seen, and when.
2. **Belief:** where he thinks everything is.
3. **Intent:** his role and his decision.
4. **Motion and expression:** skating, body, head, stick and voice.

The puck stays physical through all of it. A skater's belief may be wrong, but when the puck reaches his blade, the physics decides. The order below is not the layer order. It puts cheap, visible fixes first, builds each layer a piece at a time, and leaves a playable game after every step.

**How to test each step.**
- **Self-play:** re-run this report's probe after each change (change 1 puts it in `prototype/`). Compare with the baseline in section 4.
- **Headset:** one change at a time. A, then B, then A, 3 minutes each, at the same level.
  - After each pair, two forced choices: "Which felt more like playing with people?" and "Which was fairer?", plus one sentence on why. Paired choices reduce the order and consistency effects that ratings show [S].
  - His usual comfort check after each condition.
  - Swap the order on another day: in one study 11 of 16 players worked out what was being tested [M].
  - Put each A/B switch in the settings menu, like the other settings.
  - Later, also show him 30 s of replay from above. Judging while playing may distort the judgement [E, the authors' argument, untested].

| # | Group | Change | CPU | Comfort risk | Self-play check, now → target |
|---|---|---|---|---|---|
| 1 | measure | Log the AI (`ai.csv`) and score it with a metrics script | ~13 kB/s of log | none | reproduces section 4's baseline |
| 2 | puck | Puck under the drawn blade; Jon's blade contact takes it off the AI; `CARRY` 0.85 → 0.95 | none | none | puck-to-blade gap 0.39-0.43 m → < 5 cm |
| 3 | person | Staggered reaction to possession changes | ~20-50 µs/tick | none | same-tick role changes 95% → ≤ 25%; median 0 → 0.2-0.3 s |
| 4 | person | Commit to roles; smooth targets | µs | lower | target jumps 48 → < 2 per skater-min; chaser changes 4.3 → < 1 per loose-min |
| 5 | skate | Steer round people; no snaps | tens of µs | lower | shoves 27 → < 1 per skater-min |
| 6 | skate | AI skaters on Jon's skating model | about the same as now | low | accel reversals at the limit 36 → < 2 per skater-min; jerk p99 458 → < 100 m/s³ |
| 7 | skate | Cruise and burst | none | low-medium | mean speed 0.84 → 0.40-0.55 of top; time at ≥ 90% of top 64% → ≤ 10% |
| 8 | puck | Honest catches (no 45% roll) | none | none | intercepted passes after a missed catch 43% → < 15% |
| 9 | think | Passes by time-to-intercept and value; protect; move it before contact | ~4 ms/s per carrier | none | completion 45% → 65-80%; passes with an opponent within 1 m 66% → < 25% |
| 10 | think | Defence: gap, cues, held marks, telegraphed pokes | negligible | lower | nearest defender 1.17 → 2-4 m away from his net; stick in poke reach 58% → 20-35% |
| 11 | skate | Backward, pivot, stop, glide; gait from the kinematics | branches; drawing up to ~2.8% of a core uncached | medium (pivots close by) | backward 0.4% → 8-15% |
| 12 | person | A head that looks; a view that limits what each skater knows | tens of µs | none | no decision uses an unseen player; back-door goals appear |
| 13 | think | Support by openness and value; give-and-go; regroup | ~4 ms/s | none | carrier time with no open teammate 29% → < 10%; regroups 0 → some |
| 14 | teammate | A teammate for Jon: read his head, pass when he can take it, get open in his view, cover, call | trivial; 3.5 MB of clips | low | AI teammates' passes to Jon 17.5% → 35-50% while he is open |
| 15 | think | Pre-decide, one-touch, disguise | trivial | none | releases under 0.15 s on prepared plays: none → some |
| 16 | person | Individuals and level through perception | trivial | none | Jon can name the playmaker |
| 17 | puck | A real AI blade in the 1 kHz contact model | ~0.26% of a core per blade, off the GIL (compiled) | low | holds the puck 10 s standing and on 4-8 m curves |

### 1. Log the AI, and score it

- **Build.**
  - `game.py`'s log: an `ai.csv` at 50 Hz with each AI skater's position, velocity and facing (later its head, body state and intent), the goalies, and who has the puck. About 12.6 kB/s as text [D: 50 × 7 × 6 numbers × about 6 bytes].
  - Move this report's probe (`research_notes/Lifelike AI players/scripts/synth_probe.py` and `synth_analyze.py`) into `prototype/` (for example `selfplay_metrics.py`, or a printing test in `tests/test_threes.py`). It should print section 4's table for self-play and for any `ai.csv`.
- **Why.** The game recordings do not log AI positions every tick, so nothing measured here can be checked on Jon's real games. "Was the sickening 3v3 about the AI's motion?" also needs it [E].
- **Cost.** Trivial.
- **Check.** The script reproduces section 4's baseline within the spread between seeds.

### 2. Three quick honest-puck fixes

- **(a) The puck under the drawn blade.**
  - Now: the puck rides `STICK_R` = 0.75 m straight ahead. `figures._local_cached` draws the blade from (1.05 m ahead, 0.42 m aside) to (1.12, 0.12). The nearest point of the blade is 0.39 m from the puck, its middle 0.43 m [D]. It reads as a puck floating ahead of the stick.
  - Build: make `Player.stick()` and the drawn blade the same point: the blade's middle, about 0.8-1.0 m ahead and 0.15-0.25 m to the shooting side [E]. Pickups, pokes and lanes measure from `stick()`, so re-run the baseline afterwards.
- **(b) Jon's contact takes the puck off the AI.**
  - Now: `_possession` counts the puck as lost only if it ends more than 0.5 m from the carry point, or moving 3 m/s faster or slower than him. A smaller touch from Jon is undone at the next tick. In his three logged games (14.8 minutes) the log has 10 "lost by you" events [D].
  - Build: pass the physics' contact (`imp` in `GamePhysics._game`) to `Game.update`. When Jon's blade touches a puck an AI is carrying, the AI loses it and it is a loose puck. The 0.5 m / 3 m/s test stays only for the boards and nets.
  - This also follows Jon's rule against magnets: today the AI's puck is a magnet that his stick can only beat by a big hit.
- **(c) `CARRY` 0.85 → 0.95.** U16 national-team players were 4.9% (elite) and 4.3% (sub-elite) slower on an agility course with the puck [M]. Round 2 already suggested 0.92.
- **Cost.** None. Small effort.
- **Comfort.** None.
- **Check.** Gap under 5 cm; carry speed p90 0.85 → 0.95 of the AI's top. A/B for (b): "Do light pokes count now?"
- **Interim note on pokes against Jon.** An AI poke on Jon's puck now moves it 0.12 m and sets it off at 5-6.5 m/s, from up to 1.3 m away. That is an action at a distance on the puck he plays, against him. Change 10 makes it visible and geometric; change 17 makes it a real stick.

### 3. Staggered reaction to possession changes

- **Build.** In `Game._targets`, or a new `Game._perceive` called before it:
  - On each change of who has the puck, and on each pass or shot, give every AI skater his own reaction time [E]:
    - 0.18 s plus an exponential tail with a mean of 0.1 s (median about 0.25 s), when the puck is within about 50° of his facing;
    - +0.1 s in the side of his view (50-110°);
    - behind him (more than 110°): +0.2 s more for now; after change 12, nothing until he checks, hears a call, or the puck comes within 1.5 m.
  - The new carrier, the passer and the intended receiver react at once.
  - Until his time is up, a skater keeps his old target.
  - Contact with the puck stays instant and physical.
  - `level` and each player's profile set the base (section 3).
- **Evidence.**
  - Today: 95% same tick, median 0 s [D].
  - Lab reactions: 0.19-0.22 s to a simple visual signal, 0.38 s to choose between two (Laming, Kosinski, in Rabin's survey) [S]. Olympic sprinters' best reactions to the gun averaged 0.166 s (men) [M]. Reaction times are skewed to the right [M; the cited fit is of children].
  - Expert rugby defenders in VR started moving later than novices (268 against 193 ms) and bit on fakes less (14% against 42% of deceptive trials) [M]. A good defender reacts to the right cue, not first.
  - Halo's designers added a pause before enemies noticed the player. Playtesters read it as a bug, so it was removed [V]. So the delay must have a visible cause: a head turned away (change 12).
  - The scripted drill in `retrieval.py` already gives its skaters a 0.25 s `REACTION` to a pass.
- **Scratch test** [E: `synth_probe.py` with `DELAY=1`, four 600 s games, the same seeds as the baseline, the rule above with "behind" as +0.3 s in total, since there is no head yet]:

  | Measure | Now | With the delay |
  |---|---|---|
  | Role changes on the same tick | 95% | 23% (carriers, passers, receivers) |
  | Median reaction | 0 s | 0.31 s |
  | Target jumps over 2 m, per skater-minute | 48 | 33 |
  | ... not at a possession change | 9 | 26 |
  | Pass completion | 45% | 51% |
  | Losses per second of carrying | 0.34 | 0.27 |
  | Nearest defender to the carrier, median | 1.17 m | 1.57 m |
  | Goals in about 38 game-minutes | 25 | 22 |

  - The delay soaks up the shortest possession spells, so a third of the jumps go. The rest just come later, when each delay ends. So change 4's spring is still needed.
- **Cost.** A dot product and a random draw per skater per event: about 20-50 µs a tick [E].
- **Comfort.** None. Fewer bodies lurching at the same instant.
- **Check.** Same-tick role changes ≤ 25%; median 0.2-0.3 s, p10-p90 about 0.15-0.5 s. A/B: "Which felt more like people?" and "Did they look slow?" If Jon reads it as sluggish or buggy, bring change 12 forward.

### 4. Commit to roles, and smooth the targets

- **Build** [E for every number]:
  - `_chase`: keep the current chaser unless another skater can get there at least 0.2 s sooner.
  - `_defend`: hold marks. Switch only when two attackers cross and the swap saves both defenders more than about 2 m of skating. Log each switch as an event (change 14 can call it out).
  - `_support` and `_carry_to`: flip sides only when the carrier is 1-1.5 m past the rink's long axis (x = 0), not at it. A supporter moves to another spot only if it scores at least 20% better.
  - Then pass every target through a critically damped spring with a half-life of 0.2-0.3 s before `_skate`.
- **Evidence.**
  - Today 81% of target jumps come at a change of possession, and 9 per skater-minute come in settled play. The chaser changes 4.3 times per loose-puck minute, 39% back within 1 s. Settled play still sees 2.1 mark changes per skater per game-minute (1.9 in the hockey-IQ fact-check) [D].
  - The fact-check found that the hysteresis rules alone touch only about 20% of the jumps; a spring or a delay before switching roles is needed [D]. The scratch test above agrees.
  - People change their minds rarely, mostly to correct an error (3 subjects, dot motion) [M]. Bots that went "back and forth" were spotted after about 3 minutes (organisers' observation) [V]. Game-AI practice uses an inertia bonus or a minimum hold to stop flip-flopping [V], and a companion that filters out needless short moves [V].
  - Critically damped springs with a half-life are a standard cheap smoother in game animation [V].
- **Cost.** A few floats per skater. Microseconds.
- **Comfort.** Lower: fewer sudden changes of direction near Jon.
- **Check.** Count raw target jumps before the spring and smoothed ones after it separately [D, fact-check advice]. Smoothed jumps over 2 m: 48 → < 2 per skater-minute. Chaser changes < 1 per loose-puck minute, < 5% flipping back. Settled mark changes < 0.5 per skater per game-minute. A/B changes 4 and 5 together.

### 5. Steer round people; no snaps

- **Build.** `Game._separate`:
  - Between AI skaters: steer each one round anyone he will pass within about 1 m in the next 0.5 s, as a sideways request inside his skating limits. Keep a hard push only below about 0.6 m [E].
  - Round Jon: never snap. Start steering about 2 m out. Keep a 1 m bubble round him unless the skater is in his view and slowing [E].
- **Evidence.**
  - Today: 27 shoves per skater-minute (a skater moved more than 3 cm beyond its velocity in one tick) [D]; 19-26 in the notes.
  - `_separate` keeps Jon from being pushed by snapping the AI figure to 0.9 m from him in one tick. That is a sideways jump right beside his head (fact-check).
  - Arousal rose the closer virtual characters came (12 men, skin conductance) [M]. The Last of Us's designers never let their companion teleport [V].
- **Cost.** 15 pairs a tick in numpy: tens of µs [E].
- **Comfort.** Removes the snaps near his face.
- **Check.** Shoves < 1 per skater-minute. With Jon (or a stand-in): no AI position jump over 3 cm within 2 m of his head; log the closest approach per minute.

### 6. AI skaters on Jon's skating model

- **Build.** Round 2's change 11, still open.
  - Replace `Game._skate`'s single 5 m/s² cap with a `rig.Drive._push`-like step using Jon's numbers: push 6, glide 1.5, stop 8, carve 6 m/s², backward 0.8 of forward.
  - Its push eases into the wanted speed over `EASE` (0.1 s), which ends the hunting round the target. Its onset is still a step to 6 m/s², so also ramp the push up over 0.15-0.2 s [E].
  - Arrivals use about 0.7 × the stop rate. Idle skaters glide at 1.5 m/s², or stop at 8 when play stops.
  - `_reach` and `_lane` should use the same limits: push time and turning time, not instant top speed plus a fixed 0.15-0.25 s.
  - One numpy step for all six skaters, instead of six Python calls.
- **Evidence.**
  - Today: the acceleration sits on the cap 40% of ticks and reverses more than 90° at the cap 36 times per skater-minute; jerk p99 458 m/s³; 12 hard speed-ups and 12 hard slow-downs per skater-minute (over 2 m/s² for 0.3 s or more) [D].
  - University players made about 2.2-3.2 hard accelerations and 2.7-4.3 hard decelerations per minute, if their ice time was 15-20 minutes [D; good to about a factor of 1.5]. Braking outnumbered pushing [M].
  - Smooth, minimum-jerk motion is what viewers and their own bodies respond to as human; constant speed on a curve looks wrong [M, in arm and walking studies; carrying it to skating is [E]].
  - The current `_skate` is Reynolds' steering vehicle, which "cannot simulate effects such as skids, spins or slides" [V].
- **Cost.** `rig.Drive.update` costs 51-56 µs a call against 65-68 µs for `_skate` [D]. The six `_skate` calls are about 0.4 ms of today's 0.9 ms tick [D: 6 × 65 µs], so a vectorised step should lower the tick.
- **Comfort.** Low. Motion near Jon becomes steadier and readable.
- **Check.** Reversals at the limit < 2 per skater-minute; jerk p99 < 100 m/s³ [E target]; hard bouts 3-6 per skater-minute, with slow-downs at least as common as speed-ups.

### 7. Cruise and burst

- **Build.**
  - Each target carries a wanted speed: about 0.5-0.6 of the AI's top when supporting, holding a gap or covering; the full top only on a trigger: a loose puck he can win, a lead pass, a beaten defender, a backcheck. A carrier glides, then bursts with 2-4 quick strides at about 4 m/s² [E].
  - `Game.vmax`: tie the AI's top to 0.95 × Jon's **sprint** (4.3 m/s at his 4.5) and its cruise to about his cruise (2-3 m/s) [E]. Its average then stays at or below his, and bursts can show. Today the top is 0.95 × his cruise (2.85 m/s), so it can never burst.
  - This changes the rule "never faster than 95% of your skate speed" from his cruise to his sprint. That is Jon's call (section 5).
- **Evidence.**
  - Today: mean 0.84 of top, 64% of the time at ≥ 90%, 1.8% standing [D].
  - Kucherov 2023-24: 0.42 of top on the ice; 2 bursts over 20 mph a game [D from M]. University forwards: 0.34-0.37 of peak; 2-3% of the time above 80% of peak [D]. Elite players: standing 16-20%, gliding 18-27% of effective play [M].
  - Carriers: scouts describe gliding, then bursting [V]. No tracking study of carriers' change of pace was found.
- **Cost.** None.
- **Comfort.** Low-medium. AI speed never moves Jon's view, but a skater bursting across close in front fills it. Don't aim bursts within about 1.5 m of his head [E].
- **Check.** Mean 0.40-0.55 of top; time at ≥ 90% of top ≤ 10%; standing 10-20%; gliding (a new state) 20-30% [E targets from the elite numbers]. A/B at two cruise levels (0.5 and 0.65 of top): "Did they look like players, or asleep?"

### 8. Honest catches

- **Build.** `_loose`: replace the flat rule (always caught under 7 m/s relative to the stick, 45% from 7 to 16 m/s, never above) with a chance that falls smoothly with relative speed and depends on the receiver [E]:
  - about 1.0 up to 6 m/s, 0.5 at 12 m/s, 0.1 at 18 m/s;
  - ×0.6 if the puck comes from more than about 60° off his facing (after change 12: if he hasn't looked at it), or he is mid-turn;
  - the elite profile shifts the curve up about 2 m/s.
  - A miss is a bobble: the puck goes on, slowed and deflected. It is not 0.3 s in which he can't touch it.
  - Change 17 later replaces this with a real catch on a real blade.
- **Evidence.**
  - Today: 91 of 213 intercepted passes had reached the receiver's stick and failed the roll [D]; 52 of 111 in the fact-check [D].
  - The hockey-IQ fact-check: fix or model the catch before judging any change to pass choice, or a better choice model will look weaker than it is.
  - In the NHL, failed receptions came at higher pass speeds than successful ones, except into the slot (Sportlogiq, all 5v5 passes of 2017-18) [M]. No hockey catch curve was found, so the curve above is a guess.
- **Cost.** None.
- **Check.** Intercepted passes that followed a missed catch: 43% → < 15%. Completion rises a little on its own; most of the rise comes with change 9.

### 9. Passes chosen by time-to-intercept and value

- **Build.**
  - **Pass odds.** Replace `_lane` with a vectorised `_pass_odds` [E design, after the rink-control and passing-lane models]:
    - receive points at the receiver's projected blade (velocity × flight time), plus two leads;
    - speeds 7, 10 and 13 m/s (up to about 19 for the elite profile through a tight lane);
    - the puck's path sampled every 0.1 s with `pk.slide`;
    - each opponent's time to each point = reaction (0.2 s, +0.1 s on a pass) + the time to get there under change 6's limits (turning costs time) − 1.0 m of stick reach;
    - P = the product over opponents of a logistic of the time margin (keep the 0.12 s scale).
  - **Choice.** In `_decide`, remove the coin flip under pressure.
    - A pass is worth P × V(reception) − (1 − P) × V_opp(turnover spot).
    - Near the net, V is the shot's xG with the goalie where he will be (`gl.shot_xg` with `gl.after_tracking`). Elsewhere it is a small continuation value.
    - Compare with carrying (his own value 0.5 s ahead) and with shooting.
    - Give the current plan an inertia bonus (×1.2) and a minimum hold of 0.5-1 s, unless something clearly better appears (xG up 0.05, a lane opening).
  - **Move it before contact.** Add the time until the nearest defender's stick reaches the puck. Below about 0.3 s the carrier must pass, shoot or protect. Protecting means curling away with his body between the puck and the presser, or a delay move from the IIHF list: a tight turn to the boards, a fade, or a stop facing the middle [V].
  - **Passes behind him.** A pass more than about 100° off his facing means turning first (a turn-rate limit plus 0.15-0.3 s), or a backhand at about 70% of the speed with double the aim error [E; no measurement of backhand passes was found].
  - **Pass speed** set by distance and lane, within 7-19 m/s, instead of a fixed 10.
- **Evidence.**
  - Today: 66% of passes with an opponent within 1 m and 93% within 1.6 m; 50% more than 90° from facing; completion 45%; median length 7.3 m [D]. At least 65% of passes qualify only through the coin-flip branch [D, hockey-IQ note].
  - Completion: Liiga 79.9% of 535,449 passes [M]; elite women's games 73.5% [D].
  - NHL completed passes: median length 11.6 m [M]; flight-average speed median about 10.5 m/s, middle half 7.7-13.3 m/s, top 5% above about 19 m/s [D, read off a figure; completed passes only].
  - Projecting receivers and opponents along their velocity cut the error in where the receiver took the pass for over 94% of NHL passes [M]. The rink-control model's 0.189 s reaction comes from sprint starts, and its +0.1 s for defenders is an assumption [E].
  - Liiga danger after a successful pass: into the slot 9.1%, lateral 3.6%, outlets 1.1% [M].
  - The goalie model already pays for a quick, hard seam pass: xG 0.78 against a set goalie, 0.95 at once after a 4 m lateral pass, 0.88 after 0.3 s, back to 0.78 by 0.5 s [D]. A 20 m/s back-door pass shot within 0.1 s gains 0.14-0.22 xG; the AI's 10 m/s passes gain nothing in any geometry tried [D].
  - Kucherov's passes go across the slot and through the centre lane [S].
- **Cost.** About 0.2 ms per pass-odds call; with `shot_xg` (0.15-0.16 ms a call) about 1 ms per decision, about 4 ms per second per carrier [D/E]. Cache the xG per goalie position. Spread the work over ticks so the tick's p99 stays near today's 2 ms: the AI runs inside the 1 kHz physics tick.
- **Check.** Completion 65-80%; passes with an opponent within 1 m < 25%; passes more than 90° off facing < 15% (and those slower); losses per second of carrying 0.34 → 0.05-0.10; median pass length 9-12 m; more cross-slot passes. A/B: "Do their passes look meant?"

### 10. Defence: gap, cues, held marks, telegraphed pokes

- **Build** (`_defend`, and the pokes in `_possession`) [E design from coaching and tracking]:
  - The presser stands on the line from the carrier to the net. His gap shrinks from 3 to 1 stick lengths between the far blue line and his own: 4.3 → 1.4 m with Jon's 1.42 m stick [D]. He matches the carrier's speed and sits about 0.3 m inside.
  - He steps up when the carrier slows by more than 1 m/s within 0.3 s, or a pass is arriving within 0.3 s (coaching cues [V]). The notes also propose "turns his back" and "within 1.5 m of the boards" [E, their own ideas].
  - One presser plus one in the lane; no gang-ups unless the carrier is in the slot.
  - A poke is a visible 0.2-0.3 s reach, then succeeds or not by blade-to-puck geometry and how exposed the puck is, not by `POKE_RATE` dice. The same for pokes on Jon (`POKE_YOU`).
  - A beaten defender recovers to the inside lane, between the carrier and the net front. He does not chase the puck.
  - Marks are held as in change 4.
- **Evidence.**
  - Today: nearest defender median 1.17 m, stick in poke reach 58% of the carrier's time [D]. The presser aims at the carrier's blade plus 0.6 m goal side at every speed and in every zone.
  - Coaching: 3, 2 and 1 stick lengths at the far blue line, the red line and his own blue line; match the speed; inside shoulder [V].
  - Youth rugby 1-on-1s: within 4 m, an attacker who keeps a relative speed of 1 m/s or more wins [M]. Its transfer to hockey is unmeasured.
  - AHL tracking slides: a tight gap cuts the number of shots; controlling the space cuts their quality [V].
  - Over-committing gives up the odd-man rush. A 2-on-1 entry yields about 9 times the goals of a 3-on-3 entry [D from M].
- **Cost.** Negligible.
- **Comfort.** Lower: fewer fast approaches to Jon's face, and every poke at him is visible first.
- **Check.** Nearest defender median 2-4 m away from his own net, about 1.4 m at his blue line, tighter in the slot; stick in poke reach 20-35% of carrier time [E targets]; poke losses per second of carrying 0.34 → 0.05-0.10. Watch shots per minute and xG per shot: a looser gap may allow more shots. A/B: "Could you see him coming?" and "Was that fair?"

### 11. Backward, pivot, stop, glide; gait from the kinematics

- **Build.**
  - A new `Player.body` heading beside `facing`, and a five-state machine [E]:
    - FORWARD, body along travel;
    - GLIDE, no push, legs together;
    - BACKWARD when the wanted facing (his man, the puck) is more than about 120° from travel: top 0.8, push half. For defenders with their man in front, and the trailing supporter;
    - PIVOT: the body turns 180° at 400-600°/s while the path carries on;
    - STOP when the wanted direction is more than 120° from travel above 1.5 m/s: body 90° to travel, braking at 8 m/s², then pushing the new way.
    - Each state holds at least 0.3 s.
  - `figures` draws `body`, and the gait from the kinematics:
    - a stride that lengthens with speed: about 1.5-2 m a push at 2-3 m/s, 3-4 m at 5-6 m/s; short, quick strides only when accelerating hard;
    - legs together while gliding or braking; a stop pose; backward C-cuts; crossovers when the sideways acceleration passes about 2 m/s²;
    - a lean into turns of atan(a/g): 31° at 6 m/s² [D];
    - the feet push back and out against the ice, never sliding forward.
- **Evidence.**
  - Today: backward 0.4% of moving time; facing turns up to 515°/s (p99); a reversal is a straight-line brake facing forward, legs striding, then a body swing [D].
  - Elite players skated backward about 12% of effective play [M]. Defencemen skate backward and pivot more than forwards, with no difference between Major Junior and university [M]. Coaches criticise "curling away" instead of stopping and starting [V].
  - Hard stops average 0.8-1 g [M, round 2].
  - The drawn figure pushes once every 0.85 m whatever the speed. Real forward strides at speed are 4.0-4.4 m [S], so it is 3-5 times too short, and it never glides [D].
  - The direction of walking is carried entirely by the motion of the feet [M]. Stick figures hide pose changes better than solid models, but not a bad path [M].
- **Cost.** A few branches per skater. Drawing: lean, state and head angle multiply the cache keys. An uncached figure costs 59-78 µs, so 5 figures at 72 Hz is 2.1-2.8% of a core in the render thread, which shares the GIL [D]. Quantise lean and state to keep most frames cached.
- **Comfort.** Medium for pivots: a figure spinning at 500°/s right in front of Jon. Keep fast pivots more than about 2 m from his head, or slow them there [E].
- **Check.** Backward 8-15% (defenders more); straight-line reversals → 0 (they become stops or pivots); body turns over 400°/s only inside a pivot. A/B with changes 6 and 7 in: "Did they look like people skating?"

### 12. A head that looks, and a view that limits what each skater knows

- **Build.**
  - `Player.head`: a yaw drawn as a visor or nose line on the head rings.
  - Where it points, in order [E]:
    - the puck by default;
    - ahead into a turn, by about 0.2 s and up to about 30°;
    - quick checks of 30-90° toward what matters (the back door, his man, the open lane) for 0.3-0.5 s, at the profile's scan rate (0.2-0.6 a second), fewer with an opponent close;
    - the passer before a reception; Jon when Jon has the puck and this teammate wants it.
  - Perception reads the head: central view about ±50°, side view to about ±110°, then behind. Each skater keeps a belief: what he last saw, moved on by its velocity. `_decide`, `_targets` and the pass odds read the belief, not the truth. A check refreshes it. Events behind him wait for a check, a call, or the puck within 1.5 m.
- **Evidence.**
  - Today: the puck is behind an off-puck skater 16% of the time, and he still reacts to it on the next tick [D]. Acting on things not looked at gave game bots away [S].
  - Walking people's heads lead a change of direction by about 0.2 s and up to about 30° [M]; their gaze leads the pelvis by about 0.56 s [M]. Carrying this to skaters is [E].
  - Elite junior hockey players' fixations last about 135 ms; 47-53% of forwards' first fixations go to open space [M]. Premier League players scan 0.44 times a second, less with an opponent within 1 m [M].
  - A head that sizes up two targets "can telegraph deep intelligence" [V].
  - Gaze helped a realistic avatar but hurt a "match-stick" one (conversation in shared VR) [M]. Jon's figures are match-stick figures, so test it.
- **Cost.** Dot products per skater per tick, tens of µs [E]; a few line segments to draw.
- **Comfort.** None.
- **Check.** A unit test: no decision uses a player outside the view who was not seen in the last ~2 s. In self-play, back-door goals appear (a receiver his mark had not seen). A/B head on/off: "Could you tell what they were looking at? Did the heads look odd?"

### 13. Support, give-and-go, regroup

- **Build.**
  - `_support`: every 0.1-0.2 s each supporter scores 8-12 candidate spots: a ring 5-9 m from the carrier, the back door, the high slot, and the gap between two defenders. Score = P(pass completes) × V(spot) × "he gets there before it closes". He moves only to a spot at least 20% better [E].
  - In 3v3, one supporter always stays above the puck.
  - After a pass, the passer skates into the space behind his own defender for about 1 s, ready for the return [E].
  - `_carry_to`: three states, attack (a mismatch exists), probe (keep it moving) and regroup: when outnumbered and nothing beats carrying, curl to the half wall or the blue line; if nothing opens within about 2 s, take it back over the blue line and come again [E].
- **Evidence.**
  - Today: for 29% of the carrier's time no teammate's lane is open; no AI touch in 761 included a second of skating away from the net [D].
  - 3-on-3 overtime coaching: "possession at all costs"; pull it back out and try again [V]. Winners had 53-57% of possessions, possession time and offensive-zone time (243 overtimes, hand-tracked) [S].
  - A 2-on-1 entry led to a shot on goal 43.7% of the time at 22.0% shooting; a 3-on-3 entry 20.8% at 5.2% [M]: about 9 times the goals per entry [D].
  - Drawing defenders out of place creates space for teammates (soccer tracking) [M, method].
- **Cost.** About 0.2 ms × 2 supporters × 10 Hz ≈ 4 ms per second [D/E].
- **Check.** Carrier time with no open teammate < 10%; regroups appear (no measured target exists); 2-on-1s appear (log entries by type).

### 14. A teammate for Jon

- **Build** [E design throughout]:
  - **Read him.** `_you_update`: project his path from his head yaw plus his velocity. His left stick pushes relative to where he looks (`rig.Drive._want`), so his head is his steering wheel.
  - **Pass when he can take it.** To his projected blade, only while he faces within about 60° of the passer and isn't mid-turn. A/B 6.5 against 9 m/s, and log each pass's speed, closest approach to his blade and outcome.
  - **Get open where he can see it.** When he has the puck, supporters pick spots within about ±45° of his head direction, on his forehand side (he shoots left), 5-9 m away, and show a target: blade flat toward him for 0.5-1 s.
  - **Give-and-go.** He passes to an AI and skates for the net: the AI returns it within 0.5-1.0 s if the lane is open, having decided during the pass's flight.
  - **Cover.** When possession flips and he is caught up ice, the nearest AI takes the high role and his man until he is back.
  - **A fair share.** If he hasn't touched the puck in about 20 s and is open, prefer him.
  - **Calls.** Pre-render about 12 short calls in 2-3 voices at load, trim the silence, play by priority: "Man on!" (an opponent he hasn't looked at within about 3 m or 1 s), "Time!", "Here!", "Shoot!", "Wheel!", "Switch!". About one call per 2-3 s per team at most, and none when he already looked. Opponents' calls quieter.
- **Evidence.**
  - Jon's three logged games: AI teammates made 40 passes, 7 of them to him (17.5%, 0.47 a minute) [D]. With a scripted stand-in, the AI rated his lane open 36% of the time against 55% for its AI teammates [D].
  - Teammates built around a model of human play coordinated better with people than self-play-trained ones; the effect was weaker with real people [M]. People preferred a rule-based Hanabi teammate to a learned one, at equal scores [M]. So: explicit, learnable rules.
  - People find a partner by how he responds to them (65.9% of clicks against 23.0% for a copy that could not respond) [S].
  - 77% of players' talk in football pairs was orienting talk [M]; usually one or two words [S]. Dialogue showed the player that squad coordination was meant (F.E.A.R.); a companion called out threats the player hadn't seen (The Last of Us) [V].
  - The headset voice takes 0.34-0.75 s to render a one-word call and pads it to 1.1-1.3 s [D], so live rendering is too late.
- **Cost.** Trivial in the AI. About 3.5 MB of clips [D: 36 clips × 0.5 s × 48,000 samples/s × 4 bytes], rendered at load off the main thread.
- **Comfort.** Low. Keep any lifted pass to him under about 0.3 m within a few metres of him.
- **Check.** AI teammates' passes to Jon 35-50% while he is open [E; with two AI teammates, half of each one's options is him]; his reception rate from the log. A/B: "Did they play with you?", and calls on/off.

### 15. Pre-decide, one-touch, disguise

- **Build.**
  - `_take` and `_decide`: a receiver picks his next action from the state projected to the puck's arrival. On arrival he acts within 0.1-0.2 s if the plan still holds (a one-timer, a one-touch return); otherwise he protects it and decides again. The 0.15-0.35 s minimum stays for pucks he had to chase [E].
  - **Disguise** [E]:
    - a visible wind-up (stick up, square to the net) that leads to a shot or a pass, chosen late, from the same spot;
    - the head turned toward a decoy about 0.3 s before a pass (needs change 12);
    - a toe drag of 0.1-0.3 m across before a release when a stick is in the shot lane;
    - AI defenders react to what they see: the wind-up makes them lean into the lane.
- **Evidence.**
  - Today: no release under 0.161 s; 15% of shots come within 0.5 s of a received pass, but none is a true one-touch [D]. In elite women's games one-timers were 14.1% of attempts and scored 15.6% of shots on net, against 6.0% [D].
  - Kucherov: "we buy, I don't know, half a second for each other" [V]. On the power play the same look leads to a pass or a shot [V].
  - Elite goalies' final fixation sat on the puck or stick in 70.5% of trials and on the shooter's body in 2.1% [M]. So deception through the puck and blade matters more than body fakes [E].
  - A head fake slowed novices looking at photos by at most 34 ms, when the head turned 300 ms before the pass [M]. A flavour, not a weapon.
- **Cost.** One more state per carrier; drawing.
- **Check.** Releases under 0.15 s on prepared plays appear; one-timers 10-20% of shots [E]. A/B: "Could you read their shots?"

### 16. Individuals, and level through perception

- **Build.**
  - A `Player.profile` set at creation: reaction base (±0.04 s), scan rate (0.2-0.6 a second), anticipation (0.1-0.5), `SHOOT_XG` (0.10-0.22), patience (0.5-2.0 s), aggression, chatter [E]. One archetype per AI: playmaker, shooter, grinder, two-way D, puck-moving D.
  - Small style ranges: top speed and stride ±5-10%, lean, check rate. Slow, in-phase variation on arms and stick of about 15-17% of a swing, never white jitter.
  - A distinct look for each: a helmet band or number, height ±5 cm, stance width, stick length.
  - `level` maps onto perception and decision knobs (section 3), not onto speed, dice or aim.
- **Evidence.**
  - Five game "personas" that differed only in their utility weights played in distinct styles [M].
  - Copied appearances are far easier to spot than copied motion [M], so five identical figures read as copies whatever their tendencies [E].
  - Viewers preferred in-phase arm noise of about 17% of the swing to none or more (a male runner; no usable level for a female runner) [M].
  - A strong engine plus noise does not play like a weaker human: weakened Stockfish matched human moves 35-40% of the time, a model trained on human games 46-52% [M].
  - Racing developers dropped speed rubber-banding because "it's obvious when AI riders are going superhumanly fast or brain dead slow" [V]. Google Research Football's bot sets difficulty by reaction time and decision making [V].
- **Cost.** Trivial.
- **Check.** After a game, Jon names the playmaker. Pairwise: "Which team felt like individuals?" Win rate and "fair?" at two levels.

### 17. A real AI blade in the 1 kHz contact model

- **Build.**
  - `physics_core.sim_step` takes 1-3 AI blade arrays (only blades within about 0.5 m of the puck) and a compiled controller. The controller pushes along the wanted puck velocity, closes on the puck at no more than 0.8 m/s, follows it across, and goes over the puck to switch forehand and backhand.
  - The 50 Hz AI sets the intent: where the puck should sit relative to the body, the sweep's size and rate, and passes and shots as sweeps.
  - `_carry` stops placing the puck. `_take`'s 0.6 m pickup becomes a real catch (replacing change 8). Pokes become blade contacts. `figures` draws the stick where the blade is.
  - Give the blade a finite effective mass: the sim's 0.15 kg, inside the held-stick range of 0.13-0.20 kg from the Shot release round. Or have it yield when Jon's blade is on the puck too. Otherwise a stick battle feels like pushing a post.
- **Evidence.**
  - A scratch prototype hit the puck only through the sim's own compiled contact. It carried and stickhandled at 3-5.5 m/s with ±0.1-0.25 m sweeps at 1-2 Hz for 10 s in 9 of 9 runs, with a median error of 6-18 cm [D].
  - It lost the puck within about 1 s standing still with sweeps of ±0.2 m, and on curves of 4 and 8 m radius [D]. The standing ±0.1 m case "held" only because the puck sat still [D].
  - Sweep passes from rest left at the blade's speed ±1% after 49-333 ms of contact; skating at 4 m/s they went 7-15° off line [D].
  - Varsity players moved the puck sideways at up to 2.9-3.0 m/s against 2.5 m/s for recreational players, in one standing drill on synthetic ice [M]. The author reads the varsity technique as "volley and catch" [M, his reading].
- **Cost.** The compiled contact costs 0.59-0.65 µs per substep in contact: about 2.6 ms per second of play per blade, 0.26% of a core, outside the GIL [D]. The controller must be compiled too: in Python it took 69-90 µs per ms, 7-9% of a core holding the GIL [D]; compiled, about 1-3 µs per ms [E]. Effort: large.
- **Comfort.** Low. Shielding the puck must use puck and blade placement, never backing into Jon.
- **Gate.** Before it ships, self-play must keep the puck on the blade for 10 s standing still and on 4-8 m curves, and with Jon's stick, the boards or a defender in the way. Then A/B: "Does it feel like a puck on a stick?"

**For whoever owns `goalie.py`.** Hard, quick seam passes already pay in the goalie model, and change 9 lets the AI make them. Making the goalie's reach depend on time since the puck last crossed his line is a later option. It would fit Valiquette's "half a second of clear sight" [V] and goalies' final fixations of 0.8-0.95 s [M]. Leave it until changes 8-9 are measured.

---

## 3. What a Kucherov-style player is in parameters

**The archetype** [M/D where tagged; every setting is [E]]:
- Ordinary legs: top speed at the 61st percentile in 2025-26 [M]; on-ice mean 0.42 of top in 2023-24 [D].
- Many touches: 41.5 possessions per 20 minutes against 31.3 [M]. None of them long: under the 1.67 s top-10 cut-off [M].
- Passes across the slot and through the centre lane [S].
- A hard, accurate shot: 62.5 mph (27.9 m/s) on average against 53.2 mph for forwards; 19.1% shooting against 13.0%; 40% from high-danger areas against 19.6% [M, 2025-26].
- An off-wing shooter: left shot, listed at right wing [M].
- Patient: "buying time", "waited just long enough" [V].

| Knob | Now (every AI) | Rec setting | Kucherov setting | Basis |
|---|---|---|---|---|
| Reaction to an event in view | 0 s (same tick) | median ~0.25 s (0.20 base + tail) | median ~0.18 s (0.15 base + small tail) | lab 0.19-0.22 s simple, 0.38 s choice [S]; sprinters' best 0.166 s [M] |
| Event behind him | instant | after his next check, a call, or the puck within 1.5 m | the same, but he checks more | acting on the unseen gives bots away [S] |
| Biting on a fake | — (no fakes) | early wrong-way move on ~40% of fakes | ~15% | Brault: 42% against 14% on deceptive trials [M] |
| Head checks off the puck | none | 0.2-0.3 a second | 0.5-0.6 a second | soccer mean 0.44/s [M] |
| Pre-deciding on a pass to him | never | off: decides 0.15-0.35 s after the catch | on: acts within 0.1-0.2 s if the plan holds | — |
| Pass odds | lane model, opponents 0.25 s late at full speed; coin flip under pressure | time-to-intercept, noisy (σ about 0.15 on P), passes at P ≥ 0.8 | accurate (σ about 0.05), passes at P ≥ 0.6 | high-assist NHL players complete passes through small lanes (availability 0.59-0.70) [M]; "threading" is a reading [E] |
| Pass speed | 10 m/s (9 to Jon) | 7-12 m/s by distance | 7-19 m/s by distance and lane | NHL completed passes: middle half 7.7-13.3, top 5% ~19 m/s [D] |
| Pass more than 100° off facing | any, at full speed | turns first (~0.3 s) | turns, or backhands at ~70% speed | — |
| Patience (hold before a forced choice) | ~0.6 s median, then a coin flip | 0.5-1.0 s | 0.5-1.5 s, holding to draw a defender | NHL mean 1.29 s, 1.05 s in the offensive zone [M] |
| Getting it back | equal | equal | supports close, gives and goes, touches it ~30% more often | 41.5 against 31.3 [M] |
| Shoot threshold `SHOOT_XG` | 0.15 | 0.15 | 0.18, plus a bonus while the goalie is moving | his shooting % [M]; goalie model [D] |
| Shot speed | 22 m/s × U(0.85, 1.1) | 20-23 m/s | 24-26 m/s | rec wrist 16-26, slap 22-25 m/s [M, Shot release round]; Kucherov 27.9 [M]; the goalie is a rec goalie |
| Aim (`WILD`) | 2.2 / level | 2.2 | about 1.4 | — |
| Top speed | 0.95 × Jon's cruise (2.85 m/s), × (0.85 + 0.15·level) | 0.95 × Jon's sprint (4.3 m/s) | the same | ordinary legs [M]; no slow legs [V] |
| Pace | mean 0.84 of top | mean ~0.45 of top | mean ~0.40-0.45; bursts on reads | Kucherov 0.42 [D]; university 0.34-0.37 [D] |
| First steps (push) | 5 m/s² any way | 5 m/s² | 6 m/s² (Jon's push) | rec adults were 15% slower than university players over the first 10 m of a sprint, 7% over the last 10 [M] |
| Carry speed (`CARRY`) | 0.85 | 0.90 | 0.95 | 4.3-4.9% slower with the puck [M] |
| Defending the carrier | on his stick; random pokes (`POKE_RATE` × level) | gap by zone; telegraphed 0.3 s reach; bites on fakes | gap; commits on honest cues; 0.2 s reach when the puck is exposed | coaching [V]; rugby [M] |
| Disguise | none | none | same wind-up for shot or pass (pass 40-50% of the time); head toward a decoy 0.3 s before | [V]; head-fake timing [M, novices] |
| Regroup | never | rarely | when outnumbered and nothing is on | 3v3 coaching [V] |
| Calls | none | some | frequent | — |

**How level should scale without looking dumb or superhuman** [E, built on the [V] and [M] above]:
- **Scale the mind, not the body.** Level moves reaction time, scan rate, pre-deciding, fake resistance, pass-odds noise, the minimum P to pass, patience, and a little shot speed and aim. Skating limits and top speed stay honest and the same at every level, tied to Jon's. Today level mostly slows the legs (`vmax` × (0.85 + 0.15·level)), which reads as "brain dead slow".
- **Make errors with causes, never dice.** A weaker AI misses the back-door man because it didn't check, reacts late because the puck was behind it, or bites on a fake. Jon can see each cause and use it. A strong AI plus noise does not look like a weaker player [M].
- **Floors and ceilings at every level.** No reaction under about 0.15 s. Nothing acted on that wasn't seen. Passes to Jon at most about 12 m/s near him, any pass at most about 20 m/s, shots at most about 28 m/s, and accelerations inside Jon's own model.
- **No rubber band and no hidden help,** on any puck, for the AI as for Jon.
- **Two settings, in the menu:** "our skill" and "their skill", each from 0 (rec) to 1 (Kucherov). Playing *with* Kucherovs and playing *against* them are different games. Today's level 1 (game.py: "1 = rec") maps to about 0 on the new scale.
- **A team of Kucherovs** is the top of every mind knob, with individual styles (change 16) so they don't look like five copies.

---

## 4. Acceptance

"Now" is this report's baseline [D]: four 600 s self-play games, six AI, AI top 2.85 m/s, level 1. Definitions: a *target jump* is a skater's steering target moving more than 2 m in one tick; a *shove* is a skater moving more than 3 cm beyond its velocity in one tick; a *role reaction* is the time from a change of who has the puck to the skater's target first moving more than 1.5 m. Targets are [E] unless marked.

| Measure | Now | Target | Basis | Change |
|---|---|---|---|---|
| Role changes on the same tick as a possession change | 95% (median 0 s) | ≤ 25% (only carrier, passer, receiver); median 0.2-0.3 s | lab reactions [S]; sprinters [M] | 3 |
| Target jumps > 2 m, per skater-min (smoothed) | 48 (9 in settled play) | < 2 | none for a person | 3, 4 |
| Chaser changes, per team per loose-puck min | 4.3 (39% back within 1 s) | < 1 (< 5% back) | — | 4 |
| Mark changes in settled play, per skater per game-min | 2.1 (4.9 per min of settled defending) | < 0.5 | coaching: switches are called [V] | 4, 10 |
| Shoves, per skater-min | 27 | < 1; none within 2 m of Jon | — | 5 |
| Acceleration reversals at the limit, per skater-min | 36 | < 2 | minimum jerk [M, arms and walking] | 6 |
| Jerk p99 (commanded) | 458 m/s³ | < 100 m/s³ | — | 6 |
| Hard speed-ups / slow-downs, per skater-min | 12.2 / 12.1 | 3-6 each, slow-downs ≥ speed-ups | university 2.2-3.2 / 2.7-4.3 per min [D, ±1.5×] | 6, 7 |
| Mean speed / top | 0.84 | 0.40-0.55 | Kucherov 0.42 [D]; university 0.34-0.37 [D] | 7 |
| Time at ≥ 90% of top | 64% | ≤ 10% | 2-3% above 80% of peak [D] | 7 |
| Standing (< 0.3 m/s) | 1.8% | 10-20% | elite 16-20% [M] | 7 |
| Gliding | none (no glide state) | 20-30% | elite 18-27% [M] | 6, 7, 11 |
| Skating backward (body > 120° off travel, moving) | 0.4% | 8-15%, defenders more | elite ~12% [M] | 11 |
| Puck to drawn blade | 0.39-0.43 m (code) | < 5 cm | — | 2 |
| Jon's blade touches an AI's puck | lost only past 0.5 m or 3 m/s | always a loose puck | Jon's rule | 2 |
| Carry speed p90 / AI top | 0.85 | 0.95 | 4.3-4.9% slower with the puck [M] | 2 |
| Intercepted passes after a missed catch | 43% (91 of 213) | < 15% | — | 8 |
| Pass completion (intended receiver next) | 45% | 65-80% | Liiga 79.9% [M]; women's elite 73.5% [D] | 8, 9 |
| Passes with an opponent within 1 m | 66% | < 25% | — | 9 |
| Passes > 90° from the passer's facing | 50% | < 15%, and slower | — | 9 |
| Median pass length (to the stick) | 7.3 m | 9-12 m | NHL completed 11.6 m [M] | 9, 13 |
| Losses per second of carrying | 0.34 (all pokes) | 0.05-0.10 | Liiga about 0.05 [D from M; definitions differ] | 9, 10 |
| Touches ending in a poke | 34% | < 15% | — | 9, 10 |
| Nearest defender to the carrier, median | 1.17 m | 2-4 m away from his net; ~1.4 m at his blue line | coaching gaps [V] | 10 |
| Defender's stick in poke reach | 58% of carrier time | 20-35% | — | 10 |
| Carrier time with no open teammate | 29% | < 10% | — | 13 |
| Touches with ≥ 1 s skating away from the net | 0 of 761 | some (a regroup is routine in 3v3 OT) | [V] | 13 |
| Fastest release | 0.161 s | ~0.1 s on prepared plays | — | 15 |
| Shots within 0.5 s of a received pass | 15% | 10-20%, some true one-timers | women's elite one-timers 14.1% [D] | 15 |
| Off-puck time with the puck behind | 16%, reacted to next tick | about the same, reacted to only after a check, call or sound | — | 12 |
| AI teammates' passes to Jon | 17.5%, 0.47 a minute (his logs) [D] | 35-50% while he is open | — | 14 |
| AI tick, mean / p99 | 0.90 / 1.96 ms | ≤ 1.5 / ≤ 2.5 ms | it runs inside the 1 kHz tick | all |
| AI blade (if built), per blade | — | ≤ 0.3% of a core, off the GIL | [D] | 17 |

Watch, no target: goals (0.67 per live game-minute now), shots (2.5 per game-minute), average touch (1.0 s, median 0.6 s; NHL mean 1.29 s [M]), touches per game-minute (20.3). A change that moves these more than about 30% needs a look, even if it passes its own check [E].

---

## 5. What was dropped or corrected, and open questions

### Corrected in the fact-checks, and used here as corrected

- **Where target jumps come from.** Not mainly mirrored spots, mark re-pairing and the chaser: 76-81% come within a tick of a change of possession, which happens 42-52 times a game-minute (41.5 here), often in spells under 0.3 s. Hysteresis alone will not fix them; change 4 adds a spring and change 3 a delay.
- **Why passes fail.** About half of the passes the other team ends up with first reached the receiver's stick and failed the 45% catch roll (52 of 111; 91 of 213 here). So change 8 comes before change 9.
- **Mark changes.** About half follow a change of possession, where picking up the nearest man is normal. Compare fixes with the settled rate (1.9-2.1 per skater per game-minute).
- **Pokes.** Their odds do fall with the distance from the defender's blade to the puck; what they ignore is body position, speed, facing and any cue.
- **Gamble's pace.** Mean 0.34-0.37 of peak, not 0.36-0.39. The share above 80% of peak is 2-3% for 15-20 minutes of ice time.
- **Strides.** Real forward strides at speed are 4.0-4.4 m, so the figure's 0.85 m push is 3-5 times too short. Whether that study used a treadmill is unverified.
- **`_separate`.** It does not steer round Jon. It snaps the AI to 0.9 m from him in one tick.
- **Kucherov.** The possession counts are 5v5 2023-24. "Held briefly" is not shown: only that his mean is under 1.67 s, and elite players as a group include long holders (Barzal, the Hughes brothers, Makar). He finished 2025-26 with 86 assists in 76 games (1.13 a game), not 1.21. The "snail's pace" line is about his power-play spot.
- **NHL EDGE "league averages"** are averages for forwards.
- **Reaction times.** The rink-control model's 0.189 s comes from sprint starts, and its extra 0.1 s for defenders is an assumption: both [E]. Brault's 42% and 14% are for deceptive trials only. The cited reaction-time fit is of children.
- **Seam passes.** "Barely pays" holds for the AI's 10 m/s passes. A 20 m/s back-door pass shot within 0.1 s gains 0.14-0.22 xG.
- **Royal-road numbers.** The 30% against 8.5% is Chris Boyle's, not Valiquette's. The women's-data recount rests on 41 shots and depends on the definition.
- **Shootout routes.** The gap between curving and straight routes is within chance. Read it as "NHL shooters mostly curve", not "curving scores more".
- **Noise on the figures.** Uncorrelated noise looks odd only when it is large; the 17% did not hold for the female runner.
- **Possession length.** Only the means match the NHL; the AI's median is 0.6 s and the NHL uses its own possession model. "Already fine" became "not obviously wrong".
- **Smaller tag fixes** used as corrected: the BotPrize "3 minutes" is an observation [V]; Google Research Football's difficulty knob is a description [V]; "one or two words" is [S]; ranks *reduce* rating effects [S]; F.E.A.R. never tested coordination without dialogue; Rabin does not call the head look "most powerful"; the Liiga backcheck remark is [V]; "turns his back" and "pinned on the boards" as step-up cues are the note's own ideas [E].

### Where the notes disagreed, and what this report does

- **The blade's effective mass.** The puck-skills note quotes 0.2-0.28 kg from an earlier round. The Shot release report later put the held stick at 0.13-0.20 kg and kept the sim's 0.15 kg. Change 17 uses 0.15 kg.
- **One global delay or staggered delays.** The hockey-IQ note proposes decisions that read a world 0.2 s old; the presence note proposes a per-skater delay that depends on where he is looking. A global lag still has everyone react at the same instant, so change 3 uses per-skater delays.
- **Shares that depend on speed.** The puck-skills note measured at the default top speed (5.8 m/s): 58% of passes more than 90° off facing, 59% with an opponent within 1 m, 9% of shots within 0.5 s of a pass. At Jon's setting (2.85 m/s) this baseline gives 50%, 66% and 15%. Section 4 uses the headset setting.
- **Mark-change rates.** 3.9 per defender per minute (hockey IQ), 8.8-9.5 per defender-minute while defending a carrier (presence) and 4.9 per minute of settled defending (here) count different things. Section 4 gives the settled rate in both units.
- **Heads.** The skating note calls the head a cheap, strong cue; the presence note warns that gaze hurt match-stick avatars. Both are in change 12, behind an A/B.

### Rejected by this synthesis

- **Hysteresis alone for steady targets:** it touches about 20% of the jumps.
- **Speed as the difficulty dial,** rubber-banding, and dice for anything Jon can see.
- **"Elite" as faster skaters:** Kucherov's legs are ordinary.
- **A procedural stickhandle with the puck still placed:** it is still a magnet; a poke would hit a puck that teleports back. Only as a look test.
- **Motion matching and learned controllers:** they need motion capture and a skinned skeleton, and buy nothing for line figures [V/E].
- **Learned policies:** 8 × 10^10 steps and six weeks for humanoid 2v2 football; 500 million steps for Google Research Football's hard bot [M].
- **Copying hockey xT from student papers, or a learned Q-function from NHL events:** thin data, or data the sim doesn't have; build values from `goalie.shot_xg` and self-play instead.

### Open questions only Jon's play can answer

1. Does a staggered 0.2-0.3 s reaction read as human, or as sluggish or a bug (Halo)? (Change 3.)
2. Does a cruising AI look asleep next to him? Which cruise level? (Change 7.)
3. May the AI's top speed follow his **sprint** instead of his cruise? Today's rule is "never faster than 95% of your skate speed". (Change 7.)
4. Do head lines on match-stick figures help, or look odd? (Change 12.)
5. Which pass speed to him is easier with the tracked stick, 6.5 or 9 m/s? (Change 14.)
6. Can he read "he has me" and "I've beaten him" on line figures at 72 Hz? (Changes 10-11.)
7. How generous should teammates be with the puck? A share rule bends the values; it is a design choice. (Change 14.)
8. Do calls help, and do they need to come from the caller's direction? (Change 14.)
9. Can he name the playmaker after a game? (Change 16.)
10. Does honest contact feel fair, both his light pokes now counting and, later, stick battles with a finite-mass AI blade? (Changes 2 and 17.)
11. Does any AI motion bother him? Log it (change 1) and compare comfortable and uncomfortable sessions: closest approach, and the AI's angular speed across his view. The vection study behind the worry is about the player's own motion, not about bodies moving round him [M].
12. Does he want to play *with* Kucherovs, *against* them, or both? It decides how the two skill settings start.

### Open research questions

1. **Hockey numbers nobody publishes:** turn radius against speed, pivot and crossover timing, carriers' change of pace, scan rate, reaction times in games, defender gap against speed, support distances, regroup frequency, the value of a delay, stickhandling frequency and amplitude in games, NHL pass completion by type, and Kucherov's own touch length.
2. **Walking to skating:** whether the head lead, the speed-curvature law and minimum jerk carry over to skaters is unmeasured.
3. **The AI blade's controller:** whether a "volley and catch" design keeps the puck standing still and on tight curves, and what it does with Jon's stick, the boards or a body in the way.
4. **The goalie model's generosity:** xG 0.78 from 5.7 m in close may be high, which shifts every pass-or-shoot comparison.
5. **The royal road** in larger samples: the published numbers are proprietary or rest on about 41 shots.
6. **Sports-game AI postmortems with data** (EA NHL, FIFA, NBA 2K, Rocket League) were not found; only marketing pages. No controlled human-likeness study of sports-game AI exists.

### Housekeeping

An early draft of the presence note was published by mistake as a private claude.ai page (https://claude.ai/artifact/FZ4g2fgPzHWSQKCPuoUQ3e). It is out of date. Only Jon can approve deleting it; nobody has touched it.

---

## Sources

The four notes list every source with its URL and the fact-checkers' verdicts. These are the ones this report leans on.

**Tracking, pace and skating**
- NHL.com, NHL EDGE stats for Tampa Bay (Kucherov 2023-24): https://www.nhl.com/news/topic/32-in-32/nhl-edge-stats-for-tampa-bay-lightning-32-in-32
- NHL stats API, Kucherov: https://api-web.nhle.com/v1/player/8476453/landing
- NHL EDGE API, Kucherov 2025-26: https://api-web.nhle.com/v1/edge/skater-detail/8476453/20252026/2 ; https://api-web.nhle.com/v1/edge/skater-shot-speed-detail/8476453/20252026/2 ; https://api-web.nhle.com/v1/edge/skater-skating-speed-detail/8476453/20252026/2
- NHL.com (2026-03-20), Kucherov EDGE stats: https://www.nhl.com/news/nhl-edge-stats-nikita-kucherov-hart-trophy-contender-2026
- Gamble et al. 2022, university tracking: https://pmc.ncbi.nlm.nih.gov/articles/PMC8914021/
- Brocherie, Girard & Millet 2018, elite time-motion: https://pmc.ncbi.nlm.nih.gov/articles/PMC6224850
- Lafontaine, Lamontagne & Lockwood 1998: https://ojs.ub.uni-konstanz.de/cpa/article/view/1232
- Holman 2024, 180° turn times: https://mcgill.scholaris.ca/items/8a38a945-2621-412c-90bf-270d77bfc6e3
- Stastny et al. 2023, sprint meta-analysis: https://www.termedia.pl/Testing-distance-characteristics-and-reference-values-for-ice-hockey-straight-sprint-speed-and-acceleration-A-systematic-review-and-meta-analyses-,78,48807,1,1.html
- Riby, skating economy (stride rates, abstract): https://escholarship.mcgill.ca/downloads/47429c713
- Czuzoj-Shulman 2019, NHL shootout paths (poster): https://www.nessis.org/nessis19/Nick-Czuzoj-Shulman-poster.pdf
- Round 2's skating sources (Greer & Dillman, Buckeridge, Winchester, Marino & Grasse): `research_notes/Hockey physics feel/skating kinematics.md`

**Possession, passing and value**
- Iaboni et al. 2025, Individual puck possessions Part I (LINHAC): https://cs.uwaterloo.ca/~brecht/papers/linhac-2025-part-1.pdf
- Lodhi et al. 2025, Part II: https://cs.uwaterloo.ca/~brecht/papers/linhac-2025-part-2.pdf
- Radke et al. 2021, passing and pressure: https://cs.uwaterloo.ca/~brecht/papers/hockey-aisa-2021.pdf
- Radke, Brecht & Radke 2022, completed passes: https://cs.uwaterloo.ca/~brecht/papers/passing-linhac-2022.pdf
- Radke et al. 2023, passing metrics: https://ecp.ep.liu.se/index.php/linhac/article/download/739/644
- Murto 2023, Liiga possession value: https://ecp.ep.liu.se/index.php/linhac/article/download/737/642/754
- Yu, Boucher, Bornn & Javan 2019 (Sportlogiq entries, pass speed): https://arxiv.org/pdf/1902.02020
- Ritchie, Harell & Shreeves 2022, rink control: https://ar5iv.labs.arxiv.org/html/2205.13678
- Fernández & Bornn 2018, space generation: http://www.lukebornn.com/papers/fernandez_ssac_2018.pdf
- Goeree & Gratz 2025, Stathletes slides [V]: https://docs.google.com/presentation/d/1MXXVGP7CJ5BI1FRC7hxcZpyoZbn5IbRW/htmlpresent
- Stathletes Big Data Cup 2021 data: https://github.com/bigdatacup/Big-Data-Cup-2021
- Brecht group 2024, 3-on-3 possession (cites Luszczyszyn): https://cs.uwaterloo.ca/~brecht/papers/linhac-2024.pdf
- Valiquette, the Royal Road [V]: https://cdn1.sportngin.com/attachments/document/0137/7547/The_Royal_Road_-_Scoring.pdf ; Boyle via OMHA [V]: https://www.omha.net/news_article/show/486107
- Pallotta 2023, Kucherov passing (All Three Zones) [S/V]: https://lastwordonsports.com/hockey/2023/08/18/nikita-kucherov-passing-data/

**Puck skills and deception**
- Lawrie 2014, stickhandling kinematics: https://mcgill.scholaris.ca/items/eeeb2675-8b05-4122-a533-2f476979bd4a
- Roczniok et al. 2024, carry speed: https://pmc.ncbi.nlm.nih.gov/articles/PMC11307188/
- Panchuk & Vickers 2006, goalie gaze: https://europepmc.org/article/MED/17050024
- Polzien, Güldenpenning & Weigelt 2021, head-fake timing: https://pmc.ncbi.nlm.nih.gov/articles/PMC8115800/
- IIHF Coach Development Program, individual offensive tactics [V]: https://www.hockeyeasternontario.ca/media/n4pf15hp/iihf_coachdev_off_tactics.pdf
- Prewitt 2018, Kucherov film session, SI [V]: https://www.si.com/2018/09/13/nikita-kucherov-film-session-tampa-bay-lightning
- Justin G. 2023, shot or pass, Raw Charge [V]: https://www.rawcharge.com/nikita-kucherov-and-is-it-a-shot-or-a-pass-tampa-bay-lightning-power-play/
- Vinh Cao 2025, Kucherov spotlight [V]: https://virtualhockeyscout.substack.com/p/2024-25-season-spotlight-nikita-kucherov
- Leahy 2019, NBC Sports [V]: https://www.nbcsports.com/nhl/news/wednesday-night-hockey-nikita-kucherov-is-a-master-of-deception

**Defence and 3-on-3**
- HockeyShare, gap control [V]: https://www.hockeyshare.com/blog/gap-control-basics
- Passos et al. 2008, rugby 1-on-1s: https://doi.org/10.1080/02640410802208986
- Fraser 2018, NHL Coaches' Room [V]: https://www.nhl.com/news/nhl-coaches-room-overtime-success-303255732
- Corsi 2018 [V]: https://www.nhl.com/news/overtime-approach-no-longer-run-and-gun-295721154

**Perception, reaction and the head**
- Rabin, Agent Reaction Time [V/S]: http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter05_Agent_Reaction_Time_How_Fast_Should_An_AI_React.pdf
- Lipps, Galecki & Ashton-Miller 2011, sprint starts: https://pmc.ncbi.nlm.nih.gov/articles/PMC3198384
- Brault et al. 2012, VR rugby side-steps: https://pmc.ncbi.nlm.nih.gov/articles/PMC3372470/
- Resulaj et al. 2009, changes of mind: https://pmc.ncbi.nlm.nih.gov/articles/PMC2875179
- Grasso et al. 1996, head leads walking turns: https://pubmed.ncbi.nlm.nih.gov/8817526/
- Hicheur, Vieilledent & Berthoz 2005, head on a figure-eight: https://pubmed.ncbi.nlm.nih.gov/15936517/
- Authié et al. 2015, gaze and head anticipation: https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2015.00312/full
- Bespomoshchnov et al. 2026, scanning in junior elite hockey: https://doi.org/10.1080/02640414.2026.2744018
- Jordet et al. 2020, scanning in the Premier League: https://pmc.ncbi.nlm.nih.gov/articles/PMC7573254
- Rabin, The Illusion of Intelligence [V]: http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter01_The_Illusion_of_Intelligence.pdf

**Motion perception and animation**
- Troje & Westhoff 2006, the feet carry walking direction: https://pubmed.ncbi.nlm.nih.gov/16631591/
- Flash & Hogan 1985, minimum jerk: https://pubmed.ncbi.nlm.nih.gov/4020415/
- Viviani & Stucchi 1992, speed and curvature: https://pubmed.ncbi.nlm.nih.gov/1500865/
- Kilner, Hamilton & Blakemore 2007: https://pubmed.ncbi.nlm.nih.gov/18633814/
- Hodgins, O'Brien & Tumblin 1998, stick figures against solid models: https://www.sciweavers.org/publications/perception-human-motion-different-geometric-models
- Bodenheimer, Shleyfman & Hodgins 1999, motion variability: https://eecs.vuse.vanderbilt.edu/People/bobbyb/pubs/variability99.pdf
- McDonnell et al. 2008, Clone attack: https://doi.org/10.1145/1360612.1360625
- Reynolds 1999, steering behaviours [V]: https://www.red3d.com/cwr/steer/gdc99/
- Spring-It-On, critically damped springs [V]: https://theorangeduck.com/page/spring-roll-call

**Game AI, teammates and presence**
- Butcher & Griesemer 2002, Halo AI [V]: https://halo.bungie.org/misc/gdc.2002.haloai/talk.html?page=19 (also page 16)
- Orkin 2006, F.E.A.R. [V]: https://pages.cs.wisc.edu/~dyer/cs540/handouts/gdc2006_orkin_jeff_fear.pdf
- Dyckhoff, Ellie in The Last of Us [V]: http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter35_Ellie_Buddy_AI_in_The_Last_of_Us.pdf
- IAUS wiki, inertia bonus [V]: https://github.com/ProjectBorealis/IAUS/wiki
- Schrum, Karpov & Miikkulainen, BotPrize 2012: https://people.southwestern.edu/~schrum2/AAAI-BotPrizePoster.pdf
- Even, Bosser & Buche 2021: https://www.frontiersin.org/articles/10.3389/fcomp.2021.774763/full
- Świechowski & Ślęzak 2025, survey: https://arxiv.org/pdf/2505.20011
- McIlroy-Young et al. 2020, Maia: https://arxiv.org/abs/2006.01855v3
- Holmgård et al. 2015, personas: https://doi.org/10.1609/aiide.v11i5.12849
- Pure racing AI [V]: https://www.gamedeveloper.com/design/the-pure-advantage-advanced-racing-game-ai
- Kurach et al. 2020, Google Research Football: https://arxiv.org/pdf/1907.11180
- Liu et al. 2022, humanoid football: https://ar5iv.labs.arxiv.org/html/2105.12196
- Carroll et al. 2019, human-aware coordination: https://arxiv.org/abs/1910.05789
- Siu et al. 2021, Hanabi teammates: https://arxiv.org/abs/2107.07630
- Auvray & Rohde 2012, perceptual crossing: https://pmc.ncbi.nlm.nih.gov/articles/PMC3377933
- Garau et al. 2003, avatar gaze: https://doi.org/10.1145/642611.642703
- Llobera et al. 2010, approaching characters: https://doi.org/10.1145/1857893.1857896
- Teixeira, Miellet & Palmisano 2022, unexpected vection: https://www.frontiersin.org/journals/virtual-reality/articles/10.3389/frvir.2022.860919/full
- Blaser & Seiler 2019, talk in football pairs: https://www.frontiersin.org/articles/10.3389/fpsyg.2019.00077/full
- Yannakakis & Martínez 2015, ratings against ranks: https://www.um.edu.mt/library/oar/bitstream/123456789/22952/1/Ratings_are_Overrated.pdf
- Togelius et al., assessing believability: https://www.um.edu.mt/library/oar/bitstream/123456789/22848/1/Assessing_Believability.pdf
