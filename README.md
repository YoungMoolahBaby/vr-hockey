# vr-hockey

A VR hockey trainer whose stick and puck physics feel right, aiming past Sense Arena on
puck feel. Sense Arena trains reading the play well, but its virtual puck control draws
the complaints: the puck slips under the stick, contact registers on the wrong side, and the
stick has to be recalibrated to stay on the ice.

**You hold two controllers, never a physical stick.** The stick is virtual:
- **sized from your height:** length, lie and curve
- **fitted once in your top hand**
- **held with the grip buttons:** either hand can hold it alone, like taking the top hand off on D

The bet is that the hard part is not the physics engine but four VR problems at the blade:

1. **Tracking at the blade.** The blade is about 1.4 m from the top hand. Small hand errors grow on
   the way down the shaft: about 2.5x if the shaft runs through both hands 55 cm apart, or
   1 degree of wrist error = 2.4 cm at the blade if the stick is fixed in the top hand. The puck
   is 2.5 cm tall and 7.6 cm wide.
2. **Speed against frame rate.** A shot moves the blade about 15 to 25 m/s, which is 16 to 28 cm
   per 90 Hz frame. Contact lasts only a few frames, so the stick-puck simulation needs about
   1 to 2 kHz steps, with swept collision and poses interpolated between frames.
3. **What simple models skip.** Stick flex (the whip), friction so the blade can cup and drag
   the puck, and a full 3D puck that rolls on its edge, flips and wobbles.
4. **Nothing holds the blade on the ice.** With no stick or floor contact, the game has to keep
   the blade on the ice: a physics stick that slides on the ice, pulled toward the hands by
   springs, with sharp contact haptics in the controllers.

## Spikes

| spike | question | status |
|---|---|---|
| **0: tracking** ([spike0/](spike0/)) | Holding the virtual stick with the grip buttons: how well do the controllers track (heads-up, one-handed, mid-swing), how well does the blade stay on the ice (sizes the assist), how fast does it move? | run 1: tracking 100%, jitter about 1 mm; the stick reworked to height-sized + in-hand fit + grip buttons; next: a run with the new stick |
| 1: puck sim | A 3D puck plus a physics stick on the ice, with 1 to 2 kHz substeps, swept collision, friction and flex, replaying swings recorded in Spike 0 on the desktop. Includes the **ice assist** (below), tuned on those recordings. Rust. | not started |
| 2: in the headset | Spike 1 live in Bevy + OpenXR (the bigmark222/bevy `multiview-xr` fork has an OpenXR proof of concept). | not started |

Spike 0 decides the stick model, how much the game must steady and hold the blade, and how
fast Spike 1 has to step.

## Ice assist (wanted)

With no floor under the blade, the game helps keep it on the ice. The ice works like a floor,
not a magnet:

- **Floor (always on):** the blade can't go below the ice. It slides on it, and the spring
  between the hands and the stick takes up the difference.
- **Snap (a dial):** when the blade is within a few cm of the ice and moving sideways, it eases
  down onto the ice. The pull fades with height.
- **Let go:** a deliberate lift (the hands rising quickly, or the blade above the snap zone)
  turns the snap off. Some hysteresis stops it flickering on and off. Saucers, lifts, shots and
  batting the puck stay free.
- **Feel:** a controller buzz that grows the harder you push into the ice, standing in for the
  floor.

To tune it: Spike 0's blade-height spread while stickhandling sizes the snap zone. Spike 1
replays the recorded stickhandling through the assist to set the strength. Both are exposed
as dials to tune in the headset.
