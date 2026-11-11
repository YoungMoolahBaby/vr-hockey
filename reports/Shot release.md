# Shot release: the change list

*2026-11-10. How the puck leaves the blade in the sim, compared with real shots, and what to change. No code was changed to write this.*

**Sources:**
- The four research notes and their fact-checks in [`research_notes/Shot release/`](../research_notes/Shot%20release/): puck release, shot outcomes, stick loading, and tracked contact in VR.
- The code on main at 6e3420a: `puck.py` (`Flex`, `Sim`, `ice_rest`), `physics_core.py` (`sim_step`, `collide_blade`), `sandbox.py` (`Physics`, the settings) and `grab.py`.
- This round's replays of Jon's sessions through the physics (scratch scripts `fullreplay.py`, `presses.py`, `touchstats.py` and `spikes.py`). Two small integrations of the sim's flex were run for this report (`calc/handoff.py`, `calc/earlylift.py`). All of them are in the session scratchpad.

Only claims the fact-checkers confirmed are used as evidence. Claims they marked unsupported appear only as labelled estimates (see [section 5](#5-what-was-dropped-or-corrected-and-open-questions)). The tracked-contact note's analysis of Jon's recordings was not re-run by its fact-checker. Those numbers are tagged [D], and the replay tool should re-check them before they gate anything.

Tags: **[M]** measured in the cited study. **[D]** derived: arithmetic shown, or our own analysis of Jon's recordings and of replays through the sim. **[E]** estimate, physics with stated assumptions, or a model's output (including scratch models of the sim). **[V]** vendor claim, coaching text or anecdote. **[S]** secondary: read in a source that cites the primary. Statements about the code are read from the code and carry no tag.

## 1. The short version

**The contact model is not the problem.**
- The sim already sends the puck off faster than the blade when the hands drive through the hit: 1.08-1.28x, in 2 touches over 18-27 ms. When the hands stop, the puck leaves at 0.77-0.93x [E, scratch model of the sim's blade]. A slow tap leaves at 0.98 of the blade's speed [D].
- Real shots sit in the same ranges [M/D]:
  - wrist shots leave at 0.91-0.98 of the toe's speed;
  - slap shots leave at 1.02-1.16 of the blade's speed (the means of six shooters);
  - a hand-free stick fired on by a cannon sends the puck off at 0.62-0.84.
- So `blade_pop`, the blade's mass and a "faster than the blade" rule are not the levers.
- Don't cap contact time either. Wrist shots keep the puck on the blade for 80-290 ms [M].

**Three things are wrong, and no real stick does any of them:**
1. **The blade leaves a press in one step.** After a deep press, the blade sits still on the ice while the hands rise. Then it jumps to their full rising speed in one tick [D]. A real blade lifts at zero speed and zero acceleration. It catches up with the hands over about 20-40 ms with shooting hands, or 45-90 ms with stickhandling hands [E].
2. **The puck rides a rising, accelerating blade.** In the scoops, the puck rides a blade that is off the ice for about 75 ms of repeated contacts. It leaves at 8-14 m/s upward and rises 3-10 m [D].
   - In real slap shots the puck spends only about 10-25 ms on the blade after the blade leaves the ice [D].
   - A shot on net from 4 m or more needs only 5.0-6.6 m/s upward: about 7 m/s from 3 m and 9.7 m/s from 2 m [D].
3. **Flicks no real stick allows.** The fast tail is real tracked motion, not jitter.
   - Both controllers are fully tracked 98.3-99.9% of the time during the fastest swings [D].
   - With the controllers 19-23 cm apart and no stick inertia, a wrist flick swings the shaft at 22-33 rad/s. The blade then moves at 37-47 m/s [D].
   - Real blades meet the puck at about 30 m/s at most: university elite players at 29.1 ± 1.4 m/s, and pros' blade tips at only 10-17 m/s [M].
   - The per-tick blade velocity is about 10 times noisier than it needs to be. But filtering trims the tail of blade speeds by only 2-12% [D].

**The changes, in order** (section 3):
1. **Take the blade's contact velocity from a 4 ms window**, with the true time step and a tighter jump guard. The noise falls 4-5 times, for 2 ms of delay on the contact velocity only.
2. **Ease the blade off the ice after a press.** Hand the last 2ζu/ω of the bow to the flex spring, where u is how fast the hands rise. At today's spring that is 0.9 cm per m/s of lift with shooting hands and 2.3 cm with stickhandling hands. The blade then lifts at zero speed and reaches the hands' speed after about 21 ms (shooting hands).
3. **Cap the rigid blade's speed at contact at 30 m/s**, measured relative to the body. The cap acts only on the impulse; the blade is drawn and swept where the hands put it.
4. **Call shot speeds from the puck's free flight**, the same way in the game and in the replays.

**Keep:** `blade_pop` 0.30, `BLADE_MASS` 0.15 kg, `blade_grip` 0.35, `ICE_BEND` 12 cm storing no energy, pose sampling at "now", no contact-time cap, no ice-friction loading.

**Check offline first** (section 4). Replay the 2026-11-10 sessions through each change. The changes pass when:
- shot speeds have p90/median ≤ 1.45 and max/median ≤ 1.8, as for every NHL player sampled;
- launches above 6 m/s upward are ≤ 5% of shots (now 25% and 38%), and none passes 10 m/s or 3 m of height;
- the blade leaves a press at zero speed;
- ordinary shots move by ≤ 3%, and stickhandling touches by ≤ 10%.

None of these changes moves the view, so none carries a comfort risk.

---

## 2. Measured against the sim

"The sim now" comes from Jon's recordings replayed through the current physics (main 6e3420a), or from the brief, unless marked.

| Quantity | Real | Source and conditions | The sim now |
|---|---|---|---|
| Contact time, strikes | Pro slap shot 20 ± 2 ms; one-timer 15 ± 2 ms [M]. Lab slap shots: 27 ± 5 ms touching (rec), 38 ± 9 ms (elite), in a window of about 33 / 44 ms [M/D]. 1-4 separate touches [M/D] | Swarén 2019: 2 DEL pros, on ice, 300 Hz. Villaseñor 2004: 4 elite and 5 rec men, polyethylene, a 260 g puck on a cable (so an upper estimate for a game puck) | Hands driving through: 18-27 ms in 2 touches [E, scratch model] |
| Contact time, sweeps (wrist shots) | 150-180 ms on average, 80-290 ms in all; the puck rides 0.84-1.79 m with the blade [M] | Michaud-Paquette 2008: 25 university men, targets 4 m away, silicone-sprayed polyethylene, 240 Hz | Not measured yet (section 4) |
| Contact with the blade off the ice | About 10-25 ms in slap shots. The blade lifts 7-13 ms after first touching the puck [D] | Lomond 2005: 8 elite, 7 rec, wired puck, polyethylene. **Slap shots only**; nothing measured for wrist shots, flips or saucer passes | About 75 ms of repeated contacts in the scoops [D] |
| Puck ÷ blade speed | Wrist: 0.91-0.98 of the toe, 1.27-1.32 of the heel [M/D]. Slap: 1.02-1.16 of the incoming blade (means; about 1.15 after Kays's video-over-radar correction), best single shot 1.27 [M/D]. Pros: about 1.4-1.7 against the blade tip before ice contact [D, read off a figure]. Hand-free cannon: 0.62-0.84 [M/D] | Michaud-Paquette 2008; Kays 2013 (6 mixed-skill shooters, 2 on real ice); Swarén 2019 (n = 2); Smith & Bigford (pivoted stick, no hands) | Slow tap 0.98 [D]. Hands driving 1.08-1.28, hands stopping 0.77-0.93 [E]. Jon's hard shots: 0.95-1.09 of the blade's 1 ms peak, 1.18-1.29 of its 20 ms speed [D] |
| Restitution | Frozen puck 0.27 at 55 mph; warm 0.34-0.39 (rigid plate, WSU). Warm 0.427 at 35 mph (Kays, 12 pucks) [M]. In an FE slap shot, e from 0.23 to 0.60 changed puck speed by ≤ 0.8 mph [E] | WSU theses; Kays 2013 | `blade_pop` 0.30 |
| Effective mass at the blade | Held stick: 0.13-0.20 kg [D, m = k/(2πf)² from Cross & Lindsey's clamp test]. Single hit on pivoted sticks: 0.16-0.32 kg [D/E] | Cross & Lindsey 2016 (not peer-reviewed); Kays; Smith & Bigford | 0.15 kg. One hit gives 0.61 of the blade's speed, against 0.70-0.81 [D] |
| Upward speed a shot on net needs | 5.0-6.6 m/s from 4-18 m; about 7 m/s from 3 m; about 9.7 m/s from 2 m [D] | Crossbar 1.22 m (USA Hockey Rule 105); flight without drag | Launches crossing 6 m/s: 16 and 32 per session. Peaks of 8-14 m/s, rising 3-10 m [D] |
| How often real shots go high | 1.54% of NHL shot attempts miss over the net; 0.45% hit the crossbar [M] | NHL stats API, 2025-26, 152,892 attempts | Launches above 6 m/s for 25% and 38% of replayed shots [D] |
| Lifting the puck | Top-corner wrist shots pitch the blade more during contact (57-58° against 35-39°): a "scoop" under the puck, then a flick [M]. Nothing measures the follow-through after release | Michaud-Paquette 2008 | The puck keeps riding the blade after it leaves the ice |
| Shot speed, adult rec player | Wrist: 16.0 ± 2.5 m/s (36 mph; lab, radar) to 26.4 ± 3.0 m/s (59 mph; real ice, motion capture). Slap: 23.3 ± 3.9 (Wu), 24.6 ± 1.8 (Lomond, game pucks), 22.4 ± 6.6 m/s (Hannon) [M] | Wu 2002; Robbins 2021; Lomond 2005; Hannon 2010. Groups of 7-10 | Median 41-44 mph [D] |
| Spread of shot speed | p90/avg 1.18-1.46, p99/avg 1.31-1.70, season top/avg 1.38-1.80 [D from M]. For a 42 mph median: p90 50-57 mph [D], p99 55-71 mph [D] (58-65 is a judgement [E]), a ceiling of about 70 mph standing and 75 mph skating [D] | NHL EDGE, 11 players with 288-598 attempts each | p90 77 mph, max 105 mph (the sprint session); 10-16% of shots at 30 m/s (67 mph) or more [D] |
| Skating's gain | +1.9-2.1 m/s on wrist shots for 1.7-1.8 m/s more body speed; +2.1 m/s on slap shots [M] | Robbins 2021 (real ice); Doré & Roy 1975 (9 skilled adult amateurs) | Skating adds almost nothing to the blade-speed tail: p99.99 39.4 m/s relative to the rig, 39.2 in the world [D] |
| Blade speed at puck contact | Rec 26.5 ± 0.7, university elite 29.1 ± 1.4 m/s (slap shots, at impact) [M]. Pros' blade tip: 10-17 m/s at puck contact, 27-37 m/s only in the recoil around release [M, read off a figure] | Woo 2004: 5 + 5 men, lab polyethylene, wooden stick, 60 Hz. Swarén 2019 Fig. 2, read by eye | 20 ms peaks of 37-44 m/s; the runtime's velocity up to 47 m/s; single 1 ms ticks over 40 m/s [D] |
| Swing rate and grip | Rotation gives 16.0-17.4 m/s of the blade's speed in slap shots, about 11-12 rad/s over 1.4 m [M/D]. Hands 0.34 m apart in wrist shots and 0.60 m in slap shots [M] | Woo 2004; Wu 2002 | Median 22 rad/s in shots of 30 m/s or more, up to 33 rad/s; controllers 19-23 cm apart in those shots [D] |
| Shaft bend at the blade | Rec slap shot 9-13 cm; skilled 12-16 cm, up to about 20 cm; wrist 5-10 cm [D from M angles]. Only 3-7 cm at puck contact. The bend peaks about 14 ms after puck contact, as the blade leaves the ice [M/D] | Pearsall 2001; Kays 2013; Lomond 2005 | Bow ≤ 12 cm (stores no energy), flex ≤ 15 cm. Jon presses 19 cm below the ice (median), 31 cm (p90) [D] |
| Force on the blade | Slap shots: peak vertical force 165 ± 50 N (skilled), 105 ± 48 N (unskilled). Wrist shots about 45 N [M]. 12 cm on a held stick takes about 85-180 N [D] | Pearsall 2001, force plate in a lab | Kinematic hands, no force limit. 19-31 cm would take 130-470 N [D] |
| Held-stick stiffness | About 0.6-2.6 kN/m at the blade; first mode about 11 Hz, quarter period 21-23 ms [M/D] | Cross & Lindsey (two clamps); Kays (bench rollers) | 2.57 kN/m at flex 75: 20.8 Hz, 12.0 ms. That is 1.2-4.4 times too stiff, 2 times in the middle [D] |
| Recoil's share of puck speed | A few percent, about 10% at most. From measured bend energy, rescaled to a 0.17 kg puck: ≤ 2.5% (rec), ≤ 9% (elite). Angle-based bends allow 10-15% [D]. Changing stick flex moves shot speed by 0-4% [M/D] | Villaseñor 2004; Pearsall, Grover, Kays & Smith, Léger | 0% from the bow. The dropped ice-load trial gave +5-11% [D] |
| Lift-off after a press | Zero speed and zero acceleration. Hand speed after 30-38 ms at ζ 0.6 (about 10% overshoot); 90% of it after 70-90 ms at ζ 1.5 (stick at 0.8-1.3 kN/m) [E] | Physics only; no study tested it | A step to the hands' full speed in one tick [D] |
| Ice before puck (slap shot) | 10-19 ms (mean 14) and 27-41 cm behind the puck [M]. Shaft strain starts 85 ± 136 ms before puck contact in high-calibre players, 349 ± 299 ms in low-calibre players [M] | Kays 2013; Hannon 2010 (synthetic ice; start set by a strain threshold) | About 200 presses per session. A swing over 12 m/s follows within 0.6 s after 42-50% of them [D] |
| Blade velocity noise | A real blade tip accelerates at about 400-600 m/s² [D, read off Swarén's figure] | — | Per 1 ms tick, p99 changes of 1.5 m/s (handling) and 13 m/s (shots): thousands to 15,000 m/s² [D] |

---

## 3. Ranked changes

1 = do first. Changes 1-4 can ship together once they pass the offline checks. Test 2 and 3 one at a time in the headset. None of the changes moves the view, so the comfort risk of every one is none; the risk column is about feel.

| # | Change | Now → proposed | Confidence | Risk to feel or comfort |
|---|---|---|---|---|
| 1 | Contact velocity from a short window; true time step; tighter jump guard | 1-tick pose difference, dt clipped to 0.2-10 ms, jumps over 0.2 m/tick → least-squares slope over **4 ms** (A/B 8 ms); true dt, with a stall over 20 ms treated as a jump; jumps over **0.05 m/tick**, checked against the runtime's velocity; no impulse from untracked hands | high for the noise; low that it fixes the tail | none: 2 ms of delay on the contact velocity only |
| 2 | Ease the blade off the ice after a press | velocity step to the hands' speed → the last **2ζu/ω** of the bow handed to the flex spring; the blade lifts at zero speed and acceleration, reaching hand speed after **~21 ms** (ζ 0.6) and 90% after **~47 ms** (ζ 1.5) | medium | low: the blade trails a lift out of a press for 20-50 ms |
| 3 | Blade-speed cap at contact | none → rigid contact speed ≤ **30 m/s** relative to the body (A/B 28), in the impulse only | medium | low: only flicks over 30 m/s lose speed; nothing visible changes |
| 4 | Shot speed called from free flight | peak 3D speed within 0.25 s of a hard contact → mean speed over **10-20 ms** after the last contact; no call if the speed changes by more than **4.5 m/s** within the first 50 ms of free flight; the same rule in the replays | high | none |
| 5 | The puck's release: keep the mechanism | `blade_pop` 0.30, `BLADE_MASS` 0.15, `blade_grip` 0.35; **no contact-time cap**; contact time used only to flag scoops | high | none |
| 6 | Pressing into the ice: keep it energy-free; optional press cue | no change to the physics; a single short buzz when the bow reaches 12 cm | high (physics); low (cue) | none |
| 7 | A held-stick spring (later, blind A/B) | 2.57 → about **1.3 kN/m** at flex 75 (span 1.0 m, two-hand supports) | low-medium | medium: reception and stickhandling feel |
| 8 | Airborne carry limit (only if 1-3 miss the launch target) | none → contact with both blade and puck off the ice ends after **25 ms** (A/B 40 ms) | low | medium: may cut deliberate flips |
| 9 | Pose look-back A/B | "now" → **5 ms** back; never predicted | low | low-medium: the physics stick 5 ms behind the drawn one |
| 10 | Stick inertia (experiment only) | none → shaft angular acceleration ≤ **150 rad/s²** about the top hand | low | high: a lagging stick reads as "floaty" |

Keep as they are: `blade_pop` 0.30, `BLADE_MASS` 0.15 kg (do not go above about 0.3 kg, earlier report), `blade_grip` 0.35 (0.45 only with puck spin, earlier report), `ICE_BEND` 0.12 m storing no energy, `Flex.MAX_BEND` 0.15 m, `Flex.DAMPING` 0.60 and `HANDLE` 1.5, `HOLD_JUMP` 60 m/s, and `PREDICT = False`.

### 1. Contact velocity from a short window; the true time step; a tighter jump guard

- **Now.**
  - The blade's velocity at a contact is one controller sample's pose difference: `vb_r = (rigid_bot - last_bot) / dt` in `physics_core.sim_step`.
  - `Physics._tick` clips dt to 0.2-10 ms.
  - The jump guard is `JUMP_M` = 0.2 m per tick, which lets through anything under 200 m/s.
  - The physics needs only the VALID pose bits (`record.NEED_POSE`), so inferred (untracked) poses drive the blade.
- **Proposed.**
  - **Velocity.** Fit a least-squares line to the rigid blade edge points over the last **4 ms**, using the true sample times. A/B 8 ms. The other option is the runtime's own `XrSpaceVelocity`, mapped to the blade (top hand's velocity plus the swing). The sampler already logs it.
  - **Positions.** The swept contact keeps using the raw poses. The flex and the ice's hold rate are added to the velocity as now.
  - **Time step.** Use the true interval. Keep the substep at or under 0.25 ms by raising the substep count when dt is long. Treat a stall over 20 ms like a jump: no sweep and no velocity from it.
  - **Jump guard.** 0.05 m per tick (50 m/s). Jon's fastest real blade moves 4.7 cm per tick [D]. Also treat |Δp|/dt more than 3 times the runtime speed plus 2 m/s as a jump.
  - **Untracked hands.** No impulse from a tick in which either hand is only inferred, as the earlier report proposed.
- **Evidence.**
  - Per-tick change of the blade's velocity at p99 [D]:

    | Estimator | Handling (0.5-3 m/s) | Shots (10-40 m/s) | Delay |
    |---|---|---|---|
    | 1 ms pose difference (now) | 1.5 m/s | 12.5-13.6 m/s | ~0.5 ms |
    | 4 ms window | 0.30-0.33 m/s | 3.0 m/s | 2 ms |
    | 8 ms window | 0.16-0.18 m/s | 1.5 m/s | 4 ms |
    | Runtime velocity | 0.16-0.17 m/s | 1.5-2.0 m/s | 2-9 ms |

  - The 1 ms differences imply accelerations of 10,000-15,000 m/s² at p99.9. The runtime velocity implies about 1,050 m/s² [D]. Pros' real blade tips reach about 400-600 m/s² [D, read off Swarén's Fig. 2].
  - Observers could not tell a release shifted by ±10 ms from the original. Shifts of ±20 ms or more were noticed (FauxThrow 2022, n = 34, third-person video of throws) [M].
  - Stalls over 10 ms happen 5-7 times per session, up to 38 ms. The clip at 10 ms then overstates velocity up to 3.8 times on that tick [D].
  - Re-acquired poses moved the controller at most 30 mm, and inferred runs never started during fast motion [D].
  - Do not use the 1€ filter here. Its cutoff rises with speed, so it passes the speed-proportional spikes the contact needs removed [M/D].
- **Expected effect.** Per-tick noise falls 4-5 times (4 ms) or about 9 times (8 ms). The tail of blade speeds falls only 2-4% with a 4 ms window, and 7-12% with 20 ms [D]. This change cleans the impulses; it does not fix the shot tail.
- **Flags.**
  - Under steady acceleration a 4 ms window reads low by a·W/2: 0.7 m/s at the blade's p99 acceleration of about 350 m/s² [D].
  - Nobody knows whether `XrSpaceVelocity` is raw gyro, filtered or predicted. Its 2-9 ms lag is an indirect estimate.
- **Code.** `sandbox.Physics._tick` (keep a short ring of edge points with their times; the dt clip), `JUMP_M`, `physics_core.sim_step` (take the blade velocity as an input instead of computing `vb_r` and `vt_r`), and `record.Sampler` (pass the tracked flags and runtime velocity on to the physics).
- **Confidence:** high that it cuts the noise; low that it moves the tail. **Risk:** none. The delay touches only the contact velocity; the stick is drawn and swept where the hands are.

### 2. Ease the blade off the ice after a press

- **Now.**
  - When the hands push the blade under the ice, the ice holds it up. The shaft bows up to 12 cm, storing no energy, and past that the stick slides up through the hands (`ice_rest`).
  - As the hands rise, the hold shrinks and the blade stays still. Its contact velocity includes the hold's rate since 6e3420a, so it reads as still.
  - When the hold reaches zero, the blade's velocity steps to the hands' full rising speed in one tick [D]. The flex never sees the press.
- **Proposed (A, faithful).**
  - While the hands lift out of a press, call the rate at which the hold shrinks u (upward, m/s).
  - When the bow left falls to 2ζu/ω, hand that last part of the bow to the flex as spring bend, with the blade at rest on the ice. ω and ζ are the flex's own: ω = √(k/m) = 131 rad/s today, and ζ is set by the trigger.
  - From there the flex's spring and damper lift the blade. No new constant is needed.
  - The rest of the bow stays energy-free, so a press still stores nothing. The handed-over bend lies along the bow (across the shaft, toward up), never along the face normal.
  - If the hands stop rising before lift-off, put the bend back into the energy-free bow.
  - How much bow is handed over [D, 2ζu/ω]:

    | Hands' lift u | Shooting hands (ζ 0.6) | Stickhandling hands (ζ 1.5) |
    |---|---|---|
    | 1 m/s | 0.9 cm | 2.3 cm |
    | 6 m/s | 5.5 cm | the whole 12 cm |

- **What it does** [E, 1 µs integration of the sim's flex, `calc/earlylift.py`]:

  | Spring | Hands | Lift-off | Reaches hand speed | 90% of hand speed | Overshoot | Peak acceleration (6 m/s lift) |
  |---|---|---|---|---|---|---|
  | today, 2.57 kN/m | ζ 0.6 | zero speed, zero acceleration | 21 ms | 18 ms | 9% | 392 m/s² |
  | today | ζ 1.5 | zero speed (see below) | — | 46-49 ms | none | 301 m/s² |
  | held, 1.3 kN/m (change 7) | ζ 0.6 | same | 29 ms | 25 ms | 9% | 281 m/s² |
  | held | ζ 1.5 | zero speed (see below) | — | 53-69 ms | none | 632 m/s² |

  - With stickhandling hands and a fast lift, 2ζu/ω is more than the whole 12 cm bow. The blade then lifts at once, at zero speed but not zero acceleration. That is where the ζ 1.5 peaks at 6 m/s come from (301 and 632 m/s²).
  - The other peaks sit under pros' real blade-tip accelerations of about 400-600 m/s².
- **Fallback (B, simpler).** At lift-off, start the flex from the pinned blade's velocity, with no bend handed over [E, `calc/handoff.py`].
  - It stores nothing, and the velocity no longer steps.
  - But the blade starts at 2ζω·u, which is 940 m/s² for a 6 m/s lift with shooting hands. It reaches hand speed after 6.6-8.9 ms and overshoots by 25% (ζ 0.6) or 8% (ζ 1.5).
  - That overshoot whips the blade up faster than the hands, so B may not cut scoops. Use it only if A fails the no-fire test.
- **Evidence.**
  - With the sim's flex form, a blade pressed into the ice lifts with 1.3-4.1 cm of bend left (at 1 m/s), at zero acceleration. It reaches hand speed after 30-38 ms (ζ 0.6, about 10% overshoot), and 90% of it only after 70-90 ms (ζ 1.5), for a 0.8-1.3 kN/m stick [E, the stick-loading note's §7 as corrected in its fact-check].
  - In real slap shots the blade leaves the ice 7-13 ms after first puck contact [D, Lomond], about when the bend peaks, 14 ms after contact [M, Kays, one shot]. The ice holds the bend and lets it go through the spring, never as a step [E].
  - The scoops come partly from this kink [D, this round's replays].
- **Flags.**
  - No study has tested a press and lift without a swing.
  - A session-2 version in which the ice loaded the flex spring fired a resting puck at 6 m/s (comment on `ICE_BEND` in `puck.py`). So A must pass two tests: `tests/test_hands.py` (the pinned-blade launch), and a new one in which a stick held low is lifted beside a resting puck, which must stay under 0.5 m/s.
  - With stickhandling hands and a fast lift, the whole 12 cm bow becomes spring (up to 18.5 J at today's stiffness). The damper takes it back into the hands with no overshoot in the integration, but that is the case the no-fire test must cover.
- **Code.** The hold block of `physics_core.sim_step` (bow, slide, `v_hold`) and `puck.Sim.step_ref`; the flex state (`fx`, `fv`).
- **Confidence:** medium. **Risk:** low. After a deep press the blade trails the hands for 20-50 ms, showing a bow. A quick lift over a puck straight after a press may feel slower with stickhandling hands.

### 3. Cap the blade's speed at contact at 30 m/s

- **Now.** The contact velocity is the rigid stick's, with no limit.
  - In the 12:08 session (2026-11-10), 43 swings put the blade over 30 m/s (20 ms speed), with peaks of 37-44 m/s, and the runtime's velocity reached 47 m/s [D].
  - Six of the eight shots over 80 mph came from swings with blades at 30-38 m/s and the hands 18-23 cm apart [D].
- **Proposed.**
  - Before the impulse, scale the rigid blade's contact velocity, relative to the body's motion, so that its speed at the contact point is at most **30 m/s**. A/B 28 m/s. The body's motion is the `body` array the cradle already uses, so skating still adds honestly.
  - Add the flex's and the hold's velocity after the cap. The flex's recoil can still send the puck past the blade.
  - The cap acts only on the impulse. The blade is still drawn and swept where the hands are.
- **Evidence.**
  - Blade speed at impact in slap shots: 29.14 ± 1.39 m/s for 5 university varsity players, 26.46 ± 0.66 m/s for 5 recreational players (Woo 2004, lab polyethylene, wooden stick, 60 Hz) [M]. Mean + 2 SD: 31.9 and 27.8 m/s [D].
  - Two pros on ice: the blade tip is at 10-17 m/s when it meets the puck. It passes 30 m/s only in the recoil around release, at 27-37 m/s (Swarén 2019, 300 Hz, read off Fig. 2) [M].
  - Group means top out at about 29 m/s. Some single elite trials probably pass 30 m/s (Lomond 2005, SD 4.3 m/s) [D].
  - The rotation part of a real slap shot's blade speed is 16.0-17.4 m/s; translation gives the other 9-13 m/s (Woo) [M]. Jon's shots over 30 m/s got 27-31 m/s from rotation alone [D].
  - A real stick (about 0.35-0.45 kg·m² about the top hand) [E] would need a hand couple of 330-430 N to swing like his median shot over 30 m/s, and 560-720 N for his fastest flick. That is 3-8 times the measured per-hand sum of grip forces, 91-118 N (Zane 2012, Table 6) [D].
- **Expected effect.** With the flex's 1.08-1.28x, pucks top out at about 32-38 m/s (73-86 mph) [D]. If the spread still fails the shape tests (section 4), try 28 m/s.
- **Flags.**
  - A cap is a limit, not physics. It stands in for the stick inertia the controllers lack. The honest version is change 10, which the earlier research advises against (see there).
  - The narrow grip multiplies the problem. With the controllers 22 cm apart, the blade, 1.4 m from the top hand, moves 6.4 times as far as the bottom hand moves relative to the top hand. At a real grip of 34 cm (wrist) or 60 cm (slap) [M, Wu 2002], it is 4.1 or 2.3 times [D: 1.4/0.22, 1.4/0.34, 1.4/0.60]. Don't fix this with a gain: the earlier report found hand gains cost precision and leave after-effects. Ask Jon to try a real grip instead (section 5).
- **Code.** `physics_core.sim_step`, just before `collide_blade` (`vbc`, `vtc`). A new `Params.blade_cap` (30 m/s) needs a new index in `prm` and in `warm()`, since numba does not check bounds.
- **Confidence:** medium. **Risk:** low. Only flicks over 30 m/s lose speed, and nothing visible changes.

### 4. Call shot speeds from the puck's free flight

- **Now.**
  - `Physics._call_shot` starts a shot at a contact with an impulse over 2 m/s and a puck over 6 m/s. It calls the peak 3D puck speed over the next 0.25 s, re-contacts and vertical speed included.
  - The replay script uses a different rule: the peak within 0.3 s of any contact, counted only over 15 m/s. That is one reason its medians (50-65 mph) sit above the 41-44 mph called in the sessions.
- **Proposed.**
  - Call the shot from the puck's mean speed over 10-20 ms of free flight, starting once no contact has happened for 5 ms.
  - Don't call while the blade still touches the puck.
  - Make no call if the speed changes by more than 4.5 m/s within the first 50 ms of free flight. That catches a re-contact.
  - Log the horizontal and vertical speeds and the launch angle with each shot.
  - Use the same function in the game and in every replay tool.
- **Evidence.**
  - Radar and lab trackers measure the puck in flight. Radar read 6.9 mph (wrist) and 3.8 mph (slap) below high-speed video for 2 shooters (Kays 2013) [M].
  - Manning (2020) excluded 5 of 360 shots whose speed changed by more than 4.5 m/s within a 54 ms window starting 20 ms after peak speed [M]. It is a window rule, not a per-sample rule.
- **Confidence:** high. **Risk:** none. Jon may hear slightly different numbers.

### 5. The puck's release: keep the mechanism, and don't cap contact time

- **Keep** the swept impulse contact, `blade_pop` 0.30, `BLADE_MASS` 0.15 kg and `blade_grip` 0.35.
- **Exit faster than the blade.** The sim already gets the excess the honest way: from hands that keep moving through the hit, plus the spring's recoil [E, scratch model]. Measured ratios in section 2 cover what it gives.
  - One hit cannot beat the blade unless the effective mass exceeds m/e, about 0.57-0.63 kg [D]. No stick comes close, so neither pop nor a heavier blade is the lever.
  - Restitution barely matters. In an FE model the puck's speed changed by ≤ 0.8 mph for e from 0.23 to 0.60 [E]. Puck temperature made "no measurable difference" to pivoted sticks (Smith & Bigford) [M].
  - A blade mass of 0.15 kg sits inside the held-stick range of 0.13-0.20 kg [D].
- **No contact-time cap.**
  - Wrist shots keep the puck on the blade for 80-290 ms, over 0.84-1.79 m [M]. Strikes last 15-44 ms in 1-4 touches [M/D].
  - No physics engine or shipped VR title documents a contact-time cap. A hobby paddle's 50 ms hit cooldown "hinders the possibilities of directions they can hit their ball" [V].
  - So a cap under about 300 ms would cut real wrist shots.
- **Use contact time only as a flag.** In the replays, off-ice contact on a rising blade longer than 25 ms marks a scoop. The 25 ms comes from slap shots only, so it is a diagnostic, not a rule (change 8 is the rule, if it is ever needed).
- **Confidence:** high. **Risk:** none.

### 6. Pressing into the ice: keep it energy-free; an optional press cue

- **Now.** `ICE_BEND` 0.12 m bows the shaft without storing energy; beyond it the stick slides up through the hands. Jon presses 19 cm below the ice (median) and 31 cm (p90), about 200 times a session. He does it to load the flex before a shot, and a swing over 12 m/s follows within 0.6 s after 42-50% of presses [D].
- **Proposed.**
  - No change to the physics. Don't bring back ice-friction loading.
  - Optional: a single short buzz when the bow reaches 12 cm and the stick starts to slide. Pressing deeper then reads as doing nothing, which is honest: at a held stiffness 12 cm already takes 85-180 N [D].
- **Evidence.**
  - The recoil adds a few percent of puck speed, about 10% at most [D, section 2]. Players differ by 32% and sticks by 14% (Kays & Smith 2014) [M]. Across studies, stick flex moves shot speed by 0-4%, in either direction [M/D].
  - A vertical press bends the shaft in its own vertical plane, not toward the target. Its energy goes back to the hands as they rise, and it fires nothing [E].
  - A bend released before the puck is wasted: one shooter built "nearly 4 degrees" on the ice, lost it, and shot slowest [M, n = 1].
  - Real loading is short: in slap shots the ice comes 10-19 ms (mean 14) and 27-41 cm before the puck [M]. Skilled players' shaft strain starts 85 ± 136 ms before puck contact; low-calibre players' starts 349 ± 299 ms before it (Hannon 2010, synthetic ice) [M]. So a long press is not how skilled players load, though rec players may do something like it.
  - 12 cm of bow matches a typical skilled slap shot's peak bend, 12-16 cm [D]. Jon's 19-31 cm presses would need 130-470 N, more than any measured shot (165 ± 50 N peak, skilled) [D/M].
  - The case for friction loading is weak. Kays's FE model gained +14% (75 to 85.2 mph) as blade-ice friction went from 0 to 0.35, with prescribed hand motion. The same model overstated speed by 15% because its hands were too rigid [E]. This round's trial gave +5-11% on a synthetic slap shot, and more launches in the replays (16 → 27 and 32 → 41) [D].
- **If it is ever revisited.** Store energy only from friction while the blade sweeps on the ice, capped at about 5 J. Measured bend energy is about 2-6 J for recreational players [D]. Release it only along the sweep, and drop it if the blade lifts before reaching the puck. Accept it only if it adds ≤ 5% and no launches.
- **Code (cue).** `Physics._feel`: one buzz when `sim.slide` first becomes non-zero, not repeated while it stays.
- **Confidence:** high for keeping the physics; low for the cue. **Risk:** none.

### 7. A held-stick spring (later, blind A/B)

- **Now.** `tip_stiffness` converts flex over a 1.17 m span, then clamps a 0.80 m cantilever at the bottom hand: 2,568 N/m at flex 75, 20.8 Hz, a 12.0 ms quarter period.
- **Proposed.** A `FLEX_SPAN` of 1.0 m, and the stick supported by two hands: k = 3EI/(a²(a+b)), with EI = 3.65 × flex N·m², a = bottom hand to blade and b = hand spacing.
  - Flex 75 gives 1,325 N/m with a slap grip (a 0.68 m, b 0.66 m) and 698 N/m with a wrist grip (a 0.93 m, b 0.43 m) [D].
  - Start with one value, about 1.3 kN/m: 15 Hz, a 16.7 ms quarter period with the 0.15 kg blade [D].
- **Evidence.**
  - Cross & Lindsey clamped 85-flex sticks at two points 50 cm apart: 770-890 N/m, about 11 Hz, a quarter period of 20.7-23.3 ms [M; not peer-reviewed].
  - Kays's bench test measured 1.0-1.4 kN/m near the heel [M].
  - The formula reads 4-20% high against the first and 26-44% low against the second. So the honest band is about 0.6-2.6 kN/m, and the sim is 1.2-4.4 times too stiff, about 2 times in the middle [D].
- **What else changes** [D]:
  - Halving k doubles how far the blade lags under steady hand acceleration.
  - The blade gives about 1.4 times more under a pass: 3.4 → about 5 cm for a 10 m/s pass.
  - The lift-off of change 2 slows from 21 to 29 ms (ζ 0.6).
- **Code.** `puck.tip_stiffness`, `FLEX_SPAN`, `FLEX_LEVER`.
- **Confidence:** low-medium. The two bench tests disagree by 1.4-2 times. **Risk:** medium: reception and stickhandling feel. Check "hands" damping and reception give at the same time.

### 8. Airborne carry limit (only if changes 1-3 miss the launch target)

- **Proposed.** When the blade and the puck are both off the ice, contact may go on for at most 25 ms (A/B 40 ms). After that the blade gives the puck no more impulse until it is 5 cm clear, or until either touches the ice.
- **Evidence.**
  - In slap shots the puck spends about 10-25 ms on the blade after the blade leaves the ice [D, Lomond: wired puck, polyethylene].
  - No study measures it for wrist shots, flips or saucer passes, so this is a rule, not physics.
  - Lift during contact is real: top-corner wrist shots "scoop" under the puck [M]. What nothing shows is the puck riding the follow-through after release [E].
- **Confidence:** low. **Risk:** medium. It could cut deliberate flips and saucer passes, for which there is no data.

### 9. Pose look-back A/B (optional)

- **Proposed.** Keep sampling the physics poses at "now", and never predicted. A/B a 5 ms look-back (`lag_ms` already exists in `record.Sampler`), then re-measure the noise table of change 1.
- **Evidence.**
  - OpenXR runtimes must keep at least 50 ms of interpolated history before the most recently received pose (spec §2.16) [M, spec text]. Over Link that pose may itself be a few ms old, so a 5 ms look-back may still extrapolate partly [E].
  - Prediction over-compensates after a motion onset [M] (Warburton 2023; no Quest tested). Jon's predicted session had about 3 times the 1 ms rotation noise, and shots jumped to 75-100 mph [D, project log].
- **Confidence:** low. **Risk:** low-medium. The drawn stick comes from its own grab at display time, so the physics stick would trail it by 5 ms more: about 10 cm at a 20 m/s blade [D].

### 10. Stick inertia (experiment only)

- **Proposed.** The stick turns about the top hand with an angular acceleration of at most α_max = τ_max/I, both drawn and in the physics. Start with I = 0.4 kg·m² and τ_max = 60 N·m, so α_max = 150 rad/s². A/B 100-200.
- **Basis.**
  - I = 0.35-0.45 kg·m² about the top hand [E, from WSU's measured inertias by the parallel-axis rule].
  - τ_max ≈ 21-71 N·m: 62 N (the largest single face force) × 0.34 m (wrist grip), up to 118 N (the per-hand sum) × 0.60 m (slap grip) [D from M]. That gives α of about 47-203 rad/s² [D].
  - Jon's fastest flick needed about 320 rad/s² [D].
- **Why it is last.** In that flick the stick would trail the controllers by about 12° after 50 ms [D: ½ × (320 − 150) × 0.05², if both start at 17 rad/s]. The earlier report put the unnoticed limit at about 4.5° (Zenner & Krüger 2019), and players call lagging weapons "floaty". Try it only if the cap in change 3 feels wrong, and blind.
- **Code.** After `grab.step` in `Physics._tick`, and in the display grab, so the drawn stick and the physics stick stay the same.
- **Confidence:** low. **Risk:** high, for feel.

---

## 4. Checking the changes on Jon's recordings, before the headset

**The tool.**
- Use this round's whole-session replay, `fullreplay.py` (session scratchpad).
  - It drives the sandbox physics with the hands in `rec.csv`, which are world poses.
  - It lays the arena out from the session's "rink" event and drops pucks where the session dropped them.
  - It reproduced the 594.3 s launch.
- Copy it into `prototype/` before the scratchpad goes (for example as `replay.py --session`). Add to it:
  - the shot call of change 4;
  - each launch's peak vertical speed and peak height (it now logs the speed at the moment it crosses 6 m/s);
  - one row per contact episode: start, end, number of touches, time with the blade's lowest point more than 3 mm above the ice, blade vertical speed and acceleration, puck ÷ blade speed;
  - for each press episode (blade more than 12 cm under the ice), the blade's vertical velocity at lift-off and the time it takes to reach 90% of the hands' rising speed;
  - the blade-velocity noise statistics of `spikes.py`, and the stickhandling touch statistics of `touchstats.py`.

**Sessions.**
- Free skates 2026-11-10 06:00 and 12:08 (the main pair; 12:08 has the sprint and the 105 mph shot).
- Free skates 2026-11-09 16:36 and 16:54.
- Sandbox 2026-11-07 11:59 (standing, no locomotion).
- Use each session's own end settings, as the script does.

**Baseline** (main 6e3420a, this round's replays) [D]:

| Session | Replayed shots (over 15 m/s) | Median / max (mph) | Over 60 mph | Launches crossing 6 m/s up | ... crossing at over 8 / 10 m/s |
|---|---|---|---|---|---|
| Free skate 11-10 06:00 | 65 | 54.1 / 85.7 | 24 | 16 | 3 / 0 |
| Free skate 11-10 12:08 | 85 | 64.9 / 98.1 | 50 | 32 | 4 / 2 |
| Free skate 11-09 16:36 | 12 | 52.7 / 66.8 | 3 | 2 | 0 / 0 |
| Free skate 11-09 16:54 | 17 | 50.4 / 70.4 | 4 | 3 | 0 / 0 |

The speed at the crossing understates the peaks, which reach 8-14 m/s [D]. Re-baseline once change 4 and the extra logging are in.

**Order.** Run each change alone against the baseline, then 1-4 together. Change one setting at a time.

**What each change should move:**
- **Change 1:** the noise rows below. Report the launches and the tail too; expect little change there.
- **Change 2:** the lift-off row. Launches with the stick still sliding at launch (1 and 6 today) should go to zero. Launches within 100 ms of a lift-off from a press should at least halve.
- **Change 3:** the shot-speed rows and the blade speed at contact.
- **Changes 1-4 together:** every row.

**Acceptance targets:**

| Check | Target | Today | Basis |
|---|---|---|---|
| Spread of shot speeds | p90/median ≤ 1.45 and max/median ≤ 1.8 | 77/42 = 1.8 and 105/42 = 2.5 (called in the session) | Every one of 11 NHL players sampled: p90/avg 1.18-1.46, top/avg 1.38-1.80 [D from M]. These shapes test the physics and tracking, not Jon's strength |
| Absolute shot speeds (median about 42 mph) | p90 ≤ about 57-61 mph; max ≤ about 70 mph standing, 75 mph with the sprint; shots of 30 m/s (67 mph) or more: a few % at most | p90 77, max 105 mph; 10-16% at 30 m/s or more | NHL ratios × 42 [D]; Wu's rec slap shot mean + 2 SD = 31.1 m/s (70 mph) [D]; skating adds about 2-3 m/s [M] |
| Ordinary shots | Shots under 22 m/s today change by ≤ 3% (median per shot) | — | No evidence that they are wrong |
| Launches over 6 m/s upward | ≤ 5% of shots (about 3-4 per session) | 25% and 38% | NHL: 1.54% of attempts miss over the net [M]; roof shots in tight need 7-10 m/s [D] |
| Launches peaking over 8 m/s | ≤ 1 per session, unless it is a visible flip (face open, hands rising, blade under the puck) | 3-4 at the crossing, more by peak | "A few per hour at most" for rec shooting [E] |
| Launches over 10 m/s, or rising over 3 m | 0 | 0 and 2 at the crossing; scoops peak at 3-10 m | Only a deliberate lob does this [E] |
| Launches with the stick still sliding through the hands | 0 | 1 and 6 | A pinned blade can't throw anything [E] |
| Contact off the ice on a rising blade | ≤ 25 ms in strikes; list and inspect every case over 40 ms | about 75 ms in the scoops | Slap shots: about 10-25 ms [D]. A flag only for wrist shots and flips |
| Strike contact windows | 15-45 ms, 4 touches or fewer | — | [M/D] |
| Sweep contact (puck on the ice) | ≤ 300 ms, and ≤ 1.8 m carried | — | Michaud-Paquette: 80-290 ms, 0.84-1.79 m [M] |
| Puck ÷ blade speed, slow taps (blade under 3 m/s) | median 0.9-1.05 | 0.98 [D] | Wrist shots 0.91-0.98 of the toe; about 0.94-1.04 at the release point [M/D] |
| Puck ÷ blade speed, hard shots (windowed blade at the contact point) | 0.75-1.3; flag any over 1.3 | 1.18-1.29 against the 20 ms blade [D] | Kays: 1.02-1.16 means, 1.27 best; one poor hit 0.75 [M/D] |
| Blade velocity noise, p99 per tick | ≤ 0.3 m/s (handling), ≤ 3 m/s (shots) | 1.5 and 13 m/s | [D] |
| Implied blade acceleration, p99.9 | ≤ 2,000 m/s² | 10,000-15,000 m/s² | Runtime velocity about 1,050 m/s²; pros' tips 400-600 m/s² [D] |
| Blade speed at contact, p99.99, relative to the body | ≤ 30 m/s | 37-44 m/s (20 ms) | Woo [M]; Swarén [M] |
| Lift-off after a press | 0 upward speed at lift-off; 90% of hand speed after ≥ 15 ms (ζ 0.6) and ≥ 40 ms (ζ 1.5); overshoot ≤ 10% | a step to 100% in one tick | Section 3, change 2 [E] |
| Stickhandling | Touch separation and gain (p50, p90) within ±10% of today's (`touchstats.py`) | — | No evidence that they are wrong |
| No fire from a press | `tests/test_hands.py` passes; a stick lifted out of a press beside a resting puck leaves it under 0.5 m/s | — | The session-2 history |

**Then the headset.**
- Change one thing per session, 5-8 minutes per condition.
- Use free skate with no players. Take 20 shots from the slot and 20 from the point, plus 2 minutes of stickhandling.
- Record Jon's words in the run's notes.
- Order: change 2, then change 3 at 30 and at 28 m/s.
- Ask him to say when he means to flip the puck, so that deliberate lifts can be told apart from scoops.

---

## 5. What was dropped or corrected, and open questions

### Corrected or narrowed in the fact-checks, and how this report uses them

- **"The puck outruns the blade by 1.1-1.3x in slap shots."** True of Kays's six mixed-skill shooters. Two pros on ice reach about 1.4-1.7x the blade tip's speed before ice contact. The 0.75-1.3 target applies to a recreational adult.
- **"No blade exceeds 30-32 m/s, for anyone."** Wrong for pros, whose blade tips peak at about 34-37 m/s. But that happens in the recoil around release; at puck contact the tips are at 10-17 m/s. The 30 m/s cap applies at contact, and to rigid blade speed only.
- **"No measured blade moves faster than 30 m/s."** Group means top out at about 29 m/s; single elite trials probably pass 30 (SD 4.3 m/s). The highest single value reported is 28.0 m/s (toe, wrist shot).
- **Effective mass of 0.2-0.28 kg.** Retagged [D/E]: three of the four methods used pivoted sticks with no hands, and the methods span 0.16-0.32 kg. The held-stick estimate is 0.13-0.20 kg, so the sim's 0.15 kg stays.
- **Kays's numbers.** The "18.5 m/s averaged over contact" was one shot. The blade recovers to 19.4 m/s (mean). The +3.8 mph video-over-radar offset comes from 2 shooters.
- **The recreational slap-shot bound.** 22.3 m/s came from a 260 g wired puck. Wu's mean + 2 SD is 31.1 m/s. With game pucks: Lomond 24.6 ± 1.8 m/s, Hannon 22.4 ± 6.6 m/s (35.6 m/s at + 2 SD).
- **The vertical-speed bound.** The crossbar is 1.22 m, not 1.0 m. A shot needs 5.0-6.6 m/s upward from 4-18 m, about 7 m/s from 3 m, and 9.7 m/s from 2 m. So no flat 6 m/s cap: it would block real roof shots in tight. Only a puck rising 3-10 m from range is clearly not a shot.
- **The 25 ms off-ice contact limit.** Derived from slap shots only (wired puck, polyethylene). Used here as a flag, and as a last-resort rule (change 8), not as physics.
- **Lifting the puck.** The first draft swapped top and bottom corners in Michaud-Paquette's table. Its "roll" is the heel-to-toe line's angle, not face opening. "Lifting is not carrying the puck upward" was retagged [E]. The thesis calls top-corner shots a "scoop" under the puck during contact. So lift during contact is fine; only riding the follow-through after release is targeted.
- **The recoil's share.** "At most 2-6%" became "a few percent, at most about 10%": 2.5% (rec) and 9% (elite) for a 0.17 kg puck, and 10-15% from angle-based bends.
- **"40-50% of slap-shot speed from the bend."** Traced to Roy et al. 1974 (4 junior B players, film) [S]; its method is not described. The measured energies rule it out.
- **Held-stick stiffness.** "2x too stiff" became 1.2-4.4x (0.6-2.6 kN/m), because two bench tests disagree with the formula in opposite directions.
- **Lift-off after a press.** "12-16 ms, 25% overshoot" holds only if the hands do all the damping. With the sim's flex form it is 30-38 ms (ζ 0.6) and 70-90 ms to 90% (ζ 1.5). Change 2 uses the corrected form.
- **Long presses.** Low-calibre players' strain starts 349 ± 299 ms before puck contact. "Not how real players load" became "not how skilled players load".
- **Léger's 103-107 ms wrist contact.** The paper defines no release event. Read it as "about 0.1 s of push". Michaud-Paquette's 80-290 ms is the measured wrist-shot contact used here.
- **Zane's "160 N".** The top of a colour scale, not a measurement. The flick needs 3-8 times the measured per-hand force, not 2-4.5 times.
- **Wrist-shot contact "about 100 ms" (Plesch).** An estimate [E], not a measurement.
- **Prediction and tracking.** The OpenXR 50 ms history counts back from the last pose received, not from "now". Warburton's under- and overestimation while accelerating and decelerating is the authors' reasoning [E]. Godden's 14-221 ms is detection latency. The DESP overshoot quote is Casiez's. Meta's Link blog names only the headset pose and "input state" as sent unpredicted.
- **"Jon's ordinary shots match Woo's rotation."** It crosses shot types: Woo measured slap shots only.
- **Smaller fixes used as corrected.** Drag 0.006-0.010 /m (not 0.007-0.008); Manning's exclusion is a window rule; Wu's CV 9-17%; the rec p99 of 58-65 mph is a judgement inside 55-71 mph; Robbins's rec group is "any level lower than" major junior or university, and their approach speed was not measured. Pearsall 1999's speeds are [S]. Wu's r = 0.80 is unsupported. Kays & Smith 2014's "bouncing blade" uses the same six shooters as Kays 2013.

### Rejected by this synthesis

- **Ice-friction loading**, the +5-11% trial: more launches, and the evidence for its size is a rigid-hands FE model. It stays dropped (change 6).
- **A contact-time cap**: it would cut real wrist shots (80-290 ms).
- **A 6 m/s cap on vertical speed**: roof shots in tight need 7-10 m/s.
- **Raising `blade_pop` or the blade's mass** to make pucks outrun the blade: neither is the lever, and the excess already comes from the hands and the recoil.
- **The 1€ filter on the contact velocity**: its cutoff opens with speed.
- **Pose prediction for the physics**: it made the noise and the shots worse.
- **A hand or grip gain** to undo the narrow grip: the earlier report found such gains cost precision and leave after-effects.
- **"The shot tail is pose jitter"** (the brief's guess): the fast moments are fully tracked, repeated poses are rare while the hands move (0.01% bottom hand, 1.1% top hand above 2 m/s) [D], and filtering trims the tail by only 2-12%. The tail is real motion through a short lever with no stick inertia.

### Open questions

1. **Were any of the scoops meant?** Some may have been deliberate flips. Ask Jon, and have him say "flip" in the next session.
2. **Why are the controllers only 19-25 cm apart?** Real grips are 34 cm (wrist shots) to 60-66 cm (slap shots) [M]. Is it how he holds them, or the grip fit? One session at a real grip spacing would show how much of the tail it removes, with no code. Nobody has measured hand spacing during real shots.
3. **Does skate height change the presses?** The skate-height setting in the working tree puts the ice a few cm below the floor. If some of the 19 cm presses come from standing on the "ice", press depth should fall with it. Re-run `presses.py` on a session that uses it.
4. **Off-ice contact for wrist shots, flips and saucer passes** is unmeasured. So is any launch-angle distribution for game shots.
5. **The held stick's real stiffness.** A home test would settle the spring for Jon's own stick. Clamp the handle at the two hand positions, hang about 5 kg on the blade and measure the deflection; then pluck it and count the vibrations per second.
6. **Link.** The rate and age of the controller poses that reach the PC, and whether `XrSpaceVelocity` is raw, filtered or predicted, are not published. Log the pose age, if the runtime exposes it, before the look-back A/B.
7. **Drag.** Real shots lose speed at 0.006-0.010 /m, 1.5-2.4 times the sim's `air_k` of 0.0043. Higher drag would also shave pop-up heights a little. That is a separate A/B.
8. **No adult recreational shot-speed distribution has been measured.** The shape tests borrow the NHL's.
9. **Puck spin.** Real shots spin at 14-27 rev/s and fly tilted about 21° to their path [M]. The sim has no spin (earlier report, change 19).
10. **Net hand torque.** If change 10 is ever tried, τ_max rests on squeeze forces on the shaft, not on a measured torque.
