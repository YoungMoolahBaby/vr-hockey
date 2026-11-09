# Skating kinematics: numbers for a thumbstick locomotion model

Topic: how hockey players actually skate (speeds, acceleration, glide, stops, turns), turned into a locomotion model the thumbsticks in `rig.py` can drive, plus the AI skaters in `threes.py`. No code was changed.

How to read the tags:
- **[M]** measured in the cited study.
- **[D]** derived by me from measured numbers, with the arithmetic or assumption given.
- **[E]** estimate or physics with stated assumptions; no direct measurement found.
- **[S]** secondary source (blog, summary or citing paper), not the primary study.

## Bottom line

- **Top speed.** A recreational adult sprints to about **8 m/s**. NHL forwards top out around **9.8 m/s** (22 mph), and the fastest reach about **11 m/s**. But game play is mostly slow. University players spend about half their ice time under 3 m/s and only about 5% above 6.7 m/s. Elite amateurs averaged **3.8-4.2 m/s** while play was on.
- **Acceleration.** The best data are 30 m sprints with split times. From standstill a rec adult reaches 3 m/s in about 0.55 s and 90% of top speed in about 3 s (about 15 m). The mean acceleration over the first 6 m is **3.5-4.1 m/s²**. Peak accelerations measured in games are about **4 m/s²**.
- **Glide.** Hockey blades are almost frictionless (μ ≈ 0.007). A coasting skater loses only about **0.1 m/s² at 3 m/s** and 0.25-0.35 m/s² at 8 m/s, so a glide from 3 m/s carries about 50 m. Real players almost never coast for long: they accelerate or brake actively.
- **Stopping.** Peak decelerations measured in games are about **5.5-6 m/s²**, which is a hard hockey stop. That stops you from 3 m/s in about 0.9 m.
- **Turning.** Turning is limited by lateral acceleration, a = v·ω = v²/r, and the skater leans by atan(a/g). Elite long-track skaters were measured holding 5.3-6.3 m/s² on curves at about 30° of lean. I found no direct measurement of hockey tight turns. My estimate is 4-6 m/s² sustained for a rec player and up to 8-10 m/s² briefly for elite players. So the maximum heading rate falls as 1/speed: about 105°/s at 3 m/s, 53°/s at 6 m/s and 39°/s at 8 m/s (for a = 5.5).
- **What the current rig gets wrong.** The time it takes to reach 3 m/s, and to stop from it, is about right. What is not hockey is everything else:
  - the onset of acceleration is front-loaded (20 m/s² at the first instant);
  - letting go of the stick is a 20 m/s² stop, with no glide;
  - looking somewhere else re-aims your velocity at up to about 28 m/s² (2.9 g), which no skater can do;
  - strafing is as fast as forwards.
  A model with momentum and bounded accelerations fixes these. It probably also removes the large visual accelerations that may be what made 4 m/s feel too fast. That last point is a hypothesis to A/B test.

---

## 1. Speeds

### 1.1 Top forward speed

