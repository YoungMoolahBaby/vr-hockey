# Puck on ice: how a hockey puck moves, as numbers the engine can use

Scope: puck-ice friction (value, speed, ice and puck temperature), air drag, the puck off the boards, glass, posts and ice, rims round the corners, and bouncing, rolling and wobble. The aim is honest values for `puck.py` / `physics_core.py` (no assists). Researched 2026-11-09. No code was changed.

Source-quality tags: **[measured]** a measurement (the quality is said each time), **[secondary]** a number quoted from another source that I could not read myself, **[estimate]** my own calculation from physics and the cited inputs, **[design goal]** a stated target, not a test.

The model now: Coulomb ice friction `ice_mu` 0.085 (Jon's setting; code default 0.05), no air drag, `board_bounce` 0.55 (posts and crossbar use it too), `BOARD_MU` 0.12, `ice_bounce` 0.25, `net_bounce` 0.08, puck 0.170 kg.

## Headline

1. **Jon's ice_mu = 0.085 sits inside every number I could find for a puck on ice**: about 0.07-0.12 measured on fresh rink ice at 1-2 m/s (a student video study), 0.05-0.20 "typical" (a patent), "< 0.15" (Haché, quoted), and 0.1 as physicists' usual assumption. There is no good lab measurement of a puck's kinetic friction on rink ice. The literature gap is real, not a search failure.
2. **What the model is missing is air drag, not a different mu.** By my estimate (Cd about 0.6 on the puck's 76 x 25 mm side profile) drag slows a sliding puck about as much as ice friction does at **about 14 m/s**, and **about 8 times as much at 40 m/s**. Physicist Rhett Allain's independent estimate (Physics World, 2020) implies almost the same drag constant. Over 15 m, a hard pass (10-20 m/s) loses 1.5-3 times more speed than the model now says. A shot from the point loses 8-11% by the net instead of 1-4%. Slow pucks (stickhandling, soft passes under 5 m/s) barely change.
3. **Coulomb (constant-mu) friction is a reasonable model for a puck.** A puck presses on the ice about 10,000 times more lightly than a skate blade, so it cannot make the meltwater film that gives skates their speed-dependent friction. The only speed-dependent part worth adding is the drag term.
4. **The boards are too lively.** A frozen game puck fired at a rigid plate at 55 mph rebounds with a coefficient of restitution (e) of about 0.26; a warm puck about 0.35-0.38. A dasher-board patent sets "at least 30-40%" rebound as the design goal. Recommend `board_bounce` 0.30, down from 0.55. Posts get the same value.
5. **Board friction 0.12 is a sensible *effective* value** for a puck with no spin. A real puck rimming the boards spins up and then rolls along them, which caps its loss at about a third of its speed. That is about what 0.12 gives over a full 180 degrees of corners.

---

## 1. Puck-ice friction

### 1.1 What has been measured or quoted

| Value | What it is | Source | Quality |
|---|---|---|---|
| mu about 0.066 → 0.118 as the puck slowed from 2.1 to 0.8 m/s (mean deceleration about 0.90 m/s², so mu about 0.09) | Video of an NHL puck (164 g) hand-slid on fresh, dry, resurfaced ice at the Utah Olympic Oval; VideoPoint tracking, cubic fit | Mitchell, Stejskal, Davis & Farrell, "Friction is a Drag", Westminster College Physics 211 project (c. 2004-05), Table 1, "smooth ice trial 2" — [PDF](http://cs.westminstercollege.edu/~ccline/courses/resources/wp/proj/211-W-frictiondrag.pdf) | [measured] by undergraduates. 5 smooth, 3 rough, 3 wet trials; 30 fps; the rising mu at low speed comes from a cubic fit and may be a fitting artifact. The authors note "no numerical consistency between trials". Rough (heavily used) ice gave a higher starting mu than smooth ice. |
| 0.05 - 0.20 | "the typical range for coefficient of friction (sliding) between a regulation ice hockey puck (vulcanized rubber) and ice" | Vellines, US Patent 5,269,520 "Street hockey puck" (1993) — [Google Patents](https://patents.google.com/patent/US5269520A/en) | [secondary]; no test is cited |
| "roughly less than 0.15" | puck on ice | Deane-Shinbrot & Rapp, WPI MQP (2013), citing Haché, *The Physics of Hockey* — [PDF](https://digital.wpi.edu/downloads/hh63sx19v) | [secondary] |
| about 0.06 (static) | "rubber on ice (i.e. hockey puck to ice)" | Westminster report above, citing "Ableman, 2004" and "Kurtus, 2003" (web pages) | [secondary], weak |
| 0.1 | "assuming the coefficient of friction is about 0.1 for our puck on ice" | Rhett Allain, "Physics on ice", *Physics World*, April 2020 — [article](https://physicsworld.com/a/physics-on-ice/) | an assumption, not a measurement |
| frozen pucks slid about 26% farther than room-temperature ones from the same slingshot (427 vs 339 in on average; pucks at about -13 °C vs about 18 °C) | 5 trials per group on an outdoor rink | Calgary Youth Science Fair project — [CYSF](https://platform.cysf.org/project/b1957273-035d-4053-afee-35e82d4103b8/) | [measured], school science fair, n = 5, ice not controlled. With the same launch speed, slide distance goes as 1/mu, so mu(warm) is about 1.26 x mu(frozen). |

Haché's own book (*The Physics of Hockey*, 2002) is on the Internet Archive only as a restricted loan, and Google Books returned no puck-on-ice coefficient in its snippets. Its dynamic-friction table lists rubber on concrete, steel on steel, wood on wood, wax on snow and steel on ice, apparently with no puck-on-ice row. I did not find any peer-reviewed tribometer study of a hockey puck on rink ice. Several searches came back empty, and the theses above say the same ("little research has been performed").

**Takeaway:** mu = 0.085 is consistent with the only on-ice measurement (about 0.07-0.12 at 1-2 m/s, fresh ice) and with every quoted range. The data cannot tell 0.07 from 0.10, so feel can decide within that band. "0.02 felt like air hockey" agrees with the data: 0.02 is below anything quoted for a puck.

### 1.2 Speed dependence: is constant (Coulomb) friction right?

- Ice friction for skates and runners falls with speed because frictional heat melts a thin lubricating water film. Kietzig, Hatzikiriakos & Englezos's review "Physics of ice friction" (J. Appl. Phys. 107, 081101, 2010) describes boundary, mixed and hydrodynamic regimes that depend on film thickness, temperature and speed [secondary; review seen only through citations]. A Physics viewpoint on Liefferink, Hsia, Weber & Bonn, *Phys. Rev. X* 11, 011025 (2021) reports friction high at about -100 °C, lowest at intermediate temperatures, and rising again toward 0 °C. It also reports ploughing setting in at about -20 °C for a small sphere and -8 °C for a skate section ([Physics 14, 20](https://physics.aps.org/articles/v14/20)). These are steel sliders, not rubber.
- **[estimate] A puck is in a different regime.** Its weight (0.170 kg x 9.81 = 1.67 N) spreads over a 76 mm face (45.6 cm²), a nominal pressure of about **370 Pa**. A skater's blade presses at several MPa. The frictional heat flux mu·p·v at 10 m/s is about 0.085 x 370 x 10 ≈ **300 W/m²**, roughly 10^4 times less than a skate's. A puck cannot melt its own lubricating film the way a skate does, so the classic "friction falls as 1/sqrt(v)" meltwater behaviour should not apply. It stays in the boundary (dry-ish) regime, where friction is roughly independent of speed.
- At very low speed rubber gets sticky on ice. In a vendor tribometer test (6 mm rubber ball, 2 N, speeds of 0.03 mm/s to 2.6 cm/s), the friction coefficient was above 0.3 at -10 °C, and about 0.8 static and 0.2 dynamic at -40/-50 °C ([Nanovea application note](https://nanovea.com/low-temperature-tribology/)) [measured, vendor; much higher contact pressure than a puck]. It agrees with the student finding that mu rises as the puck stops. For the game this only affects the last few centimetres, and the Coulomb model already stops the puck dead.
- **Conclusion:** keep Coulomb friction and add a quadratic air-drag term (section 2). Voyenli & Eriksen (American Journal of Physics 53, 1149, 1985) analysed a puck that slides and spins at once: friction couples the two motions so that **both stop at the same moment**. A consequence [estimate, my reading of the physics]: while a puck spins fast, the friction against its straight-line motion is less than mu·m·g ([AJP abstract](https://pubs.aip.org/aapt/ajp/article-abstract/53/12/1149/1052455/On-the-motion-of-an-ice-hockey-puck); [Tel Aviv U. physics quiz summary](https://www.tau.ac.il/~kantor/QUIZ/96/A05.96.html)). That matters only if puck spin is ever added.

### 1.3 Ice temperature and quality

- NHL arena ice crews target a surface temperature of about **22-22.5 °F (-5.6 °C) at puck drop**. Ice at about 19 °F is "a little brittle", and at 24-25 °F players feel they are sinking into it. Hot, humid buildings make a lot of snow, which gets sticky and makes pucks bounce; bouncing pucks are the crews' main complaint (Nashville Predators operations staff, [NHL.com, 2024](https://www.nhl.com/predators/news/your-questions-answered-as-predators-operations-team-reinstalls-ice-at-bridgestone-arena-for-2024-25-season); paraphrased except the quoted words) [practitioner, official site].
- Fresh vs late-period ice: the only numbers come from the Westminster project, where heavily used ("many asperities") ice gave a higher starting mu than freshly resurfaced ice, but without consistent values. **[estimate]** On fresh ice mu is probably near the low end (0.06-0.08). Snow late in a period raises it, perhaps to 0.10-0.12, and makes the puck bounce and roll (section 4). No source quantifies this.

### 1.4 Frozen vs warm pucks

- NHL game pucks are kept frozen. In-play puck temperatures measured with an infrared sensor at two rinks on four occasions were **12-25 °F (-11 to -4 °C)** (Anderson 2008, WSU MS thesis, section 3.7 — [WSU Sports Science Lab PDF](https://ssl.wsu.edu/documents/2015/10/experimental-characterization-of-ice-hockey-sticks-and-pucks.pdf/)) [measured].
- Freezing is done mainly to cut bounce (Anderson; WPI). Lower friction is a claimed second reason (WPI MQP, citing a web source) [secondary]. The CYSF glide test (frozen pucks slid about 26% farther) is the only direct comparison I found, and it is weak.
- The game should treat every puck as a frozen game puck. That fits mu 0.085 and the frozen restitution values below.

---

## 2. Air drag

### 2.1 The estimate

- No measured drag coefficient for a puck was readable online. Böhm, Schwiewagner & Senner measured puck drag, lift and pitching moment in a wind tunnel against angle of attack and Reynolds number (*Sports Engineering* 10:75-85, 2007, [doi:10.1007/BF02844205](https://doi.org/10.1007/BF02844205)), but the paper is paywalled and I could not get its values.
- **[estimate]** A puck sliding flat presents a 76.2 x 25.4 mm side profile, **A = 19.4 cm²**. On the ice it acts roughly like a short cylinder in cross-flow plus its mirror image (length/diameter about 0.67). For finite cylinders in cross-flow, General Electric's APEX-299 chart gives **Cd = 0.725 at L/D = 2, Re = 5x10⁴** ([EES drag-coefficient function, citing Heddleson, Brown & Cliffe 1957](https://fchartsoftware.com/ees/drag_coefficients/hs1030.htm)), and shorter cylinders have lower Cd. I take **Cd ≈ 0.6 (range 0.45-0.8)**. The Reynolds number is 6x10⁴ at 10 m/s and 2.3x10⁵ at 40 m/s. Sharp edges fix the separation points, so Cd should stay roughly constant over that range.
- Rink air near the ice is about 0-10 °C, so rho ≈ 1.27 kg/m³. The drag deceleration is a_drag = k v² with

  **k = ½ ρ Cd A / m = 0.5 x 1.27 x 0.6 x 1.94e-3 / 0.170 ≈ 0.0043 per m** (range 0.0033-0.0058).

- **Cross-check:** Allain (*Physics World*, 2020) gives a 170 g puck at 160 km/h (44.4 m/s) with mu 0.1 a stopping distance of "just over 1000 m" without air and **227 m** with it ("air resistance plays a significant role"). Solving the same model for k gives **k ≈ 0.0055 per m** (Cd about 0.8 on D·H with ρ 1.2). That is independent and within my range. Both are estimates, not measurements.
- **Counter-claim:** a news story about a foam-puck skills-competition shot ([infonews.ca](https://infonews.ca/?p=333680)) paraphrases Haché as saying a regular rubber puck is too heavy for air to have any tangible effect. Against that, the plain numbers: k v² at 40 m/s is 7 m/s², more than 8 times the ice friction (0.83 m/s²). Over 18 m, drag alone takes about 7.5% off a 40 m/s shot, roughly 3 m/s or 7 mph. That is small next to the shot's speed but large next to ice friction. "Not tangible" holds for a single shot's flight, not for the slide of a hard pass or dump-in.

### 2.2 Size of the effect

| speed | ice friction mu·g (mu 0.085) | air drag k·v² (k 0.0043) | drag / friction |
|---|---|---|---|
| 2 m/s (stickhandling) | 0.83 m/s² | 0.02 | 2% |
| 5 m/s (soft pass) | 0.83 | 0.11 | 13% |
| 10 m/s (firm pass) | 0.83 | 0.43 | 52% |
| 14 m/s | 0.83 | 0.84 | about 1 (the crossover; 12-16 m/s across the k range) |
| 20 m/s (hard pass, dump) | 0.83 | 1.72 | 2.1x |
| 30 m/s | 0.83 | 3.87 | 4.6x |
| 40 m/s (a hard slap shot; elite play reaches "70-100 miles per hour", 31-45 m/s, per Anderson 2008) | 0.83 | 6.9 | 8.3x |

Jon's 40-46 mph shots are 18-21 m/s, so at his speeds drag is already about twice the ice friction.

---

## 3. Concrete checks: current (mu 0.085, no drag) vs recommended (mu 0.085 + drag k 0.0043)

Formulas for the recommended model (a = mu·g):
- stopping distance s = ln(1 + k v0²/a) / (2k)
- speed after distance x: v² = (v0² + a/k)·e^(−2kx) − a/k
- launch speed needed to arrive at v1 after x: v0² = (v1² + a/k)·e^(2kx) − a/k
- position at time t: s(t) = ln(cos(φ0 − √(ak)·t) / cos φ0) / k, with φ0 = atan(v0·√(k/a)), valid until t_stop = φ0/√(ak)

### 3.1 How far a puck slides (to a stop on open ice), and how long it takes

| v0 | current (0.085) | **recommended (0.085 + drag)** | drag low k 0.0033 | drag high k 0.0058 | old code default (0.05) |
|---|---|---|---|---|---|
| 1 m/s | 0.6 m, 1.2 s | **0.6 m, 1.2 s** | 0.6 m | 0.6 m | 1.0 m, 2.0 s |
| 2 m/s | 2.4 m, 2.4 s | **2.4 m, 2.4 s** | 2.4 m | 2.4 m | 4.1 m, 4.1 s |
| 3 m/s | 5.4 m, 3.6 s | **5.3 m, 3.5 s** | 5.3 m | 5.2 m | 9.2 m, 6.1 s |
| 5 m/s | 15.0 m, 6.0 s | **14.1 m, 5.8 s** | 14.3 m | 13.8 m | 25.5 m, 10.2 s |
| 8 m/s | 38.4 m, 9.6 s | **33.2 m, 8.7 s** | 34.2 m | 31.7 m | 65.2 m |
| 10 m/s | 60.0 m, 12.0 s | **48.4 m, 10.4 s** | 50.5 m | 45.5 m | 101.9 m |
| 15 m/s | 134.9 m, 18.0 s | **89.6 m, 13.7 s** | 96.5 m | 81.2 m | 229.4 m |
| 20 m/s | 239.9 m, 24.0 s | **130.2 m, 16.1 s** | 143.8 m | 114.7 m | 407.7 m |
| 30 m/s | 539.7 m, 36.0 s | **201.2 m, 19.0 s** | 230.0 m | 170.9 m | 917.4 m |
| 40 m/s | 959.4 m, 48.0 s | **258.7 m, 20.6 s** | 301.9 m | 215.1 m | 1631 m |

(Distances past about 30 m are notional: the puck hits the boards first. They show how much speed the puck still carries.)

### 3.2 A 15 m pass: speed left on arrival and travel time

| pass speed | current | **recommended** |
|---|---|---|
| 5 m/s | stops at 15.0 m (just fails) | **stops at 14.1 m** |
| 8 m/s | 6.24 m/s (−22%), 2.11 s | **5.73 m/s (−28%), 2.19 s** |
| 10 m/s | 8.66 m/s (−13%), 1.61 s | **8.03 m/s (−20%), 1.67 s** |
| 12 m/s | 10.91 (−9%), 1.31 s | **10.15 (−15%), 1.36 s** |
| 15 m/s | 14.14 (−6%), 1.03 s | **13.20 (−12%), 1.07 s** |
| 20 m/s | 19.36 (−3%), 0.76 s | **18.11 (−9%), 0.79 s** |

Travel times barely change (by 0.03-0.08 s), so the AI's pass timing barely changes. Arrival speeds of hard passes fall by 0.6-1.3 m/s.

### 3.3 Dump-ins and icing

Regulation (NHL) rink: 61 m (200 ft) long, red line 30.5 m from each end board, goal line 3.35 m (11 ft) from the end boards, so red line to goal line is 27.15 m. Our game rink is 46 m long, so its red line is 23 m from the end boards.

| launched from the red line at | speed at end boards, 61 m rink: current | **recommended** | 46 m rink: current | **recommended** |
|---|---|---|---|---|
| 8 m/s | 3.6 m/s | **2.1** | 5.1 | **4.2** |
| 10 m/s | 7.0 | **5.7** | 7.9 | **6.9** |
| 15 m/s | 13.2 | **11.3** | 13.7 | **12.2** |
| 20 m/s | 18.7 | **16.2** | 19.0 | **17.1** |
| 25 m/s | 24.0 | **20.9** | — | — |
| minimum launch speed to reach the end boards | 7.1 m/s | **7.6 m/s** | 6.2 | **6.5** |
| minimum launch speed to cross the goal line (icing), 61 m rink | 6.7 m/s | **7.1 m/s** | | |

Any real dump-in or icing clear (10-25 m/s) reaches the end boards under either model, as it does in real hockey. The models differ in how much speed the puck has left for the rim and the rebound.

**A dump-in rimmed round the whole end** (red line, down the wall, round both 8.53 m corners and out the far corner, 61 m rink; my integration with continuous wall contact, board mu 0.12, no spin):

| launch | current | recommended (drag) | recommended with board mu 0.2 |
|---|---|---|---|
| 15 m/s | 6.9 m/s out of the far corner | 4.1 | 1.6 |
| 20 m/s | 11.4 | 8.2 | 5.7 |
| 25 m/s | 15.3 | 11.5 | 8.5 |

### 3.4 Shots along the ice

| shot speed | at the net from the slot (9 m): current / **rec** | from the point (18 m): current / **rec** | time to 18 m: current / rec |
|---|---|---|---|
| 20 m/s (about Jon's 45 mph) | 19.6 / **18.9** | 19.2 / **17.7 (−11%)** | 0.92 / 0.96 s |
| 30 m/s | 29.7 / **28.6** | 29.5 / **27.3 (−9%)** | 0.61 / 0.63 s |
| 40 m/s | 39.8 / **38.3** | 39.6 / **36.6 (−9%)** | 0.45 / 0.47 s |
| 45 m/s (elite slap shot) | 44.8 / **43.1** | 44.7 / **41.3 (−8%)** | 0.40 / 0.42 s |

A radar gun at the shooter reads the launch speed. With drag the puck reaches the goalie 0.7-3.5 m/s slower, and up to about 40 ms later.

---

## 4. Off the boards, glass, posts and ice; rims; bouncing and rolling

### 4.1 Coefficient of restitution of a puck

| e | condition | source | quality |
|---|---|---|---|
| 0.45-0.55 | room-temperature puck, drop test on a rigid surface | Haché 2002, quoted in Anderson 2008 (ref 3.1) | [secondary] low speed |
| 0.12-0.27 | frozen puck, same drop test | same | [secondary] |
| **0.383 (brand A), 0.349 (brand B)** | room temperature (72 °F), fired edge-on (sabot, vertical orientation) at a rigid steel strike plate at **55 mph (24.6 m/s)**, light gates in and out, 12 pucks per brand, 6 good impacts each | Anderson 2008, WSU MS thesis (Lloyd V. Smith lab), section 3.3 — [PDF](https://ssl.wsu.edu/documents/2015/10/experimental-characterization-of-ice-hockey-sticks-and-pucks.pdf/) | [measured] |
| **0.267 (A), 0.256 (B)** | frozen to 25 ± 2 °F (−4 °C), 55 mph | same, section 3.7 | [measured]. Freezing cut e by 32% (A) and 26% (B) and raised dynamic stiffness by 626% and 488%. Below 25 °F the impact force exceeded the load cell's range. |
| e falls linearly with impact speed (warm brand A, tested at 55-85 mph) | | same, section 3.9, Fig. 3.17 | [measured]. The plot puts the drop-test value (0.45-0.55) at 24.5 mph, and the 55 mph value is 0.383; higher speeds give lower e (I could not read the exact 85 mph point). |
| "rebound at at least about 30-40% of its impact velocity", vs "less than 10%" without the stiffening structure; "a rebound speed of at least 30-40 mph" for a 100 mph puck | dasher-board kickplate | Kapsalis et al., US 2013/0040745 A1 "Dasher board assembly" (filed 2012) — [Google Patents](https://patents.google.com/patent/US20130040745A1/en) | [design goal], no test data |
| 45-55% of its velocity kept when a puck bounces on the ice | | WPI MQP 2013, ref [4] (unidentified) | [secondary]; probably a warm puck |

**Reading:** a frozen game puck hitting something rigid (the post, a stiff kickplate) at game speed rebounds at e ≈ 0.25-0.3. Real boards flex and dissipate a little more, and the board makers aim for at least 0.3-0.4. Our 0.55 matches a *warm* puck dropped at low speed, the opposite of game conditions. With e = 0.55 a 20 m/s puck fired square into the end boards comes back 56 m (recommended friction) and runs the length of the rink. With e = 0.30 it comes back 20 m, to about the top of the circles, which matches hockey experience.

| straight-in hit at | e 0.30: rebound speed, slides back | e 0.55 (now): rebound, slides back |
|---|---|---|
| 5 m/s | 1.5 m/s, 1.3 m | 2.8 m/s, 4.4 m |
| 10 m/s | 3.0 m/s, 5.3 m | 5.5 m/s, 16.9 m |
| 20 m/s | 6.0 m/s, 19.8 m | 11.0 m/s, 56.4 m |
| 30 m/s | 9.0 m/s, 40.6 m | 16.5 m/s, 102 m |

(Slide-back distances use the recommended friction and drag.)

- **Glass:** I found no rebound data for puck on glass. Tempered glass or acrylic in a flexible mount is probably near the boards' value. Use the same 0.30 until someone measures it.
- **Posts and crossbar:** steel tube about 60 mm across (the code's POST_R 0.03 fits), effectively rigid, so the frozen rigid-plate value applies: **0.30**. A separate `post_bounce` would allow tuning later. Today posts borrow `board_bounce`.
- **Ice (a flipped or airborne puck landing flat):** the frozen drop-test range 0.12-0.27 applies. The current 0.25 is at its top; 0.2-0.25 is fine.
- **Net mesh:** no data; 0.08 with the existing 0.97-per-step damping is plausible.

### 4.2 Friction along the boards and rims round the corners

- No measured coefficient for puck rubber on the HDPE board facing was found. Allain says only that it "would likely be much higher" than on ice. **[estimate]** Rubber on a smooth polymer is probably 0.2-0.4.
- **[estimate] The spin argument matters more than the number.** On a curved wall the normal force is m v²/R. A puck with no spin, in continuous contact, keeps exp(−mu_b·θ) of its speed through an angle θ: with mu_b 0.12 that is 0.83 through one 90 degree corner and 0.69 through both (180 degrees); with mu_b 0.3 it is 0.62 and 0.39. A real puck is not a no-spin slider, though. The wall's friction spins it up (for a disc, I = ½ m r²), and the slip speed at the wall falls three times as fast as the forward speed. Once the puck **rolls along the boards** it has lost exactly **one third** of its speed (it keeps 2/3 of its energy), and after that the wall takes almost nothing. With mu_b 0.2-0.3 it reaches rolling within about 60-95 degrees of an 8.5 m corner. So a real rim loses about 1/3 in the first corner and little in the second, and the current no-spin mu_b 0.12 loses 0.69 over both. **The total is about right, so keep 0.12** while the model has no spin. Raising it toward the "true" value without spin would kill rims: even 0.2 cuts a 20 m/s dump to 5.7 m/s out of the far corner rather than 8.2 (section 3.3).
- The puck may also bounce where a straight board meets a curved one, losing contact for a moment (Allain).

### 4.3 Bouncing, rolling on edge, wobble, flipping

- **When pucks bounce or roll:** on snowy or sticky ice (NHL.com: snow "can make pucks bounce", the crews' "main complaint"), with warm pucks (the reason pucks are frozen: e is about a third lower frozen, per Anderson), and after deflections off sticks, skates or the boards, which can stand a puck on its edge. **No source gives frequencies.** I found nothing on how often a puck rolls or bounces in a game.
- **Spin and slide:** a sliding, spinning puck stops spinning and stops sliding at the same moment (Voyenli & Eriksen 1985). Shots leave the blade spinning; a blade cover that adds grip raised puck spin by about 6% (Plesch et al. 2019, arXiv:1903.02635, already in the stick-feel notes).
- **In flight:** puck flight is modelled with drag, lift and pitching moment that depend on angle of attack (Böhm et al. 2007). A spinning puck holds its plane gyroscopically, and a wobbling one presents more area and loses more speed (no numbers found).
- **For this project:** our puck is a flat disc with no tilt or spin. Rolling on edge is mostly bad luck that a VR player cannot read or control, so leave it out for now (an open question below). Drag on an airborne puck can use the same k (a puck flying flat shows the same side profile).

---

## 5. Recommendations for this project

| parameter | current | recommended | why |
|---|---|---|---|
| `ice_mu` | 0.085 (Jon); code default 0.05 | **0.085**, and make it the code default (feel band 0.07-0.10) | Inside the only on-ice measurement (about 0.07-0.12 at 1-2 m/s) and every quoted range (0.05-0.20, < 0.15, 0.1). 0.05 is at the very bottom. Jon chose 0.085 by feel, and the evidence cannot beat that. |
| new: air drag `air_k` (deceleration k·v², on the ice and in the air) | none | **0.0043 per m** (range 0.0033-0.0058) | ½ρ·Cd·A/m with Cd ≈ 0.6 on the 76 x 25 mm side profile. It matches ice friction at about 14 m/s and is 8x it at 40 m/s. An independent estimate (Allain 2020) implies 0.0055. It leaves stickhandling alone (under 3 m/s it adds less than 5% to the deceleration). Over 15 m, hard passes (10-20 m/s) lose 9-20% rather than 3-13%. Shots from the point lose 8-11% by the net rather than 1-4%. |
| friction speed dependence | none (Coulomb) | **keep Coulomb**; no extra term | A puck presses on the ice at about 370 Pa, about 10^4 times less than a skate, so meltwater lubrication should not set in. The only speed-dependent physics that matters is drag. |
| `board_bounce` (boards and glass) | 0.55 | **0.30** (0.25-0.40) | A frozen puck at a rigid plate at 55 mph: e 0.26 (warm 0.35-0.38). Board design goal: 30-40% rebound. 0.55 is a warm puck's low-speed drop value. |
| posts and crossbar (now `board_bounce`) | 0.55 | **0.30**, ideally its own `post_bounce` | Steel, effectively rigid, so the rigid-plate value. |
| `BOARD_MU` (zone.py) | 0.12 | **keep 0.12** (it is an effective value for a puck with no spin) | A real puck spins up and rolls along the boards, losing about 1/3 of its speed; 0.12 over 180 degrees gives 0.69. A "true" rubber-on-HDPE mu (0.2-0.4, est.) without spin would kill rims. |
| `ice_bounce` | 0.25 | **0.25** (or 0.2) | Frozen drop test 0.12-0.27. |
| `net_bounce` | 0.08 | **keep** | no data |
| `puck_mass` | 0.170 | **keep** | Regulation 5.5-6 oz (156-170 g) (Anderson 2008). |
| analytic predictions: `threes._path`, `retrieval.rim_launch`, `powerplay` (a = ice_mu·G) | Coulomb only | **use the drag closed forms in section 3** if `air_k` is added | Otherwise the AI and drills mispredict hard pucks. At 15-20 m/s the 2 s path is 1.7-2.8 m too long, and rim launch speeds come out too low. |

Implementation sketch (for whoever changes the code; nothing changed here): in `_integrate` on the ice, `dec = (ice_mu*G + air_k*s*s)*h` in place of `ice_mu*G*h`. In the air, `v -= air_k*|v|*v*h`. At 1 kHz with 4 substeps the drag step is far below any stability limit (k·v·h ≈ 0.0043 x 45 x 0.00025 ≈ 5e-5).

## 6. Open questions

1. **No real measurement of puck-ice kinetic friction across speeds.** Jon could measure it at his rink: film a puck from above at 120-240 fps over a taped 5 m scale, at 2, 5, 10 and 15 m/s. Fitting a + k·v² to the slowdown would give both mu and the drag constant, on fresh ice and again late in a session.
2. **The Böhm et al. (2007) wind-tunnel drag coefficient** is paywalled. Its Cd would firm up `air_k` (my range is ±35%).
3. **Board and glass restitution on real boards**, by speed and by height (the kickplate vs the upper board vs the glass), and whether some arenas' "lively boards" are measurable. No data found.
4. **Rim losses:** how fast a rim really comes out of the far corner. A rink video could test both the 2/3 spin-up rule and mu_b. If puck spin is ever modelled, use the physical mu_b (0.2-0.4) with spin, not 0.12 without it.
5. **Late-period ice:** mu, and how often pucks bounce or roll, on snowy vs fresh ice. A per-period "ice wear" setting (mu 0.075 → 0.10) is a design option with no data behind its size.
6. **Low-speed rise of mu** (sticky rubber below about 0.5 m/s): does it matter for stickhandling feel? Possibly for a puck settling on the blade. Untested.
7. **Rolling on edge and wobble:** whether to model them at all. They are real, but they are luck and hard to read in VR. A first step could be cosmetic only (tilt the drawn puck after deflections, physics unchanged).

## Sources

- Anderson, R. L. (2008). *Experimental Characterization of Ice Hockey Sticks and Pucks*. MS thesis, Washington State University (chair L. V. Smith). [WSU Sports Science Lab PDF](https://ssl.wsu.edu/documents/2015/10/experimental-characterization-of-ice-hockey-sticks-and-pucks.pdf/); [WSU repository record](https://rex.libraries.wsu.edu/esploro/outputs/graduate/Experimental-characterization-of-ice-hockey-sticks/99900525153101842)
- Haché, A. (2002). *The Physics of Hockey*. Johns Hopkins University Press. (Drop-test COR, quoted by Anderson; "mu < 0.15", quoted by Deane-Shinbrot & Rapp.)
- Deane-Shinbrot, S. J. & Rapp, J. A. (2013). *Mechanical Characteristics of Elastomeric Hockey Pucks under Practice and Game Conditions*. WPI Major Qualifying Project. [PDF](https://digital.wpi.edu/downloads/hh63sx19v)
- Mitchell, J., Stejskal, S., Davis, C. & Farrell, M. (c. 2004-05). "Friction is a Drag". Westminster College Physics 211 project. [PDF](http://cs.westminstercollege.edu/~ccline/courses/resources/wp/proj/211-W-frictiondrag.pdf)
- Vellines, J. W. (1993). US Patent 5,269,520, "Street hockey puck". [Google Patents](https://patents.google.com/patent/US5269520A/en)
- Calgary Youth Science Fair project, puck temperature vs glide distance. [CYSF](https://platform.cysf.org/project/b1957273-035d-4053-afee-35e82d4103b8/)
- Allain, R. (2020). "Physics on ice". *Physics World*, April 2020. [article](https://physicsworld.com/a/physics-on-ice/)
- infonews.ca, "University professor: Physics have hidden effects on NHL slapshots" (Haché paraphrased on foam vs rubber pucks). [article](https://infonews.ca/?p=333680)
- Böhm, H., Schwiewagner, C. & Senner, V. (2007). "Simulation of puck flight to determine spectator safety for various ice hockey board heights". *Sports Engineering* 10, 75-85. [doi:10.1007/BF02844205](https://doi.org/10.1007/BF02844205) (not read: paywalled)
- Heddleson, C. F., Brown, D. L. & Cliffe, R. T. (1957). *Summary of Drag Coefficients of Various Shaped Cylinders*, APEX-299, General Electric. Via the [EES finite-cylinder drag function](https://fchartsoftware.com/ees/drag_coefficients/hs1030.htm)
- Voyenli, K. & Eriksen, E. (1985). "On the motion of an ice hockey puck". *American Journal of Physics* 53, 1149. [abstract](https://pubs.aip.org/aapt/ajp/article-abstract/53/12/1149/1052455/On-the-motion-of-an-ice-hockey-puck); [Tel Aviv U. quiz summary](https://www.tau.ac.il/~kantor/QUIZ/96/A05.96.html)
- Liefferink, R. W., Hsia, F.-C., Weber, B. & Bonn, D. (2021). "Friction on Ice: How Temperature, Pressure, and Speed Control the Slipperiness of Ice". *Phys. Rev. X* 11, 011025. Via the [Physics viewpoint](https://physics.aps.org/articles/v14/20)
- Kietzig, A.-M., Hatzikiriakos, S. G. & Englezos, P. (2010). "Physics of ice friction". *J. Appl. Phys.* 107, 081101. (Seen through citations.)
- Nanovea, "Rubber friction on ice from 0 to −50 °C" (application note). [page](https://nanovea.com/low-temperature-tribology/)
- Kapsalis, M. et al. (2013). US 2013/0040745 A1, "Dasher board assembly". [Google Patents](https://patents.google.com/patent/US20130040745A1/en)
- NHL.com (2024). "Your questions answered as Predators operations team reinstalls ice at Bridgestone Arena". [article](https://www.nhl.com/predators/news/your-questions-answered-as-predators-operations-team-reinstalls-ice-at-bridgestone-arena-for-2024-25-season)
- Rink geometry (61 x 25.9 m, 8.53 m corners, goal line 3.35 m from the end boards): NHL dimensions, as already encoded in `prototype/zone.py`.

---

## Verification

A second reader checked these claims on 2026-11-09 against the sources themselves. I downloaded and text-extracted the PDFs, and read the scanned Voyenli & Eriksen paper as an image. I re-ran every calculation separately, using the closed forms plus a numerical integration with a 10 µs step. Verdicts: **confirmed** means the source says it, with these numbers. **Corrected** gives the right value or section. **Unsupported** means it was not found, or the source does not say it. No claim ended up unsupported.

1. **Westminster video study (mu 0.066-0.118): confirmed.** Table 1, "smooth ice trial 2", shows v 2.109 → 0.818 m/s, a −0.651 → −1.154 m/s² (mean about 0.90), and a mu column of 0.0664 → 0.1178. The puck weighed 164.2 g. The site was the "Olympic Ice Oval in West Valley, Utah". "Smooth" ice means resurfaced and then left to solidify. The puck was slid by hand, and the timestamps are 0.033 s apart (30 fps). The authors say there is "no numerical consistency between trials". They also say the cubic fit "may introduce a physical property that does not necessarily exist". Note that in every smooth trial, mu *fell* as speed rose. This is the only speed data for a puck on ice (see item 20).
2. **Vellines patent (0.05-0.20): confirmed.** It says: "The typical range for coefficient of friction (sliding) between a regulation ice hockey puck (vulcanized rubber) and ice is 0.05 to 0.20". It was filed on 19 Feb 1993 and published on 14 Dec 1993. No test is cited.
3. **WPI MQP (< 0.15, citing Haché): confirmed.** It says: "The coefficient of friction between a puck and ice, μ, is roughly less than 0.15 [1]", where [1] is Haché (2002). A side correction to the table in 4.1: the second paper's "45-55% of its original velocity" bounce figure cites [4], which is also Haché (2002). It is not an unidentified source, and it is the warm drop-test value.
4. **CYSF frozen vs warm pucks: corrected (minor).** The averages, 427.2 vs 339.4 in (26% farther), are right. The groups' average temperatures were about −12.8 °C and **16.9 °C**, not 18 °C. The rink was outdoors and the student noted snow on the ice. One trial of five went the other way. The evidence is still weak.
5. **Anderson, warm COR 0.383 / 0.349 at 55 mph: confirmed.** The numbers are in thesis **section 3.6 (Brand Comparison)**; section 3.3 only describes the method. Test conditions: 72 ± 2 °F, 55 ± 1 mph, 12 pucks per brand, 6 good edge-on impacts each, into a rigid plate on load cells. The PDF at the ssl.wsu.edu link is the shorter Anderson & Smith conference paper. Its text has no COR numbers (they are only in its figures), and it says the brands are "commonly used in recreational play". The numbers are in the MS thesis ([WSU repository record](https://rex.libraries.wsu.edu/esploro/outputs/graduate/Experimental-characterization-of-ice-hockey-sticks/99900525153101842), file R_Anderson_042308.pdf). Neither document says the pucks were NHL game pucks.
6. **Anderson, frozen COR 0.267 / 0.256: confirmed.** Thesis section 3.7 says "e = 0.267 for PA and e = 0.256 for PB" at 25 ± 2 °F. COR fell by 32% / 26% and dynamic stiffness rose by 626% / 488%.
7. **Haché drop tests (0.45-0.55 warm, 0.12-0.27 frozen): confirmed as quoted.** The figures appear in thesis ref [3.1] and conference-paper ref [1]. I did not check Haché's book directly. Extra evidence: WPI's own drop tests (a 1.8 m drop onto the floor, timed by the ASTM F2117 method) found that frozen *game* pucks taken straight from a −30 °C freezer rebounded only 2.8 mm (e about 0.04). Practice pucks rebounded 14.9 mm (e about 0.09) and generic pucks 54 mm (e about 0.17). Bounce rose as the pucks warmed toward −4 °C.
8. **COR falls linearly with speed: confirmed, but the section is 3.8 (Rate Dependence), Fig. 3.17.** Section 3.9 is about quasi-static stiffness. The test used warm PA pucks only, at 55-85 mph. The drop-test point at 24.5 mph is Anderson's own assumption (a 20 ft drop). The conference paper adds that COR "plateaus" at low temperature, and suggests the plateau may also hold for speed. A frozen puck's e may therefore change little with speed.
9. **In-play puck temperatures 12-25 °F: confirmed.** Thesis section 3.7 reports measurements at two rinks on four occasions.
10. **Kapsalis dasher-board patent: confirmed. It is a design goal with no test data.** It says a puck should rebound "at at least about 30-40% of its impact velocity", against "less than 10%" without the structure. Claim 13 says "at least 30%". It was filed on 31 May 2012 and published on 14 Feb 2013.
11. **NHL.com (Predators): confirmed.** Nigel Schnarr, senior director of ice operations, 3 Sep 2024. He targets a "22-degree, 22-and-a-half degree surface temp" at puck drop; Fahrenheit is clear from the context. About 19 °F before resurfacing is "a little brittle", and at 24-25 °F players feel they are "sinking into the ice". On hot, humid days sticky snow makes a long pass "start bouncing", and bouncing pucks are "the main issue".
12. **Drag constant k ≈ 0.0043 per m: confirmed as an estimate, with a caveat.** The arithmetic checks: 0.5 x 1.27 x 0.6 x 19.35e-4 / 0.170 = 0.00434, and Cd 0.45-0.8 gives 0.0033-0.0058. The EES page gives Cd 0.7251 at L/D 2, Re 5x10⁴, and cites APEX-299 with garbled author names. DTIC lists the authors as Heddleson, Brown & Cliffe (GE, April 1957), as the notes say. Cd 0.6 at L/D about 0.67 is the researcher's extrapolation. It goes the right way, but no source I read gives values below L/D 2. I found no measured drag coefficient for a puck, and Böhm et al. are still unread. Caveat on section 2.1: at 40 m/s, Re is 2.3x10⁵, close to where a circular cylinder's drag crisis starts. The air separates from the puck's rounded, knurled edge, not from a sharp corner. Cd may therefore fall at slap-shot speeds, so "roughly constant Cd" is not established.
13. **Allain (227 m, implying k ≈ 0.0055): confirmed.** Physics World, 9 April 2020: mu "about 0.1", 160 km/h, "just over 1000 m" without air, and "227 m" for a 170 g puck with air. The article gives no Cd or area. Solving for k gives 0.00548 per m (Cd about 0.80 on D·H with ρ 1.2), as claimed.
14. **Crossover at about 14 m/s: confirmed.** √(0.085·9.81/k) = 13.9 m/s, or 12.0-15.9 m/s for k from 0.0058 to 0.0033.
15. **Slide distances (15.0/14.1, 60.0/48.4, 240/130, 959/259 m): confirmed.** Every cell of table 3.1 reproduces. The s(t) closed form matches the numerical integration to 0.1 mm.
16. **15 m pass at 10 m/s (8.66 vs 8.03 m/s; 1.61 vs 1.67 s): confirmed.** The rest of table 3.2 matches too.
17. **Minimum launch speed to the end boards (7.1 vs 7.6 m/s): confirmed.** I get 7.13 vs 7.63 m/s on the 61 m rink, 6.19 / 6.51 on the 46 m rink, and 6.73 / 7.14 for icing. The dump-in table and the rim table in 3.3 also reproduce exactly (6.9 / 4.1 / 1.6, 11.4 / 8.2 / 5.7, 15.3 / 11.5 / 8.5). `zone.py` has the 85 ft width and the 28 ft corners.
18. **Spin-up along the boards: corrected in part.** The result that the puck rolls once it keeps 2/3 of its speed (and 2/3 of its energy) is right: for I = ½ m r², the slip falls 3 times as fast as the forward speed. **The angle is wrong.** With wall friction alone, rolling starts after θ = ln(1.5)/mu_b. That is **116° for mu_b 0.2 and 77° for 0.3**. The quoted 60-95° needs mu_b of about 0.25-0.4. With ice friction and drag at 20 m/s it is 100° and 74°. So with mu_b 0.2-0.25 the puck is still slipping in the second corner, and "loses about 1/3 in the first corner" holds only for mu_b ≳ 0.26. The conclusion survives. I ran a spin-up model of a 20 m/s dump with drag (slipping until it rolls, then no loss to the wall; ice torque on the spin ignored). It comes out of the far corner at 8.0 m/s for mu_b 0.2 and 7.4 m/s for 0.3, against 8.2 m/s for the current no-spin 0.12.
19. **Spin and slide stop together (Voyenli & Eriksen): confirmed.** AJP 53(12), 1149 (Dec 1985), property (e): "The translation and the rotation come to a simultaneous stop, regardless of the initial velocities". The paper adds that the coupling increases the stopping times for both. An independent source agrees: Farkas, Bartels, Unger & Wolf, *Phys. Rev. Lett.* 90, 248302 (2003) ([arXiv physics/0210024](https://arxiv.org/abs/physics/0210024)), say a disk "always stops its sliding and spinning motion at the same moment". Their sliding friction force tends to zero when spin dominates, so the reading in 1.2 (less than mu·m·g while the puck spins fast) is right.
20. **Contact pressure about 370 Pa: confirmed (1.668 N over 45.6 cm² = 366 Pa). The argument built on it is weaker than stated.** (a) The heat-flux ratio to a skate is about 10^3, not 10^4, because a skate's mu (about 0.005-0.01) is a tenth of the puck's. (b) Frictional heating depends on the real contact at the asperities, not on the nominal pressure. (c) A tyre-rubber-on-ice study at −5 °C ([KAKEN 06650168 summary](https://kaken.nii.ac.jp/grant/KAKENHI-PROJECT-06650168)) found mu roughly constant at 1-10 cm/s but falling above about 20 cm/s. Those pressures were far higher than a puck's. (d) The only puck-on-ice data (item 1) show mu falling as speed rises. So Coulomb friction is a reasonable simplest model, chosen because there is no data to fit anything better. The physics does not establish it.

Other spot checks: "70-100 mph" for elite slap shots is in thesis section 3.1 (the conference paper says 70-110). Thesis section 1 gives the puck as 5.5-6 oz. Posts and the crossbar do borrow `board_bounce` (`puck.py` lines 238-239). The AI's 2 s path error is **1.7 m at 15 m/s and 2.9 m at 20 m/s**, not 1.7-2.8 m.

### What changes in the recommendations

- `ice_mu` 0.085 as the code default: **stands.** Jon tuned 0.085 by feel with no drag in the model. With drag added, hard passes slow down more, so check the feel again; he may end up a little lower (about 0.075-0.08), which is still inside the band.
- `air_k` 0.0043: **stands, as an estimate.** If a drag crisis sets in at slap-shot speeds, the low end of the range (0.0033) is somewhat more likely there. Make it a tunable setting.
- Coulomb (no speed dependence): **stands as a modelling choice, but the reason changes.** Drop "the physics rules it out" (see item 20). Measuring at the rink (open question 1) is how to settle it. Fit mu(v) as well as k.
- `board_bounce` 0.30 and posts 0.30: **stand.** The pucks tested were brands used in recreational play, not certified game pucks. Frozen e is about 0.26 off a rigid plate and seems to change little with speed, so 0.30 is fine.
- `BOARD_MU` 0.12: **stands, and is better supported than before** (8.2 vs 7.4-8.0 m/s out of the far corner). Correct the 60-95° detail in 4.2.
- `ice_bounce`: **lean toward 0.2.** WPI's drop tests of frozen pucks (e about 0.04-0.17) sit at or below the low end of Haché's 0.12-0.27.
- `net_bounce` and `puck_mass`: **stand.**
- Analytic predictions with the drag closed forms: **stand.** The size of the error is 1.7-2.9 m.
