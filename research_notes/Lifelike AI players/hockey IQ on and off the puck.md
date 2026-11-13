# Hockey IQ: decisions, support and defence that read like real players

Research round "Lifelike AI players", 2026-11-13.

Topic: how high-IQ players decide, where they go without the puck and how they defend, turned into rules the 3v3 AI in `threes.py` can compute at 50 Hz. The note pays special attention to 3-on-3 and to AI teammates who play with Jon. Skating, puck skills and VR presence have their own notes this round (see `elite skating and body motion.md`). This note touches them only where a decision depends on them.

It builds on two notes from the earlier round. `VR hockey sense training/simulation_and_scoring.md` has the rink-control model's agent parameters, pass value as P(success) × location value, and scanning. `defenseman_coaching.md` has gap rules, angling and the 2-on-1. This note does not repeat them. It adds NHL puck-and-player tracking results from 2021-2025, Liiga and Sportlogiq value tables, how teams play 3-on-3 overtime, and measurements of the current AI.

Tags: **[M]** measured in the cited study. **[D]** derived: arithmetic shown, or our own measurement of the sim or Jon's recordings. **[E]** estimate or design proposal, with assumptions stated. **[V]** vendor claim, coaching text, commentary or anecdote. **[S]** secondary: read in a source that cites the primary. 1 ft = 0.305 m.

## Bottom line

