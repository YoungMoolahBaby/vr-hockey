# Hockey physics feel: the change list

*2026-11-09. What to change next so the puck, the skating and the turning feel like hockey. No code was changed to write this.*

**Sources:**
- The four research notes and their fact-checks in [`research_notes/Hockey physics feel/`](../research_notes/Hockey%20physics%20feel/): puck on ice, skating kinematics, VR skating locomotion and comfort, and stick and puck contact.
- The code in `prototype/` as it stands today (the uncommitted working tree, including `rig.py` and `game.py`).
- Two checks run for this report (see the appendices): the boards and air drag in the compiled engine, and Jon's own skating, measured from his session recordings.

Only claims the fact-checkers confirmed are used as evidence. Claims they marked unsupported appear only as labelled estimates, or are left out (see [What was dropped or corrected](#what-was-dropped-or-corrected)).

## The short version

**The puck.** Jon's ice friction of 0.085 is right, so make it the code default. Two things are wrong:
- **No air drag.** Hard passes, dump-ins and shots keep too much speed.
- **The boards are almost twice too lively.** They use 0.55, against 0.26 measured for a frozen puck.

The blade's "pop" and the low-speed bounce fade change nothing measurable in this model. Set pop to the honest 0.30, remove the fade, and stop tuning them.

**The skating.** Keep 3 m/s for now. The speed is not what makes it feel unlike hockey; the dynamics are:
- every start and every release begins at 20 m/s² (2 g);
- letting go stops you dead in 0.45 m;
- reversing begins at 40 m/s²;
- a glance re-aims your path at up to 28 m/s²;
- you strafe as fast as you skate forward.

The fix is to replace the exponential easing in `rig.Drive` with momentum and hockey limits:
- push at 6 m/s²;
- glide when you let go;
- a hockey stop when you pull the stick back against your motion;
- a path that cannot turn harder than 6 m/s² of sideways acceleration;
- backward and sideways top speeds of 0.8 and 0.5 times forward.

Give the AI skaters the same limits.

**The skating dynamics may also be what made him sick.** I measured how often Jon's view accelerated past 6 and 10 m/s²:

| Sessions | Above 6 m/s² | Above 10 m/s² |
|---|---|---|
| 3v3 games at 4 m/s | 14-18% of the session | 8-10% |
| First 3v3, at 6 m/s | 32% | 25% |
| Free skates at 3 m/s | 4-6% | 1-2% |
| Head alone, no locomotion | 0.1% | 0.1% |

None of the 3v3 games had the vignette. The proposed limits keep every acceleration at or below about 8 m/s², and only a deliberate stop reaches that. This is a hypothesis to test, not a finding: the logs do not say which session made him sick.

## Ranked changes

1 = do first. Changes 1-4 carry no comfort risk and can ship together. Changes 5-9 are the new skating model; test them one at a time in that order.

| # | Area | Change | Now → proposed | Confidence | Comfort risk |
|---|---|---|---|---|---|
| 1 | boards | Board, glass and post restitution | `board_bounce` 0.55 → **0.30** | high | none |
| 2 | puck | Air drag on the puck; `ice_mu` default | none → **k = 0.0043 per m** (new `air_k`); default 0.05 → **0.085** | medium | none |
| 3 | ai | Puck-path predictions that include drag | Coulomb only → closed forms with drag (`threes._path`, `retrieval.rim_launch`, `powerplay`) | high (needed with 2) | none |
| 4 | comfort | Log the rig's motion and a 0-10 discomfort rating | not logged → per-frame rig log plus a rating every 4 min | high | none |
| 5 | skating | Bounded push | exponential τ 0.15 s (20 m/s² onset) → **6 m/s²** with a 0.1 s ease; backward 3 m/s² | medium | low |
| 6 | stopping | Hockey stop: stick pulled more than 120° against the motion | none (pulling back reverses at 40 m/s²) → **8 m/s²** (6 as the gentler option) | medium | low |
| 7 | stopping | Glide on release (a "glide" setting) | release stops you (20 m/s² onset) → coast at **1.5 m/s²**, stepped down to 1.0, then 0.5 | low | medium |
| 8 | turning | Path-turn limit; yaw capped at speed | none; 150°/s at any speed → **A_lat 6 m/s²**; yaw = min(150°/s, 6/v rad/s) | low | low |
| 9 | skating | Backward and sideways top speeds | 1.0 / 1.0 → **0.8 / 0.5** × forward | medium | low |
| 10 | blade | Remove the low-speed bounce fade; pop to the honest value | `soft_hands` 3.0 → **0**; `blade_pop` 0.15 → **0.30** | high | none |
| 11 | ai | AI skaters on Jon's model | ACCEL 5 m/s² in every direction, idle ×(1 − 4dt) → push 6, stop 8, lateral 6, idle glide 1.5 | medium | low |
| 12 | puck | Ice bounce | `ice_bounce` 0.25 → **0.20** | medium | none |
| 13 | blade | Replace the "blade pop" setting with "hands" (`Flex.damping`) | pop setting (a placebo) → damping setting, default 0.60 | medium | none |
| 14 | skating | Top speed A/B, after 5-9 | 3.0 → try **3.5**, then 4.0; `MOVE_MS` default 4.0 → 3.0 | medium | high |
| 15 | turning | Body heading instead of head heading (a setting) | head yaw → rig yaw plus a lazy follow of the head | low | medium |
| 16 | stopping | Index-trigger stop, as a second stop input | unbound → analog trigger, 8 m/s² at full press | low | low |
| 17 | skating | Skate and stop sounds; never any camera bob | none → a stride scrape, a glide hiss, a stop spray | low | none |
| 18 | ai | Carrier speed | `CARRY` 0.85 → **0.92** | low | none |
| 19 | puck | Puck spin about the vertical axis, then a higher blade grip | no spin → one spin value (I = ½mR²); `blade_grip` 0.35 → 0.45 | medium | none |

Keep as they are: `ice_mu` 0.085 (Jon's value), `zone.BOARD_MU` 0.12, `net_bounce` 0.08, `puck_mass` 0.170, `BLADE_MASS` 0.15 (do not go above about 0.3 kg), `Flex.damping` 0.60, `TURN_TAU` 0.08, the vignette at 0.7, `threes.PASS_MS` 10 and `SHOT_MS` 22.

---

## The changes

### 1. Boards: `board_bounce` 0.55 → 0.30

- **Now.** `Params.board_bounce = 0.55` sets the boards in all three rinks: `physics_core.rink_sandbox`, and `_zone_end` through `_bounce` for the zone and the arena. The posts and the crossbar borrow it: `puck.Puck._rink` lines 238-239 and 249, `rink_sandbox`, and the front edge of the net in `_zone_end`.
- **Proposed.** 0.30 for boards, glass and posts (range 0.25-0.40). No new parameter is needed while posts and boards share one value. Split out a `post_bounce` only if they ever need different values.
- **Evidence (confirmed).**
  - Frozen pucks (25 °F) fired edge-on into a rigid plate at 55 mph rebound at e = 0.267 and 0.256 (Anderson 2008, WSU MS thesis, §3.7). Warm pucks rebound at 0.35-0.38 (§3.6).
  - In-play puck temperatures were 12-25 °F (§3.7).
  - A dasher-board patent sets "at least 30-40%" rebound as its design goal (Kapsalis, US 2013/0040745; no test data).
  - The current 0.55 matches a warm puck dropped at low speed.
- **Flags.** The tested pucks were recreational brands, not certified game pucks. There is no data for glass.
- **What it does in the engine** (Appendix A).
  - A puck hit straight into the end boards at 10 m/s now rebounds at 5.4 m/s and slides 17.6 m back up the ice. With 0.30 plus drag (change 2) it rebounds at 2.9 m/s and slides back 5.1 m.
  - At 20 m/s it now runs back the whole length of the 46 m rink. With the change it stops after about 19 m.
  - Rims round the corners do not change. In this model rim speed is set by `BOARD_MU`, not by the bounce.
  - Pucks that hit the boards at an angle keep slightly more speed along them, because `_bounce` scales the friction impulse by (1 + e).
- **Keep `zone.BOARD_MU` at 0.12.** It is an effective value for a puck with no spin. A real puck spins up and rolls along the boards. A spin-up model of a 20 m/s dump-in comes out of the far corner at 7.4-8.0 m/s, against 8.2 for no-spin 0.12 (confirmed). A "true" rubber-on-plastic friction of about 0.2 without spin would kill rims.
- **Code.** Change the default of `puck.Params.board_bounce`. To A/B it in the headset, add a temporary "boards" entry to `sandbox.SETTINGS` and wire it in `Tuning.apply`. The tests pass 0.55 explicitly, so they don't break. The retrieval drill's `corner_keep(board_bounce)` cache recomputes on its own.
- **Confidence:** high. **Comfort risk:** none.

### 2. Air drag on the puck, and the `ice_mu` default

- **Now.** Friction is Coulomb only. `Puck._integrate` and `physics_core.integrate` use dec = `ice_mu`·G·h on the ice; in the air there is only gravity.
- **Proposed.**
  - Add a deceleration k·v² with k = `Params.air_k` = **0.0043 per m** (range 0.0033-0.0058). It applies on the ice and in the air:
    - on the ice: `dec = (ice_mu*G + air_k*s*s)*h`;
    - in the air: `v -= air_k*|v|*v*h`.
  - Make the `ice_mu` default 0.085, Jon's value. Its feel band is 0.07-0.10.
- **Evidence.**
  - k = ½ρCdA/m with Cd ≈ 0.6 on the puck's 19.4 cm² side profile, ρ 1.27 and m 0.170. The arithmetic is confirmed (0.00434).
  - Allain's independent estimate (*Physics World*, 2020) implies 0.0055 (confirmed).
  - Drag equals ice friction at about 14 m/s (12-16 m/s across the range). It is about twice the ice friction at Jon's 18-21 m/s shots, and 8 times at 40 m/s.
  - For `ice_mu`, the only on-ice measurement is 0.066-0.118 (mean about 0.09) at 0.8-2.1 m/s on fresh ice (Westminster student video study; confirmed). Quoted values: 0.05-0.20 (a patent) and "< 0.15" (Haché, quoted by WPI); both confirmed as quoted.
- **What it changes** (fact-checked tables, plus Appendix A):

  | Case | Now | With drag |
  |---|---|---|
  | Stickhandling and soft passes (< 5 m/s) | — | under 5% change |
  | 15 m pass at 10 m/s: arrival speed, travel time | 8.7 m/s, 1.61 s | 8.0 m/s, 1.67 s |
  | 15 m pass at 15 m/s: arrival speed | 14.1 m/s | 13.2 m/s |
  | 20 m/s shot from the point (18 m): speed at the net | 19.2 m/s | 17.7 m/s |
  | 46 m rink, from the red line at 15 m/s: speed at the end boards | 13.7 m/s | 12.2 m/s |
  | Rim along the boards at 20 m/s: speed out of the far corner (engine) | 11.6 m/s | 8.8 m/s |

- **Flags.**
  - The value of k is an estimate, not a measurement. No measured Cd for a puck was found; the one wind-tunnel paper (Böhm 2007) is paywalled.
  - At slap-shot speeds Cd may fall (a drag crisis near Re 2.3×10⁵), so the low end of the range (0.0033) is a little more likely for hard shots. Make `air_k` a setting.
  - Keeping friction Coulomb is a modelling choice, not something the physics establishes. The "10⁴ times less pressure than a skate" argument was overstated (the heat-flux ratio is about 10³), and the only puck data show mu *falling* as speed rises.
  - Jon tuned 0.085 with no drag in the model, so re-check it once drag is in. He may settle at 0.075-0.08.
- **Code.**
  - Add `Params.air_k: float = 0.0043`, and use it in both branches of `Puck._integrate` and `physics_core.integrate`.
  - The `prm` array grows to 13 values. Add `air_k` at index 12 in `puck.Sim._step_fast` *and* in `physics_core.warm()`. numba does not check bounds, so a 12-value `prm` would silently read garbage; `tests/test_physics_core.py` line 186 already warns about this.
  - Leave the net's 0.97 damping as it is.
  - Add a sandbox setting "air drag" (0-0.008, step 0.001) for the A/B.
  - `retrieval.corner_keep` should simulate with `air_k=0`, so that it measures board loss only (see change 3).
  - Stability: k·v·h ≈ 5×10⁻⁵ per substep, so the step is far from any stability limit.
- **Confidence:** medium for the value; high that drag matters above about 10 m/s. **Comfort risk:** none.

### 3. Puck-path predictions with drag (ships with 2)

- **Now.** Three predictions assume Coulomb friction alone:
  - `threes._path` predicts a loose puck's 2 s path;
  - `retrieval.rim_launch` builds each leg from a = `ice_mu`·G, and the corner from `corner_keep`;
  - `powerplay.make_scenario` computes `t_arr` the same way.
- **Proposed.** Use the closed forms, with a = `ice_mu`·G and k = `air_k`. As k → 0 they fall back to the Coulomb forms:
  - position: s(t) = ln(cos(φ0 − √(ak)·t) / cos φ0) / k, with φ0 = atan(v0·√(k/a)). It holds until t_stop = φ0/√(ak), after which s = s_stop = ln(1 + k·v0²/a)/(2k).
  - time to cover x: t = (φ0 − acos(cos φ0 · e^(kx))) / √(ak);
  - speed after x: v² = (v0² + a/k)·e^(−2kx) − a/k;
  - launch speed to arrive at v1 after x: v0² = (v1² + a/k)·e^(2kx) − a/k. Use this for each leg of `rim_launch`, and include the corner arc in the drag.
- **Evidence.** The closed forms match a numerical integration to 0.1 mm (confirmed). Without them, the AI's 2 s path for a hard puck comes out 1.7 m too long at 15 m/s and 2.9 m too long at 20 m/s (corrected from 1.7-2.8).
- **Code.** `threes.Game._path`; `retrieval.rim_launch` and `corner_keep`; `powerplay.make_scenario` (line ~255). Add a unit test that compares each closed form with an engine slide.
- **Confidence:** high. **Comfort risk:** none.

### 4. Log the rig's motion and a discomfort rating (before changes 5-9)

- **Now.** The rig's motion is not logged; I had to rebuild it from the head's world pose (Appendix B). Nothing records how he feels.
- **Proposed.**
  - **Per frame**, log the stick inputs, `Drive.vel`, `Drive.omega` and the mode (push, coast, stop), in `events.jsonl` or a small `rig.csv`.
  - **In `meta.json`**, add a session summary: time moving, acceleration events above 2 m/s² per minute, time above 6 m/s², mean and peak turn rate, and time with the vignette above 0.5.
  - **Every 4 minutes**, a voice prompt ("comfort?") that Jon answers 0-10 with the left stick, as in the tuning menu, logged as an event. Stop a test at 4 or more.
- **Evidence (confirmed).**
  - Individual thresholds vary widely but correlate within one person, so the authors recommend tuning per person (Terenzi & Zaal 2020, NASA).
  - A rating of 4 out of 10 is where nausea "started becoming more notable" (Farmani & Teather 2020).
- **Code.** `sandbox.py` main loop, right after `drive.update` (line ~867), using `log.event`; the meta summaries in `game.py` and `sandbox.py`.
- **Confidence:** high. **Comfort risk:** none; it is how the other changes get judged.

### The new skating model (changes 5-9) in one sketch

`rig.Drive.update(move_xy, turn_x, head_R, dt)` keeps its signature and its output, `(vel, omega)` handed to `Rig.drive`. The 1 kHz physics is untouched. The new constants go in `rig.py`; make each one a sandbox setting while it is being A/B tested.

```python
A_PUSH = 6.0        # m/s^2 forward push ("push"; 4 = gentler)
PUSH_BACK = 0.5     # backward push = 0.5 x A_PUSH
EASE = 0.1          # s: the last of the speed eases in
A_STOP = 8.0        # m/s^2 hockey stop ("stop"; 6 = gentler)
A_COAST = 1.5       # m/s^2 on release or easing off ("glide"; real ice ~0.1-0.3; 20 ~ today)
A_LAT = 6.0         # m/s^2: the path bends at most A_LAT/|v| rad/s ("edge"; A/B 8)
BACK, SIDE = 0.8, 0.5   # top speed backward / sideways, x forward

# each frame:
# 1. want: the stick direction in the frame of fwd (the head, as now), magnitude
#    = move_ms * _shape(m) * ellipse(dir), where ellipse = 1 / sqrt((c/F)^2 + (s/SIDE)^2),
#    with F = 1 forward and BACK backward, c and s the cosine and sine of the direction from forward
# 2. yaw: want_om capped at min(turn_deg_s, A_LAT/|vel|) when |vel| > 0.5; ease with TURN_TAU as now;
#    rotate vel by omega*dt (you carve with your body, so view and path stay together)
# 3. |vel| < 0.5: step vel toward want, |dv| <= A_PUSH*dt (pivot freely when slow)
#    else, with u = vel/|vel|:
#    - angle(want, u) > 120 deg  -> STOP: speed -= A_STOP*dt; below 0.3 m/s, push toward want
#    - otherwise turn u toward want's direction by at most (A_LAT/|vel|)*dt
#      speed up toward |want|: a = min(A_PUSH or A_PUSH*PUSH_BACK, (|want| - speed)/EASE)
#      speed above |want| (released or eased off): speed -= A_COAST*dt, never below |want|
```

Every acceleration is then bounded: about 6 pushing, 8 stopping and 6 sideways, or about 8.5 m/s² when pushing and turning at once. Today's peaks are 20, 28 and 40 m/s².

`tests/test_rig.py` needs new expectations:
- `test_drive_directions` expects a strafe at the full `MOVE_MS`; it becomes 0.5 ×. Its check that the slide has stopped after 200 frames with the stick released depends on the glide value, and on the speed the strafe left it at.
- `test_drive_eases_in` still holds: 6 m/s² for one frame is far under full speed.

### 5. Bounded push: 6 m/s² with a 0.1 s ease

- **Now.** `vel += (want − vel)·(1 − e^(−dt/0.15))`: 20 m/s² at the first instant, 95% of the speed in 0.45 s. The same easing re-aims the velocity whenever the direction changes.
- **Proposed.**
  - Speed rises at up to 6 m/s², and the last part eases in with τ 0.1 s. From standstill to 95% of 3 m/s takes about 0.55 s (now 0.45 s), with a peak of 6 m/s² instead of 20.
  - Pushing backward is half as hard, 3 m/s².
  - A "push" setting (4-8). 4 is the gentler option: about 0.75 s to 95%.
- **Evidence.**
  - A fit to measured 30 m splits puts a recreational adult at 3 m/s after about 0.56 s, a mean of about 5.4 m/s² (Buckeridge 2015; the source is confirmed and the fit is the researcher's).
  - Elite players' mean acceleration over the first 6.1 m was 3.5-4.1 m/s², though their own kinematics imply 4.4-5.2 (Greer & Dillman 1984; confirmed).
  - Peak game acceleration was 4.06 m/s² in 20 Hz tracking, which is probably smoothed (Gamble 2022; confirmed).
  - Backward C-cut starts average about 2.4 m/s over the first 5 m (Psilander 2025; confirmed), about half of forward.
  - The fact-checker raised the skating note's 4 m/s² to 6 for these reasons. The comfort note's 4 is kept as the gentler option.
- **Flags.**
  - There is no comfort evidence for any particular ramp shape. The one controlled test found no difference between speed profiles (Widdowson 2021, abstract only).
  - Even 4-6 m/s² is 6-9 times NASA's mean onset threshold for forward acceleration (0.70 m/s²).
- **Code.** `rig.Drive.update`, the along-track branch of the sketch.
- **Confidence:** medium. That 20 m/s² is wrong is certain; that 6 is the right value is less so. **Comfort risk:** low. The peak falls from 20 to 6 m/s², and the time to reach speed barely changes.

### 6. Hockey stop: pull the stick back, 8 m/s²

- **Now.** There is no stop control. Letting go eases you to a stop. Pulling the stick back means "skate backward" at full speed through the same easing. At 3 m/s that starts at (3 + 3)/0.15 = **40 m/s²**, and backward is as fast as forward.
- **Proposed.**
  - When the left stick points more than 120° away from your motion (and you are moving faster than 0.3 m/s), brake at 8 m/s² until below 0.3 m/s, then push the new way. From 3 m/s that takes 0.375 s and 0.56 m.
  - A "stop" setting (4-10). 6 is the gentler option: 0.5 s and 0.75 m.
  - Hold the vignette closed through the stop: open it when the stop ends, not as the speed falls.
  - Add an ice-spray sound (change 17).
- **Evidence.**
  - Junior B players stopped from 8.35-8.61 m/s in 0.81-0.84 s, over 4.1-4.4 m, a mean of 8-10.4 m/s² (Winchester 2007, Brock thesis, Table 3; confirmed after a correction).
  - The peak game deceleration was −5.99 m/s², from 20 Hz tracking that probably understates peaks (Gamble 2022; confirmed).
  - Active control is less sickening than passive motion (Stanney & Hash 1998; confirmed).
- **Flags.** The skating note's original 4.9-5.9 m/s² rested on an assumed approach speed and was corrected; this report uses 8.
- **Code.** `Drive.update`, the stop branch. The vignette's `tunnel` lives in `sandbox.py` (line ~870); add a "stopping" hold there.
- **Confidence:** medium. **Comfort risk:** low. The stop is deliberate and short, and gentler than today's release (20 m/s² onset) and reversal (40).

### 7. Glide on release, starting at 1.5 m/s²

- **Now.** Letting go stops you: 20 m/s² at first, 0.45 m in all.
- **Proposed.**
  - With the stick in the deadzone, or eased off part-way, you slow at a constant rate set by a "glide" setting (range 0.1-20; 20 is about today's behaviour).
  - Start at **1.5 m/s²**: from 3 m/s you coast for 2.0 s and 3.0 m.
  - Over later sessions, step down to 1.0 (3 s, 4.5 m) and then 0.5 (6 s, 9 m) as Jon adapts.
- **Evidence.**
  - Hockey blades slide with friction μ = 0.0071 (Federolf 2008, a sled test; confirmed).
  - Players coast only about 10% of the time in play; they brake actively (Dillman 1984; confirmed).
  - No study has tested a VR glide.
- **Flags.**
  - The honest coasting rate, about 0.1 m/s² at 3 m/s (a 50 m glide), is a physics estimate with an assumed drag area. The fact-checker marked it unsupported as a measurement.
  - So the proposed value is a design choice.
  - The comfort argument for a glide is inference, not evidence. Bonato 2008 tested reversals of direction, not stopping and starting, and So 2001 held speed constant. The argument is that steady motion provokes least and that start-stop cycles are worse.
- **Comfort risk:** medium.
  - Motion carries on after he lets go, so it is partly passive.
  - He spends more time moving.
  - His habit is release-to-stop, so he will drift at first.
  - His rig is not kept inside the boards (only the puck and the AI are), so a glide can carry him through them. Add a soft stop at the boards: remove the velocity into them over about 0.2 s (Meta's guidance is to slow down before stopping).
- **Code.** `Drive.update`, the coast branch. `A_COAST` plus a "glide" setting. The boards check uses `arena.keep_on_ice`-style geometry on the head position in `game.py`.
- **Confidence:** low. The value is a design choice, and tolerance is the main open question.

### 8. Path-turn limit (6 m/s²) and a yaw cap at speed

- **Now.**
  - The velocity re-aims toward where you look, through the τ 0.15 s easing. A 90° glance at 3 m/s starts at 28 m/s².
  - The right stick turns 150°/s at any speed. At full stick and 3 m/s that needs 7.3-7.9 m/s² of sideways acceleration.
- **Proposed.**
  - The path's direction turns at most A_lat/|v| rad/s, with A_lat = 6 m/s². There is no limit below 0.5 m/s, so you can still pivot on the spot.
  - The yaw is capped at min(turn setting, A_lat/|v|). That is unchanged below 2.3 m/s and 115°/s at 3 m/s.
  - When the right stick turns you, the velocity turns with you (you carve), so the view and the path stay together.
- **Evidence.**
  - Physics: lateral acceleration = v·ω.
  - Elite long-track speed skaters held 5.3-6.3 m/s² on curves at 26-32° of lean (Kimura & Yokozawa 2024; confirmed).
  - Rotation is the most provoking axis (Terenzi & Zaal; confirmed).
  - Multidimensional visual motion makes sickness worse (Allison & Palmisano 2025, meta-analysis of 97 studies; confirmed).
  - In Jon's own logs, the path bent at more than 6 m/s² for 8-13% of his moving time at 3 m/s, 35% at 4 m/s and 50% at 6 m/s (Appendix B).
- **Flags.**
  - The value is low-confidence. It comes from speed skating at 12 m/s, applied to hockey at 3 m/s.
  - The hockey figures (4-6 m/s² sustained, 8-10 m/s² briefly) are estimates the fact-checker marked unsupported.
  - A skidding blade takes 0.8-1 g (Winchester), so 8 may be fairer; A/B 6 against 8. At 3 m/s an A_lat of 8 leaves the yaw at 150°/s (the cap is 153°/s), so the yaw cap only bites with A_lat below about 7.8.
- **Code.** In `Drive.update`, cap `want_om`, rotate `self.vel` by `omega*dt`, and add the across-track limit.
- **Confidence:** low. **Comfort risk:** low. It lowers sideways acceleration and yaw at speed. The path now lags a glance by design, which may feel floaty; change 15 addresses that if it bothers him.

### 9. Backward 0.8 and sideways 0.5 of forward

- **Proposed.** Top speed on an ellipse: forward 1.0, backward 0.8 and sideways 0.5. At 3 m/s that is 2.4 m/s backward and 1.5 m/s sideways.
- **Evidence.**
  - Backward C-cuts reach 82% of forward speed (Marino & Grasse 1993) and 81% (Wu 2015); both confirmed. A U12 study gives 78%.
  - Sideways has no measurement; 0.5 is an estimate.
  - Lateral optic flow is no more comfortable than forward flow (NASA thresholds, not significantly different).
- **Code.** `Drive.update`, the `ellipse()` step of the sketch.
- **Confidence:** high for backward, low for sideways. **Comfort risk:** low.

### 10. Remove the bounce fade; `blade_pop` 0.30

- **Now.**
  - `Params.soft_hands = 3.0`: below a 3 m/s impact the bounce fades, to nothing by 0.5 m/s.
  - `blade_pop` is 0.15 (Jon's value; the default is 0.20).
  - Naming: when Jon says "soft hands off", he means `Params.magnet` (now 0). The fade is a different mechanism, and it is still on.
- **Proposed.** Set `soft_hands` to 0, and delete the fade from `Puck._collide_blade` and `physics_core.collide_blade`. Set `blade_pop` to 0.30, constant.
- **Evidence.**
  - In this engine, a puck coming off a still blade (0.15 kg, on a spring damped at 0.6) rebounds at 0.13-0.17 of its speed for any pop from 0.15 to 0.50, fade on or off. Shot speeds change by 1% or less. The re-run is confirmed.
  - Rubber bounces *more* at low speed, not less: warm pucks measured 0.39 at 55 mph and 0.34 at 85 mph against a rigid plate, and about 0.50 in a drop test (WSU; confirmed). So the fade is backwards.
  - A frozen puck at 55 mph: 0.27 (WSU; confirmed).
- **Flags.** The low-speed anchor of about 0.35 for a frozen puck rests on a newspaper quote of a test Haché proposed. So use a constant 0.30, with no speed curve.
- **Why bother, if it changes nothing now.**
  - The fade would become an assist if the blade got heavier: with a rigid blade it cuts a 1 m/s bounce from 0.24 to 0.03.
  - The pop slider invites tuning a knob that does nothing.
  - Do not raise `BLADE_MASS` above about 0.3 kg without checking: the response to pop turns erratic at 0.4-0.6 kg (the fact-checker's extra run).
- **Code.**
  - Change the `Params` defaults, and the "pop" value in `sandbox_settings.json`.
  - Either keep `prm[6]` and pass 0, or drop the field and renumber `prm`, updating `warm()` to match.
- **Confidence:** high. **Comfort risk:** none.

### 11. AI skaters on Jon's model

- **Now.** In `threes._skate`:
  - the velocity change toward the target is capped at `ACCEL·dt` = 5 m/s² in every direction, so AI turns are already limited to 5 m/s²;
  - the arrival speed follows √(2·ACCEL·dist);
  - idle skaters slow by `v *= 1 − 4dt`, about 11 m/s² at 2.85 m/s;
  - `vmax` = min(5.8, 0.95 × Jon's top) × (0.85 + 0.15·level). With Jon at 3 m/s that is 2.85 m/s at level 1.
- **Proposed.**
  - Split the velocity change into the parts along and across the skater's motion. Speeding up is capped at A_PUSH (6), slowing at A_STOP (8) and the sideways part at A_LAT (6). Import the constants from `rig.py`.
  - Base the arrival profile on about 0.7 × A_STOP.
  - Idle skaters glide at 1.5 m/s², or stop at A_STOP when play stops.
  - Keep `YOU_FRAC` at 0.95.
  - `_reach` assumes instant top speed (+0.15 s); add the push time.
- **Evidence.** The same as changes 5, 6 and 8.
- **Flags.**
  - The fact-checker reframed this item. "Lateral 6" lets the AI turn a little *harder* than now (5 m/s²); it is about consistency, not about stopping the AI out-turning Jon.
  - The 0.85-1.05 speed spread by level is a design choice. Buckeridge's 7% and 15% are the gaps between groups, not the spread among recreational players.
  - The AI always skates facing forward. Backward skating for defenders is a separate, larger change.
- **Code.** In `threes.py`, replace `ACCEL` with `A_PUSH`, `A_STOP` and `A_LAT`, and update `_skate` and `_reach`.
- **Confidence:** medium. **Comfort risk:** low. The motion in view becomes consistent and readable.

### 12. `ice_bounce` 0.25 → 0.20

- **Evidence.** Haché's frozen-puck drop tests: 0.12-0.27 (as quoted by Anderson; secondary). WPI drop tests of frozen pucks: 0.04-0.17 (confirmed by the fact-checker from the MQP).
- **Effect.** It affects only airborne pucks landing on the ice.
- **Code.** The `Params.ice_bounce` default.
- **Confidence:** medium. **Comfort risk:** none.

### 13. Replace the "blade pop" setting with "hands" (`Flex.damping`)

- **Why.** The flex damping, not pop, sets how far a puck bounces off a held blade: damping 0.6 gives 0.17 v, 0.3 gives 0.27 v, and 0.1 gives 0.38 v (re-run confirmed). Physically it stands for grip firmness. A HockeyShot coaching article says a "death grip" makes the puck "bounce off a rigid stick like it does the boards" (quote confirmed).
- **No catching assist needed.** The model already rewards a real give: moving the blade back at 0.1 v for 150 ms cuts the bounce from 0.17 v to 0.03-0.04 v (confirmed).
- **Code.**
  - In `sandbox.SETTINGS`, replace `("pop", "blade pop", …)` with `("hands", "hands", 0.05, 0.1, 1.0, "{:.2f}")`.
  - `Tuning.apply` writes to `Params`, but damping lives on `Flex`. So set `pl.sim.flex.damping = values["hands"]` in `_refresh` (`sandbox.py` line ~302), just before `set_flex`, which recomputes `c` from it.
- **Confidence:** medium. **Comfort risk:** none.

### 14. Top speed: keep 3.0, then A/B 3.5 and 4.0

- **Proposed.** Change nothing until changes 5-9 are in and comfortable. Then try 3.5 m/s, and 4.0 on another day, in free skate first. Make the `rig.MOVE_MS` default 3.0; it is 4.0 now, and `game.py`'s docstring also says 4.
- **Evidence.**
  - A recreational adult sprints at about 8.1 m/s, averaged over the last 10 m of 30 m (Buckeridge; confirmed).
  - The average speed in play is 3.3-4.2 m/s (Gamble 2022 derivation, Dillman 1984; confirmed).
  - University forwards spend roughly half their time under 3 m/s (derived; 42-59% depending on an assumption).
  - So 3 m/s is the slow half of real play.
  - Sickness rose with speed from 3 to 10 m/s, though of the SSQ subscores only the oculomotor one changed (So 2001; confirmed).
- **What the logs say.**
  - The first 3v3 (11:15) ran at 6.0 m/s for 4 min. The next two (11:20 and 11:34) ran at 4.0 m/s for 9 and 8 min.
  - None of the three had the vignette; the setting did not exist yet.
  - The free skates (13:33 onward) ran at 3.0 m/s with vignette 0.7.
  - So "3 m/s is comfortable, 4 was not" is confounded with the vignette and with game against free skate.
- **Confidence:** medium. **Comfort risk:** high.

### 15. Body heading instead of head heading (a setting, later)

- **Proposed.** A "skate with: head / body" setting.
  - With "body", forward is a heading that the right stick turns (`heading += omega*dt`).
  - The heading follows the head lazily: only when the head stays more than about 35° off it for more than about 1 s, with a time constant of about 1 s. Both numbers are guesses.
  - For a fixed chair, offer pure rig yaw.
- **Evidence.** In Bowman 1997, gaze-directed steering meant you "can't look at object & move another direction", and steering by pointing was faster in a relative-motion task (9.60 against 12.36 s; confirmed). Hockey is played looking at the puck.
- **Comfort risk:** medium. He may use the right stick more, which means more artificial yaw, the most provoking axis. Once change 8 is in, a glance bends the path at only 6 m/s², so try this only if glances still bother him.
- **Code.** In `Drive`, keep `self.heading` and compute `fwd` from it instead of from `head_R`.
- **Confidence:** low.

### 16. Index-trigger stop (only if the pull-back stop isn't enough)

- **Now.** The triggers are unbound. `record.py` binds squeeze, both thumbsticks, A, B, X, Y and the left-stick click.
- **Proposed.** Add an action for `/user/hand/{left,right}/input/trigger/value`. Braking = trigger press × A_STOP.
- **Risk.** He may press it by accident while gripping for a shot. Test which hand works.
- **Confidence:** low. **Comfort risk:** low.

### 17. Skate and stop sounds; never any camera bob

- **Proposed.**
  - Put the stride rhythm in sound, never in the camera: a blade scrape per stride while pushing (about 2-2.5 per second), a soft hiss while gliding, and a spray on a hockey stop.
  - Play them through the existing contact bus and mixer (`audio.py`, `sounds.py`).
- **Evidence.**
  - Vertical camera oscillation at 1.8-7.4 Hz roughly doubled SSQ scores (58.2 against 29.7; Palmisano 2007; confirmed).
  - Junior B sprint starts ran at 2.42-2.52 strides/s; cruising is slower (confirmed).
  - The sound itself is untested for comfort.
- **Confidence:** low. **Comfort risk:** none.

### 18. `CARRY` 0.85 → 0.92

- **Evidence.** Youth players were 4.9% slower over 30 m with the puck (Sports 2020; U12, n = 13). Confirmed, but weak.
- **Confidence:** low. **Comfort risk:** none.

### 19. Puck spin, then `blade_grip` 0.45 (later)

- **Why.** The puck has no spin. Where the blade grips it, the code removes *all* of its sliding speed along the face. A real disc (I = ½mR²) loses only a third and then rolls (arithmetic confirmed). A lower grip partly hides this.
- **Proposed.**
  - Add one spin value about the vertical axis.
  - Then raise `blade_grip` to 0.45: a puck on cloth tape measured 0.43-0.50 (Plesch 2019 preprint, with the puck caged against turning; confirmed).
  - With spin, board friction could also take a physical value (0.2-0.3). Rims barely change: 7.4-8.0 m/s out of the far corner, against 8.2 now.
  - A sliding, spinning puck stops sliding and spinning at the same moment (Voyenli & Eriksen 1985; confirmed).
- **Cost.** It touches the puck state, both integrators, the blade and board contacts, and the tests. Do it after everything above.
- **Confidence:** medium. **Comfort risk:** none.

---

## Headset tests

**Rules:**
- Change one thing per test, and run each condition for 5-8 minutes.
- Use the same course every time.
- Rate discomfort 0-10 every 2 minutes. At 4 or more, stop and end the session.
- Keep sessions to 10-15 minutes while adapting.
- `meta.json` already records the settings.

**The course** (free skate, `game.py --free --empty`): from centre ice to the near blue line; round both faceoff circles in that end; stop at the crease; back up to the top of the circles; shuffle sideways across the slot; then one lap of the rink.

**Session A, the puck** (no comfort risk; done standing still or with gentle skating):
1. **Boards, 0.55 against 0.30.** From the top of the circles, fire 5 hard pucks at the end boards beside the net, then rim 5 round the end. *Real:* the rebound dies around the net front and the hash marks, and doesn't come back to the slot.
2. **Drag, 0 against 0.0043.** 10 hard passes up the boards to the far blue line, 5 dumps from the red line, 2 min of stickhandling. *Real:* hard passes and dumps arrive noticeably slower, and stickhandling feels the same.
3. **With drag on, re-tune `ice_mu`:** 0.075, 0.085 and 0.095, on soft passes and loose pucks. Pick one.
4. **Blind check of the fade and pop.** 2 min of stickhandling with the fade on and pop 0.15, then the fade off and pop 0.30. *Expect:* no difference. If he can tell them apart, note how.
5. **"Hands" 0.45, 0.60 and 0.75**, receiving passes in the power-play drill. *Real:* a firm pass onto a stiff stick kicks off; a give kills it.

**Sessions B-H, the skating** (in this order; move on only when the last one rated under 4):
- **B, push.** Push 6 against today, then push 4 against 6. *Judge:* does the start feel like a skater's first strides, and is it any easier on the stomach?
- **C, stop.** The pull-back stop at 8, then at 6, with release still stopping as today. *Judge:* skate in from the blue line and stop at the crease. Does it feel like a hockey stop?
- **D, glide.** Glide 1.5, with the pull-back stop; on later days 1.0, then 0.5. *Judge:* rating; how often he drifts past where he meant to stop; whether the glide feels like skating or like being carried.
- **E, turning.** A_lat off, 6 and 8. *Judge:* can he still cut tight round the faceoff dot when slow? Does looking at the puck still drag his path?
- **F, backward and sideways.** 0.8 / 0.5 against 1.0 / 1.0. *Judge:* is backing up and side-stepping to line up a shot too slow?
- **G, top speed.** 3.5 against 3.0 in free skate; 4.0 on another day.
- **H, the 3v3.** Only then a 10-minute 3v3, with the AI on the same model (change 11).

**Optional, later:** body heading against head heading (change 15); the trigger stop (change 16).

---

## What was dropped or corrected

These are claims the fact-checkers marked unsupported or corrected, and how this report treats them:

- **"Coulomb friction is what the physics says"** (puck note) was corrected to a modelling choice. The pressure argument was overstated (the heat-flux ratio is about 10³, not 10⁴), and the only puck data show mu falling with speed. Coulomb is kept because nothing better can be fitted yet.
- **Rim spin-up angle**: corrected from 60-95° to 77-116° for board mu 0.3-0.2. The conclusion (keep 0.12) stands.
- **Frozen-puck restitution of 0.12-0.27 from Haché**: per the contact note, those may be bounce *heights*. Nothing here depends on it: board 0.30 rests on WSU's 0.26, and the ice bounce leans to 0.20 on WPI's drop tests.
- **Coasting deceleration of about 0.1 m/s²** for a skater: unsupported as a measurement, because the drag area is assumed. It is used only to say that a real glide is very long; the proposed glide is a design choice.
- **Hockey tight turns at 4-6 m/s² sustained and 8-10 briefly**: unsupported (estimates). A_lat = 6 rests on confirmed speed-skating data, applied to hockey and labelled low confidence.
- **Hockey stop at 4.9-5.9 m/s²**: corrected to 8-10.4 m/s² (Winchester's approach speed is 8.35-8.61 m/s). This report uses 8.
- **Push of 4 m/s²**: the fact-checker raised it to about 6 m/s² with a 0.1 s ease. This report uses 6, with 4 as the gentler option.
- **"4 m/s felt too fast"**: the project record disagrees with itself. `rig.py` says 6 m/s, the README says the AI skated 5.8 "to your 4", and the brief says 4. The logs settle the speeds (6.0 m/s, then 4.0, then 3.0) but not which session made him sick.
- **Recreational adult wrist shot of 17-20 m/s**: unsupported. It is not used for any change. Jon's 18-21 m/s is "plausible" only as a judgement.
- **"NHL average shot about 30 m/s"**: unsourced, and dropped. `SHOT_MS` 22 stays, on recreational slap shots measured in labs (22.3-23.3 m/s).
- **AI "lateral 6 so it can't out-turn Jon"**: reframed. The AI is already capped at 5 m/s² in every direction.
- **The VMAX spread rationale**: corrected. It is a design choice.
- **Kelly's vignette result**: it came from an all-or-nothing restriction applied only during translation, so it doesn't speak directly to Jon's speed-scaled vignette. Fernandes & Feiner 2016 and Teixeira & Palmisano 2021 support the dynamic kind; the vignette stays.
- **Render rate**: 90 Hz alone may not help, because Wang 2023 found the benefit at 120 fps and above. Left out of this list; see the open questions.
- **Blade rebound "15-17%"**: corrected to 0.13-0.17 v. The conclusion (pop is inert) is unchanged.

## Open questions

1. **Which 3v3 made Jon sick, and when in it?** The logs show 6 m/s (4 min), then 4 m/s (9 and 8 min), all without the vignette. Ask him. Then re-try 4 m/s *with* the vignette and the new dynamics before treating 4 m/s as his limit.
2. **Does he tolerate a glide, and at what rate?** No study exists. This is the main skating experiment (session D).
3. **Real puck friction and drag at his rink.** Film a puck from above at 120-240 fps over a taped 5 m scale, at 2, 5, 10 and 15 m/s, on fresh ice and late in a session. Fit mu(v) and k.
4. **Real board, glass and rim behaviour**, for example how fast a rim comes out of the far corner. A phone video would test both 0.30 and the 2/3 spin-up rule.
5. **Hockey turn kinematics.** Jon could film himself at the rink, using the faceoff circles (4.57 m radius) as scale. That would settle A_lat at 6 against 8.
6. **His seat.** Swivel chair, fixed chair, or standing in a small space? That decides between body heading and pure rig yaw (change 15).
7. **Trigger ergonomics.** Can he press an index trigger while gripping the stick, without braking during shots?
8. **120 Hz rendering** as a separate comfort test, if the Python frame loop can hold it.
9. **Late-period ice** (mu rising from about 0.075 to 0.10, and bouncing pucks): a design option with no data behind its size.
10. **A puck's rebound off a hand-held stick** has never been measured. The model gives 0.13-0.17 v, which is plausible from rigid-body maths but unvalidated.

---

## Appendix A: boards and drag in the compiled engine

Scratch script `boards_check.py` (in the session scratchpad). It runs `physics_core.sim_step` on the 46 m arena (kind 2), with no blade, `ice_mu` 0.085 and `BOARD_MU` 0.12. Drag is applied after each 1 ms step as v·(1 − k|v|dt), which needs no code change.

| Test | Now (e 0.55, no drag) | e 0.30 | e 0.30 + drag 0.0043 |
|---|---|---|---|
| Rim along the boards at 15 m/s: speed out of the far corner | 7.2 m/s | 7.2 | 4.9 |
| … at 20 m/s | 11.6 | 11.6 | 8.8 |
| … at 25 m/s | 15.5 | 15.5 | 12.1 |
| 45° dump from centre ice into the side boards at 20 m/s: out of the far corner | 3.5 | 4.2 | 0.05 (barely round) |
| … at 25 m/s | 6.3 | 7.3 | 4.7 |
| Straight into the end boards at 5 m/s: rebound speed, slide back | 2.6 m/s, 4.0 m | — | 1.4 m/s, 2.0 m |
| … at 10 m/s | 5.4 m/s, 17.6 m | — | 2.9 m/s, 5.1 m |
| … at 20 m/s | 11.0 m/s, the whole rink (46 m) | — | 5.9 m/s, 19.4 m |
| … at 30 m/s | 16.5 m/s, the whole rink | — | 8.9 m/s, 39.9 m |

**Reading:**
- The bounce value does not change rims; drag does.
- A lower bounce keeps a little more speed in angled hits, because the board friction impulse scales with (1 + e).
- With drag, steep dump-ins into the side boards barely make it round the end. If that feels wrong in the headset, the open question is board friction and spin (change 19), not drag.

## Appendix B: Jon's skating, measured from his recordings

**Method.** Scratch script `skate_logs.py`.
- The head's pose in `rec.csv` is recorded in the world: the rig moves the room into the world. So the head's world motion is his skating plus his own head motion.
- The pose is resampled at 100 Hz, and position and velocity are each smoothed over 100 ms. Acceleration comes from the smoothed velocity.
- "Moving" means faster than 0.5 m/s.
- "Lateral" is the part of the acceleration across the motion, measured while faster than 1 m/s.
- "Stops" are drops from above 70% of top speed to under 0.3 m/s within 1.5 s.

**Noise floor.** In two sandbox sessions with no locomotion (2026-11-07), the head alone gave |a| p99 2.6 m/s², and exceeded 6 m/s² only 0.06-0.1% of the time.

| Session | Top speed | Vignette | Length | Moving | p90 \|a\| while moving | Time > 6 m/s² | Time > 10 m/s² | Lateral > 6 m/s² (share of time > 1 m/s) | Stops per min |
|---|---|---|---|---|---|---|---|---|---|
| Free skate 14:20 | 3.0 | 0.7 | 8.3 min | 15% | 10.6 m/s² | 6.0% | 2.1% | 13% | 3.5 |
| Free skate 14:32 | 3.0 | 0.7 | 7.3 min | 11% | 10.3 | 4.1% | 1.3% | 8% | 3.1 |
| 3v3 11:20 | 4.0 | none | 9.1 min | 36% | 15.3 | 17.9% | 10.0% | 35% | 3.5 |
| 3v3 11:34 | 4.0 | none | 8.0 min | 29% | 16.7 | 14.0% | 8.1% | 35% | 1.5 |
| 3v3 11:15 | 6.0 | none | 4.1 min | 43% | 24.2 | 32.2% | 24.8% | 50% | 4.2 |

**Reading:**
- In the 3v3s he was moving 2-3 times as much of the time as in free skate.
- Large accelerations were 3-4 times as frequent at 4 m/s as at 3 m/s, and 6-8 times at 6 m/s.
- Each stop is a 20 m/s² onset, and he made 1.5-3.5 of them a minute.
- Under the proposed model none of these could exceed about 8.5 m/s².

**Limits:**
- The head-world yaw rate includes his own neck turns, so the rig's turn rate cannot be separated out. That is why change 4 logs the rig directly.
- The 11:34 game had the possession magnet on, which doesn't affect locomotion.
- Nothing in the logs says which session made him sick.
