# Spike 0: two controllers as a virtual stick, how steady is the blade?

You hold a Quest controller in each hand, the way you hold your stick (no physical stick).
A guided session of about 4 minutes records both controllers and the headset at about 1 kHz.
The analysis builds the virtual stick four ways from the same data and measures each at the
blade (where the puck is):

| stick model | how the stick follows the hands |
|---|---|
| `two_hand` | the shaft runs through both grips (moving the bottom hand tilts the stick) |
| `top_hand` | the stick is fixed in the top hand (the wrist steers it) |
| `bottom_hand` | the stick is fixed in the bottom hand |
| `blend` | the average of the two_hand and top_hand directions |

What it measures:
- **blade noise at rest**: each controller's jitter while lying still, carried onto your stance
  and through each stick model. Pure tracking noise at the blade.
- **holding still**: the blade in your stance, held still. Tracking plus real hand tremor.
- **jitter while stickhandling**: what a game would have to smooth away (smoothing costs latency).
- **blade near the ice**: nothing physical holds the blade down, so this shows how much the game
  must help keep it on the ice.
- **tracking loss**: per controller, heads-up and mid-swing, and how it depends on where you look.
  Here "tracked" means the runtime is optically tracking the controller; the alternative is
  guessing from its motion sensors (IMU). Quest's camera-based hand tracking is not used.
- **peak blade and hand speeds**: how many cm per frame the blade moves, and what physics step
  rate the puck sim needs.

It ends with a **GO / MARGINAL / NO-GO** for controller tracking and for each stick model, plus
a recommended model.

## Setup

1. Wrist straps on. Clear about 3 x 3 m (shots swing wide).
2. Draw a room-scale boundary. Its floor becomes the virtual ice.
3. Use a Link cable if you have one. Tracking runs on the headset either way, but Air Link adds
   Wi-Fi jitter to when the PC gets poses; measure that separately if you play on Air Link.
4. A voice guides you through the default Windows audio device. Set the headset (Oculus Virtual
   Audio Device) as default, or keep the PC speakers loud enough to hear.

## Run

```powershell
cd C:\dev\vr-hockey\spike0
uv run python xrcheck.py          # runtime, extensions, and whether the headset is connected
uv run python record.py --notes "Quest 3, cable Link"
```

The voice explains each step. **Three low beeps = get ready, high beep = go, two falling beeps
= stop.** In the headset you see the ice as a grid (green while a step records) and each
controller's axes. After the stance, the virtual stick appears in white with its blade in yellow.

| step | time | what you do |
|---|---|---|
| stance | 10 s | hold the controllers like your stick, in your stance, blade on the ice, still. No stick is shown yet: the stick is fitted to this (redone if it looks off) |
| rest | 15 s | put both controllers down on a table or chair, still, and look at them |
| stickhandle | 30 s | stickhandle looking at the blade, keeping it on the ice, slow then fast |
| heads_up | 30 s | stickhandle looking straight ahead |
| wrist_shots | 40 s | six full-speed wrist shots |
| slap_shots | 40 s | five full-speed slap shots (`--no-slap` skips them) |

Options:
- `--shoots left` puts the right hand on top. By default the higher hand in the stance is the top.
- `--stick-length 1.45` fixes the stick length (top grip to heel). By default it is fitted to your stance.
- `--show-model top_hand` changes which model the headset shows. You steer the one you see, so
  that model gets an edge on "blade near the ice"; the other measures are fair to all four.
- Ctrl+C stops early and keeps what was recorded. `--only stance stickhandle` runs only some steps.

Then:

```powershell
uv run python analyze.py data\<timestamp>
```

This writes `data\<timestamp>\report\report.md`, `summary.json` and three plots. Or just tell
Claude the folder name.

## Worth trying after the first run

- `--show-model top_hand` or `blend`, to feel and fairly judge another stick model.
- `--lag-ms 20` queries poses 20 ms in the past. The runtime's history may be smoother than
  its "now", which is usually extrapolated. If it is much better, the game can trade 20 ms of
  latency for a steadier blade.
- Cable vs Air Link.

## Files

| file | what |
|---|---|
| `record.py` | OpenXR recorder (pyopenxr + OpenGL). A sampler thread locates both controllers and the head at a fixed rate; the main thread renders the ice and stick; a protocol thread runs the voice and steps |
| `analyze.py` | metrics, verdicts, `report.md`, plots |
| `stickmath.py` | the stance fit and the four stick models (positions and velocities) |
| `protocol.py` | the steps and what the voice says |
| `recfmt.py` | the `rec.csv` / `meta.json` format |
| `synth.py` | synthetic recordings with known truth (noise, drift, dropouts, 500 Hz updates, a sliding and wobbling bottom hand) |
| `xrcheck.py` | runtime and headset check |
| `tests/` | `uv run pytest`: model maths exact, velocities match numerical derivatives, and the analysis recovers the synthetic truth |

The thresholds behind the verdicts are my heuristics, sized against the puck (25 mm tall,
76 mm wide). They are in `analyze.py` (`THRESHOLDS`) and printed at the end of every report.