1. **The AI's biggest gap is passing judgement, not touch length.** Only 45% of AI passes reach a teammate. After 51% of them, the next player to control the puck is an opponent [D: 438 passes in 40 min of AI self-play at Jon's 3 m/s setting]. In Finnish league tracking, 79.9% of 535,449 passes succeeded [M]. 93% of AI passes are made with a defender within 1.6 m. At least 65% of them qualify only through the `_decide` branch that passes on a coin flip when pressed [D]. *Corrected in fact-check:* judgement is only part of it. In a re-run (4 × 300 s, 204 passes), 52 of the 111 passes that an opponent ended up with had first reached the intended receiver's stick and failed the reception roll in `_loose`: at 7 m/s or more relative to his stick (almost every 10 m/s pass) a receiver takes the puck only 45% of the time [D]. So about half the failed passes are reception failures, and the fix needs the reception rule as well as the choice.
2. **Carrying is too risky, and defenders are glued on.** AI carriers lose the puck about 0.35 times per second of carrying. Liiga carriers keep it through 95.4% of one-second carries, about 0.05 losses per second [D from M]. The nearest defender sits a median 1.2 m from the AI carrier, with his stick in poke range 58% of the time [D]. Pokes are dice rolls, so nothing the carrier or Jon does changes them. *Corrected in fact-check:* the odds do fall with the distance from the defender's blade to the puck (`(1 - d/POKE_R)` in `_possession`), so keeping the puck away from a stick helps a little; what the roll ignores is body position, speed, facing and any cue.
3. **Elite players touch the puck often and briefly, and their legs are ordinary.** NHL 5v5 possessions last 1.29 s on average, and 1.05 s in the offensive zone [M, 1,194 games]. Kucherov had 41.5 possessions per 20 minutes, against 31.3 for the average forward. He was not in the top 10 for possession length, where the cut-off was 1.67 s [M/D]. *Corrected in fact-check:* these possession numbers are 5v5 in 2023-24, not 2025-26. "Briefly" is not shown for elite players in general: the same paper's longest holders (Barzal 2.03 s, Quinn Hughes 2.00 s, Makar, Eichel, Draisaitl, Bedard, Jack Hughes) are elite too. Kucherov's own mean possession length is not published; he is only outside the top 10. In 2025-26 he scored 130 points with a top speed at only the 61st percentile and an even-strength distance per 60 at the 59th [M, NHL EDGE]. So "a team of Kucherovs" means better decisions, made earlier. It does not mean faster skaters.
4. **3-on-3 is about possession and mismatches, and the AI never regroups.** NHL coaches teach "possession at all costs", changing lines only with the puck, and pulling it back out to re-attack [V]. Rushes pay. A 2-on-1 controlled entry leads to a shot on goal 43.7% of the time, at 22.0% shooting. A 3-on-3 entry does so 20.8% of the time, at 5.2% [M, Sportlogiq, NHL 2017-18]. That is about 9 times the goals per entry [D]. In self-play, no AI touch ever included a full second of skating away from the net with the puck (0 of 761) [D].
5. **The models that make this computable are small.** They need three parts [M] (fact-check: these are not hockey measurements. The 0.19 s is borrowed from sprint-start reaction times and the extra 0.1 s is the authors' assumption, so read both as [E]. The 94% and the Liiga values are measured):
   - Pass success from time-to-intercept: reaction 0.19 s, and defenders react 0.1 s later still.
   - Receivers and defenders projected along their velocity. This cut the error in the receiver's location for over 94% of NHL passes.
   - A value for each spot. In the Liiga, passes into the slot carried 9.1% goal danger, lateral passes 3.6% and outlets 1.1%.

   On this PC, a 2 m rink-control grid costs 0.13 ms and 900 pass-path points cost 0.21 ms. Today's whole AI tick is 0.8 ms (median) [D].
6. **Defence should hold a gap and commit on cues.** Coaching gives a gap of 3, 2 and 1 stick lengths at the far blue line, the red line and the defender's own blue line. The defender matches the attacker's speed and stays on his inside shoulder [V]. In rugby 1-on-1s, once the gap is under 4 m, an attacker who keeps a relative speed of at least 1 m/s wins, and one who drops below it loses [M]. The AI should commit when the carrier slows, turns his back, is pinned on the boards or is receiving the puck, and otherwise contain. (Fact-check: "slows" and "receiving" have coaching sources; "turns his back" and "pinned" are this note's own proposals [E]. See section 4.) That also gives Jon readable "I have him" and "I'm beaten" moments.
7. **Teammates ignore Jon.** In his three logged games, AI teammates made 40 passes, and 7 of them went to him (17.5%, 0.47 a minute) [D]. With a scripted Jon at 3 m/s, the AI rated his lane open 36% of the time, against 55% for its AI teammates [D]. Teammates designed around a model of human play coordinate better with people than teammates trained by self-play, and people prefer rule-based, readable teammates [M, Carroll 2019; Siu 2021]. (Carroll's effect was clear against a simulated human and, in their words, "less strongly" in the study with real people.) Jon's head leads his path: in walking it leads by about 0.2-0.26 s [M], and in this rig his skating direction follows his head. So teammates can read where he is going.
8. **Elite-looking decisions need limited, human-like perception.** Elite soccer players scan about 0.44 times a second, and less under tight pressure [M]. Junior elite hockey forwards aim 47-53% of their first fixations at open space [M]. An AI that sees everything instantly never loses a man at the back door. A 0.2 s reaction buffer and a view cone with memory are cheap, and they create honest mistakes.

## 1. The current AI, measured [D]

**Method.** A scratch probe subclasses `threes.Game`. It plays the real 1 kHz physics exactly as `tests/test_threes.py` does and logs every AI tick. Each configuration ran four seeds of 600 s.
- **Main configuration:** AI only, with `you_ms` = 3.0 (Jon's skate setting). That makes `vmax` 2.85 m/s and carriers 2.42 m/s.
- **Second configuration:** the same, plus a scripted stand-in for Jon. It skates at 3 m/s with its blade 0.9 m in front, goes to a spot opposite the carrier, and carries a received pass for 1.5 s before shooting.
- **Jon's logged games:** three sessions on 2026-11-09, 14.8 min of play, at skate setting 4.0. (*Fact-check note:* 14.8 min runs from the first drop to the last event, so it includes goal pauses and faceoffs. The first session's `meta.json` predates the skate setting, so only the later two show 4.0.)

Scripts and outputs are in the round's scratchpad folder (`ai-round/hockey-iq`).

| Measure | AI only, 3 m/s | With Jon stand-in | Real reference |
|---|---|---|---|
| Puck on an AI stick, share of live time | 34% | 35% | — |
| Puck loose, or a pass on its way | 65% | 59% | — |
| Touches per minute, both teams | 19.0 | 15.4 | NHL forward: 31.3 possessions per 20 min of ice time [M] (another format) |
| Touch length, mean / median | 1.00 / 0.60 s | 1.31 / 0.71 s | NHL 5v5: mean 1.29 s [M] |
| ... by third (own / neutral / attacking), mean | 1.23 / 0.85 / 0.84 s | 1.93 / 1.09 / 0.71 s | 1.43 / 1.47 / 1.05 s [M] |
| How touches end: pass / shot / puck lost | 53 / 12 / 34% | 49 / 12 / 39% | — |
| Losses per second of carrying | 0.35 (0.344 / 0.996 s) | 0.30 | Liiga: about 0.05 (95.35% of 1 s carries kept) |
| Decisions (every ~0.25 s): carry / pass / shoot | 81 / 15 / 3.5% | 87 / 11 / 2.5% | — |
| Passes made with a defender within 1.6 m | 93% | 84% | — |
| Pass reaches a teammate / next control by an opponent | 45 / 51% | 54 / 44% | Liiga: 79.9% successful [M] |
| Pass length, median | 6.7 m | 7.2 m | — |
| Nearest defender to the carrier, median (p10-p90) | 1.18 m (0.90-4.27) | 1.45 m | No public hockey average. One Stathletes example frame: 18 ft (5.5 m) [V] |
| Defender's stick within poke reach (1.3 m) | 58% of carrier time | 51% | — |
| Two defenders within 2.5 m of the carrier | 6% of carrier time | 4.5% | — |
| Defender to his man (non-carriers), median | 4.6 m | 4.6 m | — |
| Mark changes per defender per minute | 3.9 (about half at possession changes; 1.9 in settled possession, fact-check) | — | — |
| A supporting teammate's lane open (`_lane` > 0.55) | 49% | AI 55%, Jon 36% | — |
| Carrier time with no open teammate | 29% | 25% | — |
| Best pass beats carrying, on the AI's own values | 21% of ticks | 31% | — |
| Touches with ≥1 s skating away from the net | 0 of 761 | 0 of 615 | 3v3 OT: routine [V] |
| AI skaters at ≥90% of their top speed | 63% of the time | 64% | see `elite skating and body motion.md` |
| Shots / goals per minute, both teams | 2.35 / 0.63 | 1.83 / 0.35 | NHL OT: 4.3 shots on goal per overtime; the goal comes after 2:12-2:31 on average [M] |
| AI tick cost, median / p99 | 0.80 / 1.49 ms | 0.74 / 1.42 ms | — |

What the numbers say:

- **The pass trigger.** I re-ran 4 × 300 s with the branch logged. Of 197 AI passes, 65% qualified only through the pressure branch: a defender within 1.6 m, a lane above 0.5, and a 50% coin flip. Another 27% qualified through both branches, and 7.6% through the value branch alone [D]. My value check left out the shot-xG term, so it lets through more passes than the game does, and 65% is a lower bound. The AI mostly passes because it is about to be poked, not because someone is open. (Fact-check: re-run, same counts: 128 / 54 / 15 of 197.)
- **Why passes fail (added in fact-check) [D].** About half of the passes an opponent ends up with are not cut out in the lane. The puck reaches the intended receiver's stick, and `_loose` gives him only a 45% roll whenever the relative speed is 7 m/s or more, which almost every 10 m/s pass is (the puck loses about 0.9 m/s over a median 6.7 m pass, per `pk.slide`, and the receiver skates at most 2.85 m/s, so the relative speed drops under 7 m/s only when he skates almost straight away from the passer). After a miss he cannot touch it for 0.3 s (52 of 111 such passes in a 4 × 300 s re-run). Better pass choice alone will not reach the Liiga's 80%.
- **Comparing touch lengths.** The NHL counts a possession from a first touch confirmed by a second touch, and counts one-touch passes and shots as brief possessions [M]. An AI touch runs from pickup to release. The two are close but not identical.
- **Support spots ignore the defence.** `_support` sends teammates to fixed points (back door, high, trail). For 29% of the carrier's time no teammate is open, and the carrier keeps skating into defenders.
- **Defenders.** The presser aims at the carrier's blade plus 0.6 m goal side at every speed and in every zone. His median distance is 0.9 m within 16 m of the net he defends and 1.7 m beyond 25 m. (The probe measures the nearest defender's body to the carrier's body, which is almost always the presser; skaters are pushed apart at 0.9 m, so 0.9 m is the floor.) Marks are re-paired greedily every 0.6 s, giving 3.9 changes per defender per minute. Some of those come at possession changes (10.7 turnovers a minute). *Corrected in fact-check:* about half do. Splitting the same 4 × 300 s runs, 2.0 per defender per minute come within 0.65 s of the attacking team changing (or a faceoff), and 1.9 come during a settled possession [D]. Compare any fix with the 1.9.
- **Jon's games.** His AI teammates made 40 passes: 18 to U1, 15 to U2 and 7 to Jon. The opponents made 90 [D]. With the stand-in, 16 passes went to "Jon" in 40 min. They passed a median 0.34 m from his blade at 9.0 m/s relative to it [D]. The game counts the puck as his only under 6 m/s relative (`_possession`), so he has to absorb most of that speed with his real stick. The stand-in's low openness partly reflects my simple script. *Fact-check note:* 15 of those 16 passes were next controlled by an opponent. That is an artifact: the stand-in's blade is only a point with no physical stick in the puck physics, so a 9 m/s pass can never drop under the 6 m/s rule and simply slides past. It says nothing about Jon's real reception rate. It also pulls the stand-in column's pass completion down by up to about 5 points (15 of 319 passes).
- **AI at full speed.** At the 5.8 m/s default (`you_ms` None), the same patterns hold. 49% of passes reach a teammate, 32% of touches end with the puck lost, and 91% of passes are made under pressure [D].

## 2. Models from tracking data that an AI can run

### 2.1 Who gets there first: rink control

- **Ritchie, Harell & Shreeves (2022)** adapted Spearman's pitch control to hockey. They used Olympic women's tracking from broadcast at 30 fps and 289 offensive-zone passes, all on power plays [M, method; parameters already in `simulation_and_scoring.md`]:
  - Each player's time to each point comes from a motion model: reaction 0.189 s, then a first-order velocity response.
  - Control weighs each player by τ^-2.5.
  - Pass success is the chance that the passer's team gets to the puck first along its path.
  - Defenders react 0.1 s later to a pass.

  What is new here is using the model to drive the AI rather than to score Jon.
- **Stathletes (Goeree & Gratz, 2025)** built "region control" from AHL broadcast tracking (about 280 games; the slides say 289 on slide 1 and 280 on slide 3, 2024-25 season). It adds reaction time, **turn time** and an "effective speed" [V, conference slides].
  - In their example, a skater recorded at 17 ft/s gets effective speeds of 25 ft/s (7.6 m/s) and 11 ft/s (3.4 m/s), labelled "moving faster" and "moving slower". I read this as depending on direction relative to his motion [E].
  - This matters for the sim. The current `_lane` and `_reach` let a skater go in any direction at full speed after a fixed 0.25 s or 0.15 s.
- **Fernández & Bornn (2018, FC Barcelona and SFU)** used Metrica Sports tracking of 20 matches in Spain's first and Segunda B divisions. Each player's influence is a 2-D Gaussian stretched along his velocity [M, method]. They separate two kinds of space:
  - **occupation:** space a player takes for himself;
  - **generation:** space he creates for teammates by drawing opponents at least 3 m out of place.

  Generation is the Kucherov-type decoy: hold the puck, draw two defenders, then pass.
- **Cost.** On this PC, a vectorised time-to-reach for 7 skaters costs 0.13 ms on a 13 × 23 grid (2 m cells, 299 points) and 0.40 ms at 1 m cells. At 10 Hz that is 1.3-4 ms per second of game [D].

### 2.2 Will this pass get there?

- **Radke et al. 2021** used NHL tracking of two 2020 Final games (players at 12 Hz, the puck at 60 Hz) [M, method]:
  - A pass's "availability" is the size of an asymmetric passing lane when the first opponent fits inside it.
  - The receiver's end of the lane grows three times faster than the passer's end, because an opponent near the receiver has more time to react.
  - A teammate's "openness" is that value, measured at every moment his mate has the puck.
- **Radke et al. 2022** studied 198 NHL games from November 2021 [M]:
  - 84.4% of completed passes were direct, 10.2% used one bank off the boards and 2.6% were rims.
  - They projected receivers and opponents along their velocity for the pass's flight time. That cut the error in where the receiver took the pass for over 94% of completed passes.
  - In 59% of completed bank passes, the bank lane was at least as open as the direct one.
- **Radke et al. 2023** covered 1,221 games in 2021-22 [M]:
  - The median forward completes about 12 passes per 20 minutes, and the median defenseman about 17.
  - Many of the highest-assist players complete passes through relatively small lanes (average availability 0.59-0.70).

  Elite playmakers thread tight lanes. They do not wait for wide ones. [E: our reading; the authors say only that this "may suggest" a link between assists and completing passes through smaller lanes.]
- **Pass speed (Yu, Boucher, Bornn & Javan 2019).** They used Sportlogiq data on all 0.50 million NHL 5v5 passes in 2017-18. Except for passes into the slot, failed receptions came at significantly higher pass speeds than successful ones [M]. Harder is not always better. This matters for passes to Jon (section 6).
- **Liiga base rates (Murto 2023).** Wisehockey tracked 872 matches at 20 Hz [M]:
  - 79.87% of 535,449 passes succeeded.
  - 95.35% of one-second carries kept the puck.
  - 5.29% of shots scored.
  - 39.67% of dump-ins and 69.88% of dump-outs succeeded.

### 2.3 What a spot, a pass or an entry is worth

- **Possession value (Murto 2023, Liiga) [M, method].**
  - Reward is the chance the team in possession scores in the next 8 s. Risk is the chance it concedes.
  - Each action is valued as success × reward − failure × risk.
  - In the 2022-23 playoffs (out of sample), successful passes carried this much danger: into the slot 9.1%, lateral (east-west) 3.6%, behind the net 3.3%, entry passes 2.3%, low-to-high 2.1%, high-to-low 1.4%, outlets 1.1% [M].
  - Entries had this much danger: 1-on-0 12.7%, 2-on-1 7.4%, 1-on-1 5.4%, 3-on-2 4.6%, 2-on-2 4.3%, 3-on-3 3.3%, 2-on-3 3.1% [M]. The counts are small (18 to 473 entries per type).
- **Entries in the NHL (Yu et al. 2019, 5v5, 2017-18).** The first two columns are [M]. The last is [D]: shot rate × shooting %, assuming one shot per entry.

| Entry | Shot on goal after entry | Shooting % (within 5 s) | ≈ goals per entry |
|---|---|---|---|
| 1-on-0 | 66.6% | 26.2% | 0.17 |
| 3-on-1 | 48.8% | 25.5% | 0.12 |
| 2-on-1 | 43.7% | 22.0% | 0.096 |
| 3-on-2 | 31.5% | 10.4% | 0.033 |
| 1-on-1 | 29.9% | 8.8% | 0.026 |
| 2-on-2 | 26.2% | 7.1% | 0.019 |
| 3-on-3 | 20.8% | 5.2% | 0.011 |
| 2-on-3 | 21.6% | 4.6% | 0.010 |
| dump-in | 1.1% | 6.2% | 0.0007 |

- **Pace before the shot.** Yu et al. split shots into quintiles by the puck's average speed over the 5 s before them, from 10 to 42 ft/s. True shooting rose from 2.9% to 4.1% (+38%), at the same distance of 37-40 ft [M]. A hand-tracked model of 72,000 shots showed that passes before the shot improve xG a little: AUC 0.797, against 0.774 from play-by-play alone. The royal-road pass was the first pass variable the model used [M, Novet 2019].
- **Kucherov's passes.** In hand-tracked 5v5 data, teammates shot 21.2% and then 27.6% on his cross-slot passes (2022 and 2023 seasons), and 10.9-16.2% on his centre-lane passes. He was at the 100th percentile for shot assists in 2023 [S: Corey Sznajder's All Three Zones data, read in Pallotta 2023]. In the same article, about 10% of all shots on goal scored [S].
- **Our goalie model already rewards a quick cross-slot shot.** Take a shooter 5.7 m out and 2 m off centre:
  - Against a set goalie, xG is 0.79.
  - 0.0 s after a 4 m lateral pass, xG is 0.95. After 0.3 s it is 0.88.
  - By 0.5 s the goalie has recovered, and xG is back to 0.79 [D, `goalie.shot_xg` with `goalie.after_tracking`].

  *Corrected in fact-check:* re-running this (shooter 2 m off centre and 5.7 m out from the goal line, 22 m/s, goalie set or tracking from a puck 4 m across) gives 0.78 for the set goalie, then 0.95, 0.88 and 0.78. The point stands.

  The AI never looks for this. `_threat` ignores where the goalie will be, and a receiver waits 0.15-0.35 s before his first decision. The model's xG in close is generous (a rec goalie), so only the differences matter here.
- **Expected threat (xT) for hockey** exists only in student papers on event data: Sportlogiq data on a 16 × 9 grid, and SHL entries from 156 games [M, thin]. It is not worth copying. The sim can build its own spot values from `goalie.shot_xg` and self-play.
- **Learned values.** A Q-function learned with an LSTM from about 3 million NHL events exists (Liu & Schulte 2018) [M]. It needs event data the sim does not have, and inference per tick would cost far more than rules. I don't recommend it now [E].

### 2.4 Getting open ("soft ice")

- No source I found defines "soft ice" with numbers. Coaching separates "open" (no defender near) from "available" (a lane to the passer also exists) [V, Dudar 2023]. Radke's openness is the measured version of "available".
- 16 junior elite players (USA Hockey NTDP) wore mobile eye trackers in scrimmages. After a look away from the puck, forwards aimed 47-53% of their first fixations at open space [M, Bespomoshchnov 2026]. They look for space first, then for people.
- **A support spot for the AI is good when all four hold [E]:**
  - (a) his team controls it (rink control well above 0.5);
  - (b) the pass from the carrier to it is likely to complete;
  - (c) it is worth something;
  - (d) he can get there before it closes.

  "Soft ice" is then the point between two defenders where both have their longest time to reach it. It is usually behind the defender who is watching the puck.

### 2.5 The value of delaying

- The evidence is thin. I found no study that measures "delay" plays or regroups as a category.
- **The indirect evidence:**
  - Rushes with extra attackers are worth far more than even entries (the tables above).
  - Teams that keep the puck win 3-on-3 overtime (section 3).
  - Coaches tell players to pull up and wait for support or a line change [V].
- **Rule for the AI [E]:** delay when all three hold:
  - (i) no option beats carrying by a margin;
  - (ii) a teammate is arriving (his time to a support spot is under about 1 s);
  - (iii) no defender has committed to the carrier.

  Kucherov's numbers (many short touches) say delays should be short and have a purpose: protect the puck, let the play develop for 0.5-1.5 s, then move it. (*Fact-check note:* "many" is measured; "short" is only that he is outside the top 10 for possession length, so treat the 0.5-1.5 s as a design guess [E].)

## 3. Offence off the puck, and 3-on-3

### What NHL teams do in 3-on-3 overtime

- **Pace.** The average time to the overtime goal was 2:16 (2017-18 to February), 2:12 (2016-17) and 2:31 (2015-16). Overtime decided 61-66% of games that went past regulation, and teams averaged 4.3 shots on goal per overtime in 2017-18 [M, NHL.com 2018].
- **Possession wins.** In 243 overtimes from 2015 to 2021, with possessions tracked by hand, the winners had 53% of individual possessions, 54% of possession time and 57% of offensive-zone time [S: Luszczyszyn 2021 in The Athletic, read in the Waterloo team-possession paper].
- **Faceoffs barely matter.** Over 4,861 overtime faceoffs from 2015-16 to 2022-23, teams that won the opening draw went 698-670 (51%). The R² against winning was 0.0004 [M, blog analysis of Evolving-Hockey data]. The author's reading is that teams now avoid turnovers and wait for chances, and that the real danger is the odd-man rush after a failed attack [V].
- **Coaching [V].**
  - Curt Fraser (NHL.com 2018):
    - "Overtime is all about puck possession and maintaining it at all costs."
    - "You only change with possession."
    - Be patient enough to retreat and change personnel, even with 30-40 s left, and wait for one good chance. *Corrected in fact-check:* Fraser says good teams retreat and change "even if 30-40 seconds tick off the clock", that is, they will spend 30-40 s on it. It is not about how much time is left.
    - Think of the ice "as one big zone".
    - Beat man-on-man coverage with quick pivots, direction changes, tight turns, close outlets and switches.
    - Draw defenders out to create separation, and move the puck through the middle rather than along the wall.
  - Jim Corsi (NHL.com 2018): "drive wide, drive inside and if nothing is there, pull it back out and try again."
  - Andrew Trimble (2023): make every possession "a coordinated scoring possession", and avoid low-angle shots that rim out into the other team's rush.
- **For the AI [E].** The 3v3 needs three attacking states that the code lacks:
  - **attack:** a mismatch exists (2-on-1, a beaten defender, an open man in the slot);
  - **probe:** keep the puck moving and look for one;
  - **regroup:** take it back above the top defender, or to the neutral zone, when outnumbered or when nothing is on.

  The defending team must also respect the counter-attack, which means one man stays high.

### Support: angles, distances, timing

- **Distances.** I found no measured support distances for hockey. Coaching asks for "close outlets" and support that works switches (Fraser 2018), and teammates who give the carrier options to keep the puck moving (Dudar 2023) [V]. Neither gives a distance.
- **From the sim's own lane model [D].** Take a pass at 10 m/s against a defender reacting 0.25 s late at 2.85 m/s with 1.0 m of stick reach. A defender 2 m off the passing line can reach any point the puck passes after 0.6 s, which is beyond 6 m along the pass. A defender 3 m off can do so after 0.95 s, beyond 9.5 m.
  - So, in this sim, support at 5-9 m from the carrier is safe unless a defender is within 2-3 m of the line [E]. Real players skate faster than the AI's 2.85 m/s, so real safe lengths are shorter.
- **Timing [E].** A supporter who parks in a spot is easy to cover. He should arrive as the pass is made, and the pass should go to where he will be (Radke's projected location, above).
- **Give-and-go [E].** After an AI passes, he should skate into the space behind his own defender for about 1 s, ready for the return. Today the passer simply goes to a fixed support spot.

### Kucherov as the template

- **What he is [M].** Ordinary skating speed (NHL EDGE). Many touches, at 41.5 per 20 min, held briefly. Passes across the slot and through the centre lane [S]. In 2025-26 he led the league with 1.21 assists per game, and his offensive-zone time was 45.7% (91st percentile) [M, NHL.com EDGE article, March 2026].
  - *Corrected in fact-check:* the 41.5 touches are from 2023-24 5v5 (Iaboni 2025). "Held briefly" is [unverified]: his mean possession length is not published, only that he is outside the top 10 (so under about 1.67 s, against a 1.27 s forward average). The 1.21 assists per game was a mid-season figure (20 March 2026, 114 points in 63 games). His final 2025-26 line in the NHL API is 44 goals, 86 assists and 130 points in 76 games, which is 1.13 assists per game; I did not check whether that still led the league. The 45.7% offensive-zone time (92nd percentile) matches the final EDGE data.
- **What the AI should copy [E]:**
  1. Take the puck often: support close, give it back, get it again.
  2. Hold it briefly, mainly to draw a defender.
  3. Pass into or across the slot through lanes that rec players would call closed.
  4. Shoot from the high slot when the goalie is moving.
  5. Never skate it into two defenders.

## 4. Defence

### Gap and pressure

- **Coaching [V].** Keep 3 stick lengths at the defender's offensive blue line, 2 at the red line, and 1 stick length or contact at his own blue line. Match the forward's speed through the rush (HockeyShare 2010). Keep your outside shoulder on his inside shoulder (Bertagna, in the earlier round's report).
  - **On this rink [D].** Jon's stick was 1.42 m long in his logged games, so the gaps are about 4.3, 2.8 and 1.4 m. On the 46 m rink, the blue lines sit 17.25 m from each end (`BLUE_FRAC`).
- **Pressure zone [M, method].** NHL tracking work defines pressure on a carrier as reaching 5 ft (1.5 m) behind him and 15 ft (4.6 m) in front, toward the net he attacks. It rises linearly as the defender gets closer (Radke 2021, adapted from soccer).
- **Gap and shape [V, AHL tracking model, conference slides].** A tight gap cuts the number of shots more than their quality. Controlling the space cuts quality but not number. Compact units with stretched-out patrolling go with quality chances against. Put simply: the gap stops shots, and the shape stops good shots. *Corrected in fact-check:* slide 22 lists two separate findings: condensed units (a small hull area) and high "stretch" scores (defending in lanes or ellipses) are each strong indicators of quality chances against. Slide 23 says region control, not gap, is what suppresses quality.
- **Distance and relative speed (Passos et al. 2008, youth rugby 1-on-1s) [M].**
  - Below 4 m apart, an attacker who kept or increased a relative speed above 1 m/s was predicted to win.
  - A sudden drop below 1 m/s, at the same distance, predicted a defender win.
  - **Transfer to hockey is unmeasured [E].** Sticks add about 1-1.5 m of reach, and skating is faster. Use the shape of the rule, not its numbers.
- **The current AI [D].** The presser is always on the carrier, at a median 1.2 m. That is tighter than any gap rule, at every speed and in every zone.

### When to step up, and when to hold

- **Step-up cues** come from the coaching in the earlier round [V]:
  - the carrier turns his back to the play;
  - he slows down or stops;
  - he is on the boards with no outlet;
  - he is receiving, with his eyes and stick on the puck. The earlier report describes Makar striking at the moment the attacker looks down at the puck (Revak).

  *Corrected in fact-check:* only some of these cues are in the earlier round. `defenseman_coaching.md` (not the report) has the Makar cue (Revak), "step up on delays" (Hockey Canada) and "attach to pass-receiving threats" (Revak). "Turns his back" and "on the boards with no outlet" as step-up cues are this note's own additions [E]; the earlier round mentions a pinned attacker only as the moment to switch to two hands.
- **Hold when outnumbered.** On a 2-on-1, the stick owns the pass lane and the defender does not commit early (HockeyShare, in the earlier report) [V].
- **In 3-on-3 [V/E],** an over-committed defender gives up the odd-man rush, which is worth about 9 times an even entry (section 2.3).

### Man or zone in 3-on-3, and switches

- **Coaching [V].** 3-on-3 is played man-on-man. Know who you have, stay on the defensive side, and decide who each incoming skater replaces (Trimble 2023). Attackers beat man coverage with switches (Fraser 2018).
- **The current AI [D]** re-pairs marks greedily every 0.6 s: 3.9 changes per defender per minute. That reads as zone defence done badly, and nobody is ever "beaten". (*Fact-check:* 1.9 of the 3.9 happen during a settled possession; the rest follow a change of possession, where picking up the nearest man is normal.)
- **Rule for the AI [E].** Hold marks. Switch only when two attackers cross and the swap saves both defenders more than about 2 m of skating. The defender whose man is far from the puck (more than about 10 m) sags toward the slot to help.

### Backchecking

- I found no measured hockey data. One remark from the Liiga paper: it is fairly common for entry types "to change a couple seconds after the entry is performed in the favor of the defending team as their forwards hustle to join the backcheck" [V: the authors' informal observation from watching entries, not a measurement; tag corrected in fact-check].
- **Rule for the AI [E].** A beaten defender, no longer goal side, skates to the inside lane between the carrier and the net front. He does not chase the puck. His stick goes into the lane to the weak side.

### "I'm beaten" and "I have him"

- **The carrier's read [E, built from M rugby and V coaching].**
  - He is contained when the defender matches his speed within about 4 m, stays inside, and has his stick in the lane.
  - He has the defender beaten when the defender is flat-footed (relative speed above about 1 m/s), has committed to a poke, or is outside his inside shoulder.
  - The defender's read is the mirror image.
- **Use it in the AI [E].** For each defender-carrier pair, compute the gap, the closing speed, the inside/outside offset and whether the defender has committed. Label the pair contained, even or beaten. Then use the label three ways:
  - (a) Carriers attack beaten defenders and protect the puck against contained ones.
  - (b) A beaten defender recovers inside.
  - (c) The figures show it: a containing defender skates matched or backward, and a beaten one turns and chases (skating note).

## 5. Decision timing and anticipation

- **Possession length [M].** NHL players hold the puck for 1.29 s on average, and 1.05 s in the offensive zone. The longest average holders run 1.67-2.03 s (Barzal 2.03 s, Quinn Hughes 2.00 s). Those are carriers, not quick passers. Players have the puck for 3.3-4.2% of their ice time.
- **Scanning [M].**
  - Elite soccer (9,574 possessions): 0.44 scans per second. Scanning is lowest with an opponent 0-1 m away and levels off by 4 m. Completed passes followed 0.46 scans per second, and incomplete ones 0.40.
  - Swedish pro hockey (2,545 actions): scanning before a reception went with a higher chance of a successful next action (β = 0.12).
  - Junior elite hockey: 58.1% of scans held a single fixation, fixations lasted 134.5 ms, and scans just before a reception were shorter and simpler.
- **Recognition [M].** 23 expert and 14 non-expert players were filmed in games (118 decisions). Experts called situations familiar more often (p = .021), and coaches rated decisions in familiar situations as better (p = .01) (Mulligan & Hodges 2010). High-IQ decisions are pattern-based "if this, then that", not a search of every option. [E: our reading of a small study; it did not test search against recognition.]
- **Reaction.** The rink-control model uses 0.189 s, and defenders react 0.1 s later still to a pass [M, model parameters]. *Corrected in fact-check:* neither is a hockey measurement. Ritchie took 0.189 s from sprint-start reaction times (Lipps et al. 2011), and the extra 0.1 s for defenders is their stated assumption ("we assume"). Treat both as [E].
- **The current AI [D].** Its first decision comes 0.15-0.35 s after a pickup (median 0.265 s), then one every 0.2-0.33 s. It never decides before the puck arrives. It knows everything, everywhere, with no delay.
- **For the AI [E]:**
  1. **Pre-decide while the pass travels.** The receiver picks his next action from the state projected to the moment of reception. On arrival, he acts within 0.1-0.2 s if the plan still holds (one-timer, one-touch return). Otherwise he protects the puck and decides again.
  2. **Delayed perception.** Decisions read the world as it was 0.2 s ago (a ring buffer of 10 AI ticks).
  3. **A view cone with memory.**
     - Each AI sees players within about ±100° of where he faces, live. Others he remembers at their last-seen position, moved on by their velocity.
     - A scan (a visible head turn) refreshes his picture every 1.5-3 s, less often under pressure.
     - A defender near the puck watches the puck (puck-watching is a named common defensive error [V, Revak, in `defenseman_coaching.md`]).

     This is what lets back-door plays work honestly.
- **Level knobs [E].** These replace speed as the main difficulty dial:
  - elite (the Kucherov setting): early pre-decision, frequent scans, accurate pass odds that thread tight lanes, reaction 0.15 s;
  - rec: late decisions, few scans, noisy pass odds, reaction 0.25 s.

## 6. Playing with Jon

### Reading Jon

- **Head.** 10 people walked figure-eight and limaçon paths. Their head yaw led the path by about 200 ms pooled (264 ms in the light), and by 15° in the light [M, Authié et al. 2015].
  - **In this rig [D, code]:** the left stick pushes relative to where Jon looks (`rig.Drive._want` uses the head's forward vector). His head is his steering wheel.
  - So teammates can project his path from his head yaw plus his velocity [E].
- **Stick.** `Game` already receives his blade position every tick [D, code]. A blade on the ice, still and facing the passer, means "ready" [E]. A stick tap on the ice away from the puck could mean "give it to me". That would need a hook into the physics contacts [E].
- **Side.** Jon shoots left (`meta.json`). A pass to his forehand side should be easier to take [E].

### Passes he can take

- **Now [D, code].** A pass to Jon goes at 0.9 × 10 = 9 m/s, aimed at his blade, leading him by his velocity × flight time, capped at 2.5 m. With the stand-in, passes arrived a median 0.34 m from the blade at 9.0 m/s relative to it.
- **Evidence.** In the NHL, failed receptions come at higher pass speeds than successful ones [M]. Ritchie's model uses 13.7 m/s as an elite player's soft pass [M, parameter]. (Fact-check: 45 ft/s, the "soft" one of three speeds picked from attempted passes in women's Olympic power plays.)
- **For Jon [E].** A rec player with a tracked stick and no felt resistance should find softer passes easier, but too soft gets picked off.
  - **Speed:** A/B 6.5 against 9 m/s, and log speed, closest approach and outcome.
  - **Aim:** at his blade's projected position, using velocity plus head turn.
  - **When:** only while he faces within about 60° of the passer, because he has to see it coming, and while he is gliding or pushing straight rather than mid-turn.

### Get open for him, and give it back

- **Where to be [E].** When Jon has the puck, AI teammates choose support spots inside his view (his head direction ± about 45°), on his forehand side, 5-9 m away.
- **Call-outs [E].** When open behind him, they call for it ("Point!", "Back door!") through the voice now on the headset.
- **Give-and-go [E].** Jon passes to an AI and skates toward the net (head and velocity). The AI returns the puck within about 0.5-1.0 s if the lane is open, having decided during the pass's flight.

### Cover for him

- **Rule [E].** When possession flips and Jon is deeper than the opponents' deepest skater (caught up ice), the nearest AI takes the high, defensive role. He picks up Jon's man until Jon is back goal side.
- **Today [D, code].** `_chase` sends one AI between the puck and his net and the other up ice, wherever Jon is.

### A fair share of the puck

- **The problem [D].** AI teammates passed to Jon 17.5% of the time. The ×1.3 bonus in `_decide` doesn't help, because his lane rarely scores as open (36% against 55% for AI teammates, with the stand-in).
- **Fixes [E].** Score his openness with the human-aware read above. Add a share rule: if Jon has not touched the puck in about 20 s and is open, prefer him.
- **Evidence [M].**
  - Agents trained by self-play coordinate worse with people than agents built around a model of human play (Carroll et al. 2019, Overcooked). The gap was large with a simulated human partner and smaller ("less strongly") with real people.
  - People clearly preferred a rule-based Hanabi teammate to a learned one, with no difference in score (Siu et al. 2021).

  Keep teammate rules explicit and predictable. Jon should be able to learn "if I go to the back door, U1 finds me".

### Opponents who treat him fairly

- **Same rules as for AI carriers [E].** Use the gap and the cues, not dice. Today the defender on Jon pokes at random within 1.3 m (`POKE_YOU` 0.8 per second × level, scaled by distance) [D, code].
- **Telegraph [E].** A step-up and a visible reach of 0.2-0.3 s come before every poke, so Jon can protect the puck or move it. How it looks belongs to the skating and puck-skills notes.
- **No gang-ups [E].** One presser plus one in the lane, unless Jon is in the slot. Today two defenders are within 2.5 m only about 5% of the time [D]. Keep it so.
- **Comfort [E].** Decisions can add discomfort: a defender stepping up at high closing speed toward Jon's face, or several skaters crossing close in his peripheral view. Holding a gap instead of gluing on reduces fast motion close to his head. Body contact stays as now, only when he skates into an AI. The VR presence note owns the details.

## What this means for the sim

The changes are ordered so each can be tried alone, with a self-play metric and a headset A/B question. Costs are per second of game.

1. **Pass odds from time-to-intercept** (`_lane` → a vectorised `_pass_odds`).
   - **What.** For each receiver, take receive points at his projected blade position (velocity × flight time) plus two leads. Try speeds of 7, 10 and 13 m/s, and sample the puck path every 0.1 s (`pk.slide` for friction).
   - **Each opponent's time to each point** = 0.2 s reaction (+0.1 s on a pass) + the time to get there from his current velocity under the skating limits (turning costs time) − 1.0 m of stick reach.
   - **P** = the product over opponents of a logistic of the time margin. Keep the current 0.12 s scale.
   - **Cost.** About 0.2 ms per decision. At 4 decisions a second per carrier, under 1 ms/s [D, bench].
   - **Test.** Pass completion rises from 45% toward 75-80%, and turnovers fall from 10.7 a minute. (*Fact-check note:* this target also needs the reception rule in `_loose` changed or modelled. Today about half of the failed passes are a missed 45% reception roll at the receiver's stick, which no pass-odds model sees.)
   - **A/B question.** "Do their passes look meant?"
2. **Choose by value, with risk** (`_decide`).
   - **What.** Remove the pressure coin flip.
     - A pass is worth P × V(reception) − (1 − P) × V_opp(turnover spot).
     - Near the net, V(reception) is the shot xG with the goalie where he will be (`gl.shot_xg` with `gl.after_tracking`). Elsewhere it is a small continuation value.
     - Compare that with carrying (own value 0.5 s ahead) and with shooting.
   - **Protect.** Add a "protect" action (curl away, body between the puck and the presser) for when a defender commits and nothing beats carrying.
   - **Cost.** `shot_xg` costs 0.15 ms. 2 receivers × 3 points ≈ 1 ms per decision, about 4 ms/s per carrier. Cache the xG per goalie position to cut that.
   - **Test.** Losses per second of carrying fall from 0.35 toward 0.05-0.1, and the share of cross-slot passes rises.
3. **Defence: gap, cues, stable marks** (`_defend`, and the pokes in `_possession`).
   - **Presser's target:** on the line from the carrier to the net. The gap shrinks from 3 to 1 stick lengths (4.3 → 1.4 m) between the far blue line and his own. He matches the carrier's speed and sits 0.3 m inside.
   - **Step-up triggers:** the carrier slows by more than 1 m/s within 0.3 s, faces away from the net, is within 1.5 m of the boards, or has a pass arriving within 0.3 s.
   - **The poke:** a visible 0.2-0.3 s reach, then success from blade-to-puck geometry plus noise.
   - **Marks:** hold them, and switch only on a crossing that saves both defenders more than 2 m.
   - **Cost:** negligible.
   - **Test.** The presser's median gap grows from 1.2 m to 2-4 m away from the net, and about 1.4 m at his blue line. Mark changes fall from 3.9 to under 1 per defender per minute (fact-check: measure settled possessions separately, where today's rate is 1.9). A looser gap may allow more shots (the AHL slides tie gap to shot volume), so also watch xG per shot and losses per carry-second.
   - **A/B question.** "Can you see when he's coming?"
4. **Support spots by openness and value** (`_support`).
   - **What.** Every 0.1-0.2 s, each supporter scores 8-12 candidate points: a ring 5-9 m from the carrier, the back door, the high slot, and the gap between two defenders.
     - Score = P(pass completes) × V(spot) × "he gets there before it closes".
     - Hysteresis: move only to a spot at least 20% better.
   - **In 3v3,** one supporter always stays above the puck.
   - **After a pass,** the passer skates into the space behind his defender for about 1 s.
   - **Cost.** About 0.2 ms × 2 supporters × 10 Hz ≈ 4 ms/s.
   - **Test.** Carrier time with no open teammate falls from 29% to under 10%, touches per minute rise, and 2-on-1s appear.
5. **A regroup state for 3v3** (`_carry_to`).
   - **What.** In the offensive zone, when outnumbered near the puck and no option beats carrying, curl to the half wall or the blue line. If nothing opens within about 2 s, take it back over the blue line and re-attack.
   - **Test.** Regroups per game rise from zero. There is no measured target; coaches describe them as routine [V]. Also log shots and goals by entry type.
6. **Perception and timing** (a new per-player seen-state; `_decide`, `_targets`).
   - **What.** Decisions read a world 0.2 s old. Each AI has a view cone of ±100° with memory, and scans every 1.5-3 s, less under pressure. Receivers pre-decide during the pass.
   - **Cost.** Negligible.
   - **Test.** Back-door goals happen, one-timers come within 0.3 s of reception, and offensive-zone touches average about 1 s.
7. **Playing with Jon** (`_you_update`, `_decide`, `_pass`, `_chase`).
   - **What.**
     - Project his path from head yaw plus velocity.
     - Pass to his projected blade, only while he faces the passer.
     - A/B 6.5 against 9 m/s passes.
     - Return give-and-goes, and get open in his view on his forehand side.
     - Call out when open behind him, cover when he is caught up ice, and apply the share rule.
   - **Test.** Passes to Jon per minute (0.47 now) and his reception rate. Log speed, closest approach and outcome. Ask Jon to rate it.
8. **Opponents on Jon** (the `POKE_YOU` branch).
   - **What.** The same cue-triggered, telegraphed pokes, and no extra pressure.
   - **Test.** Jon's touch length and his "was that fair?" rating.

**Level knobs.** Level should set reaction time (0.25 → 0.15 s), scan interval (3 → 1.5 s), noise in the pass odds, the minimum P needed to pass (0.8 → 0.6, so elite players thread tighter lanes), and pre-decision on or off. Today level sets only speed, pokes and aim. "A team of Kucherovs" is the top setting on every knob, without more speed.

**Total cost [D/E].** Today's AI tick takes 0.8 ms (median), about 4% of a core at 50 Hz. Items 1-6 add roughly 5-10 ms per second of game (0.5-1% of a core) if the heavy parts run at 4-10 Hz and are spread over ticks. Keep everything vectorised in numpy: the current `_lane`, with its Python loops, costs 51 µs per lane on this PC [D]. (*Fact-check note:* the benchmark times a copy of `_lane`, not the method itself; a re-run gave 41 µs, and the grid and path-point costs re-ran at 0.125, 0.39 and 0.19 ms.)

## Open questions

- **Numbers nobody publishes** for hockey: defender gap against speed, support distances, how often teams regroup in 3-on-3 overtime, the value of a delay, and choice reaction times in hockey decisions. The Athletic's 3-on-3 study is paywalled, and I read only its summary in the Waterloo paper.
- **Pass speed for Jon.** Whether 6.5 or 9 m/s passes are easier with the tracked stick is a headset question. Logging is needed first.
- **Showing "beaten".** How the figures should show "contained" against "beaten" (skating note), and whether Jon can read it on line figures at 72 Hz.
- **How generous teammates should be.** A share rule bends the values. It is a design choice, not a research answer.
- **The goalie model's xG.** It gives 0.79 (0.78 on re-check) from 5.7 m in close, which may be too generous. That shifts every comparison of passing against shooting (see the Shot release round).
- **Stathletes' slide numbers** (an 18 ft gap, closing at 2.1 ft/s) are examples from one frame, not league averages. Their conclusions about gap and shape come from slides, not a paper.
- **The rugby thresholds** (4 m, 1 m/s) are from youth rugby, on foot. Hockey thresholds are unmeasured.

## Sources

Tracking and value models
- Iaboni, Negulescu, Pitassi, Lodhi & Brecht (2025), "Individual Puck Possessions Part I: Frequency, Duration, and Distance Travelled", LINHAC 2025: NHL 2023-24 tracking, 1,194 games, Tables 1-6. https://ecp.ep.liu.se/index.php/linhac/article/download/1208/1071/1300
- Lodhi et al. (2025), "Individual Puck Possessions Part II: Speed Bursts and Possession Times within Teams", LINHAC 2025, Table 1. https://ecp.ep.liu.se/index.php/linhac/article/download/1210/1073/1304
- Radke, Radke, Brecht & Pawelczyk (2021), "Passing and Pressure Metrics in Ice Hockey", AISA workshop at IJCAI 2021, sections 5.1 and 5.3. https://cs.uwaterloo.ca/~brecht/papers/hockey-aisa-2021.pdf
- Radke, Brecht & Radke (2022), "Identifying completed pass types and improving passing lane models", LINHAC 2022, Table 1 and section 6. https://cs.uwaterloo.ca/~brecht/papers/passing-linhac-2022.pdf
- Radke et al. (2023), "Analyzing Passing Metrics in Ice Hockey using Puck and Player Tracking Data", LINHAC 2023. https://ecp.ep.liu.se/index.php/linhac/article/download/739/644
- Murto (2023), "Towards a real-time possession value framework in ice hockey", LINHAC 2023, Tables 1, 3 and 4. https://ecp.ep.liu.se/index.php/linhac/article/download/737/642/754
- Yu, Boucher, Bornn & Javan (2019), "Playing Fast Not Loose" (Sportlogiq), Table 1, section 4.2 and section 4.3. https://arxiv.org/pdf/1902.02020
- Ritchie, Harell & Shreeves (2022), pass evaluation in women's Olympic hockey (arXiv 2205.13678), section III. https://ar5iv.labs.arxiv.org/html/2205.13678
- Fernández & Bornn (2018), "Wide Open Spaces", MIT Sloan. http://www.lukebornn.com/papers/fernandez_ssac_2018.pdf
- Goeree & Gratz (Stathletes, 2025), "The Impact of Skating Speed and Style with Tracking Data", NESSIS slides 13-24 [V]. https://docs.google.com/presentation/d/1MXXVGP7CJ5BI1FRC7hxcZpyoZbn5IbRW/htmlpresent
- Novet (2019), "Expected Goals Model with Pre-Shot Movement, Part 1", Hockey Graphs. https://hockey-graphs.com/2019/08/12/expected-goals-model-with-pre-shot-movement-part-1-the-model/
- Keller (2023), student paper on hockey xT (Basel), LINHAC 2023. https://www.ida.liu.se/research/sportsanalytics/LINHAC/LINHAC23/papers/paper-students-Basel.pdf ; LINHAC 2024 student paper on entry xT (SHL). https://www.ida.liu.se/research/sportsanalytics/LINHAC/LINHAC24/papers/linhac24student-paper3.pdf
- Liu & Schulte (2018), "Deep Reinforcement Learning in Ice Hockey for Context-Aware Player Evaluation", IJCAI. https://arxiv.org/abs/1805.11088
- Brecht group (2024), "Puck Possessions and Team Success in the NHL", LINHAC 2024 (cites Luszczyszyn 2021 on 3-on-3 overtime). https://cs.uwaterloo.ca/~brecht/papers/linhac-2024.pdf

Kucherov and NHL EDGE
- NHL EDGE API, Kucherov 2025-26: skater detail https://api-web.nhle.com/v1/edge/skater-detail/8476453/20252026/2 ; skating distance https://api-web.nhle.com/v1/edge/skater-skating-distance-detail/8476453/20252026/2 ; skating speed https://api-web.nhle.com/v1/edge/skater-skating-speed-detail/8476453/20252026/2 ; 2024-25 https://api-web.nhle.com/v1/edge/skater-skating-speed-detail/8476453/20242025/2
- NHL.com (2026-03-20), "NHL EDGE stats: Kucherov building strong case for Hart Trophy". https://www.nhl.com/news/nhl-edge-stats-nikita-kucherov-hart-trophy-contender-2026
- Pallotta (2023), Kucherov passing data from All Three Zones [S]. https://lastwordonsports.com/hockey/2023/08/18/nikita-kucherov-passing-data/

3-on-3 overtime
- Corsi (2018-02-08), "Overtime approach no longer run and gun", NHL.com. https://www.nhl.com/news/overtime-approach-no-longer-run-and-gun-295721154
- Fraser (2018-12-26), "Overtime success can be difference between making, missing playoffs" (NHL Coaches' Room), NHL.com [V]. https://www.nhl.com/news/nhl-coaches-room-overtime-success-303255732
- Puck Over The Glass, "Do faceoffs matter in 3-on-3 overtime?" (Evolving-Hockey data). https://puckovertheglass.substack.com/p/do-faceoffs-matter-in-3-on-3-overtime
- Trimble (2023-10-20), "Helpful hints to winning 3 v 3 OT" (free part only) [V]. https://andrewtrimble.substack.com/p/helpful-hints-to-winning-3-v-3-ot

Defence, support and coaching
- HockeyShare (2010-05-03), "Gap control basics" [V]. https://www.hockeyshare.com/blog/gap-control-basics
- Dudar (2023-10-15), "Being open is not good enough" [V]. https://rileydudar.substack.com/p/being-open-is-not-good-enough
- Passos, Araújo, Davids, Gouveia, Milho & Serpa (2008), J Sports Sci 26:1421-1429, abstract. https://doi.org/10.1080/02640410802208986

Perception, decisions and teammates
- Jordet et al. (2020), Front Psychol, scanning in the Premier League. https://pmc.ncbi.nlm.nih.gov/articles/PMC7573254
- Berg et al. (2025), "Scanning is associated with better performance in professional ice hockey", J Sports Sci 43:145, abstract. https://doi.org/10.1080/02640414.2024.2433899
- Bespomoshchnov, Lemoyne, Jordet & Vater (2026), "Scanning in junior elite ice hockey players", J Sports Sci, abstract. https://doi.org/10.1080/02640414.2026.2744018
- Mulligan & Hodges (2010), "Situational familiarity improves decision quality in dynamic environments", JEMS 42(1), abstract. https://scapps.org/jems/index.php/1/article/view/36
- Authié, Hilt, N'Guyen, Berthoz & Bennequin (2015), Front Hum Neurosci 9:312. https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2015.00312/full
- Carroll et al. (2019), "On the Utility of Learning about Humans for Human-AI Coordination", NeurIPS. https://arxiv.org/abs/1910.05789
- Siu et al. (2021), "Evaluation of Human-AI Teams for Learned and Rule-Based Agents in Hanabi", NeurIPS. https://arxiv.org/abs/2107.07630

Earlier rounds and this repo
- `research_notes/VR hockey sense training/simulation_and_scoring.md`, `defenseman_coaching.md`, `hockey_sense_science.md`; `reports/VR hockey sense training.md`; `research_notes/Hockey physics feel/skating kinematics.md`.
- Code read: `prototype/threes.py`, `goalie.py`, `rig.py`, `tests/test_threes.py`. Jon's logs: `prototype/data/game-20261109-111553`, `-112005`, `-113451` (`events.jsonl`, `meta.json`).

## Fact-check

Checked 2026-11-13. Scratch scripts and outputs are in the round's scratchpad folder (`ai-round/factcheck-iq`).

### What I checked

- **The self-play numbers.** I re-ran the researcher's probe (AI only, 3 m/s, 4 × 600 s, same seeds). Every count and ratio in the "AI only" column came out identical; only the tick timings moved, because other jobs were running. I re-ran the branch split (128 / 54 / 15 of 197, the same) and the mark-change count (3.88, the same). I read the stand-in and full-speed outputs, and every number quoted from them matches.
- **Jon's logs.** I recounted his three games with my own script: AI teammates made 40 passes (18 to U1, 15 to U2, 7 to Jon), opponents 90, over 14.8 min, so 17.5% and 0.47 a minute. Confirmed. His stick is 1.42 m and he shoots left.
- **The code.** Every statement about `threes.py`, `goalie.py`, `rig.py` and `arena.py` matches the code, except the one about pokes (item 3 below): `vmax` 2.85 and carriers 2.42 m/s at a 3 m/s setting, the 1.6 m / 0.5 / 50% pressure branch, the 0.55 lane test, 9 m/s passes to Jon with a 2.5 m lead cap, the ×1.3 bonus, the 6 m/s rule in `_possession`, `POKE_YOU` 0.8, the 0.15-0.35 s first decision, the 0.6 s greedy re-pairing, the presser's target (blade plus 0.6 m goal side), the fixed support spots, `_chase`, the head-relative left stick in `rig.Drive._want`, and blue lines at 17.25 m.
- **Sources.** I downloaded and read Iaboni 2025, Murto 2023, Yu 2019, Radke 2021, 2022 and 2023, Ritchie 2022, Fernández & Bornn 2018, the Waterloo 2024 paper, the two xT student papers, Liu & Schulte, Carroll and Siu. I fetched the Stathletes slides, Novet, Pallotta, the NHL EDGE API and the March 2026 NHL.com article, Corsi, Fraser, Puck Over The Glass, Trimble, HockeyShare, Dudar, Jordet, and the abstracts of Passos, Berg, Bespomoshchnov, Mulligan & Hodges and Authié.

### What is confirmed

- All the Iaboni numbers: 1.29 s, 1.43 / 1.47 / 1.05 s by zone, 1,194 games, Kucherov's 41.5 possessions per 20 min against 31.3, the 1.67 s top-10 cut-off, Barzal 2.03 s, Quinn Hughes 2.00 s, 3.3-4.2% of ice time.
- All the Murto numbers: 79.87% of 535,449 passes, 95.35% of 1 s moves, 5.29%, 39.67%, 69.88%, 872 matches at 20 Hz, the 8 s window, and both danger tables with their counts.
- The Yu entry table, row by row, and the "≈ goals per entry" arithmetic (2-on-1 ÷ 3-on-3 = 8.9). Also the pass-speed and pre-shot-pace findings.
- Radke: 2 Final games at 12 / 60 Hz, the 3× lane asymmetry, the 5 ft / 15 ft pressure zone; 198 games, 84.4 / 10.2 / 2.6%, over 94%, 59%; 1,221 games, about 12 and 17 passes per 20 min, 0.59-0.70.
- Kucherov 2025-26 in the EDGE API: 130 points, top speed 61st percentile, even-strength distance per 60 59th percentile, offensive-zone time 45.7%. Pallotta: 21.2% and 27.6%, 10.9-16.2%, 100th percentile.
- The 3-on-3 overtime numbers (2:12-2:31, 61-66%, 4.3 shots; 243 overtimes and 53 / 54 / 57%; 4,861 faceoffs, 698-670, R² 0.0004) and the coaching quotes.
- Passos (under 4 m, 1 m/s, youth rugby union), Jordet (0.44 scans/s, 9,574 possessions, 0.46 against 0.40), Berg (2,545 actions, β = 0.12), Bespomoshchnov (16 NTDP players, 47-53%, 58.1%, 134.5 ms), Mulligan & Hodges (23 / 14, 118 decisions, p = .021 and .01), Authié (10 people, 200 ms pooled, 264 ms and 14.8° in the light), Siu, Liu & Schulte (3.38 million events).
- Costs: re-run at 0.125 ms (2 m grid), 0.39 ms (1 m grid), 0.19 ms (900 path points), 0.16 ms (`shot_xg`).

### What I corrected

1. **Why AI passes fail.** The note blamed passing judgement. A new measurement shows about half of the passes an opponent ends up with first reached the intended receiver's stick and failed the 45% reception roll in `_loose` (52 of 111). The pass-odds fix alone will not reach 75-80% completion.
2. **Mark changes.** About half of the 3.9 per defender per minute follow a change of possession. During a settled possession it is 1.9.
3. **Pokes.** The odds do depend on blade-to-puck distance; they ignore body position and cues.
4. **Kucherov.** The possession numbers are 2023-24, not 2025-26. The 1.21 assists per game was mid-season (20 March); the final line is 86 assists in 76 games (1.13). "Held briefly" is unverified, and elite players as a group include long holders (Barzal, the Hughes brothers, Makar).
5. **Ritchie's reaction times.** The 0.189 s comes from sprint starts and the defenders' extra 0.1 s is an assumption, so both are [E], not [M]. All 289 passes were on power plays.
6. **Fraser.** "30-40 seconds tick off the clock" is time spent regrouping, not time left. The article title is fixed in Sources.
7. **Stathletes.** Compact units and stretched lanes are two separate findings; region control, not gap, suppresses quality. Games: 280 or 289 (the slides disagree).
8. **Step-up cues.** The Makar cue is in `defenseman_coaching.md`, not the report. "Turns his back" and "pinned on the boards" are this note's own ideas [E].
9. **Tags.** The Liiga backcheck remark is an informal observation [V]. The readings of Radke 2023 ("thread tight lanes") and Mulligan & Hodges ("pattern-based") are [E].
10. **Goalie xG example.** 0.78, not 0.79; the 0.95 and 0.88 are right.
11. **Stand-in caveat.** 15 of 16 passes to the stand-in went to an opponent because its blade has no physical stick, not because of anything Jon would do.

### What the synthesis can lean on, and what needs care

- **Lean on:** the self-play measurements (fully reproducible with the scripts and seeds); the code descriptions; the possession-length, pass-completion and entry tables; the 3-on-3 overtime facts; the scanning studies; the Kucherov EDGE skating numbers.
- **With care:**
  - The AI-to-real comparisons (touch length, losses per carry-second) mix definitions: Murto does not define a failed 1 s "move", and AI touches run pickup to release.
  - The 1-on-1 thresholds are from youth rugby on foot.
  - The Stathletes results are conference slides.
  - The rink-control reaction times are borrowed, not measured in hockey.
  - Carroll's effect with real people was weaker than with a simulated human.
  - Kucherov's touch length is not known.
  - The pass-failure split, the marks split and every target in "What this means for the sim" are this round's own measurements or design proposals.
- **First fix:** fix or model the reception roll before judging pass-choice changes. Otherwise a better `_pass_odds` will look weaker than it is.
