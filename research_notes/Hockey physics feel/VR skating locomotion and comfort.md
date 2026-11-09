# VR skating locomotion and comfort: thumbstick skating that feels like hockey without making Jon sick

Research done 2026-11-09 for the vr-hockey prototype. No code was changed. Companion notes:
- `skating kinematics.md` (same folder): how real skaters move (speeds, starts, glide, stops, turns) and a momentum model. This note covers the comfort side and the control mapping, and it agrees with that model except where it says so.
- `../VR hockey stick and puck feel/stationary_play_audio_latency.md`, section 1: the earlier locomotion survey (teleport vs steering, Meta's guidance, the VR hockey titles).

Tags:
- **[M]** measured in the cited study.
- **[D]** derived by me from measured numbers; the arithmetic is shown.
- **[E]** estimate, or physics with stated assumptions.
- **[G]** official design guidance (Meta), not a study.
- **[V]** vendor claim, developer anecdote or press impression.
- **[S]** secondary: read in a citing paper or a summary, not the primary source.

---

## Bottom line

1. **There is no tested recipe.** No shipped VR hockey game documents a comfort design for thumbstick skating. The VR games that are known for comfortable fast momentum (Echo VR, Gorilla Tag, Sprint Vector) drive the motion with the arms. Jon can't do that, because both hands hold the stick. No study has tested a glide (motion that carries on after the stick is released). So the mapping below is built from general comfort findings and from hockey measurements, and it has to be A/B tested on Jon.
2. **Comfort evidence, ranked by strength:**
   - *Strong:* dynamic field-of-view restriction (a vignette) reduces sickness. This comes from several experiments, a 201-person study and a 97-study meta-analysis.
   - *Strong:* rotation provokes sickness at lower intensities than translation, and visual oscillation (such as head-bob) and multi-axis motion make it worse.
   - *Moderate:* active control is less sickening than passive motion. Sickness grows with speed between about 3 and 10 m/s and with time spent moving.
   - *Weak or contradicted:* "use near-instant accelerations" is design guidance. The one controlled test of speed profiles found no difference.
   - *Missing:* glide, button stops and speed-dependent turn rates were never tested.
3. **The current rig's release is a hockey stop, not a glide.** With τ = 0.15 s, releasing the stick decelerates you at 20 m/s² at first [D] and stops you in 0.45 m. A hard hockey stop from 3 m/s takes about 0.33-0.5 s [D]. So what feels non-hockey isn't that you stop. It's that you stop without asking to, and that you start at 20 m/s², about five times a real skater's peak.
4. **Recommended mapping, in one paragraph.**
   - The left stick sets a desired velocity in the frame of your *body*, not your head. You reach it at a bounded push acceleration of about **4 m/s²**.
   - Releasing the stick **coasts**: start at **1.5 m/s²** and step down over sessions toward 0.5 or lower.
   - A **hockey stop** on an index trigger, or by holding the stick against your motion, decelerates at **5-6 m/s²**.
   - Backward speed is 80% of forward and sideways 50%.
   - The right stick keeps **150°/s when slow**. Above about 2.3 m/s the turn rate is capped by a lateral-acceleration limit of 6 m/s², which gives about 115°/s at 3 m/s. Your path carves with your heading.
   - Keep the speed- and rotation-driven vignette at 0.7. Never bob the camera with strides. Keep top speed at 3 m/s until the new dynamics have been tested.

---

## 1. What the prototype does now

From `rig.py` and `sandbox.py`, and Jon's `sandbox_settings.json`: skate 3.0, turn 150, snap 0, vignette 0.7.

| Behaviour | Value | Derived numbers [D] |
|---|---|---|
| Move | left stick: deadzone 0.15, power-2 curve, speed 3.0 m/s, direction from the **head's** horizontal forward | — |
| Speed easing | exponential, τ = 0.15 s, for both speeding up and slowing down | **initial acceleration = 3/0.15 = 20 m/s²** (2 g); 95% of speed in 0.45 s; stopping distance from 3 m/s = v·τ = 0.45 m |
| Strafe and backward | same speed as forward | — |
| Turn | right stick, curve power 1.3, 150°/s, eased τ = 0.08 s, turning about the head | initial angular acceleration 150/0.08 ≈ 1,900°/s²; 95% of turn rate in 0.24 s |
| Vignette | strength 0.7. It closes as speed/top × 1.3 + turn/turn-max rises (capped at 1). It closes with τ 0.08 s and opens with τ 0.25 s. It is a black ring in clip space. At strength 0.7 it is fully dark beyond clip radius 0.89 and clear inside 0.54 | at full motion it is roughly clear in the central ~60° and dark beyond ~90° [E: assumes per-eye half-FOV of about 48°; the clip-space ring is asymmetric on Quest 3] |
| AI skaters (`threes.py`) | VMAX 5.8 m/s, capped at 95% of Jon's top (2.85 m/s now), ACCEL 5 m/s² | — |
| Rink (`arena.py`) | 46 m long (regulation 61 m), regulation width and corners | crossing at 3 m/s takes 15 s. That is the same time as crossing a 61 m rink at 4 m/s [D] |

The sibling note adds one more number [D]: because velocity follows the head, a 90° glance at 3 m/s re-aims your velocity at up to about 28 m/s² (2.9 g). No skater can do that.

## 2. Real skating numbers this note relies on

The full table is in `skating kinematics.md`. The values that drive the comfort trade-off:

- **Speed during play.** Varsity men (U Sports, 20 Hz ultra-wideband tracking, 25 men) peaked at 31.2 km/h, which is **8.7 m/s**. But much of their skating distance was slow:
  - defensemen covered 33% of their distance under 10.9 km/h (3.0 m/s) and 65% under 16.9 km/h (4.7 m/s);
  - forwards covered 25% and 52%.
  - [M] distances by zone, fractions [D]: [Gamble et al. 2022, *Front. Physiol.* 13:831723](https://www.frontiersin.org/articles/10.3389/fphys.2022.831723)
  - Jon's 3.0 m/s is the top of the slowest zone in that paper ("very slow", 1.0-10.9 km/h).
- **Starts.** Peak game acceleration in men was **4.06 ± 0.43 m/s²** [M] (Gamble 2022). Junior B players averaged 3.43-3.46 m/s over the first 6 m of a sprint start [M] ([Winchester 2007, Brock MSc thesis, Table 3](https://brocku.scholaris.ca/items/60f8f3f1-9231-4162-b342-80cf75a80345)). At constant acceleration that is about **4.0 m/s²** [D: a = 2·6 m / (6 m / 3.45 m/s)²].
- **Stops.** Peak game deceleration in men was **−5.99 ± 0.64 m/s²** [M] (Gamble 2022). In Winchester's sprint test, 15 Junior B players stopped from **8.39-8.61 m/s in 0.81-0.84 s over 4.12-4.43 m** [M]. That is a mean deceleration of **8.5-10.3 m/s²** [D: v²/2d gives 8.5, v/t gives 10.3; the two disagree because the deceleration was not constant].
  - The thesis table shows the approach speed. `skating kinematics.md` assumed it was 6.5-7 m/s and got 4.9-5.9 m/s², so that line should be corrected.
  - A 20 Hz smoothed tracker probably underestimates peaks, which would explain why Gamble's −6 is lower [E].
- **Glide.** Ice friction during speed skating is μ = 0.0046 on straights and 0.0059 on curves [M] ([de Koning et al. 1992, *J. Biomech.* 25:565](https://data.zhenzhi.com/details/1/989684606)). Hockey blades measured 0.0071 in a sled test [M] (Federolf et al. 2008, via the sibling note). With air drag, a coasting skater at 3 m/s loses only about **0.1 m/s²** [E, sibling note]. A real glide from 3 m/s would carry about 50 m.
  - For comparison, the vestibular system detects horizontal linear acceleration from about **0.06 m/s²** (X axis 0.063, Y axis 0.057, Z axis 0.154; 24 people, 3 s cosine-bell motions) [M] ([Benson, Spencer & Stott 1986, *Aviat. Space Environ. Med.* 57:1088](https://pubmed.ncbi.nlm.nih.gov/3790028)). So a real glide's slowdown is barely above what a real skater can feel.
- **Backward** top speed is about **80%** of forward: 6.56 m/s backward in 10 skilled players [M] ([Marino & Grasse 1993, ISBS](https://ojs.ub.uni-konstanz.de/cpa/article/view/1699)).
- **Turns.** Gamble's tracker counts "sharp" turns as radius under 2 m. Men made about 66 turns, 45 accelerations and 58 decelerations above 2 m/s² per game [M]. No measurement of hockey turn rate against speed exists. The sibling note's estimate is a lateral acceleration of 4-6 m/s² sustained, which gives about 105-115°/s at 3 m/s.
- **Stride rhythm.** Junior B sprint strides came at 2.42-2.52 strides/s [M] (Winchester 2007, Table 3).

## 3. Comfort evidence

### 3.1 Speed

- **So, Lo & Ho 2001** [M]. 96 men took a 30-minute head-steered virtual tour at eight speeds (rms 3, 4, 6, 8, 10, 24, 30, 59 m/s). Nausea and vection ratings rose significantly from 3 to 10 m/s and levelled off above 10 m/s. Speed shortened the time until vection and nausea set in, but did not change how fast they grew with exposure time. [So et al. 2001, *Human Factors* 43:452 (author PDF)](https://www.ieda.ust.hk/dfaculty/so/pdf/So-et-al-2001a-HumanFactors.pdf)
  - For Jon: 3 m/s is the bottom of the range where sickness rose. Going to 4 m/s moves up the slope, consistent with his 3v3 report.
  - Caveat: how fast the scene seems to move depends on how much detail it has. A sparse line-drawn rink may count as "slower" than a textured city [E].
- **Terenzi & Zaal (NASA Ames / SJSU, 2020)** [M]. 18 mostly VR-naive people (median age 24) sat with their heads still while a particle field moved for 3-5 s. A staircase found where they first felt "uneasy". Mean thresholds (SD in brackets):

  | Motion | Steady speed | Constant acceleration |
  |---|---|---|
  | Forward | 1.18 m/s (0.84) | 0.70 m/s² (0.48) |
  | Lateral | 0.89 m/s (0.59) | 0.59 m/s² (0.42) |
  | Yaw | 0.473 rad/s = **27°/s** (22°/s) | 0.478 rad/s² = **27°/s²** |
  | Roll | 0.364 rad/s = 21°/s | 0.474 rad/s² |

  - Rotation thresholds were significantly lower than translation thresholds, compared at equal optic flow. Forward and lateral did not differ significantly.
  - Each person's thresholds correlated strongly across conditions. The authors therefore recommend tuning motion settings to each individual.
  - [NTRS 20200000787](https://ntrs.nasa.gov/api/citations/20200000787/downloads/20200000787.pdf)
  - Every value Jon uses is far above these onset thresholds, which is normal for games. Their use here is the ranking: rotation before translation, and a large spread between people.
- **Meta guidance** [G]:
  - Match real walking and running speeds: about **1.4 m/s** walking and **2.8 m/s** running ([Locomotion comfort and usability](https://developers.meta.com/horizon/design/locomotion-comfort-usability/)).
  - The Meta Web SDK calls slide speeds of **4-6 m/s** "reasonable" ([IWSDK slide locomotion](https://developers.meta.com/horizon/documentation/web/iwsdk-concept-locomotion-slide/)).
  - So Meta's own pages disagree by a factor of two.

### 3.2 Linear acceleration: brief steps or ramps?

- **Guidance** [G]:
  - "Keep acceleration events brief and infrequent" ([Meta, Locomotion best practices](https://developers.meta.com/horizon/design/locomotion-best-practices/)).
  - "Quantized velocity": set fixed speeds and switch between them instantly, to shorten the perceived acceleration ([Locomotion comfort and usability](https://developers.meta.com/horizon/design/locomotion-comfort-usability/)).
  - The same page also says a camera that hits something should "slow down before stopping, rather than an abrupt halt".
- **The one controlled test of the guidance found no effect** [M]. Widdowson et al. compared three speed profiles for linear motion (experiment 1) and circular motion (experiment 2), in 2-minute standing trials. Neither SSQ (Simulator Sickness Questionnaire) scores nor postural sway differed between profiles. The authors: "no convincing evidence to support the common belief that constant speed is more comfortable than variable speed profiles". [Widdowson, Becerra, Merrill, Wang & LaValle, *Human Factors* 63(2):296, 2021 (online 2019)](https://doi.org/10.1177/0018720819881254). I read the abstract only, so the exact profiles are unknown.
- **Changing vection is worse than steady vection** [M]. Steadily expanding optic flow gave lower SSQ totals and subscores than flow that alternately expanded and contracted (5 min). [Bonato, Bubka, Palmisano, Phillip & Moreno 2008, *Presence* 17:283](https://ro.uow.edu.au/articles/journal_contribution/Vection_change_exacerbates_simulator_sickness_in_virtual_environments/27740778). This is an argument against frequent start-stop-start cycles, which are what the current release-to-stop produces when Jon makes small repositioning moves [E].
- **Mixed result for acceleration in the NASA study.** At equal mean optic flow, the accelerating conditions' thresholds matched or exceeded the steady ones. The authors attribute the differences to vection building up slowly, not to acceleration as such. They estimated perceptual time constants of about 1.8 s for translation and 3.8 s for rotation [M/E] (Terenzi & Zaal).
- **What this means for Jon** [E]:
  - Whether reaching 3 m/s takes 0.45 s or 0.75-0.85 s should matter little; both count as "brief".
  - What probably matters more is how *many* speed changes he makes a minute, and whether he chose them.
  - So a model that makes him stop deliberately (glide plus a stop control) should produce fewer, more deliberate speed changes than the current one.

### 3.3 Rotation speed (smooth turning)

- **Optokinetic drum** [S]. Hu, Stern, Vasey & Koch (1989) rotated a striped drum at 15-90°/s. Symptoms rose, **peaked at 60°/s**, then declined. This is as reported by So et al. 2001 and by Farmani & Teather 2020. Farmani & Teather also cite work saying vection disappears at about 200°/s.
- **Passive rotation in an HMD** [M]. Twelve people sat while the camera yawed at 11 speeds in fixed ascending order, 5-200°/s, for 1.2 minutes each.
  - Ten of the 12 preferred **15-35°/s**.
  - Withdrawals came mostly above 65°/s (three at 100°/s, two at 200°/s).
  - The authors set 25°/s as the threshold for switching to rotation snapping.
  - In the main experiments, rotation snapping cut SSQ by 40% and translation snapping by 50%.
  - [Farmani & Teather 2020, *Virtual Reality*, doi 10.1007/s10055-020-00425-x](https://www.csit.carleton.ca/~rteather/pdfs/VR_2020_cybersickness.pdf)
  - Caveats: the order was not counterbalanced, the rotation was passive, and the exposures were long.
- **Consumer game, N = 201** [M]. Kelly, Doty, Gilbert & Dorneich ran 20 minutes of *Jurassic World Aftermath* on Quest. Smooth turning ran at up to about **180°/s**; snap turning used 22.5° steps. The FOV restriction applied during translation only: the central 40° clear, a semi-transparent band out to 60°, black beyond, reaching full strength in about 100 ms.
  - SSQ totals: no mitigation 64.4, FOV restriction only 45.5, **snap turning only 33.7**, both together 58.1.
  - Snap turning had a significant main effect, and FOV restriction and snap turning interacted significantly.
  - Combining the two tools gave no further benefit, and sometimes sickness close to the no-mitigation group.
  - [*IEEE TVCG*, in press (NSF PAR author copy)](https://par.nsf.gov/servlets/purl/10591601)
- **Defaults and guidance** [G]. Meta's Web SDK defaults to smooth turning at **180°/s** and snap turns of 45°. It calls snap turning "best default for comfort" and smooth turning preferred by experienced users ([IWSDK turn](https://developers.meta.com/horizon/documentation/web/iwsdk-concept-locomotion-turn/)). For seated users, "artificial turning is necessary, since not all chairs spin" ([Locomotion comfort and usability](https://developers.meta.com/horizon/design/locomotion-comfort-usability/)).
- **What this means for Jon** [E]:
  - 150°/s is above the 60°/s drum peak and below the 180°/s game default.
  - A brief fast turn exposes him to less rotational optic flow than a slow long one: 90° takes 0.6 s at 150°/s and 3.6 s at 25°/s. That fits his finding that 90°/s felt too slow.
  - Snap turning is the best-supported single mitigation (Kelly; Farmani & Teather), but Jon has rejected it. Keep it available as a setting (it is: `snap`).

### 3.4 Vignettes (field-of-view restriction)

- **Fernandes & Feiner 2016** [M]. Thirty seated people took part over two days, one day with restrictors and one without, in counterbalanced order. FOV shrank as "a simple function of speed and angular velocity".
  - Sickness was significantly lower with the restrictors, presence was not, and people stayed in VR longer.
  - Most people with the subtler restrictor didn't notice it, and all who noticed said they would want it in future.
  - The group that had restrictors on the first day was least queasy overall (press report).
  - [IEEE 3DUI 2016, doi 10.1109/3DUI.2016.7460053; summary in News-Medical](https://www.news-medical.net/news/20160615/Researchers-develop-new-method-to-combat-VR-sickness.aspx)
- **Teixeira & Palmisano 2021** [M]. Forty people played *Marvel Powers United VR* for 10 minutes per session over three sessions. Dynamic FOV restriction significantly reduced cybersickness, and postural instability before exposure predicted how sick people got. [*Virtual Reality* 25:433, doi 10.1007/s10055-020-00466-2](https://ro.uow.edu.au/asshpapers/106)
- **Meta-analysis** [M]. Allison & Palmisano screened 4,622 records and included **97 studies**:
  - **peripheral FOV restriction** and **independent visual backgrounds** were consistently associated with less cybersickness;
  - **visual oscillation**, **multidimensional visual motion** and simulated off-vertical-axis rotation made it worse.
  - [*Multisensory Research* 2025, doi 10.1163/22134808-bja10181 (abstract via Semantic Scholar and Epistemonikos)](https://www.epistemonikos.org/en/documents/d98741ce00bf8461d40a29f033f6f03b52d8ef9a)
- **Guidance** [G]: vignette strength of about 0.4-0.6 as a default, scaled by input. Show it only while moving and fade it out quickly when you stop ([IWSDK slide](https://developers.meta.com/horizon/documentation/web/iwsdk-concept-locomotion-slide/)).
- **Caution** [M]: stacking two mitigations can backfire (Kelly et al., above). Add or change one comfort tool at a time.

### 3.5 Control and passive motion: is a glide tolerable?

- **Active control helps** [M]. A full-control "active" condition produced less sickness than a no-control "passive" one. A coupled active-passive condition reduced it most. [Stanney & Hash 1998, *Presence* 7:447](https://stars.library.ucf.edu/scopus1990/3252)
- **No study tests a glide.** I found none on momentum or inertia after a joystick is released. Two searches aimed at this returned nothing relevant.
- **Arguments for a glide** [E]:
  - Steady motion is the state the vestibular system cannot sense at all, so it is the least conflicting state.
  - A real glide slows at about 0.1 m/s², only about 1.5 times the vestibular detection threshold (Benson 1986).
  - A glide replaces the start-stop-start pattern that Bonato 2008 associates with more sickness.
  - The glide is predictable, and the stop stays under Jon's control (Stanney & Hash).
- **Arguments against** [E]:
  - Time spent moving goes up, and sickness grows with time in motion (So 2001).
  - Motion that carries on after he lets go is partly passive.
- **Net** [E]: start with a short, firm coast and lengthen it as Jon adapts. Always give him a hard stop that he controls.

### 3.6 Which way is "forward": head, controller or body?

- **Bowman, Koller & Hodges 1997** [M]:
  - In a task of moving to a point relative to a reference object, pointing-directed steering was faster than gaze-directed steering (median 9.60 s against 12.36 s).
  - In the absolute-motion task (straight to a target) they did not differ.
  - Their comparison table lists against gaze-directed steering: "steering and view are coupled", "requires much head motion", "can't look at object & move another direction".
  - [VRAIS 1997, pp. 45-53 (author copy)](https://people.cs.vt.edu/bowman/papers/travel_final.ps)
- **Developer experience** [V]: Cloudhead Games found "Tank Move", where the body turns separately from the head, better "because it meant you could look around while you moved" ([Road to VR, 2018](https://roadtovr.com/cloudhead-games-lessons-learned-five-years-vr-locomotion-experiments/)).
- **Meta's Web SDK** [G] chooses head-relative direction, to avoid "unintended strafing from controller grip" ([IWSDK slide](https://developers.meta.com/horizon/documentation/web/iwsdk-concept-locomotion-slide/)). Controller-relative direction would be worse here, because Jon's controllers point along a stick.
- **Studies of sickness are mixed.** Gaze-directed steering is sometimes found less sickening and sometimes not; the review in the earlier note found no consistent effect.
- **For hockey** [E]:
  - A skater looks at the puck, a teammate or over his shoulder while skating somewhere else.
  - Jon looks down at a puck that moves side to side as he handles it. With head-directed motion, every glance and every look at the puck bends his path.
  - So use a *body* heading: the rig's yaw, which the right stick turns, plus a slow follow of the head.

### 3.7 Other factors

- **No head-bob or stride oscillation in the camera** [M]. Visual oscillation makes cybersickness worse (Allison & Palmisano 2025).
  - Sixteen people watched 10 minutes of constant-speed forward flow, either plain or with vertical oscillation at 1.8, 3.7 or 7.4 Hz.
  - Oscillation gave stronger vection (5.51 against 3.56) and **about twice the SSQ total (58.2 against 29.7)**.
  - [Palmisano, Bonato, Bubka & Folder 2007, *Aviat. Space Environ. Med.* 78(10):951-956, doi 10.3357/asem.2079.2007](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.3357/asem.2079.2007&format=json&resultType=core)
  - Those frequencies bracket the measured stride rate of about 2.5 strides/s. Put the stride rhythm into sound (blade scrape) and controller buzz instead.
- **Leaning interfaces.** Seated HeadJoystick and standing NaviBoard improved enjoyment, presence and performance, and reduced motion sickness, compared with a handheld controller. This was in a task where people **moved and interacted with objects at the same time**, which is like stickhandling while skating [M, abstract]. [Hashemian et al., *IEEE TVCG* 30(8):4665, 2024](https://katalog.dhi-paris.fr/vufind/Record/NLM357026802/Description). This is a candidate for later, not for now: leaning would move the head that the stick is fitted around.
- **Frame rate** [M]. Of 60, 90, 120 and 180 fps, **120 fps** was the threshold above which people reported fewer sickness symptoms without losing the experience. [Wang et al. 2023, *IEEE TVCG* 29(5):2478](https://pubmed.ncbi.nlm.nih.gov/37027727/). Jon renders at 72 Hz; Quest 3 over Link also offers 90 and 120 Hz.
- **Adaptation** [M]. SSQ scores tend to fall over repeated sessions ([Frontiers in VR 2025, CSQ-VR study](https://www.frontiersin.org/articles/10.3389/frvir.2025.1518735/full)). Cybersickness can start within 10-20 minutes (Kelly et al.). A ramp across sessions is the usual route to more speed or glide.
- **Seated or standing** makes no difference to sickness, but standing raises presence. See the earlier note (Clifton & Palmisano 2019).

## 4. What shipped games do

| Title | Locomotion | Comfort notes | Source |
|---|---|---|---|
| NHL Sense Arena (Quest) | stationary drills, standing or room-scale; no artificial skating found | store rating "Comfortable" | earlier note; [QuestStoreDB](https://queststoredb.com/app/nhl-sense-arena-26-vr-hockey-3454538864674405/) [V] |
| Hockey Player VR (PC VR) | free skating anywhere on the rink; version 0.5 was a "complete rebuild - new skating"; a **speed boost** that "runs out each period" | one user found the skating slow, with little momentum | [developer site](https://hockeyplayervr.com/) [V]; earlier note |
| Pick-up League Hockey (Quest) | "realistic skating and braking forces"; sitting, standing and room-scale modes | no comfort information | [developer site](https://electricfalcon.net/pickuphockey/) [V] |
| Hockey VR (Melcher Studios) | "physics-based"; multiple control layouts; standing or room-scale; no locomotion details published | — | [Steam](https://store.steampowered.com/app/1769010/Hockey_VR) [V] |
| Slapshot: Rebound | flat-screen PC, not VR | — | earlier note |
| Skader (VR) | "unique ice-skating VR locomotion"; no details | short sessions by design | [press release](https://gamedeveloper.com/press-release/skader-out-now-on-steam-meta-quest-and-meta-rift) [V] |
| Sprint Vector | pull the world with your arms, plus a momentum system; very high speeds | reviewers called it comfortable ("without causing any nausea", Hardcore Gamer). Survios claims arm motion "tricks your brain" | [Road to VR review](https://www.roadtovr.com/?p=74585), [Hardcore Gamer](https://hardcoregamer.com/previews/run-at-high-speeds-in-vr-without-getting-nauseous-in-sprint-vector/249554/) [V] |
| Echo VR / Lone Echo | zero-g: grab and push off, hand-pointed thrusters, constant momentum; the head is placed 1:1 relative to the grabbing hand | a nausea risk for players new to zero-g, per reviewers | [Road to VR hands-on](https://roadtovr.com/hands-on-lone-echo-nails-zero-gravity-in-vr-with-oculus-touch/) [V] |
| Gorilla Tag and its successors | moving entirely with the arms, inspired by Echo | no published comfort data found | [Road to VR 2024](https://www.roadtovr.com/new-category-of-vr-game-arm-based-locomotion/) [V] |

Takeaways [E]:
- The games known for comfortable momentum tie motion to the arms, which matches the active-control evidence.
- Jon's hands are on the stick, so arm-swing, pulling and stride gestures fight the stick (see the earlier note).
- Hockey Player VR's limited boost is a design worth copying if Jon ever wants bursts above his comfortable cruising speed.

## 5. The trade-off

| Real skating | Comfort evidence says | Resolution [E] |
|---|---|---|
| top speed 8-9 m/s; play mostly at 2-5 m/s | sickness rises from 3 to 10 m/s with time moving (So 2001); Jon: 4 m/s was too fast | keep 3 m/s cruising. The 46 m rink keeps crossing times like 4 m/s on a regulation rink. Re-test 3.5-4 once the dynamics change |
| starts at about 4 m/s² over 0.5-1 s | "brief" (Meta), but profile shape made no difference (Widdowson) | bounded 4 m/s² push. It is still brief, and it removes the 20 m/s² onset |
| glides 30+ s if you don't stop | constant velocity is the least conflicting state, but passive motion and time in motion count against it | a short coast that Jon lengthens as he adapts, plus a stop he controls |
| hockey stop at 6-10 m/s² | short and deliberate | a trigger or a counter-stick stop at 5-6 m/s², with sound |
| turn radius grows with speed; pivots are fast | rotation is the most provoking axis; multi-axis motion is worse; brief fast turns are tolerated | 150°/s when slow; lateral acceleration capped at speed; the path carves with the view (no sideways skid) |
| backward 80%, sideways slow | lateral flow is no worse than forward (NASA, not significant) | 0.8 backward and 0.5 sideways, for realism |
| strides pulse speed at 2.5 Hz | oscillation makes sickness worse | no pulsing in the camera; pulse sound and buzz instead |

## 6. Recommendations for this project

All of these are starting values for A/B testing on Jon, not answers.

| # | Parameter | Current | Recommended | Why (evidence) |
|---|---|---|---|---|
| 1 | Release behaviour ("glide", new tuning setting) | exponential τ 0.15 s: 20 m/s² at the first instant, stopped in 0.45 s and 0.45 m | constant **coast deceleration 1.5 m/s²** (from 3 m/s: 2.0 s, 3.0 m). Step it down over sessions to 1.0 (3 s, 4.5 m), then 0.5. The range runs from 0.1 (real ice) to 20 (the current behaviour) | the real glide is about 0.1 m/s² [E]. No glide study exists. Steady motion is the least conflicting; start-stop cycles are worse (Bonato 2008); time in motion counts (So 2001); adaptation (§3.7). The sibling note suggests 1.0; start a step firmer because Jon gets sick easily |
| 2 | Hockey stop (new) | none: every release is a stop | **an analog index trigger** (both are unused in the code; Jon picks the hand, default the top hand). Full press gives a constant **6 m/s²** (from 3 m/s: 0.5 s, 0.75 m). Ice-spray sound and a short buzz. Also **stick held more than ~120° against the motion** brakes at 5-6 m/s², then skates the new way once below ~0.3 m/s (stop and go) | measured game peak −6.0 m/s² (Gamble); a maximal stop averages 8.5-10.3 m/s² [D from Winchester]; it puts the stop under his active control (Stanney & Hash) |
| 3 | Push acceleration | exponential τ 0.15: 20 m/s² at first, 95% of speed in 0.45 s | **4 m/s² bounded** forward, with about 0.2 s of easing at the top (0 to 3 m/s in about 0.85 s); 2 m/s² backward. Easing off the stick part-way coasts at the glide rate instead of braking | measured 4.06 m/s² peak (Gamble), about 4.0 over 6 m [D Winchester]. A real skater can't do 20 m/s². Speed-profile shape didn't affect sickness (Widdowson). Same as the sibling note |
| 4 | Which way is forward | head yaw | the **body heading**: the rig yaw that the right stick turns, plus a "lazy" follow of the head. Follow only when the head stays more than ~35° off the heading for over ~1 s, with a time constant of about 1 s [E]. Add a setting for pure rig yaw when seated in a fixed chair | Bowman 1997: you can't look one way and move another with gaze steering, and pointing beat it for relative motion. Hockey is played looking away from your path. Removes the 28 m/s² re-aiming on glances (sibling note) |
| 5 | Backward top speed | 100% of forward | **80%** | 6.56 m/s, about 80% of forward (Marino & Grasse 1993); Wu 2015 found 81% (sibling note) |
| 6 | Sideways top speed | 100% of forward | **50%**, with acceleration limited to the push rate | no measurement [E]; sideways movement in hockey is crossovers and shuffles. Lateral flow is no more comfortable than forward (NASA, not significant) |
| 7 | Turn rate against speed | 150°/s at any speed | **min(150°/s, A_lat/v)** with A_lat = 6 m/s²: 150°/s up to about 2.3 m/s, **about 115°/s at 3 m/s**. The velocity carves with the heading, with no sideways drift | the turn-rate limit is ω = a/v; speed skaters were measured at 5.3-6.3 m/s² (sibling note). Multi-axis motion is worse (meta-analysis). Keeps the fast pivot when slow, which Jon wants (90°/s felt too slow) |
| 8 | Turn easing | τ 0.08 s | keep | short and brief; no evidence for changing it |
| 9 | Top speed (`skate`) | 3.0 m/s | **keep 3.0** until changes 1-7 have been A/B tested; then try 3.5. Optionally add a limited boost (+1 m/s for about 2 s, a few per period) for breakaways | sickness rises 3→10 m/s (So 2001); 4 m/s was too fast for Jon; Hockey Player VR's limited boost [V]. The sibling note's hypothesis is that the 20 m/s² onsets, not the top speed, made 4 m/s feel too fast. Test that |
| 10 | Vignette | 0.7; driven by speed ×1.3 plus turn; closes at τ 0.08 s, opens at 0.25 s | **keep 0.7**, still driven by speed and turn rate. Keep it closed through a hockey stop (open it after the stop ends, not as speed falls). If turning still bothers him, weight rotation more heavily. Don't add another mitigation (snap, independent background) at the same time | FOV restriction works (Fernandes & Feiner; Teixeira & Palmisano; Kelly; meta-analysis). Combining tools can backfire (Kelly). Rotation is the more provoking axis (Terenzi & Zaal) |
| 11 | Camera stride motion | none | **keep none**. Stride rhythm (about 2.5/s) in sound and buzz only | oscillation makes sickness worse (meta-analysis). Oscillation at 1.8-7.4 Hz doubled SSQ (Palmisano et al. 2007) |
| 12 | AI skaters (`threes.py`) | ACCEL 5 in every direction; stops dead | the **same model as Jon**: push 4, glide, stop 5.5-6, A_lat/v turn cap, backward 0.8. Keep the cap at 95% of Jon's speed | consistent, readable hockey; the sibling note has the AI table. Fewer abrupt object motions in view [E] |
| 13 | Render rate | 72 Hz | try **90 Hz**, and 120 if the Python frame loop holds it, as a separate test | 120 fps threshold for fewer symptoms (Wang 2023) |
| 14 | Boards (if Jon's rig is ever confined) | not confined, as far as I could tell in the code | soft stop: remove the velocity into the boards over about 0.2 s, not instantly | Meta: "slow down before stopping, rather than an abrupt halt" [G] |
| 15 | Measurement | session logs (events, settings) | log time moving, acceleration events per minute above 2 m/s², mean and peak turn rate, and vignette time. Ask Jon for a 0-10 discomfort rating every 4 min (Kelly's method) and stop a test at 4 or more. Use 10-15 min sessions while adapting | individual thresholds vary widely (Terenzi & Zaal); sickness starts within 10-20 min (Kelly); 4 out of 10 was the "notable" level in Farmani & Teather |

### How the left stick would work (summary of 1-7)

- **Desired velocity.** The stick gives a desired velocity v\* in the body frame. Its magnitude follows the existing deadzone and power-2 curve. Its maximum is scaled on an ellipse: forward 1.0, backward 0.8, sideways 0.5.
- **Along your current motion:**
  - wanting more speed accelerates at 4 m/s²;
  - easing off, or the stick in the deadzone, coasts at the glide rate;
  - the stick held against the motion, or the trigger, brakes at the stop rate.
- **Across your motion:** the velocity's direction turns toward v\* at up to A_lat/|v|, so you carve and never snap sideways.
- **Right stick:** turns the body heading at up to min(150°/s, A_lat/|v|). The velocity rotates with it, so the optic flow stays mostly straight ahead.
- **Unchanged:** the 1 kHz physics still reads continuous rig segments, and the rig still turns about the head.

### Test order (one change at a time)

1. **Free skate, the same course each time:** round the circles, stop at the net, back up. Run each condition for 5-8 min, with a 0-10 rating every 2 min.
2. **First, bounded push (4 m/s²) with today's release.** This isolates the onset.
3. **Then the glide:** 1.5, then 1.0, then 0.5, each with the trigger stop.
4. **Then body heading against head heading.**
5. **Then the turn cap at speed.**
6. **Then 3.5 m/s.**
7. **Only then a short 3v3** (10 min).

## 7. Open questions

1. **What made the 3v3 sickening?** Candidates: speed, the 20 m/s² onsets, frequent turning while chasing play, looking around (which re-aimed his path), session length, or the many moving AI bodies. The session logs could answer part of this if they record his rig velocity and turn rate.
2. **Is a glide tolerable for Jon, and at what coast rate?** No study exists. This is the main experiment.
3. **Lazy-head parameters.** The deadband (~35°) and follow time (~1 s) are guesses. Does he play in a swivel chair, a fixed chair, or standing in a small space? That decides between rig yaw and lazy head.
4. **Trigger ergonomics.** Can he press an index trigger while gripping the stick, without braking by accident during shots? Which hand?
5. **Hockey turn kinematics are unmeasured:** lateral acceleration, radius against speed, pivot time. A_lat = 6 m/s² is borrowed from speed skating.
6. **Glide friction for hockey blades** rests on one sled test (Federolf 2008, via a summary), and drag area is assumed. This barely matters, since the recommended coast is far stronger than real ice.
7. **Can the prototype hold 90 or 120 Hz over Link** with its Python render loop?
8. **A seated leaning interface (HeadJoystick-style)** reduced sickness during simultaneous movement and interaction (Hashemian 2024). Would it work with a stick fitted around the head?
9. **Combining tools.** If Jon ever wants snap turning or an independent visual background as well as the vignette, Kelly et al. show the combination may not add up. Test it.
10. **Sources read only as abstracts or summaries:** Widdowson 2021 (profile shapes unknown), Fernandes & Feiner 2016 (FOV amounts), Teixeira & Palmisano 2021 (effect sizes), Allison & Palmisano 2025 (pooled effect sizes), Hashemian 2024 (sickness scores), Wang 2023 (sample size), Hu et al. 1989 (via So 2001 and Farmani 2020).

---

## Verification

Fact-check done 2026-11-09. I looked up each claim the recommendations rest on myself, in the primary source where I could get it (PDF, PubMed abstract via NCBI E-utilities, or the publisher's page). Verdicts: **confirmed** (the source says it, with these numbers and conditions), **corrected** (the source says something different; the right value is given), **unsupported** (no source found, or the source doesn't say it).

| # | Claim | Verdict | What the source says | Source checked |
|---|---|---|---|---|
| 1 | Current rig: 20 m/s² initial, 95% in 0.45 s, stops in 0.45 m | confirmed | `rig.py`: `MOVE_TAU = 0.15`, and each frame the velocity eases toward the target by `1 - exp(-dt/τ)`, both speeding up and slowing down. `sandbox_settings.json` has `skate: 3.0`. So 3/0.15 = 20 m/s² at the first instant (about 19 m/s² averaged over the first 72 Hz frame), 95% at 3τ = 0.45 s, and a total coast of v·τ = 0.45 m. One nuance: the code zeroes the velocity only below 0.01 m/s, which takes τ·ln 300 ≈ 0.86 s, so at 0.45 s you are still moving at 0.15 m/s. The code default `MOVE_MS` is 4.0; 3.0 is Jon's saved value. The 28 m/s² glance figure also checks: 3√2 / 0.15 = 28.3 m/s² | `prototype/rig.py` lines 20-23 and 176-199; `prototype/sandbox_settings.json` |
| 2 | Gamble 2022: peak acceleration +4.06 ± 0.43, deceleration −5.99 ± 0.64 m/s², peak speed 31.16 km/h | confirmed | 25 male varsity players (8 D, 17 F), 13 regular-season games, Kinexon UWB at 20 Hz. Table 4 (men, all players): 4.06 ± 0.43 and −5.99 ± 0.64 m/s². Peak speed 31.16 ± 1.64 km/h (Results) = 8.66 m/s. Events above \|2 m/s²\|: 45.2 accelerations, 57.8 decelerations, 66.5 turns. The zone fractions in §2 also check against Table 2 (D 33% and 65%, F 25% and 52%) | [Front. Physiol. 13:831723](https://www.frontiersin.org/articles/10.3389/fphys.2022.831723) |
| 3 | Winchester 2007: stop from 8.39-8.61 m/s in 0.81-0.84 s over 4.12-4.43 m, mean 8.5-10.3 m/s² | **corrected** | Table 3 (n = 15 male Junior B, three blade hollows):<br>- initial velocity 8.389, 8.613 and **8.345** m/s, so the approach range is **8.35-8.61 m/s**;<br>- stopping time 0.812-0.836 s;<br>- distance 4.120-4.433 m.<br>The derived means are **8.0-8.5 m/s² by v²/2d** and **10.0-10.4 m/s² by v/t**: about **8-10.4 m/s²** overall, not 8.5-10.3.<br>Conditions: a maximal two-foot parallel side stop after a 48.8 m sprint, on 30 fps video split into 60 Hz fields, with a 6 Hz filter. The initial velocity is the *peak hip* velocity, but the stop distance and the end of the stop come from an *ankle* marker. That may be why d is longer than v·t/2. If the stop really is longer than v·t/2, the deceleration comes late and peaks above 10 m/s² | [Brock MSc thesis PDF, Table 3 and Glossary](https://brocku.scholaris.ca/items/60f8f3f1-9231-4162-b342-80cf75a80345) |
| 4 | Winchester 2007: 3.43-3.46 m/s average over the first 6 m (≈ 4.0 m/s²); 2.42-2.52 strides/s | confirmed | Table 3: average hip velocity over 6 m was 3.457, 3.428 and 3.448 m/s, and stride rate 2.464, 2.420 and 2.515 strides/s. The 6 m starts at the first hip movement of a front start. Constant-acceleration equivalent: 2·6/(6/3.45)² = 3.97 m/s². The stride rate is for the first 6 m of a sprint start, not for cruising | same thesis, Table 3 and Glossary (AV, SR) |
| 5 | Marino & Grasse 1993: backward 6.56 m/s, about 80% of forward | confirmed | Ten skilled male players, maximum-effort backward C-cut trials, filmed overhead at 100 Hz. Mean backward speed 6.56 m/s, and "backward speed averaged about 80% of forward speed". The abstract gives no absolute forward speed | [ISBS 1993 proceedings](https://ojs.ub.uni-konstanz.de/cpa/article/view/1699) |
| 6 | de Koning 1992: μ = 0.0046 straights, 0.0059 curves | confirmed | PubMed abstract: instrumented skates during actual speed skating. Mean μ 0.0046 on straights and 0.0059 on curves; minimum near −7 °C ice; μ rises with speed. These are speed skates on speed-skating ice, not hockey blades on hockey ice | [PMID 1517252, J. Biomech. 25(6):565-571](https://pubmed.ncbi.nlm.nih.gov/1517252/) |
| 7 | Benson 1986: thresholds 0.063 (X), 0.057 (Y), 0.154 (Z) m/s²; 24 subjects, 3 s cosine bells | confirmed | The PubMed abstract gives these values exactly. They are thresholds for detecting the *direction* of motion (p = 0.67 correct). In 8 subjects the X threshold rose with stimulus duration from 0.98 to 6.96 s, so a long, steady glide deceleration is harder to sense than a 3 s pulse | [PMID 3790028](https://pubmed.ncbi.nlm.nih.gov/3790028) |
| 8 | So, Lo & Ho 2001: nausea and vection rise from 3 to 10 m/s, level off above 10 | confirmed | 96 Chinese male students, 12 per speed (between subjects), a 30 min head-steered tour of a virtual city on a fixed path, RMS fore-aft speeds 3.3-59.2 m/s.<br>- Nausea and vection ratings rose significantly from 3 to 10 m/s, then stabilised.<br>- Speed changed onset times, not how fast ratings grew with exposure time.<br>- Of the SSQ scores, speed affected only the **oculomotor** subscore, not the total or the nausea subscore | [author PDF, abstract and Table 1](https://www.ieda.ust.hk/dfaculty/so/pdf/So-et-al-2001a-HumanFactors.pdf) |
| 9 | Terenzi & Zaal 2020: forward 1.18, lateral 0.89 m/s, yaw 0.473 rad/s; accelerating forward 0.70 m/s², yaw 0.478 rad/s²; rotation lower | confirmed | Table 4 matches exactly: FS 1.183 (SD 0.836), LS 0.890 (0.594), RS 0.364, YS 0.473 (0.381), FA 0.700 (0.481), LA 0.586, RA 0.474, YA 0.478.<br>n = 18, median age 24, 9 with no VR experience. Heads were held still, for 5 s steady runs and 3 s accelerating runs.<br>Translation against rotation was significant. Forward against lateral was not (p = 0.17 steady, 0.36 accelerating).<br>The authors recommend per-user tuning. Time constants: 1.82 s (translation) and 3.78 s (rotation) | [NTRS 20200000787](https://ntrs.nasa.gov/api/citations/20200000787/downloads/20200000787.pdf) |
| 10 | Farmani & Teather 2020: 10 of 12 preferred 15-35°/s; withdrawals mostly above 65°/s; snapping cut SSQ 40% | confirmed | Twelve students saw 11 speeds, 5-200°/s, in fixed ascending order, 1.2 min each (13 min in all).<br>- "Preferred rotation speed was between 15 and 35°/s (chosen by 10 participants)".<br>- Withdrawals came "usually … higher than 65°/s": three at 100°/s and two at 200°/s.<br>- Abstract: snapping cut SSQ by 40% for rotation and 50% for translation.<br>- A score of 4/10 was where nausea "started becoming more notable" | [author PDF](https://www.csit.carleton.ca/~rteather/pdfs/VR_2020_cybersickness.pdf) |
| 11 | Hu et al. 1989: drum sickness peaks at 60°/s over 15-90°/s (secondary) | confirmed (now from the primary source) | The primary abstract: 60 subjects, the drum at one of 15, 30, 60 or 90°/s. Symptoms rose up to 60°/s and fell at 90°/s, and tachygastria tracked them. Farmani & Teather misdate it as 1999 | [PMID 2730483, Aviat. Space Environ. Med. 60(5):411-414](https://pubmed.ncbi.nlm.nih.gov/2730483/) |
| 12 | Kelly et al.: SSQ none 64.4, FOV 45.5, snap 33.7, both 58.1 (N = 201) | confirmed | Table 1 totals: 64.37, 45.48, 33.73, 58.11. Quest 2 running Jurassic World Aftermath for up to 20 min; smooth turning about 180°/s, snap 22.5°.<br>The FOV restriction was all-or-nothing, came on within about 100 ms, and applied **during translation only**; it was not scaled by speed. It kept the central 40° clear, a semi-transparent band out to 60°, and black beyond.<br>In the ANCOVA the FOV main effect was not significant (p = .99), but FOV-only against none was (p = .013). Both tools together were worse than snap alone (p = .011) and no different from no mitigation.<br>Now published: *IEEE TVCG* 31(9):5704-5712, 2025, doi 10.1109/TVCG.2024.3470214 | [NSF PAR author copy](https://par.nsf.gov/servlets/purl/10591601); [PMID 39331562](https://pubmed.ncbi.nlm.nih.gov/39331562/) |
| 13 | Widdowson et al.: no SSQ or sway difference among three speed profiles | confirmed | PubMed abstract: linear motion (experiment 1) and circular motion (experiment 2), three profiles each, 2 min trials standing, viewed passively. "No convincing evidence to support the common belief that constant speed is more comfortable". The abstract does not give the profiles or the sample sizes | [PMID 31651196, Hum. Factors 63(2):296-311](https://pubmed.ncbi.nlm.nih.gov/31651196/) |
| 14 | Palmisano et al. 2007: SSQ 58.2 against 29.7; vection 5.51 against 3.56; n = 16; 1.8, 3.7, 7.4 Hz | confirmed | PubMed abstract: 16 subjects watched 10 min of constant-velocity forward flow, with or without vertical oscillation at 1.8, 3.7 or 7.4 Hz. SSQ total 58.18 against 29.67; vection 5.51 against 3.56 | [PMID 17955943](https://pubmed.ncbi.nlm.nih.gov/17955943/) |
| 15 | Allison & Palmisano 2025 meta-analysis (97 studies) | confirmed | Abstract: 4,622 records screened, 97 studies included. Peripheral FOV restriction and independent visual backgrounds reduce cybersickness. Visual oscillation, multidimensional motion and simulated off-vertical-axis rotation make it worse. The abstract reports no result for velocity | [Epistemonikos record, doi 10.1163/22134808-bja10181](https://www.epistemonikos.org/en/documents/d98741ce00bf8461d40a29f033f6f03b52d8ef9a) |
| 16 | Fernandes & Feiner 2016: dynamic FOV restriction reduces sickness without losing presence (30 people, two days) | confirmed (from a press summary only) | News-Medical: 30 participants, counterbalanced across two days. FOV was reduced as "a simple function of speed and angular velocity". Sickness was significantly lower, presence was unchanged, and people stayed longer; most didn't notice the subtler restrictor. I did not reach the paper itself, and "seated" is not confirmed | [News-Medical](https://www.news-medical.net/news/20160615/Researchers-develop-new-method-to-combat-VR-sickness.aspx) |
| 17 | Bowman et al. 1997: median 12.36 s (gaze) against 9.60 s (pointing); "can't look at object & move another direction" | confirmed | Table 1 (relative-motion task, no reversal): gaze-directed 12.36 s, pointing 9.60 s; pointing was significantly faster. Table 2 lists "can't look at object & move another direction" as a drawback of gaze steering. The absolute-motion task showed no difference. "Pointing" here means steering with the hand, not with the body | [author copy (PostScript)](https://people.cs.vt.edu/bowman/papers/travel_final.ps) |
| 18 | Stanney & Hash 1998: active < passive; coupled active-passive lowest | confirmed | Abstract: active control reduced symptoms compared with passive, "but did not do so as completely as" the coupled active-passive condition | [Presence 7(5):447-459](https://stars.library.ucf.edu/scopus1990/3252) |
| 19 | Meta: walk 1.4, run 2.8 m/s; brief, infrequent accelerations; slide 4-6 m/s; vignette 0.4-0.6; smooth turn 180°/s; snap 45° | confirmed | - Comfort page: "walking ~3 mph/1.4 m/s, running ~6 mph/2.8 m/s".<br>- Best-practices page: "Keep acceleration events brief and infrequent".<br>- IWSDK slide page: "Keep maxSpeed reasonable (4–6 m/s)", and "0.4–0.6 is a common default" for the vignette.<br>- IWSDK source: `turn.ts` defaults to `turningSpeed: 180`, `turningAngle: 45` and snap turning; `slide.ts` defaults to `maxSpeed: 5` and `comfortAssist: 0.5` | the four Meta pages cited in §3.1-3.4; [meta/immersive-web-sdk](https://github.com/meta/immersive-web-sdk) |
| 20 | Wang et al. 2023: 120 fps the threshold for fewer symptoms (60/90/120/180 tested) | confirmed | Abstract: "120fps is an important threshold for VR. After 120fps, users tend to feel lower SS symptoms". The abstract does not give the sample size | [PMID 37027727](https://pubmed.ncbi.nlm.nih.gov/37027727/) |
| 21 | Turn cap min(150°/s, 6/v), about 115°/s at 3 m/s; A_lat from Kimura & Yokozawa, 5.3-6.3 m/s² | confirmed (as an estimate) | Kimura & Yokozawa 2024: 14 elite women in a World Cup 3000 m, on the inner curve, at 11.85-12.41 m/s on radii of 25.6-29.0 m, with centripetal acceleration of 5.31-6.25 m/s².<br>The arithmetic holds: 6/3 = 2.0 rad/s = 115°/s, and the cap reaches 150°/s at 2.29 m/s.<br>Applying long-track skating at 12 m/s to hockey turns at 2-4 m/s is an extrapolation. No hockey measurement exists | [Front. Sports Act. Living, doi 10.3389/fspor.2024.1396219](https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2024.1396219/full) |

The recommendations also cite some sources that are not in the claim list. I checked these too:
- **Bonato et al. 2008** (*Presence* 17(3):283-292): confirmed from the abstract. Over 5 min, steadily *expanding* flow was less sickening than flow that alternated between expanding and contracting. It tested reversals of motion direction, not stopping and starting.
- **Teixeira & Palmisano 2021** (*Virtual Reality* 25:433-445): confirmed. 40 people played Marvel Powers United VR in three 10 min sessions. Dynamic FOV restriction significantly reduced sickness, and postural sway before exposure predicted how sick people got.
- **Hockey Player VR's limited boost:** confirmed. The developer site says "it runs out each period".
- **Vignette constants** in `sandbox.py` (×1.3, τ 0.08 s to close and 0.25 s to open, strength 0.7): confirmed.

### What changes in the recommendations

Every recommendation still stands as a starting value for A/B testing. The changes are to the evidence and to a few numbers.
- **No claim was unsupported.**
- **#2, hockey stop.** Change "8.5-10.3 m/s²" to **about 8-10.4 m/s²**, from an approach of 8.35-8.61 m/s. The time and distance disagree, so a maximal stop probably peaks above 10 m/s². 6 m/s² is still a sensible comfort value: it equals the measured game peak and is well below a maximal stop.
- **#1, glide.** The value stands, but its "why" overstates two sources:
  - Bonato 2008 tested reversals of direction (expanding against contracting flow), not stopping and starting. "Start-stop vection changes are more sickening" is an extrapolation.
  - So 2001 held speed constant for 30 min, so the idea that time spent moving adds to sickness is an inference.
  - Benson's thresholds rise with stimulus duration, so a slow, steady coast is even harder to feel than the 0.06 m/s² figure suggests.
  - Tag the glide argument [E] throughout.
- **#9, top speed.** Keeping 3.0 stands.
  - In So 2001, speed raised the nausea and vection *ratings* but, of the SSQ scores, only the oculomotor subscore.
  - The project record is inconsistent about the 3v3 speed. `rig.py` says "6 felt too fast in the 3v3" (code default 4), and the README says the AI skated 5.8 m/s "to your 4"; the brief says 4 felt too fast. Ask Jon which speed was too fast before treating 4 m/s as the known limit.
- **#10, vignette.** It stands, but Kelly's 45.5 against 64.4 came from an all-or-nothing restriction applied only while translating, not a speed-scaled one like Jon's. For the dynamic kind, cite Fernandes & Feiner and Teixeira & Palmisano. Update the Kelly citation to the published paper (TVCG 31(9), 2025).
- **#7, turn cap.** The arithmetic holds, and A_lat is confirmed for elite long-track skaters at 12 m/s. For hockey at 3 m/s it remains a low-confidence estimate.
- **#13, render rate.** Wang found the benefit at 120 fps and above, so 90 Hz on its own may not reduce symptoms. Try 120 Hz first if the frame loop can hold it.
- **#11, stride motion.** It stands. The 2.42-2.52 strides/s are from the first 6 m of a sprint start, so cruising strides are slower, but still near the 1.8 Hz condition in Palmisano 2007.
- **#15, measurement.** "Sickness can start within 10-20 min" is Kelly citing earlier work, not Kelly's own result. The rest holds.
