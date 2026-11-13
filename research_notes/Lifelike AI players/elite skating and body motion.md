# How elite players move on skates, and what makes a figure read as human

Research round "Lifelike AI players", 2026-11-13.

Topic: how high-skill players move on skates, in numbers a 50 Hz point-mass-plus-heading model can use; what makes moving line figures read as human; and how the current `threes.py` AI compares. No code or tracked file was changed. The scratch scripts and recordings are in `C:\Users\jhill\AppData\Local\Temp\claude\d5760a1e5391f178\c9432537-7115-4ab8-897a-637cb1235a5b\scratchpad\ai-round\skating\` (`record_selfplay.py`, `analyze_selfplay.py`, `powerlaw.py`, `timing.py`).

Tags: **[M]** measured in the cited study; **[D]** derived (arithmetic shown, or our own measurement of the sim); **[E]** estimate, assumptions stated; **[V]** vendor, coaching, scouting or industry talk; **[S]** secondary (read in a source that cites the primary). Facts marked "(round 2)" were read and fact-checked in `research_notes/Hockey physics feel/skating kinematics.md`; they are not repeated in detail here.

## Bottom line

1. **Elite players are slow most of the time; our AI is flat out most of the time.** Kucherov in 2023-24 averaged about **4.4 m/s while on the ice**, 42% of his 10.4 m/s top speed, and went over 20 mph (8.9 m/s) only about **2 times a game** [D, from NHL EDGE and NHL stats]. University forwards spent under 2% of their skating time above 80% of their own peak speed [D, from Gamble 2022]. *Corrected in fact-check:* that is about 27 s a game, and "under 2%" holds only against the 27-29 minutes of skating that the zone conversion implies; against 15-20 minutes of ice time it is 2-3%. Either way it is rare [D]. In the headset setting (Jon's 3.0 m/s), the AI spends **58% of live play at 98% or more of its top speed**, and its mean speed is **84%** of its top [D, self-play].
2. **The AI's acceleration is bang-bang.** Its commanded acceleration sits on the 5 m/s² cap in 40-75% of ticks and flips direction by more than 90° between ticks about **32 times per skater-minute** [D]. It makes 13-20 hard accelerations (over 2 m/s² for 0.3 s or more) per skater-minute, and as many hard brakings [D]. University players make about **2.2-3.2 hard accelerations and 2.7-4.3 hard decelerations per minute**, braking more often than pushing [M counts, D per minute, ice time assumed].
3. **Most of the robotic look comes from jumping targets and position shoves, not from the turn limit** [E]. The AI's target point jumps more than 2 m in one tick **48-63 times per skater-minute**, and separation and board clamps teleport skaters by more than 3 cm in a tick **19-75 times per skater-minute** [D]. The causes are in the code: support and carry spots that mirror when the carrier crosses the centre line, marks re-paired every 0.6 s, the chaser re-picked every tick, and `_separate`. *Corrected in fact-check:* the "centre line" here is the rink's long axis (x = 0, net to net), not the red line. And these causes are the minority: 76-81% of the jumps come in the same tick (±1) as a change of possession, which re-assigns everyone's role. Possession changed 42-52 times per game-minute in self-play, and about a quarter of those spells lasted under 0.3 s. Mirrored spots account for about 5% and marks, chaser, slot switch and nets together for 14-20% [D, `jump_causes.py`, `holder_changes.py` in the fact-check scratch folder].
4. **The AI never skates backward or square to the puck.** Its body faces its travel direction 99% of the time; it is more than 120° off only 0.2-0.4% of the time [D]. Elite national-team players skated backward about **12% of effective playing time**, and stood or glided **38-44%** [M]. Defensemen skate backward and pivot more than forwards [M]. A defender facing the play while he backs up is the single most "hockey" cue the AI lacks.
5. **Turn rates are already in the human range; the cues around turns are missing.** At 2-3 m/s the AI turns its path at up to 133°/s (99th percentile) [D]; elite players take about **1.2 s** for the turning phase of a 180° tight turn, about 150°/s [M, D]. Missing: a lean into the turn (tan(lean) = a/g), crossover legs, a sideways hockey-stop pose (real stops average 0.8-1 g, round 2), and slowing into tight curves.
6. **Few cues are needed, but they must be honest.** A static frame of 12 joint dots does not show naive viewers a person, while moving dots carry identity, actions and emotions [S]. The direction of walking is carried entirely by the motion of the feet [M]. A human figure moving with a minimum-jerk speed profile disturbed viewers' own movements; at constant speed it did not [M]. Constant speed on a curved path looks wrong [M]. Stick figures hide pose changes better than solid models [M], so for line figures the path and timing matter more than limb detail [E].
7. **The head is a cheap, strong cue.** When walking people change direction, the head turns toward the new direction about **200 ms** before the body path does, by up to about **30°** [M]. Elite junior hockey players' scans are brief (mean fixation **135 ms**; 58% of scans are a single fixation between looks at the puck) [M]. Our figures have no head yaw separate from the body.
8. **The legs churn too fast and never glide.** The figure does one push every 0.85 m whatever the speed: 3.4 pushes/s at 2.85 m/s and 6.8 at 5.8 m/s [D, `figures._stride`]. Real skaters push about 4 times a second only in the first strides of a sprint, and about 1.3-2.3 times a second at speed [M, S]. Long strides and visible glides are what make skating look like skating.
9. **Kucherov's finesse is not top speed.** He has it (23.23 mph, 91st percentile [M]), but a scout describes a slow, gliding pace in the offensive zone (*corrected in fact-check:* the "snail's pace" line is about his power-play spot) and a "serpentine inside-out route" in tight areas, and coaches teach crossovers that "change attack angles" [V]. In movement terms: low average speed, rare bursts, curved routes, the body open to the play.
10. **Procedural animation driven by honest kinematics is the right tool.** Jon's own `rig.Drive` step costs about the same as the current `_skate` (51 against 65 µs a call) [D]. Motion matching needs a motion-capture database and a skinned skeleton [V]; it buys nothing for line figures.

## 1. The movement vocabulary, in numbers

### 1.1 Speed and pace

| Measure | Value | Tag, source |
|---|---|---|
| Kucherov 2023-24: top speed | 23.23 mph = 10.38 m/s, 91st percentile | [M] NHL.com EDGE, 26 Aug 2024 |
| Kucherov 2023-24: bursts over 20 mph | 161, 90th percentile | [M] same |
| Kucherov 2023-24: total skating distance | 284.95 miles, 98th percentile | [M] same |
| Kucherov 2023-24: games, ice time | 81 GP, 21:40 a game | [M] NHL stats API |
| Kucherov: average speed on ice | 284.95 × 1609 m / 81 = 5,661 m a game; / 1,300 s = **4.36 m/s**, 0.42 of top speed | [D] |
| Kucherov: bursts per game | 161 / 81 = **2.0** a game; 5.5 per 60 min of ice time | [D] |
| University men, forwards (Gamble 2022, Table 3) | distance by % of own peak speed: 80-90% 178 m, over 90% 29 m, of 5,250 m in all | [M] |
| Same, as time | with mid-zone speeds: **1.6-1.7%** of skating time above 80% of peak, 14-15% above 60%; mean about 0.36-0.39 of peak. *Corrected in fact-check:* the mean is **0.34-0.37** of peak (3.0-3.3 m/s against the forwards' 8.8 m/s peak). The conversion implies 27-29 minutes of skating a game; if real ice time was 15-20 minutes, the share above 80% is 2-3% | [D; assumes 0.9-1.25 m/s in the slowest zone] |
| University women | about 3% of ice time at 80% or more of sprint speed, under 1% at 90% or more | [M] (round 2) |
| Elite national team, World Championship game (n = 10) | standing 16-20%, gliding 18-27%, slow forward 31-37%, slow backward 8-10%, fast forward 11-12%, forward sprint 3-7%, fast backward and sprint 2-4% of effective playing time, by period | [M] Brocherie 2018, Table 3 |
| Elite amateurs, offensive-zone sequences | 49% of the time accelerating, 41% decelerating, 10% coasting; typical change about 1.7 m/s² over about 2 s | [M, D] Dillman 1984 (round 2) |

A real game is mostly slow skating, standing and gliding, with short bursts. Kucherov's large total distance reflects nearly 22 minutes a night; one scout puts him below the 50th percentile in *average* skating distance, moving "at a snail's pace—or not skating at all" in the offensive zone [V, Vinh Cao 2025]. *Corrected in fact-check:* the scout writes that line about his spot on the power play, and his percentile is for 2024-25, not the 2023-24 EDGE season above.

### 1.2 Acceleration, first steps and braking

- Elite starts: about 3.5-4.1 m/s² averaged over the first 6.1 m; recreational adults were about **15% slower than university players over the first 10 m** but only 7% slower over the last 10 m of a 30 m sprint [M] (round 2: Greer & Dillman 1984; Buckeridge 2015). Rec players lose most in the first steps.
- Pooled men's sprints: 3.4 m/s² over 0-7 m, 2.0 over 15-25 m, 1.1-1.5 beyond 26 m [M, Stastny 2023 meta-analysis, Table 2]. High-calibre players pushed 22% harder per stride [S, Stetter, as tabulated there]. *Corrected in fact-check:* the table says "increased stride propulsion (+22%)", not force per stride.
- Game peaks: about 4.1 m/s² accelerating and 6.0 m/s² braking for university men [M, Gamble 2022]. These are 20 Hz positional-tracking values and look smoothed (round 2). *Fact-check:* the paper reports no filtering; "smoothed" is round 2's inference from other data [E].
- Hard stops: Junior B players stopped from 8.4-8.6 m/s in 0.81-0.84 s over 4.1-4.4 m, about **8-10 m/s²** [M, D] (round 2: Winchester 2007).
- Counts: university men made 43-49 accelerations and 54-65 decelerations over 2 m/s² per game (forwards, defence; Table 4) [M]. Ice time was not reported. At 15-20 minutes that is about **2.2-3.2 accelerations and 2.7-4.3 decelerations per minute** [D, ice time assumed]. Braking outnumbers pushing for both positions [M].

### 1.3 Turns

- I found **no measurement of hockey turn radius against speed**, as in round 2, and no elite-against-rec turn data beyond boot pressures (a 2006 McGill thesis). The best new number is a turn time: 26 elite players (12 men, 14 women) on a 22.86 m course with a 180° tight turn round a cone took **1.16-1.32 s** (condition means) from two-foot contact to the first push out of the turn [M, Holman 2024, Tables 8 and 10]. ("Elite" in the thesis means AAA or higher; 18 of the 26 were playing Canadian university hockey.) If the whole 180° happens then, that is about **150°/s** [D]. Men finished the course in 4.9-5.0 s and a 19.5 m sprint in 3.3 s [M].
- Physics from round 2: lateral acceleration a = v²/r = v·ω, and lean = atan(a/g). At a = 6 m/s² that is r = 1.5 m and 115°/s at 3 m/s, and r = 6 m at 6 m/s [D].
- Elite players attack on curves, not straight lines. In 1,154 NHL shootout attempts tracked by Sportlogiq, the straightest route ("down the middle") scored 27.8%; four of the five curving routes scored 30.9-32.9% and one 25.6%. The poster concludes that changing the angles on the goalie and skating to the backhand side appear to help [M, poster, no significance test]. *Corrected in fact-check:* this is a shootout, not open play, and even the "down the middle" cluster takes a slight curve. With 212 attempts its 27.8% has a standard error of about 3 points, so the 5-point gap to the best clusters is within chance [D]. Read it as "NHL shooters mostly curve", not as proof that curving scores more. Scouts and coaches say the same of open play: Kucherov's "serpentine inside-out route", and crossovers that "change attack angles" [V].

### 1.4 Stops, pivots, backward and sideways

- Backward top speed is about 0.8 of forward, and backward acceleration about half to two-thirds of forward [M, D] (round 2: Marino & Grasse 1993; Psilander 2025).
- Pivots: **no timing data found**, again. Round 2's estimate stands: the body turns 180° in about 0.3-0.6 s while the path carries on [E].
- Who does what: in five Major Junior and five university games, defencemen skated backward and pivoted more often than forwards, and there were **no differences between the two levels** [M, Lafontaine 1998]. The paper gives frequencies, not speeds or durations.
- Lateral shuffles and sideways crossovers: **no speed data found**. Round 2's estimate of at most half forward speed stands [E].

### 1.5 Glide and stride rhythm

- Start: about 4.25 strides/s over the first 6 m [M] (round 2: Greer & Dillman 1984).
- Backward at top speed: one two-stride cycle took 0.86 s and covered 5.65 m, so **2.3 strides/s and 2.8 m a stride** at 6.6 m/s [M, D] (round 2: Marino & Grasse).
- Forward at speed: about 1.6 strides/s [S, Stastny 2023, citing a skate-design study that I could not check for this number]. A McGill thesis reported 79-97 strides/min (1.3-1.6/s) at 5.6-6.4 m/s on a treadmill [S, search abstract only]. That is roughly **3.5-4 m a stride** [D]. *Corrected in fact-check:* the thesis's own figures pair 79.0, 85.2 and 96.6 strides/min with 336, 357 and 381 m/min, and give stride lengths falling from **4.4 to 4.0 m** [S, abstract via search]. "On a treadmill" [unverified]: the abstract seen does not say where it was measured.
- High-calibre players do not stride faster than low-calibre players; they have greater range and rate of joint motion, longer strides and more sideways push [M, Upjohn 2008, treadmill, self-selected speed].
- The current figure: one full cycle (two pushes) every 1.7 m [D, `figures._stride`]. That is 0.85 m a push, 2-4 times shorter than real strides at speed. *Corrected in fact-check:* against 2.8 m (backward, Marino) to 4.0-4.4 m (forward, Riby) it is **3-5 times** shorter [D]. The legs move whenever the skater moves, so it never glides.

### 1.6 Change of pace ("slow, then burst")

- **No tracking study of a carrier's change of pace was found.** The evidence is coaching and scouting [V]: "changing pace: gliding skills (inside edge holds), sliding skills (inside and outside edge slides, jab steps)" is taught as skating deception (The Coaches Site); a scout describes Kucherov's slow pace and "shiftiness" (Vinh Cao 2025); NBC Sports (2019) says he "waited just long enough" to use a defender as a screen.
- Tracking fits this: players brake more often than they push (1.2), stand or glide 38-44% of play and burst rarely (1.1) [M]. A carrier who cruises, glides, then bursts matches all of it [E].
- *When* to change pace belongs to the puck-skills and hockey-IQ notes. What it must look like: a glide (legs together, no push), then 2-4 quick short strides at about 4 m/s² (1.2) [E].

## 2. Body orientation decoupled from travel

- **Backward skating is about an eighth of elite play** (1.1). Defencemen do most of it (1.4). Coaching cues gathered in round 2's report [V]: on a rush the defender receives it rather than attacking it, keeps his stick in the pass lane and "never turns his back on a delay" (HockeyShare, Hockey Canada); in his own zone he plays D-side with his "head on swivel" and faces the puck at the net front (Hockey Canada); and one of the two most common errors is "curling away from the check" instead of stopping and starting (Revak).
- **The head leads the body.** Walking along circles, head direction anticipated changes of walking direction by **about 200 ms**, and was turned toward the inside of the curve [M, Grasso 1996, n = 5]. On a figure-eight path the maximum head deviation toward the future direction was **29.8 ± 7.4°** (left) and **30.9 ± 9.9°** (right) [M, Hicheur, Vieilledent & Berthoz 2005]. Before a 30° or 60° change of walking direction, people moved their eyes and head together to the end of the new path [M, Hollands 2002]. I found no skating study, so carrying this to skaters is an inference [E].
- **Shoulder checks.** Elite junior hockey players' fixations averaged 134.5 ms; 58.1% of scans held one fixation between "puck anchors"; scans before receiving were shorter and simpler; first fixations went mostly to space (47-53% for forwards) [M, Bespomoshchnov 2026, 16 USA Hockey NTDP players, scrimmage, mobile eye tracking]. No scan rate is given. Premier League soccer players made **0.44 scans/s** (SD 0.30) in the 10 s before receiving, fewest with an opponent within 1 m, levelling off beyond about 4 m [M, Jordet 2020]. Neither reports how long a head turn lasts. So a visible check is a quick head yaw of a few tenths of a second, a few times in 10 s off the puck, fewer under pressure [E].
- **Where to face.** A defender faces the carrier, watching his chest (Santagata, in round 2's report [V]). For a support player, I found no source; the natural reading of "open to the puck" is that he keeps chest and stick toward the carrier while he moves to his spot, sideways or on crossovers, rather than turning his back [E]. Nothing measured says how often players do either.

## 3. What makes motion read as human

### 3.1 Few cues, the right ones

- Johansson's point-light walkers used **12 lights** on the joints of an otherwise invisible body, and a single static frame is not enough for naive observers to see a human figure [S, Lange & Lappe 2006]. Biological motion carries the identity, actions, intentions and emotions of the mover, and the visual system is highly sensitive to it [S, Troje 2002, abstract].
- In scrambled point-light displays, the direction of walking, and the inversion effect, are "entirely carried by the local motion of the feet" [M, Troje & Westhoff 2006]. The authors call this a "life detector" for walking animals. For us: the feet must move like a skater's, pushing back and out against the ice, never sliding forward while the body moves.
- The dynamic part of gait carries more gender information than the body's shape [M, Troje 2002]. Style lives in motion, so each AI can have its own gait cheaply.
- Experts read honest kinematics: world-class badminton players kept their information pick-up when strokes were reduced to point lights, and against VR rugby side-steps experts read the centre-of-mass motion while novices were fooled by upper-trunk yaw and foot placement (round 2's report: Abernethy 2008, Brault 2012, [M]).

### 3.2 Smooth, curvature-linked movement

- Minimum jerk: human point-to-point arm movements are near straight, with bell-shaped speed profiles, and slow down where the path curves [M, Flash & Hogan 1985].
- Walking paths to a doorway (6 subjects, 40 targets) were stereotyped; a minimum-jerk model predicted the curved ones within about 10-13 cm at most (the most curved averaged 3.7 m long), less than the people's own variability [M, Pham et al. 2007]. Walkers slow in curves, with a speed-curvature power law whose exponent depends on the path's shape [M, Hicheur et al. 2005].
- Perception follows the same law. A dot is seen as moving at uniform speed only if its speed and curvature covary in the biological way; speed changes over 200% look uniform, and true constant speed on a curve looks "strongly nonuniform" [M, Viviani & Stucchi 1992].
- The velocity profile is what the body responds to. Watching a human make an incongruent arm movement disturbed people's own movements; a robot arm did not [M, Kilner 2003]. With human videos, only minimum-jerk movements interfered, not constant-velocity ones [M, Kilner, Hamilton & Blakemore 2007].
- Viewers notice added acceleration more readily than added deceleration, and horizontal velocity errors more than vertical [S, Reitsma & Pollard 2003, summary]. (Fact-check: the errors were added to the airborne part of human jumps, so carrying this to skating is an inference.) A skater that speeds up out of nowhere looks more wrong than one that slows too much [E].

### 3.3 Animacy and variability

- A single moving shape looks alive when its speed and direction change together. Animacy ratings depended on the size of the speed change and of the direction change, and on whether the object's long axis lined up with its travel [M, Tremoulet & Feldman 2000]. So a body that stays square to the puck should do it *for a reason* the viewer can see, such as backing up on a defender's man [E].
- Noise: 50 viewers chose among ten levels of noise added to a simulated runner's arms. The mean choice was about **17% of the largest joint's peak-to-peak swing**, preferred over none and over more [M, Bodenheimer, Shleyfman & Hodgins 1999]. The noise they tested was correlated and in phase with the movement (largest at the ends of each swing). In their informal tests, uncorrelated noise of any size "appears odd", because people do not twitch [V, the authors' observation, not a tested result]. *Corrected in fact-check:* the paper says white or sinusoidal noise "appears odd" *when its size is a significant fraction of the motion*, not at any size, and this is the authors' reasoning, not an informal test (their informal tests were of the in-phase noise). Also, the result did not generalise: for a simulated female runner (30 viewers) the choices were bimodal and gave no usable level [M].
- Clones: in crowds, appearance clones were much easier to spot than motion clones, and spotting cloned motion did not depend on the model [M, McDonnell 2008]. Five AI skaters with one shared gait are a minor problem next to the trajectory issues [E].
- Stick figures are forgiving: viewers detected three kinds of motion change better on a polygonal model than on a stick figure [M, Hodgins, O'Brien & Tumblin 1998]. Our line figures can be simple in pose; they cannot hide a jerky or impossible path [E].

## 4. The current AI, measured

Method [D]: eight 300 s self-play games (`tests/test_threes.py` `make()`, real 1 kHz puck physics, three AI a side), recording every AI tick. Four games used the default top speed (5.8 m/s) and four used `you_ms = 3.0`, which is what `game.py` sets from Jon's skate setting (AI top 2.85 m/s, carrier 2.42 m/s). Live play only, skipping 0.5 s after each drop; 106-109 skater-minutes per set. Kinematics are from positions, so they include separation shoves; commanded values are from `Player.vel`.

| Measure | AI, Jon's setting (top 2.85) | AI, default (top 5.8) | Real |
|---|---|---|---|
| Mean speed / top speed | 2.40 / 2.85 = **0.84** | 3.81 / 5.8 = 0.66 | Kucherov 0.42; university forwards 0.36-0.39 [D] (*corrected in fact-check:* 0.34-0.37) |
| Time at 90% of top or more | **63%** (58% at 98% or more) | 25% (18%) | under 1% (women); under 2% above 80% (men) (*corrected in fact-check:* 2-3% if ice time was 15-20 min) |
| Time standing (below 0.3 m/s) | 1.6% | 0.8% | standing 16-20% of play (elite) [M] |
| Body more than 120° off its travel (skating backward) | 0.37% | 0.20% | about 12% backward (elite) [M] |
| Commanded acceleration on the 5 m/s² cap | 40% of ticks | 75% | typical changes 1.7 m/s² over 2 s [D, from Dillman 1984] (tag corrected in fact-check) |
| Acceleration vector flips over 90° tick to tick, at the cap | 32.5 per skater-min | 31.7 | none expected: arm and walking movements are minimum-jerk [E] (tag corrected in fact-check; no skating measurement) |
| Jerk, 99th percentile | 490 m/s³ | 590 m/s³ | no hockey data |
| Hard speed changes (over 2 m/s² for 0.3 s or more): accelerating / braking | 12.9 / 12.7 per min | 19.9 / 19.1 | about 2.2-3.2 / 2.7-4.3 per min [D]; braking more often [M] |
| Heading rate at 2-3 m/s, p90 / p99 | 101 / 133°/s | 122 / 294°/s | about 150°/s through an elite 180° tight turn [D] |
| Tightest turns at 2-3 m/s (radius p1 / p10) | 0.91 / 1.52 m | 0.47 / 1.05 m (shoves included) | no measurement; physics says about 1.5 m at 6 m/s² and 3 m/s |
| Median speed when turning over 60°/s, against going straight | 2.18 against 2.92 m/s | 2.69 against 5.48 m/s | humans slow in curves [M] |
| Body (facing) turn rate, p99 / max | 515 / 555°/s | 501 / 555°/s | pivots 300-600°/s [E] |
| Direction reversals (over 135° within 1.2 s, from over 1.5 m/s) | 9.2 per skater-min | 8.0 | no data |
| Target jumps over 2 m in one tick | **48** per skater-min | 63 | none for a person |
| Position shoves (over 3 cm a tick beyond its velocity) | 19 per skater-min | 75 | none |
| Acceleration flips within 1.5 m of the target (hunting) | 23.8 per skater-min | 6.2 | none |
| Carrier: share of carrying time within 5% of carry top speed | 57% | 46% | no data; scouts describe slow, gliding carriers [V] |

What these numbers mean in the headset:
- The AI moves at one speed: its top. It changes speed by slamming the full 5 m/s² on and off, and its target point jumps about once a second, so it brakes and re-aims often and abruptly. That is the "robot" look, more than any turn limit.
- When it reverses, it brakes in a straight line facing forward with its legs still striding, then its body swings round at up to 555°/s [D, `_skate` facing update and measurement]. A real skater turns his body sideways for a hockey stop, or carves a tight turn.
- The shoves are tick-sized jumps where `_separate` pushes skaters apart and `keep_on_ice` or `_off_nets` clamps them. At Jon's speeds that is one about every 3 s per skater.
- Turning itself is not the problem. The shared acceleration cap already makes the AI slow somewhat in sharp turns, but in the headset setting the slope of log speed against log radius is only 0.14, against 0.32 at the default speed [D, `powerlaw.py`]. Physics at the grip limit gives 0.5; hand movements give one-third (Hicheur 2005 calls this the one-third power law) [M]. (Tag corrected in fact-check: [S]; Hicheur cites the hand result from earlier work.) I found no skating value.

CPU [D, `timing.py`]: one AI tick (targets, skating, possession, goalies) takes 0.87 ms, which at 50 Hz is 4.2% of a core. `_skate` is 65 µs a call. Jon's `rig.Drive.update` with his settings is 51 µs a call. An uncached line figure build (`figures._local_cached`) is 78 µs for 50 segments.

## 5. Animation methods, and which matter per unit of work

- **What we have is Reynolds' vehicle.** A point mass with a force cap, a speed cap and its orientation aligned with its velocity. Reynolds notes it "cannot simulate effects such as skids, spins or slides" and can turn at zero speed [V, Reynolds 1999]. That is the current `_skate`, and it explains why the AI cannot skate backward, stop sideways or pivot.
- **Motion matching** searches a motion-capture database every frame for the frame that best fits the current pose and the planned path, from 5-10 minutes of capture of a person moving around [V, Clavet 2016]. At scale the database passed half a gigabyte; learned motion matching shrank it to about 17 MB of network weights (8.5 MB at 16 bits) [V, Ubisoft La Forge 2020]. It needs skating capture we do not have and a skinned skeleton. Wrong tool for 50-segment line figures in a process sharing the GIL with the 1 kHz physics.
- **Learned controllers** need training data or a physics character, and cost far more than a numpy step per tick [E]. Round 2 found no public hockey tracking data to learn from. Not now.
- **Procedural, driven by kinematics, is enough**, because line figures hide pose detail (3.3) and trajectory carries the cues (3.1, 3.2). The cheap pieces, roughly in order of value per hour of work [E]:
  1. Steady targets (hysteresis, smoothing) and soft avoidance instead of shoves.
  2. Jon's skating model for the AI (push, glide, stop, carve, back), with pace choices instead of always top speed.
  3. A body heading separate from the travel direction, with a small state machine: forward, backward, pivot, stop, glide.
  4. A head yaw that leads turns and makes quick checks.
  5. Gait from the kinematics: stride length that grows with speed, glide pose, stop pose, backward C-cuts, crossover legs and a lean of atan(a/g) in turns.
  6. Per-skater style and small, correlated variation.
- Critically damped springs with a half-life parameter are a common cheap smoother in game animation, used for smoothing, inertialization blends and character movement: closed form, one exponential and a few multiplies [V, "Spring-It-On", theorangeduck.com 2021].

## What this means for the sim

Changes in testable order, each one at a time. Each lists the code, the cost and the self-play number that should move. The analysis scripts above can become a test in `tests/test_threes.py` that prints these numbers.

1. **Steady targets** (`Game._support`, `_carry_to`, `_defend`, `_chase`).
   - Give the "side" choice in `_support` and `_carry_to` hysteresis: switch only when the carrier is more than 1-1.5 m past the centre line, not at x = 0 [E]. (Fact-check: "centre line" means the long axis, x = 0, not the red line.)
   - In `_defend`, re-pair marks only when the new pairing is shorter by more than about 1.5 m in total [E].
   - In `_chase`, keep the current chaser unless another skater is clearly quicker (say 0.2 s) [E].
   - Then pass each target through a critically damped spring with a half-life of about 0.2-0.3 s before `_skate` [E].
   - Cost: a few floats per skater, microseconds.
   - Measure: target jumps over 2 m per skater-minute, now 48-63, should fall to near 0; acceleration flips should fall with them.
   - *Corrected in fact-check:* the three hysteresis rules above touch only about 20% of the jumps; 76-81% come with a change of possession (see Bottom line 3). Only the spring, or a short role-switch delay after a possession change (many possessions last under 0.3 s), will bring the count near 0. Count the raw target jumps before the spring and the smoothed ones after it separately [D, E].
2. **Soft avoidance instead of shoves** (`Game._separate`). Steer each skater around others he will pass within about 1 m in the next 0.5 s, as a sideways velocity request inside the skating limits. Keep the hard push only as a last resort below about 0.6 m [E]. Cost: 15 pairs a tick, numpy-cheap. Measure: shoves, now 19-75 per skater-minute, toward 0. Comfort: this also removes sudden jumps of figures close to Jon [E].
3. **Jon's skating model for the AI** (`Game._skate`; still open from round 2's item 11). Give each AI a `rig.Drive`-like step with Jon's numbers: push 6, glide 1.5, stop 8, carve 6, back 0.8. Its push is proportional within `EASE` (0.1 s) of the wanted velocity, which removes the hunting at the target, and it splits grip between turning and pushing [D, `rig.Drive._push`]. Its onset is still a step from 0 to 6 m/s², so also ramp the AI's push up over about 0.15-0.2 s, a jerk limit [E]. Cost: about the same as now, 51 against 65 µs a call [D]. Measure: acceleration flips at the cap toward 0, jerk p99 well under 100 m/s³ [E target], braking bouts more common than pushing ones.
4. **Pace, not top speed** (`_skate` and `_targets`). Let each target carry a wanted speed [E]: cruise at about 0.5-0.6 of the AI's top when supporting, holding or gapping; burst to the top only on triggers (a loose-puck race, a lead pass, a carrier beating his man); let carriers glide, then burst (the puck-skills note decides when).
   - Real elite mean speed is 0.4 of top (1.1). As a starting design [E], tie the AI's top to Jon's sprint (0.95 × 4.5 m/s) and its cruise to about his cruise (2-3 m/s), so its average stays at or below his while bursts show. Today `game.py` caps it at 0.95 × his cruise (2.85 m/s), so it can never burst.
   - Measure: time at 90% of top or more, now 63%, toward under 5%; mean / top, now 0.84, toward 0.4-0.55; standing or gliding toward 20-40%.
   - Comfort: AI speed does not move Jon's view, but fast skaters crossing close in front fill it; keep bursts from aiming within about 1.5 m of his head [E].
5. **Body heading and a five-state machine** (new `Player.body` beside `facing`; `figures.skater` draws `body`). States [E]:
   - FORWARD: body along travel. GLIDE: no push, legs together.
   - BACKWARD: when the wanted facing (his man, the puck) is more than about 120° from travel; top 0.8 and push about half (1.4). For defenders with their man in front, and the trailing support player.
   - PIVOT: body turns 180° at 400-600°/s while travel carries on.
   - STOP: when the wanted direction is more than about 120° from travel above about 1.5 m/s: body 90° to travel, braking at 8 m/s², then push the new way. This replaces today's straight-line reversal (9 a minute) and avoids the "curling" coaches criticise (2).
   - Hold each state at least about 0.3 s so it cannot flicker.
   - Cost: a few branches per skater per tick. Measure: time skating backward toward 8-15% (defenders more); body turn rate p99 under about 600°/s.
6. **Head yaw** (new `Player.head`, drawn as a short visor or nose line on the head rings).
   - The head leads a turn by about 0.2 s and up to about 30° (2).
   - Off the puck, a quick check of 30-90° toward an open-space sector for about 0.3-0.5 s, every 2-4 s; fewer within about 1-4 m of an opponent [E, from 2].
   - The puck-IQ note can drive where it looks; this note only says it must be visible and brief.
   - Cost: trivial.
7. **Gait from the kinematics** (`figures._stride`, `_local_cached`, `_feet`).
   - Stride length that grows with speed: about 1.5-2 m a push at 2-3 m/s, 3-4 m at 5-6 m/s; short and quick only when accelerating hard [E, from 1.5].
   - Legs together while gliding or braking.
   - Stop pose, backward C-cuts, crossover legs when the lateral acceleration passes about 2 m/s².
   - A roll of atan(a_lat/g) into turns: about 31° at 6 m/s² [D].
   - Keep the feet pushing back and out against the ice, never sliding forward (3.1).
   - Cost: lean, mode and head angle multiply the cache keys; raise the `lru_cache` size or build uncached (78 µs each; 5 figures at 72 Hz is about 2.8% of a core uncached) [D].
8. **Style and variation** (per-`Player` parameters set at creation).
   - Top speed and stride length within about ±5-10% [E], each player's own lean and head-check rate.
   - Slow, in-phase noise of about 15-17% of a swing's size on the arms and stick (3.3), never white jitter.
   - Cost: trivial. Lowest priority (3.3).

**A/B tests in the headset**, one at a time, short sessions: (1)+(2) against now; then (3); then (4) at two cruise levels; then (5); then (6)+(7) together, since they are both drawing. Ask Jon one question each time: did they look like people?

**Comfort.** None of this moves Jon's viewpoint. The risks are things filling his view near him: a burst or a stop within about 1.5 m, a figure spinning at 500°/s right in front of him, or a figure jumping sideways when it is shoved [E]. Items 1, 2 and 5 reduce those. The AI already goes round Jon rather than pushing him (`_separate`); keep that. *Corrected in fact-check:* `_separate` keeps Jon from being pushed, but it does it by snapping the AI figure to 0.9 m from him in one tick. That snap is the sideways jump close to his face that item 2 should replace with steering. Body contact from AI checking is not proposed here.

## Open questions

1. **No hockey measurement of turn radius against speed, pivot time, lateral shuffle speed or crossover timing** was found, in this round or round 2. Holman's turn time (1.2 s for a 180° tight turn) is the closest. A phone video of Jon's own games from the stands, using faceoff circles (4.57 m radius) as the scale, would give rec numbers. Public NHL tracking has no x-y positions.
2. **No tracking study of change of pace by puck carriers.** All of it is coaching and scouting [V].
3. **Scan rate in hockey** is unpublished. The 2026 NTDP study gives fixation durations, not scans per second.
4. **Will cruising AI look too slow next to Jon?** The real ratio (mean 0.4 of top) may feel sleepy if the AI's top stays near Jon's 3 m/s cruise. That is what A/B test 4 is for.
5. **Is the speed-curvature law the same on skates?** It holds for hands and walking; a skater's lean and edges may give a different exponent. Unmeasured.
6. **How much does each fix add to "real people" for Jon?** The perception studies were on screens, not in VR, and none used hockey. His A/B answers are the real test.
7. **Gamble's counts** have no stated minimum duration or ice time, so the per-minute comparison is good to about a factor of 1.5 [E].

## Sources

Hockey skating and tracking
- NHL.com, "NHL EDGE stats for Tampa Bay Lightning" (32 in 32), 26 Aug 2024 (Kucherov 2023-24 top speed, bursts, distance): https://www.nhl.com/news/topic/32-in-32/nhl-edge-stats-for-tampa-bay-lightning-32-in-32
- NHL stats API, Kucherov player landing (2023-24: 81 GP, 144 P, 21:40 TOI): https://api-web.nhle.com/v1/player/8476453/landing
- Gamble et al. 2022, Front Physiol 13:831723, university men and women, 20 Hz positional tracking, Tables 2-4: https://pmc.ncbi.nlm.nih.gov/articles/PMC8914021/
- Brocherie, Girard & Millet 2018, Biol Sport 35(3):261-267, 10 elite national-team players, one World Championship game, Table 3: https://pmc.ncbi.nlm.nih.gov/articles/PMC6224850
- Lafontaine, Lamontagne & Lockwood 1998, ISBS, time-motion analysis of skills, Major Junior and university games: https://ojs.ub.uni-konstanz.de/cpa/article/view/1232 (PDF https://ojs.ub.uni-konstanz.de/cpa/article/view/1232/1119)
- Holman 2024, MSc thesis, McGill, "A biomechanical analysis of ice hockey skate blade design", 26 elite players, Tables 6, 8, 10: https://mcgill.scholaris.ca/items/8a38a945-2621-412c-90bf-270d77bfc6e3
- McGill thesis on skate boot pressure of elite and recreational players in tight turns (2006), abstract via search: https://www.mcgill.ca/ihrg/students/alumni-and-theses
- Upjohn, Turcotte, Pearsall & Loh 2008, Sports Biomech 7(2):206-221: https://pubmed.ncbi.nlm.nih.gov/18610773/
- Stastny et al. 2023, Biol Sport 40(3):899-918, sprint meta-analysis, Table 2: https://www.termedia.pl/Testing-distance-characteristics-and-reference-values-for-ice-hockey-straight-sprint-speed-and-acceleration-A-systematic-review-and-meta-analyses-,78,48807,1,1.html
- Riby, "Skating Economy of Ice Hockey Players", McGill MA thesis, stride rates (search abstract only): https://escholarship.mcgill.ca/downloads/47429c713
- Czuzoj-Shulman 2019, "The paths we take: a player tracking analysis of NHL shootouts", NESSIS poster, 1,154 attempts: https://www.nessis.org/nessis19/Nick-Czuzoj-Shulman-poster.pdf
- Round 2 notes (Greer & Dillman 1984, Dillman 1984, Buckeridge 2015, Marino & Grasse 1993, Psilander 2025, Winchester 2007, Gamble 2024, Kimura & Yokozawa 2024, with their URLs and fact-check): `research_notes/Hockey physics feel/skating kinematics.md`
- Round 2 report, believable opponents, gap control, D-side, Brault 2012, Abernethy 2008: `reports/VR hockey sense training.md`. The coaching cues quoted from it come from Hockey Canada, *Developing Skilled Defencemen* (https://cdn.hockeycanada.ca/hockey-canada/Hockey-Programs/Players/Downloads/2018/2018-19-developing-hockey-defencemen-e.pdf), HockeyShare, "2 on 1 Dissected" (https://www.hockeyshare.com/blog/2-on-1-dissected-part-2), Revak (https://hockeysarsenal.substack.com/p/two-most-common-defensive-errors) and Santagata (https://lbxhockey.substack.com/p/how-to-play-a-1-v-1-defensemen) [V]; I read them through the report, not again.

Scouting and coaching [V]
- Vinh Cao, "2024-25 Season Spotlight: Nikita Kucherov", Virtual Hockey Scout, 17 Apr 2025: https://virtualhockeyscout.substack.com/p/2024-25-season-spotlight-nikita-kucherov
- Sean Leahy, "Nikita Kucherov is a master of deception", NBC Sports, 20 Mar 2019: https://www.nbcsports.com/nhl/news/wednesday-night-hockey-nikita-kucherov-is-a-master-of-deception
- TCS+, "Adding deception with scissor push / linear crossover manipulation", The Coaches Site (preview): https://members.thecoachessite.com/article/adding-deception-with-scissor-push-linear-crossover-manipulation

Gaze and head
- Bespomoshchnov, Lemoyne, Jordet & Vater 2026, J Sports Sci, scanning in junior elite ice hockey: https://doi.org/10.1080/02640414.2026.2744018 (abstract https://pubmed.ncbi.nlm.nih.gov/42860766/)
- Jordet et al. 2020, Front Psychol, scanning in Premier League soccer: https://pmc.ncbi.nlm.nih.gov/articles/PMC7573254
- Grasso, Glasauer, Takei & Berthoz 1996, NeuroReport 7(6):1170-1174: https://pubmed.ncbi.nlm.nih.gov/8817526/
- Hicheur, Vieilledent & Berthoz 2005, Neurosci Lett 383:87-92 (head on a figure-eight path): https://pubmed.ncbi.nlm.nih.gov/15936517/
- Hollands, Patla & Vickers 2002, Exp Brain Res 143:221-230: https://pubmed.ncbi.nlm.nih.gov/11880898/

Perception of motion
- Lange & Lappe 2006, J Neurosci 26(11):2894-2906 (describes Johansson 1973): https://pmc.ncbi.nlm.nih.gov/articles/PMC6673973
- Troje & Westhoff 2006, Curr Biol 16(8):821-824: https://pubmed.ncbi.nlm.nih.gov/16631591/
- Troje 2002, J Vis 2(5):371-387: https://pubmed.ncbi.nlm.nih.gov/12678652/
- Flash & Hogan 1985, J Neurosci 5(7):1688-1703: https://pubmed.ncbi.nlm.nih.gov/4020415/
- Pham, Hicheur, Arechavaleta, Laumond & Berthoz 2007, Eur J Neurosci 26(8):2391-2403 (preprint): https://personal.ntu.edu.sg/cuong/docs/locotraj-smoothness-cur.pdf
- Hicheur, Vieilledent, Richardson, Flash & Berthoz 2005, Exp Brain Res 162:145-154: https://pubmed.ncbi.nlm.nih.gov/15586276/
- Viviani & Stucchi 1992, J Exp Psychol Hum Percept Perform 18(3):603-623: https://pubmed.ncbi.nlm.nih.gov/1500865/
- Kilner, Paulignan & Blakemore 2003, Curr Biol 13(6):522-525: https://pubmed.ncbi.nlm.nih.gov/12646137/
- Kilner, Hamilton & Blakemore 2007, Soc Neurosci 2(3-4):158-166: https://pubmed.ncbi.nlm.nih.gov/18633814/
- Reitsma & Pollard 2003, ACM TOG 22(3):537-542 (summary): https://ri.cmu.edu/?p=8709
- Tremoulet & Feldman 2000, Perception 29(8):943-951: https://pubmed.ncbi.nlm.nih.gov/11145086/
- Bodenheimer, Shleyfman & Hodgins 1999, Computer Animation and Simulation '99, 53-63, Table 2: https://eecs.vuse.vanderbilt.edu/People/bobbyb/pubs/variability99.pdf
- McDonnell, Larkin, Dobbyn, Collins & O'Sullivan 2008, "Clone attack!", ACM TOG 27(3): https://history.siggraph.org/?p=112831
- Hodgins, O'Brien & Tumblin 1998, IEEE TVCG 4(4):307-316: https://www.sciweavers.org/publications/perception-human-motion-different-geometric-models

Animation methods [V]
- Reynolds 1999, "Steering Behaviors For Autonomous Characters", GDC: https://www.red3d.com/cwr/steer/gdc99/
- Clavet 2016, "Motion Matching and The Road to Next-Gen Animation", GDC: https://www.gdcvault.com/play/1022985/Motion-Matching-and-The-Road
- Ubisoft La Forge 2020, "Introducing Learned Motion Matching": https://www.ubisoft.com/en-us/studio/laforge/news/6xXL85Q3bF2vEj76xmnmIu/introducing-learned-motion-matching
- "Spring-It-On: The Game Developer's Spring-Roll-Call", theorangeduck.com, 2021 (page dated 04/03/2021): https://theorangeduck.com/page/spring-roll-call

## Fact-check

Fact-check of this note, 2026-11-13. I listed about 160 load-bearing claims (numbers, attributions, code statements, self-play measurements and arithmetic) and checked each one again. I read the sources again myself: full texts or tables for Gamble 2022 (Frontiers page), Brocherie 2018 (Europe PMC XML, Table 3), Holman 2024 (Tables 6, 8, 10 and the turn-time definition), Lafontaine 1998, the Sportlogiq shootout poster, Bodenheimer 1999, Pham 2007 and Lange & Lappe 2006 (PMC page). I read abstracts (through Europe PMC) for Troje & Westhoff, Troje 2002, Grasso, Hicheur 2005 (both papers), Hollands, Flash & Hogan, Viviani & Stucchi, Kilner 2003 and 2007, Tremoulet & Feldman, Upjohn and Bespomoshchnov, and the relevant passages for Jordet 2020, Stastny 2023 (Table 2 and its stride-rate citation), NHL EDGE, the NHL stats API, Vinh Cao, NBC Sports, The Coaches Site, Reynolds, Clavet, Ubisoft La Forge, Spring-It-On and McDonnell. Reitsma & Pollard and Riby were checked through search summaries only. Round 2 facts were checked against `research_notes/Hockey physics feel/skating kinematics.md` (including its fact-check table) and `reports/VR hockey sense training.md`. The code claims were checked against `threes.py`, `figures.py`, `rig.py`, `game.py` and `sandbox_settings.json`. Scratch scripts and outputs are in `C:\Users\jhill\AppData\Local\Temp\claude\d5760a1e5391f178\c9432537-7115-4ab8-897a-637cb1235a5b\scratchpad\ai-round\factcheck-skating\`.

**Confirmed (about 143 claims).**
- Kucherov: 23.23 mph (91st percentile), 161 bursts (90th), 284.95 miles (98th), 26 Aug 2024; 81 GP, 144 P, 21:40. The arithmetic (5,661 m a game, 4.36 m/s, 0.42 of top, 2.0 bursts a game, 5.5 per 60 minutes) is right.
- Gamble 2022: forwards 178 m at 80-90% and 29 m above 90% of 5,250 m; 43.3-48.5 accelerations and 53.7-65.2 decelerations over 2 m/s² (Table 4); peaks 4.11 and −6.09 m/s² for forwards. The per-minute conversion is right for 15-20 minutes. The paper gives no ice time and no minimum duration for an event.
- Brocherie 2018 Table 3, all seven categories by period; standing plus gliding 38-44%; backward 12.0-12.2% in each period.
- Holman 2024: 26 players (12 men, 14 women), turn times 1.16-1.32 s, 22.86 m course, men 4.91-5.02 s and 3.29-3.30 s.
- Stastny Table 2 (3.43, 2.03, 1.07-1.51 m/s²) and the 1.6 strides/s line, cited there to Robert-Lachaine 2012. Lafontaine, Upjohn, Bespomoshchnov (16 NTDP players, 134.52 ms, 58.1%, 47-53%), Jordet (0.44 ± 0.30 scans/s; the 1 m and 4 m pressure pattern), Grasso (n = 5, about 200 ms, inside of the curve), Hicheur 2005 (29.75 ± 7.41° and 30.86 ± 9.92°), Hollands, Lange & Lappe (12 lights; one static frame is not enough), Troje & Westhoff ("entirely carried by the local motion of the feet"), Troje 2002, Flash & Hogan, Pham (6 subjects, 40 targets, 10.3-12.7 cm, 3.7 m), Hicheur EBR, Viviani & Stucchi, both Kilner papers, Tremoulet & Feldman, McDonnell, Hodgins, Reynolds, Clavet ("5 or 10 minutes"), Ubisoft (590 MB, 17 MB, 8.5 MB at 16 bits) and Spring-It-On: all as stated.
- Vinh Cao's "serpentine inside-out route" is about Kucherov (Point is "the former"), and "below the 50th percentile in average skating distance" and "shiftiness" are as quoted. NBC's "waited just long enough" and The Coaches Site's two quotes are as quoted.
- Round 2 facts (Greer & Dillman, Buckeridge, Winchester, Marino & Grasse, Psilander, Dillman 1984, Gamble 2024, the pivot and sideways estimates) and the coaching cues from the round 2 report all match those files.
- Code: ACCEL 5, VMAX 5.8, YOU_FRAC 0.95, CARRY 0.85, SKATER_GAP 0.9; `vmax` = 2.85 m/s and the carrier 2.42 m/s when `game.py` sets `you_ms` from the skate setting (3.0); `_defend` re-pairs every 0.6 s; `_chase` re-picks every tick; `_support` and `_carry_to` mirror at x = 0; the facing ease (8/s) gives at most about 11° a tick (about 550°/s); `figures._stride` is one cycle per 1.7 m with legs moving whenever the skater moves; no separate head yaw; 50 segments with the ring; `lru_cache(512)`. `rig.Drive._push` is proportional within EASE = 0.1 s, splits grip between turning and pushing, and steps straight to the push rate. Jon's saved settings are push 6, glide 1.5, stop 8, carve 6, back 0.8, sprint 4.5. Round 2's item 11 is still open.
- Self-play: re-running `analyze_selfplay.py` and `powerlaw.py` on the eight recordings reproduces every number in section 4's table. A fresh 300 s game at each speed (seed 9) agrees within seed-to-seed spread. At Jon's setting it gave mean 0.84 of top, 57% commanded at 98% of top or more, 40% of ticks on the cap, 28 cap flips, 14.0 and 13.7 hard bouts, heading p90/p99 at 2-3 m/s of 101/135°/s, 0.39% backward, 50 target jumps, 26 shoves and 15 hunting flips per skater-minute, and a slope of 0.14. The shove and hunting counts vary most between games.
- CPU: AI tick 0.88-0.90 ms (4.3-4.4% of a core), `_skate` 65-68 µs, `rig.Drive.update` 55-56 µs, an uncached figure 59 µs (78 µs in the note; machine noise, same order).
- Arithmetic: 3.4 and 6.8 pushes/s, 150°/s, r = 1.5 m and 115°/s at 3 m/s, r = 6 m at 6 m/s, 31° of lean at 6 m/s², 15 pairs, 2.8% of a core for 5 figures.

**Corrected (16).**
1. Gamble mean speed: 0.34-0.37 of peak, not 0.36-0.39 (my arithmetic with the same 0.9-1.25 m/s slow-zone speed and mid-zone speeds; peak 8.8 m/s).
2. Gamble share above 80%: "under 2%" depends on the 27-29 minutes of skating that the zone conversion implies; against 15-20 minutes it is 2-3%. Rare either way.
3. Target-jump causes. This is the most important correction. 76-81% of the jumps come within a tick of a change of possession, which happens 42-52 times per game-minute in self-play, often in spells under 0.3 s. The causes the note named (mirrored spots, mark re-pairing, chaser re-picks, slot switch, nets) account for only about 20%. Item 1's hysteresis rules alone will not take the count to near 0; the spring or a role-switch delay will.
4. "Centre line" means the long axis (x = 0), not the red line.
5. Vinh Cao's "snail's pace" is about Kucherov's power-play spot, and his percentile is for 2024-25.
6. Stetter's +22% is "stride propulsion", not force per stride.
7. Riby's stride length is 4.0-4.4 m (his own figures), not 3.5-4 m. So the figure's 0.85 m push is 3-5 times shorter than real strides, not 2-4.
8. Bodenheimer: uncorrelated noise "appears odd" only when it is large, and that is the authors' reasoning, not an informal test. The 17% did not hold for their female runner.
9. Shootout routes: the note's "elite players attack on curves" overstated the poster. The gap is within chance (standard error about 3 points), and every cluster curves a little.
10. Comfort: `_separate` does not steer the AI round Jon; it snaps the AI figure to 0.9 m from him in one tick.
11-16. Tags: Dillman's 1.7 m/s² is [D], not [M]; "humans are minimum-jerk" for skaters is [E]; the hand one-third law is [S]; "smoothed" Gamble peaks are round 2's inference; Reitsma & Pollard's errors were in jumps; the "most of the robotic look" judgement is [E].

**Unverified (1).** Riby "on a treadmill": the abstract seen does not say. The stride rates themselves are confirmed.

**Small biases to know about.** The AI actually ticks about every 20.5 ms (2,919 ticks per 60 s), not 20 ms, because the 1 ms clock rounds up. The analysis counts skater-minutes as ticks × 0.02 s, so every per-minute rate in section 4 is about 3% high. That changes no conclusion. The self-play has 6 AI and no Jon; the headset has 5 AI and Jon, so shove counts there will differ. The AI's "hard bouts" need 0.3 s above 2 m/s², while Gamble's counts have no minimum duration. Without the duration rule the AI makes 28-38 a minute, so the gap to real players is, if anything, larger than the note says.

**What to lean on.** The self-play measurements (reproduced, and a fresh seed agrees); the code statements; the speed and pace picture (Kucherov EDGE arithmetic, Brocherie, Gamble with the corrections); Holman's turn time; the head-lead numbers for walking; the perception results (Troje & Westhoff, Kilner, Viviani, Flash & Hogan, Pham, Hodgins); and the CPU costs.

**Treat with care.** Everything about skating that was carried over from walking or arm studies (head lead, the speed-curvature law, minimum jerk) is inference. Forward stride rate at speed rests on two secondary sources. The pace-change and "inside-out route" evidence is scouting and coaching only. The shootout poster does not show that curving scores more. The per-minute acceleration comparison with Gamble is good only to about a factor of 1.5 in either direction. For the sim, the biggest practical change is that steadying targets must handle possession changes, not just the mirrored spots.
