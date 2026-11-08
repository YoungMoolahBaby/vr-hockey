# The Python prototype

Everything runs from here (Python, OpenXR via pyopenxr, a Quest 3 on Link):
- **The Spike 0 tracking recorder:** `record.py`, with `analyze.py` reporting on a recording.
- **The free-play [sandbox](#sandbox):** your stick, a puck and a net.
- **The hockey-sense drills:** [retrieval](#drill-scan-retrieve-first-pass) and the
  [power-play point](#drill-the-power-play-point-shoot-or-set-one-up).

You hold a Quest controller in each hand (no physical stick, ever). The stick is virtual:
- **Sized from your height** (`stickspec.py`): length, lie and a curved blade.
- **Fitted once in your right (top) hand** with the thumbstick.
- **Held with the grip buttons** (the middle-finger squeeze), so either hand can hold it.

The recorder's guided session of about 4 minutes records both controllers, their grip buttons
and the headset at about 1 kHz. The sandbox and drills record the same way, plus the puck and
every event.

## The stick

| | default (5'8", left shot) | change with |
|---|---|---|
| length (heel to top of the shaft) | 0.84 x height = **57.1"** (1.45 m) | `--height`, `--stick-length` |
| lie | **5**: shaft 45 deg above the ice (each step about 2 deg more upright) | `--lie` |
| blade | 29 cm heel to toe, 7.5 cm tall, mid-toe curve 1/2" deep (P92-like), mirrored for a right shot | `--shoots` |

Sources:
- [CCM size chart](https://www.scheels.com/size-chart/ccm-hockey-sticks-size-chart): a 57" stick for 5'2"-5'10".
- [Bauer size chart](https://www.scheels.com/size-chart/bauer-hockey-sticks-size-chart): measures from the heel's contact point to the top of the shaft.
- [Lie](https://www.hockeystickman.ca/pages/hockey-stick-lie): lie 5 = 135 deg blade to shaft = 45 deg shaft to ice.
- [P92 curve](https://www.stickmeta.com/curve-compare/p88-kane/p92-matthews): a mid-toe curve with a slightly open face, about 3/8"-1/2" deep.

**Fitting it in your hand** (the first run, or `--refit`): the stick appears in your right hand.
- Right thumbstick left/right turns the blade.
- Up/down tilts the stick.
- Hold B and push left/right to swing it sideways.
- Press A to save. The fit goes to `stick_fit.json` and is reused on every run.

**Holding it** (`grab.py`). Each grab gives a short buzz.

| grips pressed | the stick |
|---|---|
| right only | rigid in your right hand, exactly as fitted |
| both | your right hand holds it and sets the blade's turn; your left hand aims the shaft (and can slide along it) |
| left only (top hand off, e.g. angling an attacker on D) | stays in your left hand exactly where it was when you let go with the right |
| none | **never dropped:** it stays in the last hand that held it, exactly where it was (drawn a little dimmer). Squeezing the right grip snaps it back into the fitted hold; squeezing the left alone takes it where it is |

## What it measures

- **held as asked**: whether the grips were pressed the way each step asks.
- **blade height**: the lowest point of the blade above the ice while stickhandling, heads-up and
  one-handed. Nothing holds the blade on the ice but your hands, so this sizes the **ice assist**:
  the report gives the band that holds the blade nine times in ten.
- **jitter**: what a game would have to smooth away (smoothing costs latency).
- **tracking**: per controller, heads-up, one-handed and mid-swing, and how it depends on where
  you look. "Tracked" means the runtime is optically tracking the controller; otherwise it is
  guessing from the motion sensors. Quest's camera-based hand tracking is not used.
- **blade and hand speeds** in shots: how many cm per frame the blade moves, and what physics
  step rate the puck sim needs.

## Setup

1. Wrist straps on. The recorder's shots want about 3 x 3 m clear; the sandbox and drills work
   standing in place.
2. Draw a room-scale boundary. Its floor becomes the virtual ice.
3. Use a Link cable if you have one.
4. A voice guides you through the default Windows audio device. Set the headset (Oculus Virtual
   Audio Device) as default, or keep the PC speakers loud enough to hear.

## Run

```powershell
cd C:\dev\vr-hockey\prototype
uv run python xrcheck.py          # runtime, extensions, and whether the headset is connected
uv run python record.py --notes "Quest 3, cable Link"
```

**Three low beeps = get ready, high beep = go, two falling beeps = stop.** In the headset you see:
- the ice as a grid, green while a step records
- each controller's axes, with a green cross while that hand grips
- the stick: a white shaft and a yellow blade outline

| step | time | what you do |
|---|---|---|
| fit | until you press A | first run or `--refit`: turn and tilt the stick in your right hand until it feels right |
| stickhandle | 30 s | both grips; look at the blade and keep it on the ice, slow then fast |
| heads_up | 30 s | same, looking straight ahead |
| one_hand | 30 s | top hand off: play the stick with your left hand only, like angling an attacker to your left |
| wrist_shots | 40 s | six full-speed wrist shots, both hands |
| slap_shots | 40 s | five full-speed slap shots (`--no-slap` skips them) |

Ctrl+C stops early and keeps what was recorded. `--only stickhandle one_hand` runs only some steps.

Then:

```powershell
uv run python analyze.py data\<timestamp>
```

This writes `data\<timestamp>\report\report.md`, `summary.json` and two plots. Or just tell
Claude the folder name.

## Sandbox

```powershell
uv run python sandbox.py
uv run python sandbox.py --fresh      # start from the defaults, not your saved settings
```

Your stick, a puck and a net, laid out in front of you. Play, and tune everything as you go.

**Controls:**
- **Grip buttons:** hold the stick (as above).
- **Left stick left/right:** pick a setting. The voice says which, and its value.
- **Left stick up/down:** change it (hold to keep changing).
- **X:** a new puck, on your blade.
- **Y:** fit the stick in your hand. The right stick turns and tilts it; hold B and push to swing
  it; A saves the fit; Y again leaves without saving.
- **Hold the left stick in (1 s):** put the net straight in front of you again.
- **B:** say the current setting again.
- **A:** save the settings (`sandbox_settings.json`, used by the drills too).

**Settings:**
- stick length, lie, curve depth, face open, flex
- forgiveness (extra reach for catching the puck)
- puck weight, ice friction
- blade pop, blade grip
- buzz strength

**What you hear and feel:**
- **Sounds:** a tap when the blade lands, a dull "thock" off the puck, a ping off the posts, a
  thud off the boards. Every contact gets its own sound, from the contact bus (`contacts.py`),
  mixed (`audio.py`) straight to the headset's Link audio.
  - About 23 ms after the contact, the same every time.
  - Up to 16 at once, 5 variants of each, and louder for harder hits.
  - `--audio-device` picks another output; with no device it falls back to winsound.
- **Buzz:** every puck contact buzzes the hands holding the stick, harder hits for longer.

The voice calls each shot's speed in mph.

## Drill: scan, retrieve, first pass

```powershell
uv run python drill.py
```

**Setup:** face a clear direction in your play space; that becomes the end boards. Put your blade on
the ice and press A. The zone is laid out so your blade sits at the end boards, just left of our net.

**Each rep:**
1. A puck is dumped in down the far wall and rims around toward you from your left.
   - **Rim assist:** boards in VR have no feel, so as the puck leaves the corner it is steered gently
     off the boards to where your blade is (at most 1 m out), as if it had kicked off the corner.
2. F1 commits about 1.5 s before it reaches you. He comes down your wall, chases the puck around
   the net, or comes down the middle. F2 takes away one of your three outs:
   - up the wall to your winger
   - a reverse behind the net to your D partner
   - up the middle to your center
3. Only a shoulder check after F1 commits shows which out is open. Pass to it with your stick.

**After each rep:**
- **The voice gives:** the result, the open out, and whether you checked (none, or too early).
- **A green line on the ice:** the best pass.
- **A map at waist height:** green is the best pass, white is the puck's path, orange is where the
  forecheckers went.

**Scoring and difficulty:**
- Every out is scored by time to intercept: could a forechecker get a stick on the lane, or reach
  the receiver, before the puck?
- **Valued for your passing:** every out is valued at your own pass speed and your own time from
  control to release. These are medians of your last 20 passes, ignoring fans and glitches.
- Each out is the best one equally often.
- **F1's head start adapts** toward about 75% success.
- **Warm-up:** the first 5 reps of each session don't move the difficulty.
- **Saved between sessions:** both the head start and your passing (`drill_state.json`).
- **Reps start only while you grip the stick** and the drill is in front in the headset. A let-go
  stick stays in your hand, but that doesn't count as playing.

**Controls:**
- **A:** next rep now
- **B:** repeat the result
- **X:** skip the rep
- **Hold the left stick in (1 s):** lay the zone out again

The grips, Y fitting and left-stick tuning work as in the sandbox.

## Drill: the power-play point (shoot, or set one up)

```powershell
uv run python drill.py --drill pp
```

**Setup:** face where you want the net and press A. Your blade becomes the left point.

**Each rep:**
1. Your winger on the left half wall passes the puck up to you.
2. While it travels, the penalty-kill box commits:
   - **F1** pressures you, which closes your shooting lane but opens the seam. Or he shades the
     seam, which leaves your lane open.
   - **F2** takes away D-to-D, or drops into the seam.
   - **D1** boxes out your screen, standing in your lane. Or he plays beside your screen.
   - **D2** steps up on your seam shooter, or stays home.
3. Pick your play:
   - **Shoot:** your own shot, through the screen.
   - **D-to-D:** your partner's one-timer from the right point.
   - **The seam:** a hard pass across the box to your shooter in the far circle.

**The goalie** (`goalie.py`) is a rec goalie:
- He plays his angle and follows the puck a beat late.
- A screen means he picks up a shot only about 9 m out.
- He slides across on passes and makes saves in the butterfly. His reach has a soft edge, so it's
  never quite all or nothing.

**Scoring and difficulty:**
- Every play is valued in expected goals with that same goalie: can the pass get there, can the
  shot get through the box, and does it beat him?
- Goals are real. Your actual shot, or your teammate's one-timer, has to beat the goalie and get
  into the net.
- **Learns you:** your power-play pass speed and shot speed are learned separately from the
  retrieval drill's.
- **Pressure** is how soon F1 reaches you. It adapts, with the same warm-up.
- **The map** shows each play's goal chance as a bar; green is the best.

## Findings so far

Run 1 (2026-11-07, Quest 3 on cable Link):
- Controller tracking held 100% heads-up and through every wrist and slap shot.
- Jitter was about 0.5-1 mm.
- The runtime gives a fresh pose on about 900 of every 1000 queries.
- It also freezes a controller's pose a few seconds after it is set down, so a "controllers lying
  still" noise test doesn't work.

That run (and the cancelled run 2) used an earlier stick fitted to a still stance. It was rejected
on feel: the blade's rotation was off. So the analysis gives those recordings a tracking-only report.

**Sandbox:** 5 sessions on 2026-11-07, tuned live. Each fix answered what Jon felt:
- A real blade curve.
- Shaft flex "with forgiveness like golf clubs".
- Ice sounds ("way better with the sounds").
- The blade kept on top of the ice.
- Consistent grips.
- No more exploding puck: the ice no longer loads the flex.
- "A rubber heavy puck against a light flexible composite stick" instead of an air-hockey puck.

**Retrieval drill:**

| | reps | success | good reads | note |
|---|---|---|---|---|
| Session 1 | 57 | 31% | 46% | Most misses were rims along the boards that never touched the blade. The winger stood off the wall. |
| Session 2 | 118 | 59% | 71% | After the fixes: rim assist, winger on the wall, his own pass speed, warm-up. The free time reached 1.35 s. |

**Power-play drill, session 1:** 138 reps, 0 goals.
- 20% of incoming passes not controlled.
- 8 of 17 shots wide.
- All 6 seam passes picked off.

Next: tuning, after the feel research (`../reports/`).

**Physics rate:** the 1 kHz physics shares Python's GIL with drawing and building reps.
- Session 1: 902/s.
- Session 2: 752/s, after a too-short GIL switch interval (reverted).
- Power-play session: about 920/s.
- Off the headset, a contention harness measures 999/s.
- **Since the compiled physics** (`physics_core.py`, numba with nogil):
  - A tick costs 144 us instead of 549.
  - 60 s of real play gives the same 222 touches and identical puck paths.
  - The harness, with drawing, rep building and the headset audio stream all running, holds
    1000/s with 0 audio underruns.

## Files

| file | what |
|---|---|
| `record.py` | OpenXR recorder (pyopenxr + OpenGL). A sampler thread locates both controllers and the head at a fixed rate; the main thread reads the inputs, runs the grab rules and renders; a protocol thread runs the voice and steps |
| `stickspec.py` | the stick sized from height, lie and shot side |
| `grab.py` | the fit in the hand and the grab rules, live (one sample) and replayed (whole recording) |
| `analyze.py` | replays the grips, then metrics, verdict, `report.md`, plots |
| `protocol.py` | the steps and what the voice says |
| `recfmt.py` | the `rec.csv` / `meta.json` format |
| `synth.py` | synthetic recordings with known truth (noise, drift, dropouts, 500 Hz updates, top hand off) |
| `xrcheck.py` | runtime and headset check |
| `sandbox.py` | free play: the stick, a puck and a net, with settings tuned in the headset; its physics tick, drawing and frame loop are reused by the drills |
| `puck.py` | the puck, the blade contact, the shaft flex, the ice (the Python reference; `FAST` runs it compiled) |
| `physics_core.py` | the same physics compiled with numba (nogil): what the app runs; tested against `puck.py` to 1e-9 |
| `contacts.py` | the contact bus: every contact from the 1 kHz physics, which the sound and the buzz play from |
| `audio.py` | the mixer: a low-latency stream to the headset, each contact placed at its own sample |
| `sounds.py` | the synthesized sounds (tap, thock, ping, thud, go, whistle) |
| `stickmath.py` | rotations and quaternions |
| `replay.py`, `touches.py` | replay a recorded session's hands through the physics; measure every blade-puck touch (does the puck leave faster than the blade?) |
| `drill.py` | the drill app (a sandbox mode): lays out the zone, runs reps, draws the skaters and the after-rep map |
| `retrieval.py` | module 1's logic, without XR: scenarios, the time-to-intercept value model, forecheckers, shoulder-check tracking, scoring, the staircase |
| `zone.py` | the defensive zone: regulation boards with rounded corners (rims), our net, markings |
| `figures.py` | line-drawn skaters and the goalie |
| `powerplay.py` | the power-play drill's logic: the box's reads, expected goals per play, the rep with real shots and one-timers |
| `goalie.py` | a rec goalie: angle, screens, saves, and expected goals from the same model |
| `tests/` | `uv run pytest`. They cover: the grab rules, exact and live = replay; the analysis recovering the synthetic truth; the puck physics; the zone (rims, our net); both drills driven by a bot; the goalie and expected goals; the skater drawing |
