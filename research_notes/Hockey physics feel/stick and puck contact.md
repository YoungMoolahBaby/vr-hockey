# Stick and puck contact, and real puck speeds

Research round on "making it feel physically like hockey", 2026-11-09. Topic: how a puck behaves against a stick blade (restitution, friction, temperature), real puck speeds by skill level, stickhandling and pass reception, what makes a puck feel heavy. Values the project uses now: `blade_pop` 0.15 (Jon; code default 0.20), the low-speed bounce fade `Params.soft_hands` 3.0 m/s, `blade_grip` 0.35, `puck_mass` 0.170 kg, `BLADE_MASS` 0.15 kg on a flex spring with damping 0.60 (puck.py).

Tags: **[measured]** = a number someone measured (source given). **[derived]** = my arithmetic on measured numbers. **[estimate]** = my judgement. **[sim]** = I ran the project's own physics (compiled path, `physics_core`) in a scratch script without changing any code. **[coaching]** = coaching material, not measurement.

## The short version

1. **In our sim, `blade_pop` and the low-speed bounce fade do almost nothing.** The blade has a mass of 0.15 kg, less than the puck's 0.17 kg, and hangs on a damped spring. A puck hitting a still blade comes back at 15-17% of its speed whatever `blade_pop` is (0.15 to 0.50), and with the fade on or off **[sim]**. What sets the bounce is the flex damping (0.60) and the blade mass. That is honest physics: a light, loosely held stick can't bounce a heavy puck back much. But it means the sandbox "pop" slider is close to a placebo.
2. **The fade has the physics backwards.** Rubber's restitution goes *up* at low impact speeds, not down. A puck dropped at low speed rebounds at about 0.50; at 85 mph against a rigid plate it rebounds at 0.34 **[measured]**. A fade to zero below 3 m/s is an assist in form, though inert in effect today. Remove it.
3. **A frozen puck's restitution is about 0.27** (edge impact against a rigid plate at 55 mph, puck at 25 °F), against 0.39 at room temperature **[measured]**. Set `blade_pop` to about 0.30 and leave it there.
4. **Puck on cloth tape: friction 0.43-0.50; on a grippy blade sticker: 0.69** **[measured]**. But our puck has no spin, so friction acts on its sliding only. In a contact where the puck should roll along the blade, our puck loses up to 3x too much speed along the face **[derived]**.
5. **Jon's 40-46 mph (18-21 m/s) shots fit an adult recreational wrist or snap shot.** Adult recreational slap shots measure 22-23 m/s (50-52 mph). Elite wrist shots measure 27-29 m/s (61-66 mph). Elite 13-year-olds' snap shots measure 18-20 m/s **[measured]**. I estimate recreational adult wrist shots at about 17-20 m/s **[derived]**.

## Findings

### 1. Restitution of a puck: speed and temperature

Anderson & Smith (WSU, 2007; later published as Bigford & Smith, J. ASTM Int. 6(7), 2009, doi:10.1520/JAI101859) fired recreational pucks edge-first from an air cannon at a rigid plate on load cells, timed with light gates. COR = rebound speed / inbound speed. The values below are read off their Figures 4-6 (the text gives only the trends) — [PDF](https://ssl.wsu.edu/documents/2015/10/experimental-characterization-of-ice-hockey-sticks-and-pucks.pdf/):

| Condition | COR | Dynamic stiffness |
|---|---|---|
| 55 mph, 72 °F, brand A / brand B | 0.38 / 0.35 | ~10,900 / ~7,300 lb/in |
| 72 °F, drop test (plotted at ~15 mph, from Haché) | 0.50 (bar 0.45-0.55) | |
| 72 °F at 55 / 65 / 75 / 85 mph | 0.39 / 0.375 / 0.36 / 0.34 | ~10,000 → ~15,000 lb/in |
| 55 mph at 72 / 55 / 47 / 40 / 33 / 28 °F | 0.39 / 0.32 / 0.30 / 0.272 / 0.268 / 0.27 | ~11,000 → ~80,000 lb/in |

- **[measured]** "The COR decreased linearly with increasing speed" at room temperature. The slope is about −0.0017 per mph (−0.0037 per m/s) **[derived from the figure]**. Stiffness rises with speed: the puck "behaves as a non-linear spring".
- **[measured]** Freezing cut COR by 32% and raised stiffness by over 600%. The COR **plateaus at about 0.27 below about 40 °F (4 °C)**. The authors suggest "the plateau ... may also occur with speed at low temperature", so a frozen puck's COR may be nearly flat across speeds. That last part is their conjecture; they did not test it.
- **[measured]** Two recreational brands differed by 10% in COR and 33% in stiffness.
- **Haché's drop test.** As quoted from *The Physics of Hockey* (2002) in a Kansas City Star piece: a puck "rebounds with between 45 and 55 percent of its original velocity" off concrete or ice. A frozen and a warm puck dropped on concrete "bounce to about 12 percent and 27 percent of their original height, respectively" — [reprint](https://www.jewelsfromthecrown.com/why-hockey-pucks-are-frozen-kansas-city-star/). Bounce height scales as COR², so these mean **COR ≈ 0.35 frozen and ≈ 0.52 warm** **[derived]**.
  - **A citation slip to watch for.** The WSU paper cites Haché as giving drop-test COR "0.45-0.55 at room temperature and 0.12-0.27 for frozen pucks". The 0.12 and 0.27 are Haché's bounce *heights*, not his restitution. Our earlier note (`VR hockey stick and puck feel/hockey_hands_science.md`) repeats the 0.12-0.27 figure. The best numbers for a frozen puck are 0.27 at 55 mph (WSU cannon) and about 0.35 at drop-test speeds (from Haché's heights).
