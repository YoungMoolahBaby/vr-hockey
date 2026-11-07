# Spike 0: a virtual stick held with the controllers. Tracking, blade control, speed

You hold a Quest controller in each hand (no physical stick). The stick is virtual:
- **Sized from your height** (`stickspec.py`): length, lie and a curved blade.
- **Fitted once in your right (top) hand** with the thumbstick.
- **Held with the grip buttons** (the middle-finger squeeze), so either hand can hold it.

A guided session of about 4 minutes records both controllers, their grip buttons and the
headset at about 1 kHz.

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

1. Wrist straps on. Clear about 3 x 3 m (shots swing wide).
2. Draw a room-scale boundary. Its floor becomes the virtual ice.
3. Use a Link cable if you have one.
4. A voice guides you through the default Windows audio device. Set the headset (Oculus Virtual
   Audio Device) as default, or keep the PC speakers loud enough to hear.

## Run

```powershell
cd C:\dev\vr-hockey\spike0
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

## Findings so far

Run 1 (2026-11-07, Quest 3 on cable Link):
- Controller tracking held 100% heads-up and through every wrist and slap shot.
- Jitter was about 0.5-1 mm.
- The runtime gives a fresh pose on about 900 of every 1000 queries.
- It also freezes a controller's pose a few seconds after it is set down, so a "controllers lying
  still" noise test doesn't work.

That run (and the cancelled run 2) used an earlier stick fitted to a still stance. It was rejected
on feel: the blade's rotation was off. So the analysis gives those recordings a tracking-only report.

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
| `puck.py` | the puck, the blade contact, the shaft flex, the ice |
| `drill.py` | the drill app (a sandbox mode): lays out the zone, runs reps, draws the skaters and the after-rep map |
| `retrieval.py` | module 1's logic, without XR: scenarios, the time-to-intercept value model, forecheckers, shoulder-check tracking, scoring, the staircase |
| `zone.py` | the defensive zone: regulation boards with rounded corners (rims), our net, markings |
| `figures.py` | line-drawn skaters |
| `tests/` | `uv run pytest`: sizing, the grab rules exact and live = replay, and the analysis recovers the synthetic truth |
