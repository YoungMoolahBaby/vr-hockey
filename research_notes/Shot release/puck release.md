# How the puck leaves the blade

*2026-11-10. Research round on shot release: wrist, snap and slap shots, and passes. No code was changed. Downloaded theses, rendered figures and one scratch model are in the session scratchpad only.*

Tags: **[M]** measured in the cited study. **[D]** derived by me (arithmetic shown). **[E]** estimate, or physics with stated assumptions (this includes my scratch 1D model of the sim's blade). **[V]** vendor claim, coaching text or anecdote. **[S]** secondary: read in a source that cites the primary.

**What is new in this round.** The earlier notes cited contact times and speeds from abstracts. This round read the primary theses in full and rendered their figures:
- Kays 2013 (WSU MS thesis): on-ice blade speeds before, during and after puck contact, puck speeds, impact location, and a finite-element (FE) slap-shot model.
- Michaud-Paquette 2008 (McGill MSc): blade heel and toe speed, puck speed, spin and contact time in 25 players' wrist shots.
- The McGill theses behind the slap-shot contact times: Villaseñor-Herrera 2004, Lomond 2005, Hannon 2010.
- Smith & Bigford's pivoted-stick cannon results (their Fig. 2), and Plesch 2019's spin figures.

One correction to the earlier notes: **the "27 vs 38 ms" slap-shot contact times were measured with a 260 g instrumented puck on a cable**, not a 170 g game puck (section 1).

## Bottom line

1. **A single impact cannot send the puck faster than the blade.** Over the sub-millisecond collision, a hand-held stick behaves like about **0.2-0.28 kg at the blade** [D/E, retagged in fact-check: three of the four methods use a pivoted stick with no hands, and the methods span 0.16-0.32 kg; that the hands do not matter within 1 ms is the [E] step]. With puck restitution of about 0.3, one hit sends the puck off at **0.70-0.81 of the blade's speed** [D]. A stick fired on by a cannon with no shaft loading sent pucks off at 0.63-0.85 of the stick speed [M/D]. Beating the blade in one hit would need an effective mass over m/e ≈ 0.57-0.63 kg [D]. So `blade_pop` is not the lever, and neither is a heavier puck.
2. **The puck does outrun the blade in slap shots, by about 1.1-1.3x in Kays's shooters, because the hands keep driving and the shaft unloads during 15-40 ms of contact.** Pros go further (last bullet; corrected in fact-check).
   - Kays's six shooters (two from a university team on real ice, four on synthetic ice) [M]: at the contact point the blade ran 22.5 m/s just before contact. The impact cut that to 11.4 m/s, and the blade was back at 19.4 m/s by the last video frame (mean; corrected in fact-check: the earlier "19-21 m/s" mixed in shooter 5's single-shot peak of 20.8 m/s).
   - Their pucks left at 24.5 m/s by radar (about 26 m/s by video) [M/D].
   - So puck speed is 1.09-1.16x the incoming blade speed, and about 1.3x the blade speed after release [D].
   - Puck speed tracked the blade speed *after* impact, not before it [M].
   - Stored shaft energy alone explains only a few percent of the speed: 2.1 J recreational, 16.5 J elite, worth about 3% and 9% [D]. The rest is work the hands do during contact [E].
   - **Pros on ice exceed 1.3x** (added in fact-check). In Swarén's two DEL pros, the blade-tip marker ran about 22-25 m/s before ice contact and the pucks left at 36-37 m/s: about 1.4-1.7x [D, read off their Fig. 2]. Against the tip's peak just after contact (about 27-35 m/s), it is 1.05-1.35x.