- **Contact time** **[derived]**: t ≈ π√(m/k) from the WSU stiffness gives about 0.35 ms frozen (k ≈ 80,000 lb/in = 14 MN/m) and about 0.9 ms warm. That fits Plesch et al.'s estimate that a slap shot's blade-puck collision is "certainly less than a millisecond" ([arXiv:1903.02635](https://arxiv.org/html/1903.02635)). So a single puck impact is an instant compared with our 0.25 ms substep, and an impulse model is right.

**Why cold pucks are "dead".** Haché: freezing makes the puck "slide better and bounce less, owing to its increased stiffness" ([reprint](https://www.jewelsfromthecrown.com/why-hockey-pucks-are-frozen-kansas-city-star/)). For rubber in general, as temperature falls toward the glass transition the rubber "becomes increasingly stiff or 'logy,' loses resilience". Resilience reaches a minimum somewhat above the glass transition temperature ([ASTM D832, low-temperature conditioning of rubber](https://softbank.iust.ac.ir/Railway/Codes/ASTM-standard/ASTM_2004_Standards/ASTM%202004%20PART%20IIB/ASTM%202004%20Volume%2009.01%20Rubber,%20Natural%20and%20Synthetic%20--%20General%20Test%20Methods_%20Carbon%20Black/D%20832%20-%2092%20R97%20%20_RDGZMI05MLI5NW__.pdf)). **[estimate]** A sub-millisecond impact is a very high-frequency load, which pushes the puck rubber's effective transition upward. That would explain why a puck only a few degrees below freezing already sits on the low-COR plateau.

**Game practice.** Since 2019 the NHL has used thermochromic pucks whose logo turns from purple to clear above freezing, so officials can swap warm pucks ([ASU Global Sport Matters](https://live-global-sport-matter.ws.asu.edu/business/2019/10/07/if-its-purple-its-perfect-nhl-using-thermochromic-coating-to-id-ideal-puck-temp/), [Cronkite News](https://cronkitenews.azpbs.org/2019/10/07/nhl-hockey-puck-color-change/)). The NHL's Dan Craig: "Freezing a puck eliminates bouncing" (secondary). So a game puck sits at or below about 0 °C, which is on the WSU plateau (COR ≈ 0.27 at 55 mph).

### 2. What restitution means at a held stick

A COR is measured against a rigid plate. A stick is not rigid, and it is not much heavier than the puck.

- **[derived]** WSU's stick moments of inertia, about a pivot 35 in up from the blade, are 8,753-11,658 oz·in² (0.160-0.213 kg·m²). The effective mass of a free stick at its blade is I/Q² = **0.20-0.27 kg**, close to the puck's 0.17 kg. With rigid-body impact maths, the puck's rebound off a stationary free stick is v·(e − r)/(1 + r), where r = m_puck / M_eff ≈ 0.63-0.85. For e ≈ 0.3 that is *negative*: the puck keeps creeping forward and the stick recoils. Any bounce back comes later, from the grip and the shaft spring returning energy.
- **[coaching]** HockeyShot: grip the stick tightly and "the puck will bounce off a rigid stick like it does the boards" ([HockeyShot](https://hockeyshot.com/blogs/training-academy/hockey-skills-how-to-effectively-receive-a-pass)). So in real hockey the hands decide how much the puck bounces back, not the rubber.
- **[measured, stick side]** WSU fired 50 mph pucks at a pivoted stick and found 21% spread in "performance" between sticks: composite 95.6 mph, wood 75.6 mph predicted puck speed. I could not reconcile their collision-efficiency arithmetic with the rigid-body formula, so I use only the relative result.

**[sim] What our model does.** Setup: the `tests/test_soft_hands.py` `_sweep` harness (blade square to +z, flex 70, `ice_mu` 0.085), with runtime overrides only. "Peak rebound" is the puck's peak speed back off a still blade divided by its incoming speed:

| Blade mass, flex damping | v = 1.5 m/s, pop 0.15 / 0.30 / 0.50 | v = 3 | v = 10 | v = 20, pop 0.15 / 0.30 |
|---|---|---|---|---|
| **0.15 kg, 0.6 (current)** | **0.15 / 0.15 / 0.14** | **0.17 / 0.16 / 0.16** | **0.17 / 0.17 / 0.16** | **0.17 / 0.17** |
| 0.15 kg, 0.3 | 0.25 / 0.24 / 0.22 | 0.27 / 0.26 / 0.24 | 0.27 / 0.27 / 0.24 | 0.27 / 0.27 |
| 0.15 kg, 0.1 | 0.36 / 0.34 / 0.33 | 0.38 / 0.37 / 0.34 | 0.39 / 0.37 / 0.35 | 0.39 / 0.38 |
| 0.30 kg, 0.6 | 0.09 / 0.09 / 0.10 | 0.10 / 0.09 / 0.11 | 0.10 / 0.10 / 0.11 | 0.10 / 0.10 |
| rigid blade, 0.6 | 0.13 / 0.27 / 0.45 | 0.14 / 0.28 / 0.47 | 0.14 / 0.29 / 0.48 | 0.14 / 0.29 |

- With the current blade, `blade_pop` changes the rebound by at most 0.02 of the incoming speed. The flex damping changes it 0.17 → 0.27 → 0.38. Only a rigid blade makes `pop` matter. The rigid-blade row reproduces `pop`, which checks the measurement.
- Shots don't depend on `pop` either:
  - A wrist-like push (1.2 m/s, then a ramp to 15 m/s over 60 ms) gives a 16.7 m/s puck for pop 0.15, 0.27 and 0.50.
  - A slap-like strike at 20 m/s gives 25.2 / 25.2 / 25.0 m/s.
  - A one-timer (8 m/s pass into a 12 m/s swing) gives 15.4 / 15.4 / 15.2 m/s.
  - That fits real shots, where the puck rides the blade for 15-38 ms: 20 ± 2 ms for a pro slap shot and 15 ± 2 ms for a one-timer ([Swarén et al. 2019](https://www.scitepress.org/publishedPapers/2019/83516/pdf/index.html)); 38 ± 9 ms elite versus 27 ± 5 ms recreational for slap shots (Villaseñor et al. 2006, J Appl Biomech 22:202, as quoted in [Laliberte 2009](https://thesportjournal.org/article/biomechanics-of-ice-hockey-slap-shots-which-stick-is-best/)). A shot is a push, not a bounce.
- **[estimate]** The model's 0.15-0.17 rebound off a still blade is plausible for a normally held stick. I found no measurement of a puck's rebound off a hand-held stick.

### 3. Is the low-speed bounce fade honest?

No.

- **[measured]** A puck's own COR rises as impact speed falls: 0.50 in a drop test against 0.34-0.39 at 55-85 mph (WSU, above).
- **[theory]** For viscoelastic disks, restitution "approaches one for small velocities and decreases for increasing velocities" ([Schwager 2007, Phys. Rev. E 75, 051305; arXiv cond-mat/0701142](https://arxiv.org/abs/cond-mat/0701142)).
- So a fade to zero bounce below 3 m/s runs against the material. Low bounce in real stickhandling has other causes: the stick's light effective mass (section 2), loose hands, a closed (cupped) blade, and the hands moving with the puck. Our model already captures the first and the last.
- **[sim]** With the current 0.15 kg blade the fade makes no measurable difference: at 1.0 / 1.5 / 3.0 m/s the peak rebound is 0.13 / 0.15 / 0.17 with or without it. With a rigid blade it would matter a lot: at 1.0 m/s it cuts the rebound from 0.24 to 0.03, and at 1.5 m/s from 0.27 to 0.09. So it is an assist that happens to be inert now and would wake up if the blade got heavier.
- **Naming:** the fade is `Params.soft_hands`, while the rejected possession assist is `Params.magnet`. Its UI and comment text call the magnet "soft hands" too. Jon said he likes "softhands off", meaning the magnet. The fade is still on (3.0).

### 4. Friction between puck and blade

- **[measured, preprint]** Plesch, Plesník & Ružičková (2019) slid a puck on its edge, caged so it couldn't turn, along blade coverings, pulled by a hanging mass and filmed. They found ([arXiv:1903.02635](https://arxiv.org/html/1903.02635)):
  - grip sticker (Specter): μ = 0.69 ± 0.02
  - cloth tape (Renfrew): 0.46 ± 0.07 lengthwise, 0.43 ± 0.08 and 0.50 ± 0.11 across the tape's ridges
  - Puck temperature and sliding speed were not stated. Rubber friction depends on both, so treat these as room-temperature, slow-sliding values.
- **[measured, preprint]** The same study had 13 players, amateur to NHL. The harder, rougher sticker raised shot speed by a few percent and puck rotation by about 6%. The exact percentages are in our earlier note; I did not re-verify them this round.
- **[derived] Spin matters.** Our puck has no spin. Where the blade grips the puck instead of sliding over it (short of the μ cap), the code removes *all* of the puck's sliding speed along the face. A real puck would roll: a disc's moment of inertia is ½mR², so friction stops the sliding once the puck has lost only **1/3** of its speed along the face, and the rest becomes spin. In glancing contacts where the puck slides the whole time, the two agree. So the model over-damps the "puck rolls along the blade" cases (toe drags, a puck run along the face) by up to 3x. A lower `blade_grip` partly hides this. Adding a spin term (one scalar about the vertical axis) is the honest fix. It would also give realistic spin off the boards.

### 5. Real puck speeds

**Shots** (1 m/s = 2.237 mph):

| Shot | Level | Speed | Method | Source |
|---|---|---|---|---|
| Slap, stationary | adult recreational ("unskilled") | 23.3 ± 3.8 m/s (52 mph) | radar, n = 10 | [Pearsall et al., ISBS 2001](https://ojs.ub.uni-konstanz.de/cpa/article/view/3779) |
| Slap, stationary | varsity ("skilled") | 30.0 ± 2.5 m/s (67 mph) | radar, n = 10 | same |
| Slap, stationary | recreational / elite | 22.3 ± 3.2 / 33.6 ± 5 m/s (80.3 / 120.8 km/h) | n = 5 / 4 | Villaseñor et al. 2006, via [Laliberte 2009](https://thesportjournal.org/article/biomechanics-of-ice-hockey-slap-shots-which-stick-is-best/) |
| Slap, at rest / moving | 9 players (1974) | 26.9 ± 1.5 / 29.0 ± 1.4 m/s | microphone timing | [Doré & Roy 1975, Polytechnique Montréal EP-R-75-19](https://publications.polymtl.ca/10039/) |
| Slap / one-timer | 2 DEL pros | 36.4 ± 1.0 / 38.0 ± 2.7 m/s (81 / 85 mph) | on-ice motion capture | [Swarén et al. 2019](https://www.scitepress.org/publishedPapers/2019/83516/pdf/index.html) |
| Wrist / slap, stationary | 10 Junior A, university and pro | 27.4-27.9 / 31.7-32.0 m/s (61-62 / 71-72 mph) | Vicon, synthetic ice | [Léger et al. 2022, Sensors 22:3419](https://pmc.ncbi.nlm.nih.gov/articles/PMC9105185) |
| Wrist / slap, best of 5 | 20 pro and semi-pro (Slovakia) | 105.6 ± 10.0 / 125.2 ± 12.6 km/h (29.3 / 34.8 m/s; 66 / 78 mph) | radar, on ice | [Bezák & Přidal 2017, Acta Gymnica 47(2)](https://gymnica.upol.cz/doi/10.5507/ag.2017.007.html) |
| Wrist / slap, average | (Worobets et al. 2006) | 96.5 / 124.9 km/h (26.8 / 34.7 m/s) | — | as cited by Bezák & Přidal 2017 |
| Wrist / snap (long-hand, short-hand), pre-training | elite U14, age 13.6 | 60.0 / 70.8 / 66.4 km/h (16.7 / 19.7 / 18.4 m/s; 37 / 44 / 41 mph) | radar | [Novak et al. 2022, J Hum Kinet 82:191](https://pmc.ncbi.nlm.nih.gov/articles/PMC9465741) |
| "Typical maximum" wrist / slap | — | 20 / 30 m/s | — | Pearsall et al. 1999, as cited in [Woo et al., ISBS 2004](https://ojs.ub.uni-konstanz.de/cpa/article/view/1368/1387) |
| NHL hardest shots | NHL | 101.9-103.0 mph (2025-27 seasons) | NHL EDGE tracking | [NHL.com](https://www.nhl.com/news/nhl-edge-stats-leaders-for-2025-2026-season) |
| NHL top shot speed, average by position | NHL | about 84.5 mph forwards, 88.9 mph defence | NHL EDGE | [edge.nhl.com player page](https://edge.nhl.com/en/skater/8477384) (from a search snippet; medium confidence) |

- **Recreational adult wrist shot.** I found no primary measurement. The McGill study of 10 elite against 10 recreational players on ice reports that elite and skating shots were faster, but I could not reach its numbers ([Robbins et al. 2021, J Sports Sci 39(9)](https://www.tandfonline.com/doi/full/10.1080/02640414.2020.1853336)). **[derived]** Slap/wrist ratios in the elite studies are 1.15-1.29. Applied to recreational slap shots of 22.3-23.3 m/s, that gives a **recreational wrist shot of about 17-20 m/s (39-45 mph)**. Forum self-reports of adult rec wrist shots "in the 40s" to the high 50s mph agree loosely ([HFBoards thread](https://forums.hfboards.com/threads/how-hard-can-you-or-your-kid-shoot-the-puck.2798005); anecdote).
- **Blade speed at impact** in a slap shot is 29.1 ± 1.4 m/s elite against 26.5 ± 0.7 m/s recreational (electromagnetic tracking at 60 Hz) ([Woo et al. 2004](https://ojs.ub.uni-konstanz.de/cpa/article/view/1368/1387)). Skill and strength set puck speed; stick stiffness hardly does ([Pearsall et al. 2001](https://ojs.ub.uni-konstanz.de/cpa/article/view/3779)).

**Passes, NHL 5v5, 2017-18.** SPORTLOGiQ (Yu et al., [arXiv:1902.02020](https://arxiv.org/pdf/1902.02020)) analysed 0.5 million passes. Speed = distance ÷ time from pass to reception, so it is an average over the puck's path, a little under the release speed. Read off their Fig. 9:

| Pass type | Successful reception | Failed reception |
|---|---|---|
| D-to-D | 35 ft/s (10.7 m/s) | 44 ft/s (13.4 m/s) |
| Rush | 35 ft/s (10.7 m/s) | 47 ft/s (14.3 m/s) |
| North | 36 ft/s (11.0 m/s) | 47 ft/s (14.3 m/s) |
| South | 39 ft/s (11.9 m/s) | 46 ft/s (14.0 m/s) |
| O-zone entry | 41 ft/s (12.5 m/s) | 54 ft/s (16.5 m/s) |
| Outlet | 48 ft/s (14.6 m/s) | 60 ft/s (18.3 m/s) |
| Slot | 54 ft/s (16.5 m/s) | 55 ft/s (16.8 m/s) |
| O-zone stretch | 57 ft/s (17.4 m/s) | 74 ft/s (22.6 m/s) |
| East-west | 59 ft/s (18.0 m/s) | 67 ft/s (20.4 m/s) |
| Stretch | 67 ft/s (20.4 m/s) | 72 ft/s (21.9 m/s) |

- **[measured]** Except for slot passes, failed receptions came off significantly faster passes. Pros do bobble hard passes.
- **[estimate]** Recreational adult passes are likely slower, around 6-12 m/s. I found no measurement.

### 6. Stickhandling

- **[measured]** Lawrie (2014, McGill MSc, n = 27) studied a figure-8 drill around two obstacles set 2/3 of the player's height apart (1.22 m for a 1.83 m player). Each loop took 2.24 ± 0.30 s for varsity players against 2.76 ± 0.52 s for recreational players. Peak sideways puck speed was 2.9 against 2.5 m/s, and peak speed near the blade was 3.6 against 2.6 m/s on the forehand cross. The top hand moves least (peak about 1.2-1.5 m/s). Varsity blades move up to 0.6 m/s faster than the puck at peak, which the author reads as striking and then catching ("volley-and-catch"). Recreational players' pucks follow the blade, a "plough-push" ([thesis](https://mcgill.scholaris.ca/items/eeeb2675-8b05-4122-a533-2f476979bd4a)).
- **Comparison with Jon.** His p99 blade speed of 3.2 m/s matches these peaks; his median of 0.9 m/s is the in-between motion. His stickhandling speeds look like real ones.
- **Touches per second and side-to-side range for quick in-place handling: not found.** Only field-hockey and soccer analogues turned up. Open question.

### 7. Receiving a pass

- **[coaching]**
  - Cushion by moving the blade back as the puck arrives. Too little give and the puck "will bounce off a rigid stick like it does the boards"; too much and it dribbles off. Keep the hands away from the body, and shorten the give to "just in front of your body". The blade "will tend to pivot when you cushion ... and slide off the toe" ([HockeyShot](https://hockeyshot.com/blogs/training-academy/hockey-skills-how-to-effectively-receive-a-pass)).
  - "Give yourself a few inches or a foot to catch the puck." The top hand pushes out, which "moves the blade back and cushions the puck" ([How To Hockey](https://thepond.howtohockey.com/courses/free-lessons/pond-lessons/cushioning-the-puck/)).
- **[derived] Physics.**
  - Against a rigid blade with restitution e, a blade retreating at u = e·v/(1+e) leaves the puck dead after one impact. For e = 0.3 that is about 0.23 v.
  - Retreating at v (matching the puck) avoids an impact at all; the hands then slow the puck in the cup.
  - A closed (cupped) face tilts the contact normal down. The impulse then presses the puck into the ice instead of lifting it, which is why a closed blade traps bouncing or rolling passes.
- **[sim]** With the current blade (pop 0.30), a still blade sends 6 and 12 m/s passes back at 0.17 v. A give of only 0.1 v for 150 ms cuts that to 0.03-0.04 v; 0.25 v gives 0.02-0.03 v. The model rewards real receiving technique through Jon's own hands. No assist is needed.

### 8. What makes a puck feel heavy

- **[derived]** Momentum and the mass ratio.
  - A 0.17 kg puck at 10 m/s carries 1.7 N·s against a stick whose effective mass at the blade is only 0.20-0.27 kg (section 2). The puck visibly drives the blade back.
  - In our model the ratio is 0.17 / 0.15 = 1.13, against a real 0.63-0.85, so if anything our puck shoves the blade a little more than a real one.
  - **[sim]** On our 2,400-2,600 N/m flex spring, a still blade gives 1.6-1.7 cm to a 5 m/s pass, 3.3-3.4 cm to 10 m/s and 4.9-5.1 cm to 15 m/s. That visible give is a "heavy" cue the model already produces.
- **[derived]** Low restitution: the puck stops on contact with a dull thud instead of a click. Only possible with a dead (frozen) puck.
- **[measured]** Heavy training pucks are 260 g, against a regulation 156-170 g. Training with them raised elite U14 shot speeds more than training with light pucks did ([Novak et al. 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9465741)). A heavier puck is therefore noticeably different, but not the right reference for a game puck.
- **[measured, rule]** Regulation: vulcanized rubber, 1 in thick, 3 in across, 5.5-6 oz = **155.9-170.1 g** ([USA Hockey Rule 306](https://www.usahockeyrulebook.com/page/show/1084404-rule-306-puck); the NHL wording is the same per the [Globe and Mail](https://www.theglobeandmail.com/opinion/the-puck-remains-the-same/article554735)).
- **[sim]** Within that range, mass barely matters in our model: the wrist push gives 16.67 m/s at 160 g against 16.73 at 170 g.
- **[estimate]** With no force feedback, "heavy" in VR has to come from the blade visibly giving, rumble that scales with the impulse, and a thud sound. Those already scale with the contact impulse.

### 9. Are Jon's 40-46 mph shots plausible?

Yes, for an adult recreational wrist or snap shot:

- 40-46 mph is 17.9-20.6 m/s.
- That is below recreational adult slap shots (22-23 m/s, measured) and well below elite wrist shots (27-29 m/s, measured).
- It sits inside my derived recreational wrist range (17-20 m/s).
- It sits beside elite 13-year-olds' snap shots (18.4-19.7 m/s, measured).

Factors in each direction **[estimate]**:

- *Pushes speed up:* the virtual stick has no inertia, unlike a real 0.4-0.45 kg stick.
- *Pushes speed down:* no legs or trunk when seated (trunk rotation is linked to wrist-shot speed: [Robbins et al. 2021](https://www.tandfonline.com/doi/full/10.1080/02640414.2020.1853336)), and no ice to load the shaft beyond the model's flex.
- *Model behaviour [sim]:* our model's puck leaves about 1.1x the blade's speed on a push and about 1.26x on a strike from a distance.
- *Tracking:* Quest 3 owners report controllers losing tracking in fast throws ([Meta community forum](https://communityforums.atmeta.com/discussions/OtherTroubleshooting/unresolved-as-of-may-30-2024---quest-3-controller-tracking-issues/1090544); anecdote). Check the recordings for spikes or dropouts at release before trusting the peaks.

Nothing suggests the honest physics is inflating his shots.

## Recommendations for this project

| Parameter | Current | Recommended | Why |
|---|---|---|---|
| `Params.blade_pop` | 0.15 (Jon), default 0.20 | **0.30, constant** (honest range 0.27-0.35) | Frozen-puck COR: 0.27 at 55 mph (WSU cannon), about 0.35 at drop-test speeds (Haché). In our model it moves the rebound by ≤ 0.02 v, so set the honest value once and stop tuning it. If a speed curve is wanted: e = 0.35 below 3 m/s, falling linearly to 0.27 by 25 m/s. Never rising with speed. |
| `Params.soft_hands` (the low-speed bounce fade) | 3.0 m/s | **0 (remove)** | Backwards physics: rubber's COR rises at low speed (0.50 drop test vs 0.34-0.39 at speed). Inert with the 0.15 kg blade (≤ 0.01 v difference) but would act as an assist if the blade got heavier. It also clashes with the name of the rejected magnet. |
| `Params.blade_grip` | 0.35 | **0.45 once the puck spins**; keep 0.35 until then | Measured puck-on-cloth-tape friction is 0.43-0.50 (0.69 on a grip sticker). Our spinless puck loses up to 3x too much speed along the face when it should roll, and the lower value partly offsets that. |
| Puck spin (new state: ω about the vertical axis, I = ½ m R²) | none | **add** (code change, if Jon wants it) | Makes blade friction honest (a puck rolls along the face and keeps 2/3 of its speed along it), and gives spin off boards and posts. |
| `Params.puck_mass` / `M` | 0.170 kg | **keep 0.170** | Inside the 155.9-170.1 g regulation range. Within the range our model's shot speeds change < 0.5% and rebounds not at all. |
| `Flex.damping` (the "hands") | 0.60 | **keep 0.60**; make this the sandbox's bounce knob in place of "pop" | It is what actually sets rebound off a held blade: 0.6 → 0.17 v, 0.3 → 0.27 v, 0.1 → 0.38 v. In physical terms it is how firmly the hands hold the stick (coaching: a rigid stick bounces the puck like the boards). |
| `BLADE_MASS` | 0.15 kg | **keep** (0.15-0.25 plausible) | A free stick's effective mass at the blade, from WSU's stick inertias, is 0.20-0.27 kg; the local mass in a sub-ms impact is less. A heavier blade cuts rebound (0.30 kg → 0.10 v) and makes the puck shove the blade less. |
| `threes.PASS_MS` | 10 m/s (9 m/s to Jon) | **keep for a rec opponent; vary 8-14 m/s by distance** | NHL successful passes average 10.7-20.4 m/s by type (path average), and failed ones are faster. 10 m/s is the slow end of NHL and about right for adult rec (estimate). |
| `threes.SHOT_MS` | 22 m/s × 0.85-1.1 | **keep** | Matches adult rec slap shots (22.3-23.3 m/s) and is just above Jon's own 18-21 m/s. The NHL average is about 30 m/s. |

## Open questions

1. **The puck's rebound off a hand-held stick has never been measured** as far as I found. Our 0.15-0.17 v off a still blade is plausible from rigid-body maths but unvalidated. A phone slow-motion clip of a puck fired at a held stick would settle it.
2. **Is a frozen puck's COR flat with speed?** WSU only conjectured the plateau. Its curve plus Haché's drop test suggest about 0.27 at 55 mph rising to about 0.35 at drop speeds. A cannon sweep at 25 °F was never published.
3. **Friction of a frozen puck on tape, and its speed dependence.** The 0.43-0.50 figures are a preprint's room-temperature, slow-sliding values.
4. **Recreational adult wrist and snap shot speeds**, and **stickhandling touches per second and side-to-side range**: no primary data found. Robbins et al. 2021 has elite against recreational wrist-shot speeds behind a paywall.
5. **Quest 3 controller tracking at shot speeds** (hand speed, saturation, dropouts): no spec or study found. The project's recordings can answer it.
6. **The Pearsall/Villaseñor contact times (27-38 ms)** include the pushing phase. How long the puck stays on the blade in a wrist shot is unmeasured (Plesch estimates about 100 ms of acceleration).

## Scratch experiments

Run with the project's `.venv` Python against the compiled physics, with no code changes:

- Puck on a still blade: rebound against incoming speed, `blade_pop`, the fade, blade mass and flex damping.
- A blade tapping a resting puck.
- A wrist-like push, a slap-like strike and a one-timer.
- Pass reception with give.
- How far the blade gives under a pass.

The scripts built on `tests/test_soft_hands.py::_sweep` and lived in the session scratchpad: `contact_experiments.py`, `contact_experiments2.py`, `contact_experiments3.py`, `blade_give.py`.

## Verification

A fact-check pass on 2026-11-09. Each claim was checked against its source, read directly where possible: the PDFs were downloaded and the figures rendered, and the sim claims were re-run (`contact_experiments3.py` and `blade_give.py` with the project `.venv`, compiled path `FAST = True`, no code changes). Verdicts: **confirmed**, **corrected** (the right value is given), or **unsupported**.

| # | Claim | Verdict | What the source says |
|---|---|---|---|
| 1 | WSU, room-temperature COR against speed: 0.39 / 0.375 / 0.36 / 0.34 at 55-85 mph, against 0.50 in a drop test | **confirmed** | Fig. 5 of the [WSU PDF](https://ssl.wsu.edu/documents/2015/10/experimental-characterization-of-ice-hockey-sticks-and-pucks.pdf/) reads 0.39, 0.375, 0.36, 0.34. Text: "The COR decreased linearly with increasing speed." The 0.50 point (bar 0.45-0.55) is not WSU's own measurement. It is Haché's figure, plotted at about 15 mph: "Drop COR results [1] have been included for comparison". |
| 2 | WSU, COR at 55 mph against temperature: 0.39 / 0.32 / 0.30, then about 0.27 from 40 to 28 °F; −32% COR, +600% stiffness | **confirmed** | Fig. 6 reads 0.39 (72 °F), 0.32 (55), 0.30 (47), 0.272 (40), 0.268 (33), 0.27 (28). Abstract: "COR decreased by 32% and stiffness increased over 600% when frozen". Only brand PA was tested cold (12 pucks), and the methods give the cold condition as 25 ± 3 °F. The journal version is confirmed as Bigford & Smith, J. ASTM Int. 6(7), 2009, [doi:10.1520/JAI101859](https://store.astm.org/jai101859.html). |
| 3 | Haché: 45-55% of speed kept; frozen and warm pucks bounce to 12% and 27% of the drop height, so COR ≈ 0.35 and 0.52 | **confirmed, weak provenance** | The [reprint](https://www.jewelsfromthecrown.com/why-hockey-pucks-are-frozen-kansas-city-star/) has the quotes, with "concrete or ice" for the 45-55%. But the 12% / 27% figures come from a test Haché "proposed" for readers: the pucks "will bounce to about 12 percent and 27 percent". No drop height or temperatures are given. The page is a 2009 blog repost, and it does not name the book. √0.12 = 0.35 and √0.27 = 0.52 are correct. |
| 4 | Sim: off a still blade the puck comes back at 15-17% of its speed for any `blade_pop` from 0.15 to 0.50, fade on or off | **corrected (minor)** | The re-run reproduces the table exactly. Over 1-20 m/s the range is **0.13-0.17**: 0.14 at 1.5 m/s with pop 0.50, and 0.13 at 1.0 m/s. `blade_pop` moves it by ≤ 0.02, as claimed. |
| 5 | Sim: flex damping 0.6 / 0.3 / 0.1 gives 0.17 / 0.27 / 0.38; with a rigid blade the bounce equals pop; the fade cuts a 1 m/s bounce from 0.24 to 0.03 | **confirmed** | Re-run: 0.15-0.17, 0.22-0.27 and 0.33-0.39 depending on speed and pop. With a rigid blade (1e6 kg) the bounce comes out 5-10% under pop: 0.27-0.29 for pop 0.30, and 0.24 at 1 m/s. Fade at 1 m/s: 0.24 → 0.03. |
| 6 | Schwager 2007: viscoelastic-disk COR → 1 as speed → 0 and falls with speed | **confirmed** | The [abstract](https://arxiv.org/abs/cond-mat/0701142) says it "approaches one for small velocities and decreases for increasing velocities". This is theory for two identical disks colliding, not a puck measurement. |
| 7 | Plesch et al.: Specter 0.69 ± 0.02; Renfrew 0.46 ± 0.07 lengthwise, 0.43-0.50 across | **confirmed** | [arXiv:1903.02635](https://arxiv.org/html/1903.02635) §4.3 gives 0.69 ± 0.02, 0.46 ± 0.07, 0.43 ± 0.08 and 0.50 ± 0.11. The puck was caged against turning and pulled by a hanging mass. The preprint was later printed in BJSTR 41(4), 2022 (a low-profile journal). |
| 8 | Pearsall et al. 2001: slap shots by radar, varsity 30.0 ± 2.5, recreational 23.3 ± 3.8 m/s | **confirmed** | Table 1 and text of the [ISBS paper](https://ojs.ub.uni-konstanz.de/cpa/article/view/3779/3499), n = 10 + 10, SR 3000 radar. **Condition:** the players shot from a force platform in a lab, not on ice. |
| 9 | Villaseñor et al. 2006: elite 120.8 ± 18 km/h, recreational 80.3 ± 11.6 km/h; contact 38 ± 9 against 27 ± 5 ms | **corrected** | The elite figure is **120 ± 18 km/h (33.3 m/s)**, not 120.8 (33.6). Recreational 80.3 ± 11.6 km/h, contact times and n = 4 elite + 5 recreational are confirmed by the J Appl Biomech 22(3):202-211 abstract ([bisp-surf record](https://www.bisp-surf.de/Record/PU200708002177)). [Laliberte 2009](https://thesportjournal.org/article/biomechanics-of-ice-hockey-slap-shots-which-stick-is-best/) gives only the means, "120 km/h" and "80.3 km/h", with no ± values. |
| 10 | Léger et al. 2022: wrist 27.4-27.9, slap 31.7-32.0 m/s, stationary, synthetic ice, Vicon | **confirmed** | Table 5 of [Sensors 22:3419](https://pmc.ncbi.nlm.nih.gov/articles/PMC9105185): n = 10 (2 Junior A, 5 university, 3 pro), synthetic ice at McGill, 18-camera Vicon at 240 Hz. |
| 11 | Bezák & Přidal 2017: wrist 105.6 ± 10.0, slap 125.2 ± 12.6 km/h, best of 5, radar, on ice | **confirmed** | The [full text](https://gymnica.upol.cz/pdfs/gym/2017/02/04.pdf) has 20 pro and semi-pro players, Pocket Radar PR1000-BC, best of five, stationary on ice, with "cold (not frozen)" pucks. It also cites Worobets 2006 at 96.5 / 124.9 km/h. |
| 12 | Novak et al. 2022: elite U14 pre-training wrist 60.0 ± 9.5, long snap 70.8 ± 7.0, short snap 66.4 ± 6.3 km/h | **confirmed** | [J Hum Kinet 82:191](https://pmc.ncbi.nlm.nih.gov/articles/PMC9465741): 16 players aged 13.6 from one club in the top Czech youth league, Stalker Sport 2 radar, best of 3. |
| 13 | Swarén et al. 2019: 2 DEL pros, slap 36.4 ± 1.0, one-timer 38.0 ± 2.7 m/s; contact 20 ± 2 and 15 ± 2 ms | **confirmed** | [icSPORTS 2019](https://www.scitepress.org/publishedPapers/2019/83516/pdf/index.html), on ice, with 20 Qualisys cameras at 300 Hz. |
| 14 | Recreational adult wrist shot about 17-20 m/s, from elite slap/wrist ratios 1.15-1.29 applied to recreational slap shots of 22.3-23.3 m/s | **unsupported (estimate)** | The arithmetic checks: the ratios are 1.15 (Léger), 1.19 (Bezák) and 1.29 (Worobets via Bezák); 22.3 / 1.29 = 17.3 and 23.3 / 1.15 = 20.3. But nothing measured supports carrying an elite ratio over to recreational players. Wu et al. 2003 (Sports Eng. 6:31-39) and Robbins et al. 2021 have measured skilled against unskilled wrist shots; neither could be reached. |
| 15 | Yu et al. (SPORTLOGiQ): NHL 5v5 2017-18 passes, successful 35-67 ft/s, failed 44-74 ft/s | **confirmed** | Fig. 9 of [arXiv:1902.02020](https://arxiv.org/pdf/1902.02020), read off the rendered chart: the bars match the notes' table within about 1 ft/s. 0.50 million passes. Text: "Aside from passes to the slot, failed receptions ... occur at significantly higher speeds". A failed reception means the pass touched the receiver's blade. |
| 16 | Lawrie 2014: loop 2.24 ± 0.30 against 2.76 ± 0.52 s; puck 2.94 against 2.53 m/s; near blade 3.56 against 2.61 m/s | **confirmed** | From the [thesis PDF](https://mcgill.scholaris.ca/items/eeeb2675-8b05-4122-a533-2f476979bd4a): n = 27, obstacles 2/3 of the player's height apart. The appendix table gives side-to-side (X) peaks on the forehand cross of 2.944 / 2.531 m/s for the puck and 3.556 / 2.607 m/s for marker s3, which sits at the hosel-blade junction. Players were on skates, on an "ice surface". |
| 17 | Effective blade mass of a stick pivoted 35 in up, I/Q² from WSU's 8,753-11,658 oz·in² = 0.20-0.27 kg | **confirmed (derived)** | WSU Table 1 has the MOI range. The text ties I to the test pivot, "located 35 inches from the bottom of the stick". 8,753 oz·in² = 0.160 kg·m² and 11,658 = 0.213 kg·m²; divided by (0.889 m)² that gives 0.203-0.270 kg. This is for a stick pivoted on a fixed axis, not a free or hand-held one. |
| 18 | USA Hockey Rule 306: vulcanized rubber, 1 in × 3 in, 5.5-6 oz = 155.9-170.1 g | **confirmed** | The rulebook page (via search; direct fetch returned no rule text) gives 5½-6 oz, 1 in thick, 3 in across, vulcanized rubber. The WSU introduction gives the same. 5.5 oz = 155.9 g and 6 oz = 170.1 g. |
| 19 | Sim: a give of 0.1 v for 150 ms cuts the bounce of a 6 or 12 m/s pass from 0.17 to 0.03-0.04 v; a still blade gives 3.3-3.4 cm under 10 m/s | **confirmed** | Re-run: 6 m/s 0.17 → 0.04 and 12 m/s 0.17 → 0.03. Blade give 3.4 cm (flex 70) and 3.3 cm (flex 75) at 10 m/s. |

**Also checked (not in the claim list):** the [HockeyShot](https://hockeyshot.com/blogs/training-academy/hockey-skills-how-to-effectively-receive-a-pass) line is confirmed: "have a death grip on your stick, the puck will bounce off a rigid stick like it does the boards". The spin arithmetic is also right. For a disc with I = ½mR², a rim impulse changes the contact-point slip three times as much as the centre's speed, so the slip stops once the centre has lost 1/3 of its sliding speed along the face. Our spinless puck loses all of it, which is the "up to 3x".

**Extra sim run (blade mass × pop, damping 0.6, fade off).** At 0.20 kg the peak rebound is 0.11-0.14 v and at 0.25 kg it is 0.10-0.12 v. Pop stays inert at both, and the fade is still inert at 0.25 kg. From 0.4 kg up, the response to pop becomes erratic: at 0.60 kg, pop 0.30 gives 0.00-0.01 v while pop 0.50 gives 0.14-0.16 v and pop 0.15 gives 0.05 v. That looks like a second contact or chatter, and the notes' table left out the 0.60 kg row that showed it.

### What changes in the recommendations

- **`blade_pop` 0.30:** still holds. The 0.27 cannon value for a frozen puck is solid. The "≈ 0.35 at drop speeds" anchor rests only on a newspaper quote of a test Haché proposed, so the optional speed curve's 0.35 low-speed end is weak. Prefer the constant 0.30, and note that WSU's cold tests ran at 25-40 °F.
- **Remove the fade (`soft_hands` 3.0 → 0):** still holds. The low-speed rise in COR is measured only at room temperature (WSU Fig. 5, whose drop point is Haché's); for frozen pucks WSU only conjectured a flat plateau. Either way, nothing supports a fade to zero bounce. The re-run confirms the fade is inert at 0.15-0.25 kg blades.
- **`blade_grip` 0.45 with spin, spin term:** still hold. The friction values and the ½mR² argument check out. The friction source is a caged-puck preprint at unstated temperature (later printed in BJSTR, 2022).
- **`puck_mass`, `Flex.damping` as the bounce knob, `PASS_MS`:** still hold. The damping numbers reproduce exactly.
- **`BLADE_MASS`:** keep 0.15. The 0.20-0.27 kg range is for a stick pivoted on a fixed axis in WSU's rig. If the blade mass is ever raised, stay at or below about 0.3 kg, or first fix the erratic response to pop seen at 0.4-0.6 kg.
- **`SHOT_MS`:** keep 22 m/s, but fix the reasoning. "The NHL average is about 30 m/s" has no source here: 30.0 m/s is Pearsall's varsity (university) group, shooting from a lab force plate. The elite slap figure from Villaseñor is 33.3 m/s, not 33.6. The recreational 22.3-23.3 m/s come from lab shots (Pearsall: a force plate; Villaseñor: the setting is not stated in the abstract), not from game play on ice.
- **The recreational wrist range of 17-20 m/s** used to judge Jon's 18-21 m/s stays an unsupported estimate. Treat "plausible for a rec player" as a judgement, not a measurement.
