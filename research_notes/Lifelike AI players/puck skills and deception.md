# Finesse with the puck: what elite carriers, passers and shooters do

Research round "Lifelike AI players", 2026-11-13.

*No code or tracked file was changed to write this. Scratch scripts, downloaded papers and outputs are in the session scratchpad only (`ai-round/puck-skills/`).*

Tags: **[M]** measured in the cited study. **[D]** derived: arithmetic shown, or my own measurement of the sim, of Jon's recordings, or of public data. **[E]** estimate or model output, assumptions stated. **[V]** vendor claim, coaching text, broadcast or scouting commentary, anecdote. **[S]** secondary: read in a source that cites the primary.

## Bottom line

1. **The AI's puck is glued, not carried. A blade that really touches the puck is possible and cheap.**
   - Today `_carry` puts the puck 0.75 m straight in front of the carrier every 20 ms [D, code].
   - `_possession` only counts the puck as lost if it is more than 0.5 m from that point, or moving more than 3 m/s faster or slower than him. A smaller poke from Jon is undone at the next tick [D, code].
   - The drawn blade (`figures._local_cached`) sits about 0.43 m from the puck: its middle is 1.085 m ahead and 0.27 m to the side [D, from the segment ends].
   - I built a scratch prototype: a rigid AI blade moved by a simple controller, hitting the puck only through the sim's own compiled contact functions (`physics_core.integrate` and `collide_blade`, 4 substeps per ms).
     - It carried and stickhandled the puck at 3-5.5 m/s, with ±0.1-0.25 m side-to-side sweeps at 1-2 Hz. It kept the puck for the full 10 s in all 9 runs, with a median error of 6-18 cm from where it wanted the puck [D].
     - Sweep passes from rest left at the blade's speed (±1%), after 50-330 ms of contact [D].
     - Inside the compiled kernel, a blade costs 0.65 µs per substep in contact. That is about 2.6 ms per second of play, or 0.26% of one core, and it runs outside the GIL [D, benchmark].
     - It is not finished. It lost the puck within 1 s with sweeps of ±0.2 m or more while standing still, and on curves of 4 and 8 m radius.