3. **In wrist shots the puck does not outrun the blade.** In 25 university players' wrist shots, the puck left at **0.91-0.98 of the blade toe's speed** (18.2-18.7 m/s against 18.8-20.2 m/s), and 1.3x the heel's speed [M/D]. At the puck's release point on the blade the ratio is about 0.94-1.04 [D, assumed marker spacing].
4. **Contact lasts about 15-45 ms in a strike and 80-290 ms in a sweep.**

   | Shot | Contact | Notes |
   |---|---|---|
   | Pro slap shot, on ice | 20 ± 2 ms | [M] |
   | Pro one-timer, on ice | 15 ± 2 ms | [M] |
   | Lab slap shot, heavy wired puck | 27-38 ms of touching in a 33-44 ms window [M/D], with 1-3 separations [S: Kays's summary; Villaseñor himself says the gaps in his contact circuit may be blade vibration; retagged in fact-check] | |
   | Wrist shot | 150-180 ms on average, 80-290 ms in all; the puck rides 1.2 m with the blade (0.84-1.79 m) | [M] |

   In slap shots the blade leaves the ice about 7-13 ms after it first touches the puck. So **up to about 25 ms of contact with the blade off the ice is normal; 75 ms is not** [D]. This holds for slap shots only (Lomond: wired puck, polyethylene surface). No study measures it for wrist shots, flips or saucer passes, where the puck can ride a lifting blade (fact-check).
5. **The puck travels along the face and leaves toward the toe.**
   - In wrist shots it leaves 18.5-23 cm from the heel. It leaves about 4 cm further toward the toe on high shots [M].
   - Contact ends in one of three ways:
     - the blade slows after its recoil while the puck carries on [M];
     - the face turns: it rotated 35-58° during wrist-shot contact [M];
     - the blade rides over the puck [E].
   - Slap shots struck nearer the toe were faster, both between players and in the FE model (+5.6 mph over 6 in) [M/E].
6. **Spin at release** [M]:

   | Shot | Spin |
   |---|---|
   | Wrist, university players | 14-17 rev/s mean (7-23 rev/s in all) |
   | Wrist, 12 players including 3 NHL | 19-30 rev/s |
   | Slap, same 12 players | 27-41 rev/s |

   That is about 6-18x the stick's own rotation rate (corrected in fact-check: was 6-15x), so spin comes from the puck rolling and slipping along the face [D]. The rim moves at 3.6-8 m/s [D].
7. **What this means for the sim.**
   - Its structure (0.15 kg blade on a 21 Hz spring, rigid hands, e = 0.30) already behaves like real shots [E, scratch model]:
     - with the hands driving through contact, the puck leaves at 1.08-1.28x the hand-driven speed, in 2 touches over 18-27 ms;
     - when the hands stop, it leaves at 0.77-0.93x.
   - So the launch bugs are not a missing mechanism. They are inputs and geometry no real shot has:
     - contact lasting 75 ms on a rising, airborne blade;
     - puck vertical speeds of 8-14 m/s, where a shot on net from 4 m or more needs at most about 5-7 m/s, and a roof shot from 2 m about 10 m/s [D; corrected in fact-check: the net is 1.22 m high, not 1.0 m];
     - blade speeds above about 30-32 m/s, beyond university-elite players' 29.1 ± 1.4 m/s at impact [M/D]. On-ice pros' blade tip peaked at about 34-37 m/s just after puck contact (Swarén, n = 2) [M, read off a figure; added in fact-check], so 40+ m/s is beyond even them;
     - shot speeds of 77-105 mph, where a recreational adult's best is about 60-70 mph, plus about 2-4.5 m/s from skating [D].

## 1. The studies and their conditions

| Study | Players | Shots | Method | Puck | Main caveat |
|---|---|---|---|---|---|
| [Villaseñor-Herrera 2004, McGill MSc](https://mcgill.scholaris.ca/items/20d44d6b-f579-48c0-a068-4d118cc607cc); [J Appl Biomech 22:202, 2006](https://www.bisp-surf.de/Record/PU200708002177) | 4 elite (puck speed > 100 km/h in a pre-test), 5 recreational, adult men | stationary slap | 1000 Hz video; triaxial accelerometer in the puck at 10 kHz; foil contact circuit on blade and puck | **0.260 kg** (puck plus accelerometer), on a 10 m cable | Heavy, tethered puck: contact times and speeds are not for a 170 g puck |
| [Lomond 2005, McGill MSc](https://mcgill.scholaris.ca/items/04d8dd90-f525-493d-9689-f4848abcb01f); [Sports Eng 10:87, 2007](https://www.bisp-surf.de/Record/PU201103001703) | 8 McGill varsity, 7 university recreational (< 3 times a week) | stationary slap | two 1000 Hz cameras; force plates; uniaxial accelerometer in the puck | 0.160 kg, on a 6 m wire | The wire cut puck speed by about 30% (73.7 against 109.4 km/h elite) [M]. Lab surface of silicone-sprayed polyethylene, not ice (fact-check) |
| [Kays 2013, WSU MS thesis](https://rex.libraries.wsu.edu/esploro/outputs/graduate/Ice-hockey-wrist-and-slap-shots/99900525127201842) | 6 shooters: 2 from the WSU men's team on real ice, 4 on synthetic ice | stationary slap and wrist, 7 sticks | two high-speed cameras: slap 1000 fps, wrist 400 fps; radar | game pucks | Blade speed is extrapolated from 4 shaft markers and smoothed with cubic fits; radar read 3.8 mph (slap) and 6.9 mph (wrist) below video tracking |
| [Michaud-Paquette 2008, McGill MSc](https://mcgill.scholaris.ca/items/d0f8ff7a-b20d-4f9e-bd4d-63f0e46934b8) | 25 university men, varsity to recreational | stationary wrist shots at 4 targets, 4 m | Vicon at 240 Hz; markers on blade heel and toe and on the puck | marked game puck | Polyethylene surface sprayed with silicone; one stick (Bauer P106 pattern) |
| [Hannon 2010, McGill MSc](https://mcgill.scholaris.ca/items/212dd3a6-79f6-4e61-8e47-a6abc33141b2) (Sports Eng 2011) | 9 university-level or above, 8 recreational | stationary slap and wrist | strain gauges at 10 kHz; Vicon at 300 Hz, low-pass filtered at 8 Hz | marked game puck | Release was set where puck acceleration reached zero after an 8 Hz filter, which stretches the contact times |
| [Swarén et al. 2019](https://www.scitepress.org/publishedPapers/2019/83516/pdf/index.html) | 2 pros (German DEL) | slap, one-timer | 20 Qualisys cameras at 300 Hz, on ice | marked game puck | n = 2; 3.3 ms frame spacing |
| [Smith & Bigford, WSU](https://ssl.wsu.edu/documents/2015/10/laboratory-measurements-of-ice-hockey-stick-performance.pdf/) | 1 upper-level recreational player (video); 17 sticks (cannon) | slap; cannon impacts | 1000 fps video; puck fired at 23 m/s at a stationary stick pivoted 0.9 m from the blade | game puck, 22 and −4 °C | The cannon rig has no hands; their "loaded" speeds come from a loading model |
| [Plesch et al. 2019, arXiv:1903.02635](https://arxiv.org/abs/1903.02635) | 12 players, 3 of them NHL | stationary wrist and slap | 1000 fps camera 2 m from release, analysed at 250 fps; dots on the puck | painted game puck | Shooting mat; goal 6 m away |
| [Woo et al. 2004, ISBS](https://ojs.ub.uni-konstanz.de/cpa/article/view/1368) | 5 McGill varsity, 5 recreational | stationary slap | electromagnetic tracking at 60 Hz; sensors 24 and 145 cm from the heel | — | 60 Hz is coarse for a 30 ms event; wooden stick |

- **The heavy puck matters** [D]. Villaseñor's puck kinetic energies (152 J elite, 67 J recreational) only come out right with 0.26 kg: ½·0.26·33.5² = 146 J, while ½·0.17·33.5² = 95 J.
  - **[E]** A puck 53% heavier rides a spring-like blade longer. It also takes more momentum to reach the same speed.
  - So 27-38 ms is an upper estimate for a game puck. The on-ice pro figure of 20 ms, with an unweighted puck, sits below it.

## 2. Contact duration

### Strikes: slap shots and one-timers

| Source | Who | Contact | Notes |
|---|---|---|---|
| Swarén 2019 [M] | 2 pros, on ice | slap 20 ± 2 ms; one-timer 15 ± 2 ms | Pucks 36.4 and 38.0 m/s |
| Villaseñor 2004 [M] | recreational / elite | time actually touching: 27 ± 5 / 38 ± 9 ms | 260 g wired puck |
| Villaseñor 2004 [M/D] | same | touching / whole window = 80.9% / 86.6%, so the window (first touch to last) is about 33 / 44 ms [D: 27/0.809, 38/0.866] | "one to three separations" during contact [S: Kays's summary, not in the thesis; Villaseñor says the gaps in the contact circuit "could be explained by ... blade vibration"; retagged in fact-check] |
| Smith & Bigford [M] | 1 upper-level recreational player | 32 ms | Speed drop and rise in the first 10 ms, then 22 ms of unloading |
| Kays 2013 [M/E] | shooter 5 (video), FE model | 42 ms from first touch to release in both; the model touched for 27 ms of it, in 4 separate contacts | Video could not resolve the separate touches |
| Hannon 2010 [M] | university+ / recreational | 57.8 ± 13.7 / 79.7 ± 21.4 ms | Filtered release time; probably too long (section 1) |
| Meng & Zhao 2000; Polano 2003 [S] | Chinese "hitting shot"; 3 varsity players | about 40 ms; about 35 ms | Via [Lomond 2005](https://mcgill.scholaris.ca/items/04d8dd90-f525-493d-9689-f4848abcb01f) |

- **Skill and contact.**
  - Villaseñor found that time actually touching predicted puck speed (r² = 0.82) [M]. Elite players touched longer.
  - Hannon found the opposite ordering, with recreational players longer. But his release event is filter-dependent [M].
  - The pros on ice had the shortest contacts of all [M].
  - **[E]** So "longer contact = better" holds within one lab setup, not as a rule.
- **Bend and recoil inside the contact** (Villaseñor, [M]).
  - Elite players' shafts bent from first touch to 28.8% of the window, then recoiled until 88.6% of it.
  - Recreational shafts did not start bending until 44.4% of the window. The recoil was "relatively non existent".
  - Hannon agrees [M]: for the lower-calibre players "stick recoil was incomplete before the puck had already been released".
- **The blade leaves the ice before the puck leaves the blade.**
  - In Lomond's lab slap shots, toe-on-ice to puck contact took 14 ms (elite) and about 17 ms (recreational) [M]. The text reads "0.0017 s"; the stated 39% of the shot makes it 0.017 s.
  - Toe-on-ice to stick-off-ice took 27 and 24 ms [M].
  - So the blade left the ice about 13 ms (elite) and 7 ms (recreational) after first touching the puck [D].
  - Against 20-38 ms of contact, that leaves **about 10-25 ms of puck contact with the blade off the ice** [D]. This mixes studies, Lomond's puck was wired, and his surface was polyethylene.
  - Fact-check note: Lomond's glossary and Fig. 17 define both phases from toe contact, which is the reading used here. His "% of shot" figures do not add up under either reading (elite 13 + 29 + 58 = 100%, recreational 21 + 39 + 53 = 113%), but the ratios between phases fit this reading in both groups.
- **The ice comes first.**
  - In Kays's on-ice and lab shots, the blade hit the ice 10-19 ms (mean 14 ms) before the puck, 11-16 in (mean 12.9 in, 33 cm) behind it [M].
  - Polano's varsity players hit about 38 cm behind [S].

### Sweeps: wrist shots

- **Michaud-Paquette 2008** [M]: 25 players, about 40 shots each.
  - Mean contact time, first touch to release, was 150-180 ms across the four targets. The range was 80-290 ms.
  - The puck travelled 115.9-124.7 cm while in contact with the blade (range 83.8-179.4 cm).
  - The shaft bent at most 3.1-3.9° (range 1.3-6.1°).
- **Hannon 2010** [M]: in wrist shots, puck contact took 30-35% of the whole shot, from first blade-ice touch to release. The absolute times were not extracted.
- **Plesch 2019** [E]: "about 100ms or more" of acceleration, from a constant-force estimate.

### Passes

- I found no measurement of contact time for passes or saucer passes. A forehand pass is mechanically a short sweep [E]. Its contact should therefore sit between a tap (a single touch) and a wrist shot (80-290 ms).

## 3. Blade speed against puck speed

| Shot, source | Blade speed (where, when) | Puck speed | Puck ÷ blade |
|---|---|---|---|
| Slap, Kays, 6 shooters, means [M] | at the contact point: 23.9 m/s at ice contact; 22.5 just before puck contact; **11.4 just after**; 19.4 at the last frame. (Corrected in fact-check: the "18.5 averaged over contact" listed here was shooter 5's single shot, 41.3 mph from puck contact to release, not a six-shooter mean.) | 24.5 m/s radar mean of per-shooter means, read off Fig. 3.27 (45.4-62.5 mph); about 26.2 m/s by video [D: +3.8 mph, an offset Kays measured on shooters 1 and 2 only] | 1.09-1.16 against just-before-contact; 1.02-1.10 against ice contact; 1.27-1.35 against final [D] |
| Slap, Kays, shooter 5's best shot [M] | 51.9 mph at ice contact; 35.3 mph final | 66.0 mph (video) | 1.27 against ice contact; 1.87 against final [D] |
| Slap, Kays, shooter 6 (poor contact) [M] | 57.2 mph at ice contact; 60.4 mph before the puck (the fastest blade of the six) | 45.4 mph (the slowest) | **0.75** [D] |
| Slap, Smith & Bigford cannon, no loading [M/D] | 27 m/s (nominal stick speed) | 17-23 m/s (their Fig. 2) | 0.63-0.85 |
| Slap, Smith & Bigford, with their loading model (450 N or 60 mm) [M/E] | 27 m/s | 29.5-35.4 m/s | 1.09-1.31 |
| Slap, Woo 2004 [M] | 29.14 ± 1.39 m/s elite, 26.46 ± 0.66 recreational (blade at impact, 60 Hz) | not measured in this paper | — |
| Wrist, Michaud-Paquette, 4 target means [M] | toe 67.6-72.6 km/h (18.8-20.2 m/s); heel 50.1-52.5 km/h (13.9-14.6 m/s) | 65.6-67.3 km/h (18.2-18.7 m/s); range 40-93 km/h | **0.91-0.98 of toe**; 1.27-1.32 of heel [D] |
| Wrist, Kays [M] | 46.7 ± 2.0 mph (20.9 m/s) at the last frame | 46.9 mph radar mean of per-shooter means (about 54 by video) | about 1.0-1.15 [D]; weak, because the camera trigger timing varied and the radar "seemed to pick up the speed of the blade" |

- **Kays's per-shot efficiency** [M]. Kays reports a "COR" = (puck speed − final blade speed) ÷ incoming blade speed.
  - Per-shooter means were 0.02, 0.15, 0.175, 0.28, 0.30 and 0.385. Single shots ranged from −0.27 to 0.59.
  - This is not the rubber's restitution. It measures how far the puck outran the blade's own end speed. Negative values were "shots where there was very little puck–blade contact".
- **What predicts puck speed** (Kays, [M]).
  - Puck speed rose with the blade speed just after contact and at release (his Fig. 3.30).
  - It fell slightly with the blade speed at ice contact (Fig. 3.29).
  - In his words, it is "the ability of the player to maintain and increase speed throughout puck contact".
- **One shot's blade speed history** (shooter 5, Fig. 3.31, [M]):
  - about 52 mph at ice contact;
  - about 41 mph just before the puck;
  - about 27 mph at impact;
  - back up to a peak of about 46.5 mph 28 ms after contact;
  - then falling to 35 mph by 54 ms.
  - The puck (66 mph) left after the blade had peaked and begun to slow [D].
- **Shooter 6 is the single-impact case** [D].
  - His blade bounced off the ice and struck the puck high, giving a short contact (Kays).
  - His puck left at 0.75 of the blade speed.
  - That is what one hit predicts with Kays's effective mass: (1 + 0.3)·0.233/(0.233 + 0.17) = 0.75 (section 4).
- **How much does the shaft's stored energy give?** Villaseñor estimated bend energy at 16.49 ± 13.29 J (elite) and 2.10 ± 2.10 J (recreational), assuming 15,000 N/m [M].
  - With all of it given to a 170 g puck [D]:
    - recreational: √(22.3² + 2·2.1/0.17) = 22.85 m/s, +2.5%;
    - elite: √(33.5² + 2·16.5/0.17) = 36.3 m/s, +8%.
  - Villaseñor himself notes that "muscle work performed during blade-puck contact" was not measured [M].
  - Roy et al. (1974) credited 40-50% of slap-shot puck speed to shaft deflection, 25-34% for wrist shots and 8-10% for backhands [S, via Lomond]. Their method is not described in Lomond's summary.
  - **[E]** The measured energies support the smaller share. In this reading, most of the excess over blade speed is the hands' push during contact.
- **The first hit gives most of the speed.**
  - Plesch writes that the blade "collides in a mostly inelastic manner, while accelerating the puck to about 60% of its final speed", citing Kays & Smith 2014 [S].
  - Kays's own numbers give 18.1 m/s after the first hit (section 4), which is 69-74% of the final 24.5-26.2 m/s [D].

## 4. Effective mass at the blade, and restitution at shot speeds

**When the hands matter.**
- For a baseball bat, "the ball-bat collision is very rapid, of order 1 ms or less". The bending wave reflected from the handle returns "long since" after the ball has gone, so the grip cannot matter ([Nathan, Illinois](https://baseball.physics.illinois.edu/grip.html)) [M/E].
- A puck's own impact is just as short: 0.41 ms frozen (25 °F) and 0.81 ms warm (72 °F) at 55 mph (Anderson 2008, via Kays) [S]; 0.94 ms warm at 35 mph (Kays 2013, 12 pucks) [M]. (Retagged in fact-check: the first two are not Kays's own measurements.)
- But hockey contact goes on for 15-40 ms (strikes) and 80-290 ms (sweeps). A hockey stick's first bending period is 17-21 ms (47-60 Hz, from the earlier note) [D].
- **[E]** So the first sub-millisecond hit sees only the stick's local mass, but everything after it sees the hands. A shot is a hit followed by a hand-driven push. A rigid-hands model fits that second phase.

**Effective mass for the hit itself** (puck m = 0.17 kg unless stated):

| Method | Result |
|---|---|
| Free stick pivoted at the bottom hand: I/Q², WSU stick inertias (earlier note) | 0.20-0.27 kg [D] |
| Kays's "recoil factor" r = m·b²/I = 0.707, with m = 0.1644 kg, b = 30.9 in, I = 7865 oz·in² (pivot 36 in from the toe) | M = I/b² = 0.1439 kg·m² ÷ (0.785 m)² = **0.233 kg** [D] |
| Inverting Smith & Bigford's no-load speeds. Their "collision efficiency" e_a = v_puck/v_stick − 1, and e_a = (e − r)/(1 + r), so r = (e − e_a)/(1 + e_a). With e = 0.30: ratio 0.63 gives M = 0.16 kg; 0.74 gives 0.23 kg; 0.85 gives 0.32 kg. Composites spread over 0.62-0.75, wood sticks over 0.67-0.84 (corrected in fact-check: was 0.63-0.74 and 0.74-0.85; read off their Fig. 2, 16.8-20.2 and 18.2-22.8 m/s ÷ 27) | 0.16-0.32 kg [D]; the MOI scaling in their formula makes this approximate |
| The blade's speed drop at impact (Kays: 50.4 → 25.5 mph, ×0.506). (M − e·m)/(M + m) = 0.506 with e = 0.30 gives M = 0.17·0.806/0.494 | **0.277 kg** [D]; the speeds are smoothed extrapolations |
| The sim: `BLADE_MASS` | 0.15 kg |

- **One hit with no follow-through**: puck ÷ blade = (1 + e)·M/(M + m) [D].
  - With e = 0.30: M = 0.15 kg gives 0.61; 0.20 gives 0.70; 0.23 gives 0.75; 0.28 gives 0.81.
  - For the puck to beat the blade in one hit, M > m/e: 0.57 kg at e = 0.30, 0.63 kg at e = 0.27 [D].
  - No hockey stick comes close. Unlike golf, where a 0.2 kg head strikes a 46 g ball with e ≈ 0.8, hockey has no "smash factor" above 1 [E].
- **Restitution of the rubber** [M]:
  - against a rigid plate: frozen 0.27 at 55 mph; warm 0.34-0.39 at 55-85 mph (WSU, earlier note); warm 0.427 at 35 mph (Kays, 12 pucks, 72 °F, contact 0.94 ms);
  - nobody has measured it against a held stick at shot speeds (Gaps);
  - puck temperature (22 against −4 °C) made "no measurable difference" to pivoted-stick performance, "apparently" because the long contact minimises the trampoline effect (Smith & Bigford) [M].
- **[E]** So `blade_pop` = 0.30 stays right. The shot's outcome is set by mass, hands and contact time, not by e.

## 5. The puck's path along the blade, and what ends contact

**Where the puck sits and where it leaves.**
- **Wrist shots** (Michaud-Paquette, [M]):
  - The puck left 18.5-23.0 cm from the heel (target means; range 12.4-28.5 cm).
  - It left further toward the toe for top targets (22-23 cm) than bottom targets (18.5-18.7 cm), a significant difference.
  - A McGill press summary adds that novices released nearer the heel and better players nearer the toe, at "the center of the curve" [S, seen only in a search summary].
- **Description of the wrist shot** [V; thesis background, not measured]:
  - It "usually starts with the puck near the heel or middle of the blade".
  - "The puck rolls along the blade and eventually is released near the toe" ([Kays 2013](https://rex.libraries.wsu.edu/esploro/outputs/graduate/Ice-hockey-wrist-and-slap-shots/99900525127201842)).
  - On a curved blade the puck "naturally rolls toward the toe end … and is released at the same point every time" (Haché 2002, via Michaud-Paquette and Lomond) [S].
- **Slap shots** [M]:
  - Chalk on Lomond's puck edge left a trace of its path along the blade.
  - First contact averaged zone 5.2-5.3 of 6 zones numbered from heel to toe, with no difference by skill or stick.
  - The zone direction in the figures is not legible in the scanned copy.
- **Impact point and speed** [M/E]. Kays's shooters averaged impact 5.5-8.5 in (14-22 cm) from the toe. Those who struck nearer the toe shot faster.
  - In his FE model, moving the impact from 8.7 to 2.7 in from the toe raised puck speed by up to 5.6 mph.
  - Impacts very near the heel gave "very low impact time" in the model.
  - Smith & Bigford's pivoted, hand-free stick performed best 50-100 mm from the heel [S: stated in Kays's review of Bigford & Smith; the Smith & Bigford paper only says the best location was used for each stick; retagged in fact-check]. Anderson's cannon found a sweet spot about 3 in from the heel on one of three sticks (via Kays) [S].
  - **[E]** That is the opposite end. Without hands and a follow-through there is no sweep toward the toe.

**What ends contact.**
1. **The blade slows below the puck.**
   - After the impact, the hands and the unloading shaft re-accelerate the blade. It peaks and then slows in the follow-through "as the stick is recoiling" (Kays, Fig. 3.31) [M].
   - The puck, now faster, separates [D].
   - Elite shafts finish their recoil at 88.6% of the window, and the puck leaves soon after [M].
   - In recreational players the puck leaves before the recoil ends, losing that energy (Villaseñor; Hannon) [M].
2. **The face turns.** Michaud-Paquette measured large changes in blade orientation during wrist-shot contact [M]:
   - their "pitch" angle (between the global X axis and the blade's normal) changed by 35-58° on target means;
   - "yaw" changed by 14-36°;
   - their "roll" (of the heel-toe line) by only about 2°.

   These are the thesis's own axis definitions. **[E]** The turning face is the "rolling the wrists" in coaching language. It lifts and aims the puck and ends the push.
3. **The blade rides over the puck.** Plesch: "at certain moment the blade moves above the puck and looses the contact". A grippier blade keeps contact longer, because "the contact point will be more efficiently elevated by the blade while the centre of the puck moves further mostly horizontally" [E].
4. **The hands clamp and the shaft twists.**
   - In skilled slap shots the hands switch to an opposed clamp during recoil ([Zane 2012](https://mcgill.scholaris.ca/items/aab2df80-5fd0-437c-a6d8-cd44c577354d), earlier note) [M].
   - Strain about the shaft's minor axis peaked 10-20 ms before strain about the major axis, which suggests the shaft twists as well as bends ([Flemming 2015](https://mcgill.scholaris.ca/items/cefd38e6-93bf-4a49-b8e0-e7d58f7bedd9)) [M].
5. **The blade leaves the ice, but the puck does not leave with it.**
   - The slap-shot blade lifts 7-13 ms after first puck contact (section 2) [D].
   - In one subject's snap shots, the shaft's recoil right after the blade left the ice ran 281 and 896 °/s for two sticks (Moreno et al. 2004, via Kays) [S]. On a 0.6 m lower lever that is 2.9 and 9.4 m/s at the blade [D].
   - **[E]** That recoil is in the swing plane: it throws the blade forward, not up.

## 6. Spin at release

| Source | Shot | Spin | Conditions |
|---|---|---|---|
| Michaud-Paquette 2008 [M] | wrist | target means 4885-6131 °/s = **13.6-17.0 rev/s** (85-107 rad/s); range 2400-8381 °/s (6.7-23.3 rev/s); top targets spun more (6121-6131 °/s) than bottom (4885-5140) | 25 university players; 240 Hz; synthetic surface |
| Plesch 2019, Fig. 2 [M] | wrist | per-player means about **19-30 rev/s** | 12 players including 3 NHL; mat |
| Plesch 2019, Fig. 2 [M] | slap | per-player means about **27-41 rev/s** | same |
| Kays 2013 FE model [E] | slap | about 219 rad/s (35 rev/s) at blade friction 0.7; 87-233 rad/s as friction goes 0.1 → 0.9, while puck speed fell from 78 to 76 mph | model of a 76 mph shot |

- **Speed and spin go together, and grip raises spin more than speed** [M]. Across all of Plesch's shots, spin and speed correlated at 0.66. A grippier blade cover raised spin about 2x (wrist) and 3x (slap) as much as it raised speed.
- **Where the spin comes from** [D]. The stick itself turned at 12.9-17.2 rad/s at puck contact in Kays's slap shots (mean 14.7). Puck spin of 85-260 rad/s is about 6-18x that mean (corrected in fact-check: 85/14.7 = 5.8 and 260/14.7 = 17.7; was 6-15x).
  - So the spin is not the blade's rotation carried over. It comes from the puck rolling or slipping along the face.
  - The rim speed ωR is 2π·15·0.0381 = 3.6 m/s at 15 rev/s and 2π·35·0.0381 = 8.4 m/s at 35 rev/s.
  - **[E]** If the puck rolls without slipping at release, that is also how fast its centre moves along the face relative to the blade.
- **Friction is not what limits spin** [D].
  - A sliding contact can spin the puck up to ω = 2μ·J/(m·R). With μ = 0.45 and J = m·18 m/s, that is about 425 rad/s.
  - Measured spin is well below that, so the slip stops before friction runs out: the spin is set by how fast the puck slides along the face, not by friction.
- Coaching and older sources say the "wrist snap" keeps contact and uses blade friction "to accelerate the puck into rotation" (Falconer 1994; Therrien & Bourassa 1982, via Lomond) [S].

## 7. What this means for the sim

### 7.1 What the sim's blade is, in numbers

- **Spring** [D]. Flex 75 gives a 3-point stiffness of 75·4.448/0.0254 = 13,134 N/m.
  - That gives EI = 13,134·1.17³/48 = 438 N·m².
  - As a cantilever from the bottom hand, the stiffness at the blade is k = 3·438/0.8³ = **2568 N/m** (`puck.tip_stiffness`).
- **Frequency and timing** [D]. With the 0.15 kg blade alone, the spring rings at √(2568/0.15) = 131 rad/s = **20.8 Hz**, so a half-cycle lasts 24 ms. With a 0.17 kg puck riding on the blade (0.32 kg in all) it rings at 89.6 rad/s = 14.3 Hz, a half-cycle of 35 ms.
  - Both half-cycles match measured slap-shot contact times (20-38 ms). A real stick's free first mode is 47-60 Hz. The held stick plus puck rings lower, but nobody has measured by how much.
- **Single-hit transfer** [D]. 1.3·0.15/0.32 = **0.61**, against a real 0.70-0.81. The sim's blade is 0.54-0.75 of the measured effective mass.
- **Storable energy** [D]. At the 0.15 m flex limit the spring holds ½·2568·0.15² = 29 J. The ice bow stores nothing.
  - Villaseñor's recreational 2.1 J corresponds to a blade deflection of √(2·2.1/2568) = 4.0 cm on this spring. His elite 16.5 J corresponds to 11.3 cm.

**Scratch 1D model** [E]. The hands are a point moving at V = 20 m/s. A spring and damper join them to a 0.15 kg blade. The blade strikes a resting 0.17 kg puck through impulses with e = 0.30, on frictionless ice, with a 0.25 ms step. This is my own scratch script, not the project's physics.

| Shooting hands, damping ratio ζ | Bend stored before impact | Hands after impact | Puck ÷ V | First to last touch | Touches |
|---|---|---|---|---|---|
| 0.6 | 0 | keep 20 m/s | **1.20** | 27 ms | 2 |
| 0.6 | 3 cm (1.2 J) | keep 20 m/s | 1.23 | 25 ms | 2 |
| 0.6 | 6 cm (4.6 J) | keep 20 m/s | 1.28 | 23 ms | 2 |
| 0.6 | 0 / 3 / 6 cm | stop over 30 ms | 0.77 / 0.84 / 0.93 | 12-13 ms | 2 |
| 1.5 (stickhandling hands) | 0 / 3 / 6 cm | keep 20 m/s | 1.08 / 1.11 / 1.15 | 18-21 ms | 2 |
| 1.5 | 0 / 3 / 6 cm | stop over 30 ms | 0.80 / 0.85 / 0.90 | 8 ms | 2 |

- **Reading the model** [E]:
  - When the hands drive through the hit, the impact itself loads the spring. It whips the blade back into the puck about 20-27 ms later. That is the recoil, and it makes the puck outrun the hands by 8-28%, in two touches.
  - When the hands stop, the puck leaves slower than they were moving.
  - Both match the measured range: 1.09-1.16x for Kays's slap shots, 0.75 for a poor single hit, 0.63-0.85 for the hand-free cannon. The touch counts match too: Villaseñor saw 1-3 separations, the FE model 4 contacts.
  - The earlier contact note found 1.1x on a push and 1.26x on a strike from a distance in the real engine. That agrees.
- **So the sim does not need a new mechanism to make the puck faster than the blade** [E].
  - The honest sources of the excess are already there: hands that keep moving, plus the spring's recoil.
  - Ice-loaded bend energy would add on top. Measured, it is worth +2.5% (recreational) to +8% (elite) [D, section 3].
  - This round's dropped trial gave +5-11% on a synthetic slap shot [M, brief]. That sits in the elite range and above a recreational player's.

### 7.2 Numbers the sim should match or not exceed

| Quantity | Measured | The sim should |
|---|---|---|
| Puck ÷ blade speed at the contact point, at release, in a sweep (wrist shot, pass) | 0.91-0.98 of toe speed; about 0.94-1.04 at the release point [M/D] | stay at or below about 1.0. The sim's 0.98 on a slow push is right |
| Puck ÷ incoming blade speed in a strike, with follow-through | 1.02-1.16 (Kays's 6 shooters, means); best single shots up to about 1.3; loaded-cannon model 1.09-1.31 [M/D]; two on-ice pros about 1.4-1.7 against the blade tip before ice contact [D, read off Swarén Fig. 2; added in fact-check] | stay within about 0.75-1.3 for a recreational adult |
| Puck ÷ blade speed for one hit with no follow-through | 0.63-0.85 [M/D] | give about 0.6-0.8. The sim gives 0.61-0.93 depending on the hands |
| Contact window in a strike (first to last touch) | 15-44 ms, 1-4 separate touches [M/D] | not exceed about **45 ms**, or 4 touches |
| Contact after the blade leaves the ice | about 10-25 ms in slap shots [D]; not measured for wrist shots, flips or saucer passes (fact-check) | not exceed about **25 ms** in a strike. The 75 ms follow-through scoops are 3x this. For a lifted wrist shot or flip there is no number to tune to |
| Contact in a sweep, puck on the ice | 80-290 ms; puck carried 0.84-1.79 m [M] | not exceed about **300 ms**, or about 1.8 m of travel with the blade |
| Puck vertical speed from a shot | about 5.0-6.6 m/s reaches the top of the 1.22 m net from 4-18 m; about 7 m/s from 3 m and 9.7 m/s from 2 m [D; corrected in fact-check: was 4.5-5.5 m/s, using a 1.0 m net] | give a shot from 4 m or further no more than about **7 m/s** upward. Near the net, up to about 10 m/s is a real roof shot. 8-14 m/s, rising 3-10 m, from range is a deliberate lob at most [D: h = v²/2g gives 7.7-14 m/s for 3-10 m] |
| Blade speed at the contact point | recreational 26.5 ± 0.7, university elite 29.1 ± 1.4 m/s at impact (Woo, 60 Hz); Kays's shooters 22.5-27 m/s; wrist toe up to 28.0 m/s (max of 25 players) [M]. On-ice pros' blade-tip marker peaked at about 34-37 m/s just after puck contact (Swarén Fig. 2, n = 2) [M, read off a figure; added in fact-check] | not exceed about **30-32 m/s** for a recreational or university player (elite mean + 2 SD = 31.9); pros reach about 35-37 m/s at the toe (corrected in fact-check: was "for anyone"). A recreational adult should not pass about 28 m/s (mean + 2 SD = 27.9) [D]. Single ticks at 40+ m/s are not hand motion |
| Recreational adult slap shot | 22.3 ± 3.2 m/s with Villaseñor's 260 g wired puck [M]; 23.3 ± 3.9 (Wu 2003, via Villaseñor) [S]; 24.6 ± 1.8 with standard pucks (Lomond's practice shots, radar, polyethylene) [M]; 22.4 ± 6.6 (Hannon, synthetic ice) [M]. Mean + 2 SD = 28.2-31.1 m/s (63-70 mph), or 35.6 m/s (80 mph) with Hannon's spread [D; corrected in fact-check: was "22.3-23.3 means, 28.7-30.9 m/s", which used a heavy-puck value and 30.9 for 31.1] | rarely pass about 31 m/s (70 mph) standing |
| Recreational adult wrist shot | 20.4 ± 2.9 m/s (Hannon); mixed-skill wrist max 93 km/h (25.9 m/s) [M] | rarely pass about 26 m/s (58 mph) standing |
| Extra speed from skating | +2.1 m/s for slap shots in motion against at rest (Doré & Roy 1975, 9 skilled adult amateurs: 29.0 ± 1.4 against 26.9 ± 1.5 m/s) [M] | add no more than the skating speed (4.5 m/s at sprint is the upper bound) [D] |
| Spin at release, if spin is ever modelled | wrist 14-30 rev/s, slap 27-41 rev/s [M] | land in this range |
| Effective blade mass for a single hit | 0.2-0.28 kg [D] | 0.15 now. A value of 0.2-0.25 would match single-hit transfer, if it is ever revisited. Keep it at or below 0.3 kg (earlier note) |

**The vertical-speed bound** [D]. The crossbar is 1.22 m (4 ft) up (USA Hockey Rule 105; corrected in fact-check: was "about 1.0 m"), so the puck's centre must stay under about 1.2 m. With vz = (Δy + ½·g·t²)/t, ignoring drag:
- from 2 m at 15 m/s, t = 0.13 s, so vz = (1.2 + 0.09)/0.13 ≈ 9.7 m/s;
- from 3 m at 15 m/s, t = 0.20 s, so vz = (1.2 + 0.20)/0.20 ≈ 7.0 m/s;
- from 4 m at 18.5 m/s, t ≈ 0.22 s, so vz = (1.2 + 0.23)/0.22 ≈ 6.6 m/s;
- from 8 m at 20 m/s, t = 0.40 s, so vz = (1.2 + 0.78)/0.40 ≈ 5.0 m/s;
- from 18 m at 25 m/s, t = 0.72 s, so vz = (1.2 + 2.54)/0.72 ≈ 5.2 m/s.
- So the 6 m/s bound holds only from about 4 m out. In tight, a real roof shot can leave at 8-10 m/s upward; what it cannot do is rise 3-10 m from range.

### 7.3 Reading this round's launches against the data

- **The follow-through scoops** (8-14 m/s upward, 75 ms of repeated contacts, blade off the ice and accelerating upward) [M, brief].
  - Real contact with the blade off the ice lasts about 10-25 ms [D].
  - A real puck reaches its top speed with the blade's recoil, then leaves as the blade slows, turns over or rides over it.
  - **[E]** A model that lets the puck sit on a blade that keeps rising and accelerating for 75 ms is reproducing a hand path no real stick follows. The real ice stops the hands about 3-16 cm into the bend:
    - shaft deflection of 3.1 cm (recreational) and 4.5 cm (elite) (Wu et al. 2003, via Kays) [S];
    - bend angles of 11-15° (Woo 2004, via Zane; earlier note) [S], over a lower lever of 0.55-0.62 m (bottom hand to blade, Wu 2003 via Kays) [S]. If the bend sits at the bottom hand, that puts the blade 10.5-16 cm off the line of the shaft [D: 0.55·sin 11° to 0.62·sin 15°].
  - That fits `ICE_BEND` = 12 cm. The 19-31 cm presses in the replays [M, brief] exceed what any real stick can bow, which is why the slide-through is needed.
- **The 40+ m/s ticks** [M, brief] are 1.3-1.5x the fastest blade measured at impact (Woo's elite, 29.1 m/s) and above the pros' toe peak of about 37 m/s (Swarén; added in fact-check). The tail of called shots (77 mph at p90, 105 mph max) sits at elite and NHL levels [D].
  - **[E]** No physical mechanism in the literature makes a recreational player's puck 1.3x a real blade speed and also put it above 30 m/s.
  - When the excess comes from the hand input, the tracking is the place to look. The contact model is not.
- **The velocity kink** when a deep-pressed blade comes off the ice [M, brief].
  - A real shaft unloads in about a quarter of its first bending period, 4-5 ms at 47-60 Hz [D]. It then throws the blade at a few m/s, mainly along the swing (2.9-9.4 m/s, one subject) [S/D].
  - So a real blade does not "ease" off the ice either. It snaps off quickly, but the snap is forward, set by about 10-16 cm of bend at most, and the hands cannot be below the ice to begin with [E].

## 8. Gaps

- **No synchronized measurement of blade speed at the contact point and puck exit speed, at 1 kHz or faster, with game pucks on real ice, for wrist or snap shots.** The best wrist data are 240 Hz on a synthetic surface (Michaud-Paquette). Kays's wrist timing was inconsistent.
- **No contact time for passes, saucer passes, snap shots or one-handed flips.** Strike contact times come from slap shots and one-timers; sweep times from wrist shots only.
- **Every lab study that put a sensor in the puck changed the puck**: 260 g and tethered (Villaseñor), 160 g on a wire with −30% speed (Lomond). No unweighted, untethered contact-time measurement exists apart from 300 Hz marker capture (Swarén, n = 2).
- **The recreational slap-shot contact times disagree**: 27 ms (Villaseñor) against 80 ms (Hannon). I found no study that settles it.
- **No effective mass or restitution measured for a hand-held stick.** All values are for pivoted or free sticks in the hit. How the hands (and gloves) couple to the blade over 20-40 ms has not been measured.
- **No time history of the puck's position along the blade during contact.** Only a chalk trace (Lomond), first contact zone, and position at release (Michaud-Paquette) exist.
- **No measured vertical launch speeds or launch angles for shots, flips or clears.** The "6 m/s" bound above is derived from target heights.
- **No measured spin for slap shots on real ice with a game puck.** Plesch used a mat, and Frayne et al. (2015, 4 elite players, 200 Hz, puck angular velocity) is paywalled and was not read.
- **How much speed comes from the shaft's stored energy is unresolved**: 3-9% from Villaseñor's energies [D] against 40-50% claimed by Roy et al. (1974) [S].
- **Kays & Smith (2014, Procedia Eng 72:563)**, the source of the "60% after the first hit" claim, could not be retrieved (HTTP 403).

## Sources read in full this round

- Kays B.T. (2013) *Ice hockey wrist and slap shots: measurement and simulation*. MS thesis, Washington State University. [Record and PDF](https://rex.libraries.wsu.edu/esploro/outputs/graduate/Ice-hockey-wrist-and-slap-shots/99900525127201842)
- Michaud-Paquette Y. (2008) *Ice hockey stick and puck biomechanical predictors of wrist shot accuracy*. MSc thesis, McGill. [Record](https://mcgill.scholaris.ca/items/d0f8ff7a-b20d-4f9e-bd4d-63f0e46934b8)
- Villaseñor-Herrera A. (2004) *Recoil effect of the ice hockey stick during a slap shot*. MSc thesis, McGill. [Record](https://mcgill.scholaris.ca/items/20d44d6b-f579-48c0-a068-4d118cc607cc)
- Lomond K.V. (2005) *Three-dimensional blade position and orientation during a stationary ice hockey slap shot*. MSc thesis, McGill. [Record](https://mcgill.scholaris.ca/items/04d8dd90-f525-493d-9689-f4848abcb01f)
- Hannon A. (2010) *Dynamic strain profile of the ice hockey stick: comparisons of calibre and shaft stiffness*. MSc thesis, McGill. [Record](https://mcgill.scholaris.ca/items/212dd3a6-79f6-4e61-8e47-a6abc33141b2)
- Flemming A. (2015) *The dynamic interaction of hand grip and ice hockey stick flexion during slap shots and wrist shots*. MSc thesis, McGill (title page dated 2014). [Record](https://mcgill.scholaris.ca/items/cefd38e6-93bf-4a49-b8e0-e7d58f7bedd9)
- Smith L.V., Bigford R.L. *Laboratory measurements of ice hockey stick performance*. WSU. [PDF](https://ssl.wsu.edu/documents/2015/10/laboratory-measurements-of-ice-hockey-stick-performance.pdf/)
- Plesch M. et al. (2019) *Influence of physical properties of hockey stick blade on shots*. [arXiv:1903.02635](https://arxiv.org/abs/1903.02635)
- Woo T. et al. (2004) *The ice hockey slap shot, elite versus recreational*. ISBS. [Paper](https://ojs.ub.uni-konstanz.de/cpa/article/view/1368)
- Swarén M. et al. (2019) *Using 3D motion capture to analyse ice hockey shooting technique on ice*. icSPORTS. [PDF](https://www.scitepress.org/publishedPapers/2019/83516/pdf/index.html)
- Doré R., Roy B. (1975) Polytechnique Montréal report EP-R-75-19 (speeds at rest and in motion only). [Record](https://publications.polymtl.ca/10039/)
- Nathan A.M. *The role of the batter's grip*. [Illinois](https://baseball.physics.illinois.edu/grip.html)

## Fact-check (2026-11-10)

I checked 20 load-bearing claims against the full text of each source: the thesis and paper copies downloaded this round, with tables and figures rendered from the PDFs. I also checked the McGill record for Villaseñor, Nathan's page and the net height online. Fixes are marked inline ("corrected in fact-check", "retagged in fact-check", "added in fact-check"). Kays & Smith 2014 still returns HTTP 403, so the "60% after the first hit" claim stays [S].

| # | Claim in the note | Verdict | What the source actually says |
|---|---|---|---|
| 1 | Pros on ice: slap 20 ± 2 ms, one-timer 15 ± 2 ms; pucks 36.4 and 38.0 m/s | confirmed | Swarén 2019: 2 DEL pros, 10 shots each, 20 Qualisys cameras at 300 Hz: "0.020 ± 0.002 s vs. 0.015 ± 0.002 s"; pucks 36.4 ± 1.0 (slap) and 38.0 ± 2.7 m/s (one-timer) |
| 2 | Villaseñor: 27 ± 5 (rec) / 38 ± 9 ms (elite) of contact, with a 260 g puck on a cable; 4 elite, 5 recreational | confirmed | Thesis: "mass (accelerometer + puck) 0.260 kg"; contact circuit "linked by a 10 m cable"; accelerometer cabled to an amplifier; 4 elite (pre-test puck speed > 100 km/h), 5 recreational; "0.038 ± 0.009 s and 0.027 ± 0.005 s". Stick was wood (Bauer Supreme 3030). (Kays's review swaps the group sizes to 5 and 4; the note correctly uses the thesis) |
| 3 | "One to three separations" during Villaseñor's contacts [M] | unsupported as [M]; retagged [S] | The phrase is in Kays's review. Villaseñor's thesis only says the circuit was not continuous and that this "could be explained by a number of factors, including blade vibration that might have affected the properties of the electrical circuit" |
| 4 | Lomond's wired puck (160 g, 6 m wire) cut speed by about 30% | confirmed | Table 15: test 73.7 / 66.9 km/h against practice 109.4 / 88.5 km/h (elite / rec), mean difference 32% / 25%, 29% overall. 8 varsity, 7 recreational (< 3 times a week). Surface: silicone-sprayed polyethylene (added to the study table) |
| 5 | Slap-shot blade leaves the ice 13 ms (elite) / 7 ms (rec) after first puck contact [D] | confirmed, with a caveat | Glossary: Δt2 = toe contact to puck contact (0.014 / 0.017 s; the "0.0017" is a typo, the discussion says 0.017 s); Δt3 = toe contact to stick off ground (0.027 / 0.024 s). Fig. 17 draws both from toe contact. The "% of shot" values are inconsistent under any reading, but the phase ratios fit this one |
| 6 | Up to about 25 ms of contact with the blade off the ice is normal; the sim should not exceed it | unsupported as a general rule (confirmed for slap shots) | Derived from Lomond (wired puck, polyethylene) plus 20-38 ms contact times. No source measures off-ice contact for wrist shots, flips or saucer passes. Inline caveat added |
| 7 | Kays's six-shooter slap means: 23.9 / 22.5 / 11.4 / **18.5 averaged over contact** / 19.4 m/s; blade "recovered to about 19-21 m/s"; puck 24.5 m/s radar, 26.2 by video | corrected | 53.5 / 50.4 / 25.5 / 43.3 mph = 23.9 / 22.5 / 11.4 / 19.4 m/s are six-shooter means. "41.3 mph from puck contact to puck release" (18.5 m/s) is shooter 5's single shot, not a mean. Fig. 3.27 per-shooter slap means average 54.7 mph = 24.5 m/s (confirmed). The +3.8 mph video offset was measured on shooters 1 and 2 only |
| 8 | Puck speed follows the blade's speed after the hit, not before | confirmed | Kays: "slight negative relationship" with blade speed at ice contact and "similar" at puck contact; puck speed "did increase" with blade speed just after contact and after release (Figs. 3.29, 3.30). n = 6 shooters, 177 slap shots |
| 9 | In slap shots the puck outruns the blade by 1.1-1.3x | corrected (scope) | True of Kays's six shooters (ages 18-44, mixed skill). Swarén's two pros: blade-tip marker about 22-25 m/s before ice contact, pucks 36-37 m/s, so about 1.4-1.7x (read off Fig. 2). The note's 0.75-1.3 target for a recreational adult still stands |
| 10 | A hand-held stick acts like 0.2-0.28 kg at the blade [D, four methods] | corrected (retagged [D/E]) | Kays's 0.233 kg (recoil factor 0.707: 5.80 oz, b = 30.9 in, I = 7865 oz·in²) and the I/Q² method are for a pivoted stick with no hands. Inverting Smith & Bigford gives 0.16-0.32 kg. Only the speed-drop method (0.277 kg) comes from held sticks, and it rests on smoothed speeds and e = 0.30. The note's own Gaps section says no held-stick value exists |
| 11 | Hand-free cannon: puck 0.63-0.85 of stick speed; composites 0.63-0.74, wood 0.74-0.85 | corrected (split) | Smith & Bigford Fig. 2, no loading: 16.8-22.8 m/s at a 27 m/s nominal stick speed, i.e. 0.62-0.84. Composites 0.62-0.75; wood 0.67-0.84 (W4 18.2 m/s). Loaded: 29.2-35.4 m/s. Pucks fired at 23 ± 0.5 m/s at a stick pivoted 0.9 m from the blade |
| 12 | Smith & Bigford's pivoted stick performed best 50-100 mm from the heel [M] | unsupported in the cited paper; retagged [S] | The paper scans 8 locations from the heel in 25 mm steps and uses "the impact location providing the highest performance" without reporting where. The 50-100 mm figure appears only in Kays's review of that work |
| 13 | Wrist shots: puck 0.91-0.98 of toe speed; contact 150-180 ms (80-290); 1.2 m carried (0.84-1.79); release 18.5-23.0 cm from the heel; face pitch change 35-58°; spin 4885-6131 °/s | confirmed | Michaud-Paquette Table 4.3 (25 university men, Vicon 240 Hz, silicone-sprayed polyethylene, P106 blade): toe 67.6-72.6 km/h, puck 65.6-67.3 km/h at release; contact time 150-180 ms, range 80-290; contact distance 115.9-124.7 cm; puck-to-blade position measured from the heel marker; Δpitch 35.2-58.2°; spin 4885-6131 °/s (range 2401-8381) |
| 14 | Hannon: slap contact 57.8 ± 13.7 / 79.7 ± 21.4 ms with a filter-set release; recreational wrist 20.4 ± 2.9 m/s | confirmed | 9 university-level, 8 recreational; kinematics low-passed at 8 Hz and "the end of the trial was calculated at the point where puck acceleration was equal to zero". Also: recreational slap 22.4 ± 6.6 m/s (used in row 18) |
| 15 | Puck impact lasts 0.41 ms frozen, 0.81-0.94 ms warm [M] | corrected (retagged) | 0.41 ms (25 °F) and 0.81 ms (72 °F) are Anderson's results in Kays's literature review [S]. Kays's own: 0.939 ms, 12 pucks at 35 mph, COR 0.427 [M] |
| 16 | No blade exceeds about 30-32 m/s "for anyone" (Woo elite 29.14 ± 1.39 m/s) | corrected | Woo confirmed: 5 varsity, 5 recreational, 60 Hz, blade at impact 29.14 ± 1.39 / 26.46 ± 0.66 m/s, wooden stick. But Swarén's pros' blade-tip marker peaks at about 34-37 m/s just after puck contact (Fig. 2). The bound holds for recreational and university players, not pros. 40+ m/s ticks are still beyond anyone |
| 17 | Recreational slap: 22.3-23.3 m/s means, mean + 2 SD = 28.7-30.9 m/s | corrected | 22.3 ± 3.2 is Villaseñor's 260 g wired puck, the bias this note corrects elsewhere. Wu's 23.3 ± 3.9 is quoted via Villaseñor [S], and its mean + 2 SD is 31.1, not 30.9. Game-puck values: Lomond practice 88.5 ± 6.6 km/h (24.6 ± 1.8 m/s, so 28.2 at + 2 SD); Hannon 22.4 ± 6.6 (35.6 at + 2 SD). Smith & Bigford add, unsourced, "In recreational play, puck speeds of 31 m/s (70 mph) are common" [V] |
| 18 | A shot on net needs at most about 6 m/s upward (net top about 1.0 m) | corrected | The crossbar is 4 ft = 1.22 m (USA Hockey Rule 105). Recomputed: 5.0-6.6 m/s from 4-18 m, about 7 m/s from 3 m, 9.7 m/s from 2 m. 8-10 m/s upward is a real roof shot in tight. A puck rising 3-10 m from range is still not a shot |
| 19 | Spin at release: wrist 19-30 rev/s, slap 27-41 rev/s per-player means (12 players, 3 NHL) | confirmed | Plesch 2019 Fig. 2 (read off): wrist about 19-30 Hz, slap about 27-41 Hz; 13 recruited, 12 completed; shooting mat; 1000 fps analysed at 250 fps; speed-spin correlation 0.66. Note: these players' wrist shots ran 26-34 m/s (their Fig. 1) |
| 20 | Skating adds +2.1 m/s (29.0 ± 1.4 vs 26.9 ± 1.5 m/s) | confirmed | Doré & Roy 1975 Table 2: "nine skillful adult amateur hockey players", on ice; puck speed from microphone timing over a known distance (an average, not release speed). Skating speed was not reported, so "no more than the skating speed" stays [D] |

Tally: 9 confirmed, 8 corrected, 3 unsupported as tagged.

**Smaller checks that passed.** Kays's blade-ice lead time of 10-19 ms (mean 14) and distance of 10.8-16.0 in (mean 12.9) before puck contact. Kays's stick rotation of 12.9-17.2 rad/s at puck contact. Shooter 5's Fig. 3.31 trace and the FE comparison (51.9 / 35.3 / 66.0 mph). Shooter 6's 60.4 mph blade, 45.4 mph puck and blade bounce. Kays's COR definition. Wu via Kays: 0.031 / 0.045 m deflection, bottom hand 0.551 / 0.624 m from the blade. Moreno's 281 and 896 °/s via Kays (Kays calls those shots snap shots in one sentence and slap shots in the next). Flemming's minor-axis strain peaking 10-20 ms before the major axis. Polano's ~35 ms and ~38 cm via Lomond. Nathan's two quotes. The sim's constants (k = 2568 N/m at flex 75, MAX_BEND 0.15 m, ICE_BEND 0.12 m, BLADE_MASS 0.15 kg) match `prototype/puck.py`.

**A source result the note did not use.** Kays's FE model varied the blade-ice friction coefficient from 0 to 0.35 and found "puck speeds increased from 75 mph to a peak of 85.2 mph" (+14%), because the shaft flexed and twisted more before puck impact [E, FE model, one shot]. That is the mechanism of this round's dropped ice-friction trial (+5-11%). It is a model result, not a measurement, and it assumes the hands hold their path.