| Level | Top speed | Source |
|---|---|---|
| NHL, record | 24.82 mph = **11.1 m/s** (Miles Wood, 2024-25, said to be the fastest NHL EDGE has tracked) | [S] [Rezztek blog](https://rezztek.com/blogs/news/so-fast-so-good-fastest-nhl-skaters-these-names-will-shock-you) |
| NHL, season leaders | 24.32 mph = 10.9 m/s (Poehling); McDavid 24.16 mph, 2022-23 | [M] [NHL.com, EDGE launch](https://www.nhl.com/news/nhl-edge-launches-website-for-puck-and-player-tracking-data) |
| NHL forwards, typical season top speed | median slightly over **22 mph = 9.8 m/s**; middle 80% 21-23 mph (9.4-10.3 m/s). Defensemen: median slightly under 22 mph | [S], NHL EDGE data analysed by [Puck Over the Glass](https://puckovertheglass.substack.com/p/nhl-edge-skating-speed-part-1) |
| NHL "burst" | starts above 18 mph (8.0 m/s) and ends below 16 mph (7.2 m/s) | [S] [PenguinPoop](https://penguinpoop.com/2024/penguins-update-how-important-is-speed/) |
| University men, game peak (tracking at 20 Hz) | 31.16 ± 1.64 km/h = **8.66 m/s** (forwards 8.8, defense 8.4) | [M] [Gamble et al. 2022, Front Physiol 13:831723](https://pmc.ncbi.nlm.nih.gov/articles/PMC8914021/) |
| University women, game peak | 28.73 km/h = 7.98 m/s (2022). In 2024: 29.5 km/h in games against 28.3 km/h in straight-line sprints | [M] Gamble 2022 (above); [M] [Gamble et al. 2024, IJSPP 19(5):496](https://lida.sport-iat.de/twm/Record/4087606?lng=en) |
| High-calibre, on-ice 30 m sprint | men **8.96 ± 0.44 m/s**, women 8.02 ± 0.36 m/s | [M] [Budarick et al. 2020, Sports Biomech 19(5):601](https://lida.sport-iat.de/svd/Record/4064418?lng=en) |
| **Recreational adults** (n = 9, age 36.9 ± 5.3, 86 kg) | 30 m in 4.95 s; 0-10 m in 2.26 s; **20-30 m in 1.23 s, an average of 8.1 m/s** over the last 10 m [D]. University players (n = 9): 4.42 / 1.93 / 1.14 s, so 8.8 m/s | [M] [Buckeridge et al. 2015, PLoS ONE 10(5):e0127324, Table 2](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0127324) |
| Skilled 18-22 y (1993) | 8.03 m/s forward | [M] [Marino & Grasse 1993, ISBS](https://ojs.ub.uni-konstanz.de/cpa/article/view/1699) |

Recreational players were **12% slower** over 30 m than university players, **15% slower** over the first 10 m and **7% slower** over the last 10 m (Buckeridge 2015). So rec players lose most to better players in the start, not in top speed.

### 1.2 Backward speed

- Ten skilled players (18-22 y) skated backward with C-cuts at **6.57 m/s**, against 8.03 m/s forward: **82%**. Their cycle (two strides) took 0.86 s and covered 5.65 m. [M] [Marino & Grasse 1993](https://ojs.ub.uni-konstanz.de/cpa/article/view/1699/1601)
- Seven university players: forward 10.1 ± 1.9 m/s, backward 8.2 ± 0.2 m/s (2D video at 60 Hz), which is **81%**. The absolute values look high for a university sample, so trust the ratio more than the numbers. [M] [Wu, Pearsall, Russell & Imanaka 2015, ISBS](https://ojs.ub.uni-konstanz.de/cpa/article/view/6664)
- **Backward acceleration is slow.** In 20 high-calibre Swedish players, backward C-cuts averaged only 2.4 m/s over 0-5 m, 5.8 m/s over 15-20 m and 6.7-6.8 m/s over 35-40 m, and they were still speeding up at 40 m. [M] [Psilander, Arndt & Petré 2025, Footwear Science](https://lida.sport-iat.de/twm/Record/4095112?lng=de). For comparison, a forward rec sprinter covers the first 5 m in about 1.5 s [D, fit below], against about 2.1 s backward for these high-calibre players [D: 5 m / 2.4 m/s]. Backward acceleration is roughly **half to two-thirds** of forward [D].

### 1.3 Speeds during play ("cruising")

- **Elite US amateurs (1982 National Sports Festival games).** Twenty-two players were filmed in 3D for 13.5 s each in the offensive zone. Mean speed was **4.21 m/s**, the mean peak within a sequence 5.01 m/s, and the mean low 1.62 m/s. Players spent 49% of the time accelerating, 41% decelerating and only **10% coasting**. Each 13.5 s held about 3.4 accelerations and 3.2 decelerations of about 2.0 s each. [M] [Dillman, Stockholm & Greer 1984, "Movement of ice hockey players", ISBS](https://ojs.ub.uni-konstanz.de/cpa/article/view/1410)
  - Derived: a typical speed change in play is (5.0 − 1.6) m/s over 2 s, which is about **1.7 m/s²** [D].
- **Green et al. 1976.** Average skating speed in games was 3.78 m/s (as cited by Dillman 1984; I did not read the original). [S]
- **University men (Gamble 2022).** I converted the distance skated in each speed zone into time, using the middle of each zone's speed band [D]. For forwards, about **49% of the time was under 3.0 m/s**, 12% at 3.0-3.9, 12% at 3.9-4.7, 15% at 4.7-5.8, 7% at 5.8-6.7 and only **5% above 6.7 m/s**. Defensemen spent 58% of the time under 3 m/s and 2% above 6.7 m/s. The time-weighted mean speed is about 3.3 m/s for forwards and 2.9 m/s for defensemen. The weak point is the assumed speed inside the 1-10.9 km/h zone (I used 6 km/h).
- **University women.** They spent about 3% of their ice time at or above 80% of sprint speed and **under 1% at or above 90%**. [M] Gamble 2024
- **NHL.** McDavid skated 309.43 miles (498 km) in 2022-23 [M, NHL.com]. If he played about 22 min a game over 82 games, his average on-ice speed was about 4.5 m/s [D; I assumed the ice time and did not check it]. Low confidence.

**Takeaway.** Jon's 3 m/s top speed covers about the slowest half of real game time. A rec adult's game mostly runs at 2-5 m/s, with short bursts toward 7-8 m/s.

## 2. Acceleration

### 2.1 Measured starts

- **US National Team, 1983 (n = 11)**, standing start, first 20 ft (6.1 m) filmed: 1.53 s to 6.1 m, 6.71 m/s at 6.1 m, mean acceleration over the 6.1 m **4.13 m/s²**, stride rate 4.25/s.
- **1983 National Sports Festival players (n = 69):** 1.52 s, 6.25 m/s and **3.53 m/s²**.
- Marino's mixed-ability sample: the criterion set at one SD better than its mean was 1.80 s to 6.1 m, so the average skater in that sample was slower than 1.8 s.
- All three: [M] [Greer & Dillman 1984, ISBS](https://ojs.ub.uni-konstanz.de/cpa/article/view/1412)
- Budarick 2020: men accelerated harder in the first steps, but after that men and women gained speed stride by stride at similar rates. [M, abstract]

### 2.2 A fitted speed curve

I fitted v(t) = Vmax(1 − e^(−t/τ)) to the Buckeridge 2015 splits (10 m time, and the speed over the last 10 m) [D]:

| | Vmax | τ | 3 m/s at | 1 s gives | 90% of Vmax at | over | 6.1 m in | speed at 6.1 m |
|---|---|---|---|---|---|---|---|---|
| Rec adults | 8.1-8.5 m/s | 1.2-1.3 s | 0.56 s | 4.5 m/s | 2.8-3.0 s | 14-16 m | 1.66 s | 6.0 m/s |
| University players | 8.8-9.1 m/s | 0.9-1.0 s | 0.37 s | 5.9 m/s | 2.1-2.2 s | 11-12 m | 1.40 s | 7.0 m/s |

Checks on the fit:
- The predicted 30 m times are 0.06-0.2 s faster than measured, which is the reaction and first-step delay that an exponential leaves out.
- An exponential begins at its maximum acceleration, Vmax/τ ≈ 6.5 m/s² (rec) or 9.5 m/s² (university), and that overstates the first instant.
- The mean acceleration over 6.1 m from the rec fit is 6.0/1.66 ≈ 3.6 m/s², which agrees with Greer & Dillman's 3.5-4.1 m/s².

### 2.3 The first 2-3 strides

- Stride rate at the start is about 4 strides/s (Greer & Dillman). So the first three strides take about 0.75 s [D], and after them a rec skater is at about **3.6-3.8 m/s** having covered about 1.5 m [D, from the fit].

### 2.4 Acceleration in games

- Peak game accelerations (20 Hz tracking, smoothed) were **4.06 ± 0.43 m/s²** for university men and 3.67 for university women (Gamble 2022).
- Female university players reached 4.39 m/s² in games against only 3.34 m/s² in straight-line sprint tests. Flying starts and crossovers help (Gamble 2024).
- University men made about 45 accelerations above 2 m/s² per game (Gamble 2022).
- A typical in-play acceleration is about 1.7 m/s² for about 2 s (Dillman 1984, [D]).

## 3. Gliding (coasting)

- **Blade friction.** Standard hockey blades measured **μ = 0.0071 ± 0.0005**, from how fast a sled on three blades (53 kg each) slowed from 1.8 m/s. Flared blades were 13-22% lower, and μ fell as the load rose. [M] [Federolf, Mills & Nigg 2008, J Sports Sci 26(11):1201](https://lida.sport-iat.de/ta/Record/4014976), summarised by [Sci-Sport](https://sci-sport.com/en/friction-in-ice-hockey-comparison-of-different-models-of-skate-blades-007/)
- Speed skates during real skating: μ = 0.0046 on the straights and 0.0059 on the curves. [M] De Koning, de Groot & van Ingen Schenau 1992, J Biomech 25(6):565 (abstract via a [citation database](https://data.zhenzhi.com/details/1/989684606))
- **Air drag.** I found no drag area (CdA) for a hockey player. Speed-skating models use CdA ≈ 0.275 m² for the tuck ([S], [MDPI](https://mdpi.com/2076-3417/11/3/988), after van Ingen Schenau). At about 10 m/s, air takes about 75% of a speed skater's power and friction 25% ([S], Sci-Sport summary). For a hockey player standing fairly upright in gear I **assume CdA = 0.4-0.6 m²** [E].
- **Coasting deceleration** [E]. I used a = μg + ρ·CdA·v²/(2m), with μ = 0.0071, ρ = 1.25 kg/m³ and m = 90 kg including gear:

| Speed | Deceleration | Coasts to a stop in |
|---|---|---|
| 3 m/s | 0.10-0.11 m/s² | 52-55 m, 37-39 s |
| 5 m/s | 0.14-0.17 m/s² | 110-124 m |
| 8 m/s | 0.25-0.34 m/s² | 190-230 m |

- So physically, a coasting hockey player barely slows down. Real glides lose more than this, because of edges, knee bend and a scraping skate, but no measurement of that was found.
- **In games, players rarely just coast.** Coasting was only 10% of the time (Dillman 1984). One summary of Bracko's 1992 time-motion study reports two-footed gliding at about 39% of shift time, but in short glides averaging 1.87 s ([S], [Coaches Site](https://members.thecoachessite.com/article/using-nhl-data-to-improve-skating-performance-of-young-players-1)). Those glides probably include turning and slowing glides.

## 4. Stopping

- **Hockey stop.** Peak game decelerations were **−5.99 ± 0.64 m/s²** for university men and −5.51 for women. Decelerations above 2 m/s² (about 58 per game for men) outnumbered accelerations (about 45). [M] Gamble 2022
- **Junior B stopping distance** in the Reed Repeat Skate was **4.12-4.43 m**, depending on the hollow ground into the blade; the deepest hollow (0.63 cm) stopped shortest. [M] [Winchester 2007, Brock University thesis](https://brocku.scholaris.ca/items/60f8f3f1-9231-4162-b342-80cf75a80345). The approach speed is not in the abstract. If it was 6.5-7 m/s, the deceleration was 4.9-5.9 m/s² [D, approach speed assumed].
- **Derived stops** [D]: at 5-6 m/s², from 8 m/s you stop in 5.3-6.4 m and 1.3-1.6 s; from 3 m/s, in **0.75-0.9 m and 0.5-0.6 s**.
- 6 m/s² is about 0.6 g, which implies an effective friction of about 0.6 for a skidding, scraping blade [D]. I found no measured friction for a sideways skid.
- **Snowplow and gentle slowing.** I found no measurement. My estimate is **1.5-3 m/s²** [E]. Ordinary slowing in play averaged about 1.7 m/s² over about 2 s (Dillman 1984, [D]).

## 5. Turning

### 5.1 The physics

- A turn of radius r at speed v needs a lateral acceleration a = v²/r = v·ω, where ω is the heading rate. The skater must lean so the line from blade to centre of mass carries that force: **tan(lean) = a/g**.
- Measured check: 14 elite women in World Cup 3000 m races skated the curves at about 11.9-12.4 m/s on radii of 25.5-29 m. Their centripetal acceleration was **5.3-6.3 m/s²** and their body tilt 26-32°. [M] [Kimura & Yokozawa 2024, Front Sports Act Living, doi 10.3389/fspor.2024.1396219](https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2024.1396219/full)
  - tan(30°)·g = 5.7 m/s² [D], so the lean relation holds. These skaters keep about 0.6 g while still pushing.
- **Hockey 90° changes of direction** (n = 8, competitive players): the outside skate took 50-70% of body weight and the inside skate 12-24%. [M] [Fortier, Turcotte & Pearsall 2014, Sports Biomech 13(4):341](https://lida.sport-iat.de/twm/Record/4033900?lng=en). The abstract does not say which force component this is. If it is medial-lateral, the total lateral force is about 0.6-0.9 g [D, inference].

### 5.2 No direct measurement in hockey

I found no study that measures hockey tight-turn radius, heading rate (deg/s), pivot duration or sideways shuffle speed. Two studies come close without the numbers:
- Lafontaine et al. coded how often players use each skill (pivots, stops, turns, lateral crossovers) in Major Junior and university games, with no difference between the levels and more pivots by defensemen. They give no speeds or durations. [M] [Lafontaine, Lamontagne & Lockwood, ISBS](https://ojs.ub.uni-konstanz.de/cpa/article/view/1232)
- An FAU thesis recorded "linear crossover" and "power turn" drills with 17 IMUs, but no results were found ([Lennartz, FAU](https://www.mad.tf.fau.de/person/rebecca-lennartz-2)).

My estimates [E]:
- A rec player sustains **4-6 m/s²** of lateral acceleration (22-31° of lean).
- A strong player in a tight turn reaches **8-10 m/s²** briefly (39-46° of lean), about the most a hockey blade and leg can hold.

### 5.3 Heading rate and turn radius against speed [D, from a = v·ω]

| Speed | a = 4 m/s² | a = 5.5 m/s² | a = 8 m/s² | a = 10 m/s² |
|---|---|---|---|---|
| 1 m/s | 229°/s, r 0.25 m | 315°/s, r 0.18 m | 458°/s | 573°/s |
| 2 m/s | 115°/s, r 1.0 m | 158°/s, r 0.73 m | 229°/s, r 0.5 m | 286°/s |
| **3 m/s** | 76°/s, r 2.25 m | **105°/s, r 1.6 m** | 153°/s, r 1.1 m | 191°/s, r 0.9 m |
| 4 m/s | 57°/s, r 4.0 m | 79°/s, r 2.9 m | 115°/s, r 2.0 m | 143°/s, r 1.6 m |
| 5 m/s | 46°/s, r 6.3 m | 63°/s, r 4.6 m | 92°/s, r 3.1 m | 115°/s, r 2.5 m |
| 6 m/s | 38°/s, r 9 m | 53°/s, r 6.6 m | 76°/s, r 4.5 m | 96°/s, r 3.6 m |
| 8 m/s | 29°/s, r 16 m | 39°/s, r 11.6 m | 57°/s, r 8 m | 72°/s, r 6.4 m |

This is why "you cannot turn on a dime at top speed". At 8 m/s, even an elite tight turn has a radius of 6-8 m (a faceoff circle's radius is 4.57 m). Tight turns at speed are entered after scrubbing speed, and crossovers through a turn add speed. Both of those are coaching knowledge; I found no measurement.

### 5.4 Pivots and sideways movement

- **Pivot 180° (forward to backward and back).** I found no timing data. My estimate is that the body rotates in **0.3-0.6 s (300-600°/s)** while the direction of travel carries on [E]. The pivot turns the body, not the path.
- **Sideways movement.** Lateral crossovers and short shuffles are common skills (Lafontaine), but no speeds were found. My estimate is that sustained sideways speed is at most about **half** of forward, with low acceleration [E].

## 6. Comfort data that limits the model

This is only a brief note; locomotion comfort is covered in `../VR hockey stick and puck feel/stationary_play_audio_latency.md`.

- **Terenzi & Zaal (NASA Ames).** Eighteen people watched a moving particle field for a few seconds at a time, and a staircase method found where symptoms started. Mean thresholds:
  - at steady speed: forward 1.18 m/s, lateral 0.89 m/s, **yaw 0.47 rad/s = 27°/s (SD 22°/s)**;
  - while accelerating: forward 0.70 m/s², lateral 0.59 m/s², **yaw 0.48 rad/s² = 27°/s²**.
  - Rotation was significantly more provoking than translation, people varied a great deal, and the authors recommend tuning the settings per person.
  - The absolute values depend on how much optic flow the scene has, so they do not carry over directly to a rink.
  - [M] [Terenzi & Zaal, NTRS 20200000787](https://ntrs.nasa.gov/api/citations/20200000787/downloads/20200000787.pdf)
- **So, Lo & Ho 2001.** Eight forward speeds from 3 to 59 m/s over 30 min. Speed shifted when vection and nausea set in. A citing paper reports that sickness rose up to about 10 m/s and then levelled off. [M] / [S for the levelling off] [So et al. 2001, Human Factors](https://www.ieda.ust.hk/dfaculty/so/pdf/So-et-al-2001a-HumanFactors.pdf)
- **Instant or gradual acceleration.** The search found one study comparing instantaneous and gradual acceleration profiles that reported no SSQ difference, only a postural-sway difference. I read only the search result, not the abstract or paper ([IDEALS record](https://www.ideals.illinois.edu/items/106046)). "Keep accelerations brief and infrequent" is design guidance, and it has not been well tested.
- What this means here: rotation is the riskiest axis, and accelerations are what the vestibular system senses. The current rig's very high instantaneous accelerations (section 7) are a plausible sickness driver independent of top speed. This is a hypothesis.

## 7. The current rig, in these terms

`rig.py` and the saved settings: 3.0 m/s, MOVE_TAU 0.15 s, 150°/s, TURN_TAU 0.08 s, forward = where you look, and strafing and backwards equal to forwards. All values below are [D].

| Behaviour | Current rig | Real hockey |
|---|---|---|
| Top speed 3.0 m/s | 37% of a rec sprint (8.1 m/s); below the 3.8-4.2 m/s average in play | rec players spend about half of game time below 3 m/s |
| Start from standstill | 95% of speed in 0.45 s, but the **first instant is 3/0.15 = 20 m/s² (2 g)** | about 0.55 s to 3 m/s; about 6 m/s² at most at the first instant; 3.5-4 m/s² mean |
| Letting go of the stick | 20 m/s² initial deceleration; stopped in about 0.45 m | coasting: 0.1 m/s²; a deliberate hard stop: 5-6 m/s² over 0.75-0.9 m |
| Looking 90° away at 3 m/s | the velocity re-aims: Δv = 4.2 m/s at an initial **28 m/s² (2.9 g)**, a turn of about 0.45 m radius | 1.6 m radius at 5.5 m/s²; impossible otherwise |
| Right stick at 150°/s and 3 m/s | 7.9 m/s² (0.8 g), 39° of lean, r = 1.15 m | elite tight-turn level: plausible but at the edge |
| Backward at 3 m/s | allowed, with forward acceleration | 3 m/s backward is reachable (top about 6.5 m/s), but backward acceleration is about half to two-thirds of forward |
| Strafing at 3 m/s | allowed | sustained sideways skating at 3 m/s isn't hockey [E] |
| End to end | 46 m rink in about 15 s | a rec sprinter covers 61 m in about 8.7 s (fit) |
| Puck against skater speed | the AI's 10 m/s pass is 3.3 times your top speed; its 22 m/s shot is 7 times | against a rec player's 8 m/s sprint the same pass is 1.25 times, so here passes and dump-ins can't be chased down the way they are on real ice |

## 8. Recommended locomotion model

Keep the speed comfortable, but make everything else honest. Model your velocity as a world-frame state with momentum, and limit how fast it can change: separately along the direction of travel (pushing or braking) and across it (turning).

**State.** Your world velocity **v** (horizontal), the rig yaw ψ, and the yaw rate ω.

**1. Desired velocity from the left stick.** The stick sets a direction and a magnitude m (with the deadzone and curve kept). The top speed depends on direction relative to your facing, interpolated on an ellipse:
- Vf forward;
- Vb = 0.8·Vf backward (Marino & Grasse 82%, Wu 81%);
- Vs = 0.5·Vf sideways [E].

This gives the desired velocity **v\***.

**2. Along the direction of travel** (the component of v\* − v along v):
- **Pushing** (you want more speed): a = min(A_push, Δ/τ_end).
  - A_push is **4 m/s²** forward: Greer & Dillman's 3.5-4.1 m/s² over the first 6 m, and Gamble's 4 m/s² game peaks. Backward it is **2 m/s²** (from Psilander, [D]).
  - τ_end ≈ 0.2 s smooths the last part so you don't hit top speed with a jolt.
  - From 0 this reaches about 2.9 m/s in about 0.8-1.0 s: 0.55 s at 4 m/s² to 2.2 m/s, then the 0.2 s ease [D]. That is gentler than now and near a rec skater's 0.56 s, without the 20 m/s² spike. Raise A_push to 5-6 if it feels sluggish.
- **Braking**, in three cases:
  - **Stick released: coast at A_coast.** The honest value is 0.1-0.3 m/s² (section 3). As a starting default I suggest **1.0 m/s²**, an "easing up" glide that takes about 3 s and 4.5 m from 3 m/s. It is adjustable down to 0.15 for real glide. Make it a setting ("glide").
  - **Stick held against the motion** (more than about 120° from v): **hockey stop at A_stop = 5 m/s²**. That is rec level; university players peak at 6. It stops you from 3 m/s in 0.6 s and 0.9 m. Once you are below about 0.3 m/s, accelerate the new way: this is stop-and-go, the way a real skater reverses.
  - **Stick partly held** (you want less speed): 2 m/s², like the ordinary slowing in play (about 1.7 m/s²).

**3. Across the direction of travel (turning the path).** Rotate v toward v\* at up to ω_v = **A_lat / |v|**, with A_lat = **6 m/s²** for a rec player (between the measured 5.3-6.3 m/s² and the hockey estimates). Apply no limit below about 0.5 m/s, where you pivot on the spot. This limit applies however the direction changes: by right stick, by looking, or by the left stick.

**4. Yaw (right stick).** ω_max(|v|) = min(150°/s, A_lat / |v|), keeping the 0.08 s easing.
- It binds only above 6/2.62 ≈ 2.3 m/s. At Jon's 3 m/s full stick it caps the turn at 115°/s, so it changes nothing at standstill or at low speed.
- Choosing the cap this way keeps your view and your path together (car-like, mostly forward optic flow), rather than letting the view swing round faster than the path, which would be a sideways slide.

**5. A "real hockey" preset**, for comparison and testing only: Vf = 8 m/s, A_push about 4-6 m/s², A_coast 0.15, A_stop 5.5, A_lat 6. Expect it to be uncomfortable.

### Parameter table

| Parameter | Current | Recommended start | Real reference |
|---|---|---|---|
| Top speed forward (`skate`) | 3.0 m/s | keep 3.0 as the default; **A/B test 4.0-4.5** once the acceleration limits are in | rec sprint 8.1; play average 3.8-4.2; half of game time under 3 |
| Backward top | = forward | 0.8 × forward | 82% / 81% |
| Sideways top | = forward | 0.5 × forward | no data [E] |
| Push acceleration | 3/0.15 = 20 m/s² first instant (eased with τ 0.15) | 4 m/s² forward and 2 backward, with a 0.2 s ease at the top | 3.5-4.1 mean over the first 6 m; game peaks 4.1 |
| Coast (stick released) | about 20 m/s² first instant, stopped in 0.45 m | 1.0 m/s², adjustable 0.15-3 | 0.1-0.3 physically |
| Hockey stop (stick against motion) | not a separate input | 5 m/s² | game peaks 5.5-6.0 |
| Path-turn limit A_lat | none (about 28 m/s² possible) | 6 m/s² | 5.3-6.3 measured in speed skating; hockey 4-10 [E] |
| Yaw rate | 150°/s at any speed | min(150°/s, 6/v rad/s) | 105°/s at 3 m/s, 53°/s at 6 m/s (a = 5.5) |
| Turn easing | 0.08 s | keep | — |

### AI skaters (`threes.py`)

| Parameter | Current | Recommended | Why |
|---|---|---|---|
| VMAX and YOU_FRAC | min(5.8, 0.95 × you) × (0.85 + 0.15·level) | keep scaling to Jon. Range **0.85-1.05 × his top** by level | rec players differ by about 7% in top speed and 15% over the first 10 m (Buckeridge). Equal-level skaters are equally fast |
| ACCEL | 5 m/s², the same in every direction | push 4, stop 5.5, lateral 6 m/s² (heading rate ≤ 6/v) | same limits as Jon, so the AI can't turn on a dime either |
| Idle slowing | v × (1 − 4·dt): 12 m/s² at 3 m/s | glide or ease at about 1-1.5 m/s², or a stop at 5.5 | nobody stops dead at 12 m/s² |
| CARRY | 0.85 | 0.92-0.95 | youth players were about 5% slower over 30 m with the puck (6.4 s against 6.1 s) ([S], computed from a table in an MDPI Sports 2020 study, n = 13, U12). Weak data |
| Facing turn rate | eased at 8/s | cap the body pivot at about 360°/s, and the path at A_lat/v | pivots are fast; the path is not |

## 9. Open questions and what to measure

1. **Do bounded accelerations let Jon handle more speed?** The hypothesis is that 4 m/s felt too fast because of the 20-28 m/s² onsets and instant re-aiming, not the speed itself. Test current against bounded acceleration, at 3 and 4 m/s, with the same vignette.
2. **Glide.** Honest glide (0.15 m/s²) carries about 50 m from 3 m/s, longer than the rink. Is a long, steady glide comfortable for him? Constant velocity is generally less provoking than acceleration, but the motion is no longer under his control. Try 0.3, 1.0 and the current setting.
3. **Which way is "forward"?** Real skaters look at the puck while they skate straight. With momentum, a glance only bends the path slowly, which may be enough. Otherwise, consider making forward the rig (body) facing rather than the head.
4. **No measured hockey numbers for turning.** Tight-turn radius against speed, heading rate, pivot duration and sideways speed are all missing. Jon could film himself from the stands or with a phone, using faceoff circles (4.57 m radius) and dots as the scale. Pro tracking data with x,y positions (NHL EDGE does not publish them) would also answer this.
5. **Skid friction and snowplow deceleration** were not measured anywhere I found, and neither was a hockey player's drag area. The coasting numbers rest on μ = 0.0071 from a sled test at 1.8 m/s and an assumed CdA.
6. **Should the stick ask for a speed (as now) or a push (a force)?** A push model gives speed-dependent acceleration for free: a = A0·(1 − v/Vmax).
7. **The size of the comfort constraint.** The NASA thresholds (about 27°/s yaw) are far below 150°/s, yet Jon chose 150°/s. Thresholds vary widely between people and with the scene, so his own A/B results matter more than population means.

---

## Verification

Fact-check of the claims behind the recommendations, 2026-11-09. Each source was found again and read independently. Full texts were read for Buckeridge 2015, Marino & Grasse 1993, Wu 2015, Dillman 1984, Greer & Dillman 1984, Gamble 2022, Terenzi & Zaal and Winchester 2007, and abstracts for the rest. I also re-read `rig.py`, `threes.py` and `sandbox_settings.json`.

Verdicts: **confirmed**, **corrected** (the right value is given), **unsupported** (no source found, or the source does not say it).

| # | Claim | Verdict | What the source actually says |
|---|---|---|---|
| 1 | Buckeridge 2015: rec 4.95 / 2.26 / 1.23 s (8.1 m/s), varsity 4.42 / 1.93 / 1.14 s (8.8 m/s) | confirmed | Table 2 (full text, [Europe PMC PMC4431820](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4431820/fullTextXML)): High (varsity, n = 9, 25.7 y) 1.93 / 1.14 / 4.42 s; Low (recreational, n = 9, 36.9 y, 86.3 kg) 2.26 / 1.23 / 4.95 s. The acceleration phase is the first 10 m and the steady state the last 10 m. 8.1 and 8.8 m/s are averages over the last 10 m, not instantaneous peaks. |
| 2 | Budarick 2020: high-calibre 30 m peak, men 8.96 ± 0.44, women 8.02 ± 0.36 m/s | confirmed | Abstract ([LIDA 4064418](https://lida.sport-iat.de/svd/Record/4064418?lng=en)): static start, 30 m, as stated. |
| 3 | NHL forwards' median season top speed slightly over 22 mph, middle 80% 21-23 mph | confirmed [S] | "Looking at the middle eightieth percentiles, forwards' top speed typically fell between 21 and 23 MPH"; the median forward is "slightly more than 22 MPH" ([Puck Over the Glass](https://puckovertheglass.substack.com/p/nhl-edge-skating-speed-part-1)). The seasons covered are not stated. |
| 4 | 2022-23: Poehling 24.32 mph; McDavid 24.16 mph and 309.43 miles | confirmed | [NHL.com](https://www.nhl.com/news/nhl-edge-launches-website-for-puck-and-player-tracking-data): 2022-23 regular season; McDavid sixth at 24.16, with the league's most distance, 309.43 miles. |
| 5 | Marino & Grasse 1993: backward 6.57 vs forward 8.03 m/s (82%) | confirmed | Full paper, Table 1 ([PDF](https://ojs.ub.uni-konstanz.de/cpa/article/view/1699/1601)): n = 10 skilled, 18-22 y; backward 6.57, forward 8.03 m/s (separate maximal forward trials); cycle 0.86 s and 5.65 m. The abstract prints different figures (6.56 m/s, 4.53 m, 1.5 cycles/s); the table is what the notes use. Wu et al. 2015 ([PDF](https://ojs.ub.uni-konstanz.de/cpa/article/view/6664/6022)): forward 10.1 ± 1.9, backward 8.2 ± 0.2 m/s, n = 7 collegiate, 81%. |
| 6 | Psilander 2025: backward C-cuts 2.4 m/s over 0-5 m, 6.7-6.8 m/s at 35-40 m, still accelerating | confirmed | Abstract ([LIDA 4095112](https://lida.sport-iat.de/twm/Record/4095112?lng=de)): 20 high-calibre players from a top-three Swedish league; 2.42 / 2.38 m/s (0-5 m, two blade holders), 5.86 / 5.76 (15-20 m), 6.84 / 6.67 (35-40 m); not at maximum speed by 40 m. |
| 7 | Dillman 1984: mean 4.21 m/s, peak 5.01, low 1.62; 49 / 41 / 10%; phases about 2 s | confirmed | Full text ([PDF](https://ojs.ub.uni-konstanz.de/cpa/article/download/1410/1161)): 22 players, 1982 National Sports Festival games, 13.5 s per player from an offensive-zone faceoff or the puck crossing the blue line. 6.64 s (49%) accelerating, 5.47 s (41%) decelerating, 1.39 s (10%) coasting; 3.36 accelerations of 2.08 s and 3.23 decelerations of 2.00 s. It cites Green et al.'s 3.78 m/s. Caveat: offensive-zone sequences only. |
| 8 | Greer & Dillman 1984: National Team 6.1 m in 1.53 s, 6.71 m/s, 4.13 m/s²; Sports Festival 3.53 m/s² | confirmed | Full text ([PDF](https://ojs.ub.uni-konstanz.de/cpa/article/download/1412/1170)): National Team n = 11, 1.53 s, 6.71 m/s, 4.13 m/s², 4.25 strides/s; Sports Festival n = 69, 1.52 s, 6.25 m/s, 3.53 m/s²; criterion from Marino's sample 1.80 s. These are elite players, not rec. Note that the printed means are low against the kinematics: 6.1 m in 1.53 s from rest needs at least 5.2 m/s² at constant acceleration, and 6.71/1.53 = 4.4 m/s². |
| 9 | Gamble 2022: varsity game peaks 8.66 / 7.98 m/s, +4.06 / +3.67, −5.99 / −5.51 m/s² (men / women), 20 Hz | confirmed | Full text ([PMC8914021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8914021/)): University of Guelph varsity, 25 men and 21 women, 2019-20, 20 Hz LPS; 31.16 / 28.73 km/h (male forwards 31.73 = 8.8, defence 30.15 = 8.4 m/s); peaks as stated; about 45 accelerations and 58 decelerations over 2 m/s² per game for men. They are "maximum instantaneous" values, and the paper does not report filtering (the notes' "smoothed" is not in the paper). Rows 11 and 14 suggest these LPS peaks understate the true peaks. |
| 10 | Derived from Gamble 2022 Table 2: forwards about 49% of time under 3 m/s, 5% over 6.7 m/s | confirmed (derivation) | Reproduced from the male forwards' zone distances (1281, 650, 791, 1212, 699, 584 m), using 6 km/h for the 1-10.9 km/h zone and 26 km/h for the over-24 zone: 49.1% and 5.2%, mean 3.34 m/s. It is sensitive to the slow-zone speed: 4-8 km/h gives 42-59% under 3 m/s. The implied 26 min of skating per game is long for a forward, so the slow share may be overstated. |
| 11 | Gamble 2024: women about 3% of ice time at 80% or more of sprint speed, under 1% at 90% or more | confirmed | Abstract ([LIDA 4087606](https://lida.sport-iat.de/twm/Record/4087606?lng=en)): 17 varsity women; about 3% at 80% or more (22.7 km/h), under 1% at 90% or more (25.5 km/h); game against sprint-test peaks 29.5 vs 28.3 km/h and 4.39 vs 3.34 m/s². The sprint-test peak acceleration (3.34) is below Greer & Dillman's *mean* over 6.1 m (3.53-4.13), which is another sign that the LPS peaks are smoothed. |
| 12 | Federolf 2008: blade μ 0.0071 ± 0.0005 (sled, 1.8 m/s, 53 kg per blade) | confirmed | Abstract ([LIDA 4014976](https://lida.sport-iat.de/ta/Record/4014976)): "0.0071 (s = 0.0005)", aluminium sled on three blades, 53 kg on each, starting at 1.8 m/s; flared blades 13 / 21 / 22% lower; μ fell as the load rose. It is a sled on straight blades, not a gliding skater. |
| 13 | Coasting: about 0.10 m/s² at 3 m/s, 0.25-0.34 at 8 m/s, 52-55 m from 3 m/s | unsupported (estimate) | I found no measured coasting deceleration for a hockey player, and the CdA of 0.4-0.6 m² is assumed. The arithmetic does reproduce: 0.095-0.107 m/s² at 3 m/s, 52-55 m and 37-39 s from 3 m/s, and 0.25-0.34 m/s² at 8 m/s. |
| 14 | Winchester 2007: Junior B stopping distance 4.12-4.43 m | **corrected** | The distances are right: 4.12 ± 0.14, 4.43 ± 0.08 and 4.35 ± 0.12 m (15 male Junior B players, 19 y). But the thesis ([full text](https://brocku.scholaris.ca/bitstreams/c383fe8e-b030-4d74-82ef-6268331c53fa/download), Table 3) gives what the abstract leaves out: the speed when the stop began was **8.39 / 8.61 / 8.35 m/s**, and the stop took **0.81-0.84 s**. So the mean deceleration was about **8.0-8.5 m/s²** (v²/2d) or **10.0-10.4 m/s²** (v/t), not the 4.9-5.9 m/s² derived in section 4 from an assumed 6.5-7 m/s approach. A hard hockey stop averages about 0.8-1 g. |
| 15 | Kimura & Yokozawa 2024: about 12 m/s on 25.5-29 m radius curves, 5.3-6.3 m/s², 26-32° of tilt | confirmed | Full text ([Frontiers](https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2024.1396219/full)): 14 elite women, World Cup 3000 m, inner lane; stage and side means of 11.85-12.41 m/s, radii 25.6-29.0 m, 5.31-6.25 m/s², tilt 26.4-32.2°. This is long-track speed skating at 12 m/s. Using it for hockey turns at 2-4 m/s is an extrapolation. |
| 16 | Fortier 2014: in a 90° change of direction the outside skate takes 50-70% BW, the inside 12-24% | confirmed | Abstract ([LIDA 4033900](https://lida.sport-iat.de/twm/Record/4033900?lng=en)): 8 players with competitive experience, rapid lateral 90° left and right changes of direction; as stated. The abstract does not name the force component. |
| 17 | Hockey tight turns sustain 4-6 m/s² (rec) and reach 8-10 m/s² briefly (elite) | unsupported (estimate) | I found no hockey measurement of turn radius or lateral acceleration. The only near miss is a 2023 McGill conference abstract on hip and knee kinematics in tight turns ([IHRG list](https://mcgill.ca/ihrg/publications/conference-abstracts)), with no accelerations. The arithmetic is right (5.5/3 rad/s = 105°/s; 5.5/8 = 39°/s). Indirect support for the high end: the Winchester stops show a skidding blade taking about 0.8-1 g sideways. |
| 18 | Terenzi & Zaal: yaw 0.473 rad/s (27°/s, SD 22), forward 1.18 m/s; accelerating forward 0.70 m/s², yaw 0.478 rad/s²; rotation lower | confirmed | Full text ([NTRS](https://ntrs.nasa.gov/api/citations/20200000787/downloads/20200000787.pdf)), Table 4: forward 1.183 (SD 0.836) m/s, lateral 0.890, yaw 0.473 (SD 0.381) rad/s = 27.1 (21.8)°/s; accelerating forward 0.700 m/s², lateral 0.586, yaw 0.478 rad/s². Rotation was significantly lower (p < 0.001), compared through equalised optic flow because the units differ. 18 participants (one had no detections), 3-5 s exposures, head held still, particle field. |
| 19 | Current rig at 3 m/s: 20 m/s² at start and stop, 28 m/s² looking 90° away, 7.9 m/s² at full right stick | confirmed | In `rig.py`, velocity eases toward a head-forward target with 1 − exp(−dt/0.15), and `sandbox_settings.json` has skate 3.0 and turn 150. 3/0.15 = 20 m/s²; a 90° look gives \|Δv\| = 4.24 m/s, so 28.3 m/s²; letting go stops you in v·τ = 0.45 m. At full right stick, 3 × 2.618 = 7.85 m/s² if the path follows the view; with the 0.15 s lag the steady state is 2.79 m/s, 7.3 m/s² and 21° behind the view. Two details are off: the code comment says "6 felt too fast in the 3v3" (the brief says 4), and the `threes.py` ACCEL limits the whole Δv vector, so AI turns are already capped at 5 m/s². |
| — | (Behind the CARRY row) youth players about 5% slower over 30 m with the puck | confirmed (weak) | Sports 2020, 8(9):126 ([PDF](https://rcastoragev2.blob.core.windows.net/dce27c80701b50d360d70b8ed9fc0fa1/PMC7552761.pdf)): 13 sixth-grade U12 players (13 ± 0.35 y); baseline 30 m 6.1 ± 0.4 s without the puck and 6.4 ± 0.4 s with it (4.9%), from a standing start. Its 30 m backward time was 7.8 s, 78% of forward speed. |

### What changes in the recommendations

- **Forward top speed (keep 3.0, A/B 4.0-4.5): holds.** The sources are confirmed. The in-play average is better given as 3.3-4.2 m/s (the Gamble derivation, Green 1976 and Dillman 1984). The sickness hypothesis is still untested. Even the proposed 4-6 m/s² limits are 6-9 times NASA's mean onset threshold for forward acceleration (0.70 m/s²), so bounding accelerations reduces the visual-vestibular conflict but does not remove it.
- **Backward 0.8 × forward: holds** (81.8% and 81%, and 78% from a standing start in the U12 data).
- **Sideways 0.5 × forward: unchanged.** It is still an estimate with no data.
- **Push acceleration 4 m/s²: change it.** The 4 rests on elite *means* from 0 to about 6.5 m/s (whose own kinematics imply 4.4-5.2 m/s²) and on LPS game peaks that look smoothed (row 11). With a 3 m/s cap, only the first half second matters. The notes' own fit to Buckeridge puts a rec adult at 3 m/s in 0.56 s, a mean of about 5.4 m/s². With 4 m/s² and a 0.2 s ease, the rig reaches 2.9 m/s in about 1.0 s, almost twice a rec skater's time, not "near" it. An honest default is about **6 m/s² with a 0.1 s ease** (3 m/s in about 0.6 s), with 4 kept as the gentler comfort setting. Backward stays at about half of forward: Psilander's 0-5 m gives about 2.3 m/s² at constant acceleration, and the U12 4 m times give a ratio of about 0.63.
- **Coast 1.0 m/s²: holds as a design compromise.** The arithmetic checks out, the CdA is unmeasured, and the 10% coasting figure is confirmed. A steady 1.0 m/s² is above NASA's 0.70 m/s² mean onset threshold, while the honest 0.15-0.3 is close to constant velocity, which may be the more comfortable of the two. A/B test as planned.
- **Hockey stop 5 m/s²: change it.** A measured hard stop averages **8-10 m/s²**: Junior B players stopped from 8.4 m/s in 0.81-0.84 s and 4.1-4.4 m. Gamble's 6 m/s² is a smoothed game peak. The "why" comparison (0.9 m from 3 m/s against 4.1-4.4 m) mixes approach speeds: at 5 m/s², stopping from 8.4 m/s would take about 7 m. From 3 m/s an honest hard stop takes about 0.3-0.4 s and 0.5 m, which is roughly what the current release already does (0.45 m), only on the wrong input. Make the stop **about 8 m/s²** for honest physics, and keep 5 only as a declared comfort setting.
- **Path-turn limit A_lat 6 m/s²: holds only as an estimate.** Kimura is confirmed, but it is long-track skating at 12 m/s, and there is no hockey measurement. The skid stops show a blade taking 0.8-1 g sideways, so 6 may be conservative for a tight hockey turn. A/B test 6 against 8.
- **Yaw cap min(150°/s, 6/v): holds.** The arithmetic is confirmed (115°/s at 3 m/s; it binds above 2.3 m/s). The "7.9 m/s²" for full stick at 3 m/s is 7.3-7.9, depending on the lag.
- **`threes.py` ACCEL: reframe it.** The AI is already limited to 5 m/s² in every direction, turns included, because the code limits the Δv vector. So "lateral 6" would let the AI turn harder than it does now, and "so the AI can't out-turn him" describes Jon's rig, not the AI. Give the AI whatever limits Jon's rig ends up with: about 6 push, 8 stop and 6 lateral if the changes above are taken.
- **AI idle slowing: holds, but matters little.** It applies only when the AI has no target or play is not live (whistles, after goals). 12 m/s² at 3 m/s is only a little above a real hard stop (8-10), though it is 23 m/s² at the AI's 5.8 m/s top speed.
- **VMAX and YOU_FRAC spread 0.85-1.05: the rationale is corrected.** Buckeridge's 7% (last 10 m) and 15% (first 10 m) are the gaps between the rec and varsity *groups*, not the spread among rec players. The range is a design choice. With Jon at 3.0 m/s, the AI's top is now 2.85 × (0.85 + 0.15·level).
- **CARRY 0.92-0.95: holds, on weak data.** The 4.9% is confirmed, but it comes from one study of 13 U12 players from a standing start.
