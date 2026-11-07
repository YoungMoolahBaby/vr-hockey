# vr-hockey

A VR hockey trainer whose stick and puck physics feel right, aiming past Sense Arena on
puck feel. Sense Arena trains reading the play well, but its virtual puck control draws
the complaints: the puck slips under the stick, contact registers on the wrong side, and the
stick has to be recalibrated to stay on the ice.

**You hold two controllers, never a physical stick.** The stick is virtual and built from both
hands. The bet is that the hard part is not the physics engine but four VR problems at the blade:

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
| **0: tracking** ([spike0/](spike0/)) | With a controller in each hand, which virtual stick model keeps the blade steadiest, how much do the controllers drop out heads-up and mid-swing, how fast does the blade move? | recorder + analysis built and tested on synthetic data; needs a real session |
| 1: puck sim | A 3D puck plus a physics stick on the ice, with 1 to 2 kHz substeps, swept collision, friction and flex, replaying swings recorded in Spike 0 on the desktop. Rust. | not started |
| 2: in the headset | Spike 1 live in Bevy + OpenXR (the bigmark222/bevy `multiview-xr` fork has an OpenXR proof of concept). | not started |

Spike 0 decides the stick model, how much the game must steady and hold the blade, and how
fast Spike 1 has to step.