2. **Elite possessions are short and frequent. The AI is either too slow to move the puck or not allowed to touch it once.**
   - NHL 5-on-5 possessions in 2023-24 averaged 1.29 s, and 1.05 s in the offensive zone [M].
   - Kucherov had 41.5 possessions per 20 minutes, against a forward average of 31.3 (+33%). He is not in the top 10 for possession length [M]. So the archetype is many short touches. *Corrected in fact-check:* the paper does not give his average possession length, only that it is below the 10th-ranked forward's 1.67 s (the forward mean is 1.27 s). "Many touches, none of them long" is what the data show; "short" is an inference [E].
   - In self-play the AI holds the puck 0.62 s (median) before a pass. Nobody holds it less than 0.16 s, so one-touch passes and one-timers cannot happen [D].
   - 59% of AI passes leave with an opponent within 1.0 m: the AI passes once it is already in contact [D]. (Added in fact-check: this is built into the code. `_defend` sends the marker to the carrier's stick, so he ends up at the 0.9 m `SKATER_GAP`, and `_decide` passes half the time when an opponent is within 1.6 m. The median opponent distance at a pass was exactly 0.90 m [D].)
3. **AI passes look the least human of anything it does with the puck.**
   - 58% of AI passes go more than 90° away from where the passer faces, and 43% more than 120° [D]. In real play that needs a backhand, a drop pass or a turn [E; retagged in fact-check, this part is a reading, not a measurement].
   - Every AI pass leaves at 10 m/s. NHL completed passes averaged about 10.5 m/s over their flight, with the middle half between 7.7 and 13.3 m/s and the top 5% above about 19 m/s [D, read from a published figure].
   - AI passes are short: median 6.4 m, against about 11.6 m (38 ft) for NHL completed passes [D, M]. (Added in fact-check: the 6.4 m is to the receiver's stick for all AI passes. For completed AI passes, the distance from the passer to where the receiver took the puck was a median 5.7 m [D], so the gap is wider still.)
   - The AI completes 42% of passes. Elite women's games (Stathletes data) completed 73.5% of 10,105 attempts [D].
4. **Cross-seam ("royal road") passes are where elite playmakers make goals, but the sim's goalie barely punishes them.**
   - Valiquette's video study credits 22% of goals to royal-road passes, with shooters scoring about 30% on them against 8.5% overall [V]. *Corrected in fact-check:* the 22% is Valiquette's, but the 30% against 8.5% is not in his write-up. It is Chris Boyle's own shot-quality research, in an MSG Networks article reprinted by the OMHA in 2019 ([OMHA](https://www.omha.net/news_article/show/486107)) [V]. Valiquette's write-up says only that a puck crossing the royal road before a shot raises the chance "by over 10 times".
   - In the Stathletes women's data, shots on net within 2 s of a completed royal-road pass scored 19.5% (8 of 41). After other completed passes it was 7.1% (19 of 268) [D].
   - In the sim's goalie model (`goalie.py`), the goalie has 0.83-0.87 m to shuffle and gets there in about 0.6 s. Only a 20 m/s pass, shot within 0.1 s of arriving, gains anything: 0.01-0.10 xG [D].
     - *Corrected in fact-check:* that holds for the one geometry tested (a pass from one faceoff dot to a receiver off the far post, 11 m). For a 10 m/s pass (the AI's), I found no gain in any geometry I tried. But a shorter, faster seam pass does pay: a 20 m/s pass to a back-door receiver 1.5 m out, shot within 0.1 s, gained 0.14-0.22 xG, and a 30 m/s dot-to-dot pass gained 0.09-0.27 [D, `goalie.after_tracking` and `shot_xg`]. For a 20 m/s pass, any gain is gone once the receiver holds the puck for 0.2 s.
   - So elite passing will not pay off in this sim until the goalie (or the AI's value model) rewards lateral puck movement. (Fact-check: true for the AI's 10 m/s passes. Hard, quick seam passes already gain something in close.)
5. **Deception works through the puck and stick, and it needs timing.**
   - Elite goalies' final fixation sat on the puck or stick in 70.5% of trials, and on the shooter's body in 2.1% [M]. It lasted longer on saves (952 ms) than on goals (826 ms) [M].
   - A head fake slowed novice observers by up to 34 ms when the head turned 300 ms before the pass. With no lead it slowed them by 2 ms, which was not significant [M].
   - One-timers were 14.1% of shot attempts in the women's data, and scored 15.6% on net against 6.0% for other shots [D].
6. **Carry speed: skilled players lose about 5% with the puck.**
   - Elite and sub-elite U16 national-team players were 4.9% and 4.3% slower on a 60 m agility course with the puck [M].
   - `CARRY` is 0.85. 0.95 fits better.
7. **Stickhandling has only one usable measurement.**
   - Varsity players moved the puck sideways at up to 2.9-3.0 m/s, against 2.5 m/s for recreational players, in a figure-8 drill done standing in place, on synthetic ice in a lab [M].
   - Their blade outran the puck by about 0.6 m/s at its peak, which the author reads as a "volley-and-catch" technique [M, the reading is the author's].
   - I found no measurement of stickhandling frequency in games.
8. **Kucherov's shooting, from NHL EDGE (2025-26 regular season).**
   - His shots averaged 62.5 mph (27.9 m/s), against a league average of 53.2 mph [M]. The AI shoots at 22 m/s (49 mph) ±10-15%.
   - He scored on 19.1% of his shots on goal (league 13.0%), and on 40% from high-danger areas (league 19.6%) [M].
   - *Corrected in fact-check:* EDGE's "league averages" are for the player's position. These are the averages for forwards. The defencemen's average shot speed is 67.8 mph.
   - He is a left shot listed at right wing: an off-wing player [M].

## The current AI with the puck, measured

Six self-play games of 10 minutes each: seeds 11-16, all six skaters AI, the real 1 kHz puck. I instrumented `threes.Game` from a scratch driver without changing it.

| What | AI self-play [D] | Elite reference |
|---|---|---|
| Possessions | 1,267; median 0.63 s, mean 1.17 s | NHL 5v5 mean 1.29 s; offensive zone 1.05 s [M] |
| Hold before a pass | median 0.62 s (p10 0.22, p90 1.83); minimum 0.16 s | NHL counts one-touch passes and shots as possessions [M]; no hold-time distribution found |
| Hold before a shot | median 2.33 s (p90 5.6) | none found |
| Releases under 0.3 s | 135 of 573 passes, 49 of 312 shots | — |
| How possessions end | 573 passes, 312 shots, 293 random pokes (23%), 83 knocked loose | — |
| Pass length (to the receiver's stick) | median 6.4 m (p10 2.6, p90 10.6) | NHL completed: median 38 ft (11.6 m) [M]; women's: median 34 ft (10.4 m) [D] |
| Pass speed | 10 m/s, always (9 m/s to Jon) | NHL completed: median about 34 ft/s (10.5 m/s), quartiles 25 and 44 ft/s [D, from figure] |
| Pass completion (the intended receiver within 3 s) | 42% (240 of 573) | women's elite: 73.5% [D]; NHL: not public |
| Cross-seam passes in the offensive zone | 51, of which 15 complete (29%) | women's royal road: 52% complete [D] |
| Pass more than 90° from the passer's facing | 58% (more than 120°: 43%) | — |
| Opponent within 1.0 m at the pass | 59% | — |
| Shots per minute (both teams) | 5.2 | — |
| Shot distance | median 8.9 m (p10 3.7, p90 10.1) | — |
| Shot more than 60° from the shooter's facing | 29% (p90 129°) | — |
| Shots within 0.5 s of receiving a pass | 28 of 312 (9%) | one-timers: 14.1% of attempts [D] |
| Carrier speed | median 4.06 m/s, p90 4.93 (= 0.85 × 5.8) | carriers about 5% slower than without the puck [M] |
| AI tick cost | 0.82 ms mean (p99 1.65 ms), 50 times a second | — |

Notes on the table:
- "Knocked loose" (83) means the puck was more than 0.5 m from the carry point, or moving more than 3 m/s relative to the carrier. No one held a stick in these games, so these are boards and nets displacing the puck. The log calls them "lost by you" for team "them". In Jon's three recorded games (14.8 minutes) the log has 10 such losses, so that is the most he can have knocked off [D].
- 72 of the 312 shots scored (23%). That depends on the goalie model, not on puck skill.
- The tick cost of 0.82 ms is about 4% of a core, and all of it holds the GIL [D].

**What a defender sees.** The carrier glides at a fixed point mass's speed with the puck frozen 0.75 m ahead. Then the puck leaves at 10 m/s in any direction, often behind him, with no wind-up and no turn of the body. That is the opposite of everything below.

## Carrying and stickhandling

**Lawrie 2014 (McGill MSc) [M]** ([record](https://mcgill.scholaris.ca/items/eeeb2675-8b05-4122-a533-2f476979bd4a)) is the only kinematic study of stickhandling I found.
- **Sample:** 27 men (13 varsity, 14 recreational). The task was five figure-8 loops round two pylons spaced at 2/3 of body height (about 1.2 m), done as fast as possible with the feet planted. (Added in fact-check: it was done in a lab on a synthetic polyethylene surface, not real ice. The author lists that as a limitation.)
- **Recording:** Vicon at 240 Hz, filtered at 8 Hz.
- **Loop time:** 2.24 ± 0.30 s varsity, 2.76 ± 0.52 s recreational: 18% faster.
- **Peak side-to-side puck speed** (Appendix B, section 4): 2.94 and 2.97 m/s varsity against 2.53 and 2.52 m/s recreational (forehand and backhand crossings).
- **Blade marker:** 3.56 and 3.54 m/s against 2.61 and 2.78 m/s. (Fact-check: this marker, "s3", sits where the shaft meets the blade, not on the blade's middle. The author still calls its speed the blade's.)
- **Lateral excursion:** the puck went 0.33 m past the right pylon for varsity players and 0.37 m for recreational players. Varsity puck paths sat about 5 cm further forward.
- **Technique:** at peak speed, the varsity blade moved 0.61 m/s faster than the puck on the forehand crossing; the recreational blade, 0.08 m/s. The author suggests varsity players "volley and catch" the puck rather than "plough and push" it. That is his interpretation, not a measurement.
- **Comparison with Jon [D]:** his own stickhandling in the 3v3 (2026-11-09) stayed 99% under 3.2 m/s (the `Params.release` comment). That is the same band.
- **Limits:** standing still, pylons rather than defenders, one drill. I found **no measurement of stickhandling frequency or amplitude in games**, and no study of where skilled carriers hold the puck relative to the body while skating.

**Carry speed.**
- Roczniok et al. 2024 [M] ([J Hum Kinet 93:193-203](https://pmc.ncbi.nlm.nih.gov/articles/PMC11307188/)): 40 elite (Czech U16 national-team pool) and 23 sub-elite (Polish U16) players. On a 60 m Illinois agility course they were 4.9 ± 2.4% and 4.3 ± 2.5% slower with the puck (Table 1: 16.1 s against 15.3 s, and 16.5 s against 15.7 s). Better than the earlier round's 13 U12 players over 30 m (4.9%).
- NHL tracking [M] ([Lodhi et al., LINHAC 2025 Part II](https://cs.uwaterloo.ca/~brecht/papers/linhac-2025-part-2.pdf), Table 1, 2023-24, 5-on-5):
  - Forwards' season top speed with the puck averaged 31.5 ft/s (9.6 m/s), and their per-game top 27.3 ft/s (8.3 m/s).
  - Forwards averaged 0.44 carries a game at 20+ mph per 20 minutes. MacKinnon averaged 3.35.
  - The paper notes that Marner and other playmakers rarely carry at 20+ mph.
- **[D]** The earlier round's skating note gives a median NHL forward top speed of about 22 mph (32.3 ft/s) without the puck. So top speed with the puck is close to top speed without it. The definitions differ (EDGE's is a sustained speed), so treat this as rough.

**Protecting the puck and reacting to pressure** (coaching text only [V]):
- **IIHF Coach Development Program, Level I, Individual Offensive Tactics** ([PDF](https://www.hockeyeasternontario.ca/media/n4pf15hp/iihf_coachdev_off_tactics.pdf)):
  - Protecting: "the use of the skates and stick to maintain possession of the puck while using the body to establish position, thereby keeping the defender away from the puck."
  - Driving the net: keep "one's body position between the puck and the defender."
  - Delaying when cut off: "a tight turn toward the boards", a "fade" to the outside, or "a quick stop, facing the centre of the ice surface".
  - The turn-up: a shoulder-dip fake, then a tight turn the other way.
  - Body fakes: made "just outside the checking range of the opponent", so the puck goes through the "defensive triangle" of his skates and stick.
- **Revak (Hockey's Arsenal, 2024)** ([post](https://hockeysarsenal.substack.com/p/puck-protection-how-to-protect-the)): "the puck moving first then the skating adjusts relative to the puck"; "get a shoulder in front and ride the leverage".
- **Missing:** no measured data on where the puck sits when a carrier is pressured, or on how often each escape (cutback, curl, toe drag, shield) is used.

## Passing

**NHL tracking, completed passes only [M]** ([Radke, Brecht & Radke, LINHAC 2022](https://cs.uwaterloo.ca/~brecht/papers/passing-linhac-2022.pdf)): 198 games of 2021-22 (all played in November 2021). The puck is tracked at 60 Hz and players at 12 Hz.
- **Types:** 84.4% direct, 10.2% off the boards once (1-bank), 2.6% rimmed, 2.8% other (Table 1).
- **Length:** half of completed passes travelled 38 ft (11.6 m) or less (Fig. 5a). [D] I read the curve for all passes: quartiles at about 23 and 50 ft (7 and 15 m).
- **Speed (Fig. 5b, distance over duration, so an average over the flight) [D, read from the curve]:** median about 34 ft/s (10.5 m/s), quartiles about 25 and 44 ft/s (7.7 and 13.3 m/s), 95th percentile about 62 ft/s (19 m/s).
  - Bank and rim passes had almost the same speeds as direct ones, though they travelled further.
  - The authors expect that players pass harder at the boards.
- **Limits:** no failed passes, no saucer heights, and imprecise start and end times.

**Elite women's games, my count [D]** ([Stathletes Big Data Cup 2021 data](https://github.com/bigdatacup/Big-Data-Cup-2021), `hackathon_womens.csv`): 13 games, hand-tracked; 11 national-team games (2018 Olympics, 2019 Rivalry Series and Worlds) and 2 NCAA games.
- **Completion:** 7,424 of 10,105 passes (73.5%). Direct 76.0%, indirect (off the boards) 68.3%.
- **By length:** completion barely changed, from 70% to 76% across 0-20, 20-40, 40-60 and 60+ ft.
- **Completed pass length:** median 34 ft (10.4 m), quartiles 22 and 47 ft.
- **Royal-road passes** (both ends below the tops of the circles, on opposite sides of the centre line): 52% completed (128 of 245).
  - *Corrected in fact-check:* the count also requires the receiving end to be in front of the goal line, and the "shot within 2 s" figures in this note count only a shot that is the very next event after the pass. With those rules I get the same numbers. If passes received behind the goal line count too, completion is 64% (254 of 399), and shots after them scored 20.9% (9 of 43) against 6.8% [D]. The direction holds; the completion rate depends on the definition.
- **Limits:** the clock has 1 s resolution, there is no pass speed, and the players are women's elite rather than the NHL.

**Pass types elite playmakers use.** Data here is thin.
- Kucherov was in the 100th percentile of shot assists in 2023, the 89th and 100th of centre-lane passes per hour over two seasons, and the 93rd of high-danger passes in 2022. These are Sznajder's All Three Zones hand-tracked stats, as quoted by Last Word on Sports [S/V] ([Pallotta 2023](https://lastwordonsports.com/hockey/2023/08/18/nikita-kucherov-passing-data/)). (Fact-check: the article credits All Three Zones for the shot-assist figure. It does not name a source for the other percentiles.) That article defines high-danger passes as cross-crease, behind-the-net and centre-lane passes.
- Saucer heights (0.05-0.3 m short, up to about 3 m long) and the 20° launch of a famous long saucer are in the earlier round's [shot outcomes.md](../Shot%20release/shot%20outcomes.md) [V/S]. Nothing new was found.
- No measured data on no-look or backhand-saucer pass speeds or frequencies.

## Deception and patience

**What the goalie watches [M].** [Panchuk & Vickers 2006](https://europepmc.org/article/MED/17050024) (Human Movement Science 25:733-752) studied elite goalies facing wrist shots from 5 and 10 m on ice.
- The final fixation before the save was on the puck or stick in 70.53% of trials, on the ice in front of the release point in 25.68%, and on the shooter's body in 2.1%.
- On saves it started earlier and lasted longer (952 ms) than on goals (826 ms).
- [E] So shooter deception that matters to a goalie is in the puck and blade: a late change of release point (toe drag, curl and drag), a pass across, or a release that cuts his look at the puck short. Body fakes matter less.

**Pre-shot movement [V].** Valiquette's "(Royal) Road" study ([2014-15 write-up](https://cdn1.sportngin.com/attachments/document/0137/7547/The_Royal_Road_-_Scoring.pdf)) is proprietary video coding and not peer-reviewed.
- "Green" shots deny the goalie "half a second of clear sight prior to the release". They made 76% of goals but about a quarter of shots.
- Royal-road passes made 22% of goals; screens 10%; one-timers on the same side 9%.
- A shot from above the circles with no lateral movement scores "around 3%"; crossing the royal road through the slot, "33%".
- [D] The Stathletes check above (19.5% against 7.1%) points the same way, on a small sample (8 goals).

**Head and look fakes [M].**
- [Kunde, Skirde & Weigelt 2011](https://doi.org/10.1037/a0023756) (J Exp Psychol Appl 17:110-127): a basketball pass with the head turned the other way slowed observers' decisions. The cost is perceptual: it does not pull them toward the head's direction.
- [Polzien, Güldenpenning & Weigelt 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8115800/) (PLoS ONE 16:e0251117), 23 novices, static photos (Table 1): the head-fake cost was 2 ms with no lead, 16.5 ms at 100 ms, peaked at 34.1 ms when the head turned 300 ms before the pass, and fell to 13.6-15.8 ms at 700-800 ms.
- [Güldenpenning et al. 2023](https://doi.org/10.1016/j.humov.2022.103045), novices: making a head fake slowed the passer's own start with 0-800 ms to prepare it, but not with 1200-1500 ms.
- The IIHF manual lists the "look away", fake shots that "freeze" a shot-blocker, and change of pace as tactics [V].
- **Limits:** no hockey-specific measurement of look-offs. The effect is tens of milliseconds, so it is a flavour, not a game-changer.

**The delay and the shot-or-pass disguise [V].**
- Kucherov: "I'm buying time for number 40 to catch me", and "we buy, I don't know, half a second for each other and we can make plays" ([Prewitt, SI 2018](https://www.si.com/2018/09/13/nikita-kucherov-film-session-tampa-bay-lightning)). SI also reported him second in the NHL in 2017-18 with eight backhands.
- A Raw Charge breakdown shows him on the power-play half-boards with "his stick in the air as the puck slides to him", while goalie and defender "sell out to block what they believe will be a one-timer". He passes instead, and later shoots "from the same exact position". It quotes Brayden Point: "even if you don't think he sees you, he sees you" ([Justin G., 2023](https://www.rawcharge.com/nikita-kucherov-and-is-it-a-shot-or-a-pass-tampa-bay-lightning-power-play/)).
- [E] For the AI the rule is simple: the same look (stick up, square to the net) must lead to either a shot or a pass, chosen late, from the same spot.

## Shooting: speed, release, one-timers, screens

**Speed [M].** NHL EDGE for Kucherov, 2025-26 regular season (76 games; [API](https://api-web.nhle.com/v1/edge/skater-detail/8476453/20252026/2), [shot speed](https://api-web.nhle.com/v1/edge/skater-shot-speed-detail/8476453/20252026/2)):
- Average shot speed 62.49 mph (27.9 m/s; 95th percentile), against a league average of 53.19 mph (23.8 m/s).
- Top shot speed 92.06 mph; league average of top speeds 83.62.
- *Corrected in fact-check:* every EDGE "league average" in this section is the average for forwards, not the whole league. For defencemen the same fields read 67.85 mph (average shot) and 88.92 mph (top shot).
- 131 attempts at 70-80 mph, 63 at 80-90, 3 at 90-100.
- [D] The AI's 22 m/s × U(0.85, 1.1) gives 18.7-24.2 m/s (42-54 mph): about the NHL forwards' average, about 4 m/s under Kucherov.

**Where and how well [M].** Same source:
- 231 shots on goal, 44 goals: 19.05% (league 12.98%).
- High-danger areas: 18 of 45 (40%; league 19.6%). Mid-range 15.4%. Long range 7.9% on 38 shots, a 98.7th-percentile number of long shots.
- By EDGE's areas, 110 of his 231 shots came from the four "R" areas (R circle 37, Outside R 40, R point 22, R net side 11), against 37 from the four "L" areas.
- EDGE lists him as a left shot at right wing. [E] If EDGE's left and right are as the attacker sees them, that is the off-wing shooter on his forehand side, as the power-play breakdowns describe. I did not verify EDGE's side convention.

**Release.** The earlier round measured contact times: wrist shots 150-180 ms on average with the puck riding about 1.2 m, and pro one-timers 15 ± 2 ms ([puck release.md](../Shot%20release/puck%20release.md)) [M]. I found **no measurement of total release time** (from reception or decision to the puck leaving) for elite against recreational players.

**One-timers and screens [D]** (Stathletes women's data, the tracker's one-timer and traffic flags):
- One-timers were 235 of 1,671 attempts (14.1%), and scored on 15.6% of shots on net (15 of 96), against 6.0% (41 of 687) for other shots.
- Shots marked "traffic" scored 4.8% on net, against 8.7% without. Traffic in this data includes defenders in the lane, so it does not test screens.
- Valiquette credits screens with 10% of goals [V].

**Changing the angle.** The earlier round found coaching text for the toe drag: the puck is moved 2-4 in (5-10 cm) to change the angle past a stick, then snapped [V]. No measurement.

## Making it physical in this sim

**What the code does now [D].**
- `_carry` places the puck every 20 ms.
- `_take` makes a loose puck within `PICKUP_R` 0.6 m of an AI stick his at once, if it is slower than 7 m/s relative to him; up to 16 m/s, it is a 45% coin flip.
- `_pass` and `_shoot` set the puck's velocity at the carry point.
- AI pokes on AI carriers are random rolls (`POKE_RATE`) that set the puck's velocity.
- AI pokes on **Jon's** puck also set its velocity: 5-6.5 m/s away from the defender, after moving the puck 0.12 m (`_possession`). That is an action at a distance on the puck Jon plays. It goes against his "no magnets" rule in spirit, even though it works against him rather than for him.

**Option 1: keep placing, but honour contact (an interim step).**
- When the 1 kHz physics reports a contact between Jon's blade and the AI's puck (`Sim.contact`), the AI should lose possession and re-gather it as a loose puck. The 0.5 m / 3 m/s test should not decide this.
- Cost: none. It removes the "a light poke does nothing" feel. The puck stays glued between pokes.

**Option 2: a procedural stickhandle, still placed.** The puck is moved along a forehand-backhand path on the drawn blade.
- It looks right and costs nothing.
- It is still a magnet. A poke would hit a puck that teleports back. **Not recommended**, except as a look test.

**Option 3: a kinematic AI blade in the 1 kHz contact model (recommended).** My prototype is in the scratchpad: `ai_blade_kin.py`, `ai_sweep.py`.
- **How it works:**
  - A rigid, two-faced, slightly cupped blade, 0.28 m long and 7 cm tall, moved each ms by a controller that sees the puck.
  - Along the push direction, the blade moves at the speed the puck should have. It closes on the puck at no more than 0.8 m/s, so it pushes and never strikes. Across that direction, it follows the puck and stays centred on it.
  - To push the other way, it goes over the puck (lifted 3.5 cm) to the puck's other side: forehand to backhand.
  - While stickhandling, the faces stay across the sweep, tilted forward as much as the puck needs forward speed.
  - The puck moves only through `collide_blade`, ice friction and air drag.
- **Results [D]** (10 s runs, open ice, no boards, no defenders):

  | Skating | Sweep | Held | Median error | Blade touching |
  |---|---|---|---|---|
  | 3.0, 4.2, 5.5 m/s | ±0.1 m at 1 Hz | 10 s, all | 6-11 cm | 94-99% of substeps |
  | 3.0, 4.2, 5.5 m/s | ±0.2 m at 1.5 Hz | 10 s, all | 13-14 cm | 75-99% |
  | 3.0, 4.2, 5.5 m/s | ±0.25 m at 2 Hz | 10 s, all | 16-18 cm | 59-99% |
  | 3.0-5.5 m/s | no sweep (push ahead) | lost after 6.6-9.2 s | 3-4 cm until lost | 0-19% |
  | standing | ±0.1 m at 1 Hz | 10 s | 28 cm | 0.2% (fact-check: the puck mostly sat still while the target moved, so this is not a real stickhandle) |
  | standing | ±0.2-0.25 m at 1.5-2 Hz | lost in 0.7-1.0 s | — | — |
  | 4.2 m/s round a 4 or 8 m circle | ±0.2 m at 1.5 Hz | lost in 0.5-0.7 s | — | — |

  The skating stickhandle is the useful result. The straight push drifts off the end of the blade. Standing still and curves fail. A real implementation needs a better controller (probably the "volley-and-catch" Lawrie describes) before it ships.
- **Passes and shots as sweeps [D].**
  - From rest, a blade ramping at 60-200 m/s² to 10-20 m/s sent the puck off at 9.95-20.1 m/s, within 1% of the blade.
  - Contact lasted 49-333 ms, and the puck rode 0.43-3.6 m.
  - At 14 m/s and 120 m/s² it was 116 ms over 1.0 m. That is close to measured wrist shots (150-180 ms over about 1.2 m [M]).
  - Direction came out 1-3° short of the aim from rest (1.1-3.4° in my rerun of all nine sweeps), and up to 15° off when skating at 4 m/s. The AI must aim the blade's velocity relative to the ice, allowing for its own skating.
  - Lift needs an open face. The contact model already lifts the puck off an open face (`puck.py` docstring), but I did not test saucers.
- **Cost [D, benchmark].**
  - Compiled `integrate` plus `collide_blade` with a 7-point blade: 0.65 µs per substep in contact, 0.30 µs out of contact. At 4 substeps per ms that is about 2.6 ms per second of play per blade, outside the GIL. Only blades within about 0.5 m of the puck need checking, so 1-3 blades.
  - My controller in Python took 80-90 µs per ms (8-9% of a core, holding the GIL). (Fact-check rerun: 69-77 µs; the original runs ranged 74-94 µs. Either way it must be compiled.) It must go inside the compiled kernel, where I estimate 1-3 µs per ms [E].
  - The 50 Hz AI tick would set the intent: where the puck should be relative to the body, the sweep size and rate, and pass or shot commands.
  - `Sim.step` already costs about 18 µs per tick from Python. A few extra small arrays add a few µs [D/E].
  - The drawn stick must follow the blade, so `figures._local_cached` can no longer cache a fixed stick. About 10 segments per skater per frame in numpy; negligible [E].
- **What changes for Jon [E].**
  - A puck that is honestly on an AI blade is between touches, or at the end of a sweep, some of the time. A well-timed poke moves it, and the AI has to recover it or lose it.
  - Turnovers come from contact rather than dice. AI-on-AI pokes can stay as dice at first, because Jon never touches those pucks.
  - The AI blade must not be an infinitely heavy wall when Jon's stick is on the puck too. Give it a finite effective mass (the earlier round found 0.2-0.28 kg at the blade for a hand-held stick [D/E]), or have its controller yield when Jon is in contact. Otherwise a stick battle feels like pushing a post.
- **Reception.** Option 3 also turns `_take`'s 0.6 m pickup into a real catch. The blade meets the pass moving with it (a small closing speed, so little bounce), which is how skilled players receive. Hard, badly placed passes would then bounce off honestly.

**Comfort [E].**
- The blade and puck are small and move at most a few m/s relative to the carrier, so stickhandling adds little peripheral motion.
- Protecting the puck with the body is the risk: an AI shielding against Jon's stick wants to back into him. Keep AI bodies at least `SKATER_GAP` 0.9 m from his head, as `_separate` does now, and shield with puck and blade placement rather than body contact.
- Keep saucer passes toward Jon low (under about 0.3 m within a few metres of him), so a puck does not come at face height.

## What this means for the sim

One change at a time, in this order. Each can be measured in self-play with the driver above (`selfplay_puck.py` in the scratchpad), then A/B'd by Jon.

1. **The puck under the drawn blade** (`_carry_point`, or `figures._local_cached`).
   - Put the puck at the drawn blade's middle (about 1.0 m ahead, 0.25 m to the shooting side), or move the drawn blade to the puck.
   - Cost: none. Test: the 0.43 m gap goes to 0.
2. **`CARRY` 0.85 → 0.95.**
   - Evidence: U16 national-team players lost 4.3-4.9% with the puck [M]. The earlier round already suggested 0.92-0.95.
   - Test: carry p90 goes from 4.93 to 5.5 m/s.
3. **Jon's contact takes the puck off the AI** (`_possession`: use the physics' blade contact, not the 0.5 m / 3 m/s test).
   - Cost: none. Test: Jon A/B "light pokes count".
4. **Passes a human could make** (`_decide`, `_pass`):
   - A pass more than about 100° from the carrier's facing has two options. He turns first: a facing turn-rate limit plus a 0.15-0.3 s delay [E]. Or he makes a backhand pass at about 70% of the speed with double the aim error [E; no measurement of backhand pass speed or accuracy found].
   - Pass speed set by distance and lane, within the NHL band of about 7-19 m/s: soft to space, hard through a tight lane. This replaces the fixed 10 m/s.
   - Lead the receiver into space rather than to his stick (`LEAD_MAX` 2.5 m is fine).
   - Cost: a few lines and a dozen float operations per decision.
   - Test: in self-play, the share of passes more than 90° from facing (now 58%), completion (now 42%; aim for 60-75% [E], against the women's elite 73.5%), and median length (now 6.4 m, NHL 11.6 m).
5. **Move it before contact** (`_decide`):
   - Add the time until the nearest defender's stick reaches the puck, from his speed and `POKE_R`.
   - When it falls below about 0.3 s [E], the carrier must pass, shoot or protect. Protecting means moving the puck to the far side of his body, or a delay move from the IIHF list: tight turn to the boards, fade, or stop facing the middle.
   - Cost: one distance and one division per opponent.
   - Test: the share of passes with an opponent within 1.0 m (now 59%) falls; turnovers from pokes (now 23% of possessions) fall.
6. **One-touch play** (`_take`, `_decide`):
   - Let a receiver who decided before the puck arrived pass or shoot on the first touch.
   - Remove the 0.15-0.35 s minimum on that path, and keep it for pucks he had to chase.
   - Test: one-timers or one-touch releases near the women's 14% of shot attempts (now 9% within 0.5 s, none under 0.16 s).
7. **The deception layer** (`figures` and `_decide`):
   - A head yaw toward a decoy target 0.3 s before the pass (the head is two plain rings now; it needs a visible facing, such as a visor or nose line).
   - A visible wind-up (stick up, square to the net) that leads to a shot or a pass, chosen late.
   - A toe drag of 0.1-0.3 m across before release when a defender's stick is in the shot lane [E].
   - AI defenders should react to what they see: the wind-up makes them lean into the lane, as in the Raw Charge clip.
   - Cost: drawing only, plus one extra state per carrier.
8. **The kinematic AI blade** (Option 3: `physics_core.sim_step` gets AI blade arrays, plus a compiled controller; the 50 Hz AI sets the intent).
   - This is what lets Jon play against a puck that is really on a stick.
   - Cost: about 0.3% of a core per active blade outside the GIL, plus the controller [D/E].
   - The controller must first pass self-play tests standing still and on curves.
9. **Flag for whoever owns `goalie.py`.**
   - Seam passes and quick releases only pay off if the goalie needs set time.
   - [E] One option: make his save reach depend on time since the puck last moved across his line. That fits both Valiquette's 0.5 s of "clear sight" [V] and the 0.8-0.95 s final fixation on saves [M]. (*Corrected in fact-check:* the final fixation averaged 0.95 s on saves and 0.83 s on goals; 0.8-0.95 s spans both, not saves alone.)
   - Without it, the AI's best tactic stays "walk into the slot and shoot".

## Open questions

- **Stickhandling in games:** frequency, amplitude and where the puck sits relative to the body and the nearest defender. Only a standing pylon drill is measured. NHL puck tracking at 60 Hz could answer this, but it is not public.
- **Hold time before a pass by skill level,** and the share of one-touch passes. NHL possession models count one-touch events, but the papers report only means.
- **NHL pass completion and speed by pass type** (saucer, backhand, stretch). The public tracking papers use completed passes only.
- **Elite against recreational shot accuracy and total release time.** I found accuracy predictors (Michaud-Paquette et al. 2011, abstract only) but no numbers.
- **Whether EDGE's L and R areas are from the attacker's or the goalie's view.**
- **The prototype controller:** whether a volley-and-catch design keeps the puck standing still and on tight curves, and what it does when Jon's stick, the boards or a defender's body interfere.
- **The royal-road effect in larger samples.** Valiquette's numbers are proprietary. My check is 41 shots.

## Sources

Primary and data:
- Lawrie R. (2014). *Kinematic analysis of a stickhandling task in ice hockey and the effect of stick inertial properties.* MSc thesis, McGill. https://mcgill.scholaris.ca/items/eeeb2675-8b05-4122-a533-2f476979bd4a
- Roczniok R. et al. (2024). The relation of on-ice and off-ice performance at two different performance levels in youth ice-hockey players. *J Hum Kinet* 93:193-203. https://pmc.ncbi.nlm.nih.gov/articles/PMC11307188/
- Iaboni E., Negulescu S., Pitassi M., Lodhi F., Brecht T. (2025). Individual puck possessions Part I. LINHAC 2025. https://cs.uwaterloo.ca/~brecht/papers/linhac-2025-part-1.pdf
- Lodhi F. et al. (2025). Individual puck possessions Part II. LINHAC 2025. https://cs.uwaterloo.ca/~brecht/papers/linhac-2025-part-2.pdf
- Radke D., Brecht T., Radke D. (2022). Identifying completed pass types and improving passing lane models. LINHAC 2022. https://cs.uwaterloo.ca/~brecht/papers/passing-linhac-2022.pdf
- Stathletes Big Data Cup 2021 data (`hackathon_womens.csv`). https://github.com/bigdatacup/Big-Data-Cup-2021
- NHL EDGE API, Kucherov 2025-26 regular season: https://api-web.nhle.com/v1/edge/skater-detail/8476453/20252026/2 and https://api-web.nhle.com/v1/edge/skater-shot-speed-detail/8476453/20252026/2 and https://api-web.nhle.com/v1/edge/skater-shot-location-detail/8476453/20252026/2
- Panchuk D., Vickers J.N. (2006). Gaze behaviors of goaltenders under spatial-temporal constraints. *Hum Mov Sci* 25:733-752. https://europepmc.org/article/MED/17050024
- Kunde W., Skirde S., Weigelt M. (2011). Trust my face: cognitive factors of head fakes in sports. *J Exp Psychol Appl* 17:110-127. https://doi.org/10.1037/a0023756
- Polzien A., Güldenpenning I., Weigelt M. (2021). A question of (perfect) timing. *PLoS ONE* 16:e0251117. https://pmc.ncbi.nlm.nih.gov/articles/PMC8115800/
- Güldenpenning I., Weigelt M., Böer N.T., Kunde W. (2023). Producing deceptive actions in sports: the costs of generating head fakes in basketball. *Hum Mov Sci*. https://doi.org/10.1016/j.humov.2022.103045

Coaching, scouting, secondary:
- Valiquette S. *The (Royal) Road to the Future of Goaltender Analytics* (dated 12 Dec 2014, posted 6 Mar 2015). https://cdn1.sportngin.com/attachments/document/0137/7547/The_Royal_Road_-_Scoring.pdf
- Boyle C. (2019). Article on Valiquette's Royal Road and shot quality, MSG Networks, reprinted by the OMHA (source of the 30% against 8.5%; added in fact-check). https://www.omha.net/news_article/show/486107
- IIHF Coach Development Program, Level I, Individual Offensive Tactics. https://www.hockeyeasternontario.ca/media/n4pf15hp/iihf_coachdev_off_tactics.pdf
- Revak G. (2024). Puck protection. Hockey's Arsenal. https://hockeysarsenal.substack.com/p/puck-protection-how-to-protect-the
- Pallotta J. (2023). The data behind Nikita Kucherov's superstar passing ability. Last Word on Sports (quoting All Three Zones). https://lastwordonsports.com/hockey/2023/08/18/nikita-kucherov-passing-data/
- Justin G. (2023). Nikita Kucherov and is it a shot or a pass? Raw Charge. https://www.rawcharge.com/nikita-kucherov-and-is-it-a-shot-or-a-pass-tampa-bay-lightning-power-play/
- Prewitt A. (2018). Nikita Kucherov film session. Sports Illustrated. https://www.si.com/2018/09/13/nikita-kucherov-film-session-tampa-bay-lightning

Earlier rounds used here: [Shot release/puck release.md](../Shot%20release/puck%20release.md), [Shot release/shot outcomes.md](../Shot%20release/shot%20outcomes.md), [Hockey physics feel/skating kinematics.md](../Hockey%20physics%20feel/skating%20kinematics.md), [VR hockey sense training/simulation_and_scoring.md](../VR%20hockey%20sense%20training/simulation_and_scoring.md).

## Fact-check

Checked 2026-11-13. I checked about 62 load-bearing claims: 17 about the code, 18 self-play and prototype measurements, and 27 from sources (including the earlier rounds' numbers this note reuses). 53 were confirmed. 9 were corrected or retagged. Nothing was dropped. Scratch scripts and outputs are in the session scratchpad (`ai-round/factcheck-puck/`).

**How I checked.**
- Code: read `threes.py`, `figures.py`, `goalie.py`, `puck.py` and `physics_core.py` against every statement about them.
- Self-play: an independent probe of my own on seeds 11-13 (10 minutes each; the same games as the note's first three), plus the note's own outputs for all six seeds.
- Prototype: reran six of the stickhandling cases, all nine sweep passes, a compiled benchmark of `integrate` plus `collide_blade`, and a timing of `Sim.step`.
- Sources: fetched every cited paper, page, data set and API. I recounted the Stathletes numbers from the CSV with my own script, and re-read the NHL pass-length and pass-speed curves by pixel position.

**Confirmed.**
- All code statements: the 0.75 m carry point every 20 ms, the 0.5 m / 3 m/s loss test, the drawn blade 0.43 m from the puck (middle at 1.085 m ahead, 0.27 m aside), 10 m/s passes (9 to Jon), `_take`'s 7 and 16 m/s rules, the 5-6.5 m/s pokes on Jon's puck after a 0.12 m move, shots at 18.7-24.2 m/s, the 0.15-0.35 s first decision, carry p90 4.93 m/s, `Sim.contact`, the `Params.release` comment, and 10 "lost by you" events in Jon's three played games (about 14.8 minutes).
- Self-play: my three seeds gave 59% of passes more than 90° from facing (45% over 120°), median hold 0.58 s, minimum release 0.164 s, 62% of passes with an opponent within 1.0 m, median pass length 6.5 m, completion 41%, only 10 m/s passes, and an AI tick of 0.91 ms mean (p99 1.68). That matches the note's six-seed figures. The note's raw rows give exactly 135 passes and 49 shots released under 0.3 s, and 72 goals.
- Prototype: the reruns matched the note's table (for example 4.2 m/s with ±0.2 m at 1.5 Hz: held 10 s, median error 13 cm). Sweeps from rest left at 9.95-20.1 m/s after 49-333 ms. The compiled kernel took 0.59 µs per substep in contact and 0.31 µs out of contact. `Sim.step` took 19 µs mean (14 µs median).
- Sources: LINHAC 2025 (1.29 s and 1.05 s; Kucherov 41.5 against 31.3; one-touch actions count as possessions; 31.5 and 27.3 ft/s; 0.44 and 3.35 bursts). LINHAC 2022 (pass types; the curves read 25, 34.5 and 44 ft/s for the quartiles and 62 ft/s at the 95th percentile; length median about 37-38 ft). The Stathletes counts (73.5%, 76.0% and 68.3%, 34 ft, 128 of 245, 8 of 41 against 19 of 268, 235 of 1,671 one-timers, 15 of 96 against 41 of 687, 4.8% against 8.7%). Panchuk & Vickers (70.53%, 25.68%, 2.1%, 952 and 826 ms). Polzien (Table 1). Kunde. Güldenpenning. Roczniok (Table 1). Lawrie (all speeds, loop times, excursions, 0.61 and 0.08 m/s). Every EDGE number. Valiquette's 22%, 10%, 9%, 76%, "half a second", 3% and 33%. The IIHF, Revak, Raw Charge and SI quotes. The earlier rounds' numbers.

**Corrected or retagged.**
1. The "30% against 8.5%" on royal-road passes is Chris Boyle's figure (MSG Networks, 2019), not Valiquette's. Reattributed, with a source added.
2. EDGE's "league averages" (53.2 mph, 83.6 mph, 13.0%, 19.6%) are the averages for forwards. EDGE gives a separate average for each position.
3. "Only a 20 m/s pass, shot within 0.1 s, gains anything (0.01-0.10 xG)" holds only for the one 11 m geometry tested. Shorter back-door passes at 20 m/s gain 0.14-0.22 xG. The AI's 10 m/s passes gain nothing in every geometry I tried.
4. "Kucherov's touches are short" is an inference. The paper only shows his average possession is under 1.67 s. Retagged [E].
5. The royal-road definition left out two rules the counts use: the receiving end must be in front of the goal line, and the shot must be the next event. A looser definition gives 64% completion, and 21% against 7% for the shots.
6. The 0.8-0.95 s final fixation covers goals (0.83 s) and saves (0.95 s), not saves alone.
7. "In real play that needs a backhand, a drop pass or a turn" was tagged [D]. It is a reading [E].
8. In the prototype's standing ±0.1 m case, the blade touched the puck in only 0.2% of substeps. It "held" the puck because the puck sat still, not because it stickhandled.
9. "Passes left at the blade's speed (±1%)" is true from rest only. Skating at 4 m/s, a 14 m/s sweep sent the puck off at 14.2-14.6 m/s and 7-15° off line.

Also added: Lawrie's drill was on synthetic ice, and his "blade" marker sits where the shaft meets the blade. The 59% passes-under-contact figure follows from `_defend` and `_decide` (explained inline). AI completed passes are a median 5.7 m. My controller rerun took 69-77 µs per ms, not 80-90.

**What the synthesis can lean on.**
- The code diagnosis: glued puck, pokes undone, a blade drawn 0.43 m from the puck, passes at any angle and always 10 m/s, no release under 0.16 s, passing once the defender is on him. All of it is confirmed in the code and in self-play.
- The prototype's skating stickhandle, the sweep passes and the compiled cost. Treat it as a feasibility result only: open ice, a rigid blade, no defenders, and it fails standing still and on curves.
- The NHL tracking numbers (possession length and count, pass length and speed) and the Stathletes counts.
- Panchuk & Vickers on where goalies look.

**Treat with care.**
- Pass speeds from Fig. 5b are averages over the flight, read off a curve, for completed passes only.
- The royal-road effect: Valiquette's numbers are proprietary, Boyle's are unpublished, and my recount rests on 41-43 shots with 8-9 goals.
- The head-fake numbers come from novices looking at photos. The effect is tens of milliseconds.
- The women's data are hand-tracked elite women's games, timed to 1 s.
- Lawrie is one standing drill on synthetic ice.
- Anything about Kucherov's style that comes from scouting or commentary is [V].
- The claim that seam passes don't pay off depends on pass speed and geometry. It is strongest for the AI's current 10 m/s passes.
