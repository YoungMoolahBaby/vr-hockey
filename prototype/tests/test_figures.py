"""Line-drawn skaters: the batched drawing matches segment-by-segment, and he faces the right way."""

import numpy as np

import figures
import sandbox
import zone as zn


def test_batched_and_one_by_one_drawing_agree():
    zone = zn.Zone.placed((3.0, 0.15), np.array([0.3, 0.0, -0.8]), np.array([0.6, 0.0, -0.8]), (0.0, -1.0))
    batched = sandbox.Lines()
    figures.skater(batched, zone, (5.0, 9.0), (0.3, -1.0), figures.THEM, "R", stride=2.3, speed=5.0)
    segs = []
    figures.skater(lambda a, b, c: segs.append((*a, *c, *b, *c)), zone, (5.0, 9.0), (0.3, -1.0), figures.THEM,
                   "R", stride=2.3, speed=5.0)
    one = np.array(segs, dtype=np.float32).reshape(-1, 6)
    assert np.allclose(batched.array(), one, atol=1e-5)


def test_a_left_shot_facing_up_ice_has_his_blade_ahead_and_on_his_left():
    zone = zn.Zone(np.zeros(3), np.array([0.0, 0.0, 1.0]))
    lines = sandbox.Lines()
    figures.skater(lines, zone, (0.0, 0.0), (0.0, 1.0), figures.US, "L", ring=False)
    pts = lines.array()[:, :3]
    low = pts[pts[:, 1] < 0.03]                                  # skate blades and the stick blade
    blade = low[low[:, 2] > 0.8]                                 # the one well out in front
    assert len(blade) and np.all(blade[:, 0] > 0)                # zone +x is his left facing up ice
    assert pts[:, 1].max() > 1.7 and pts[:, 1].min() >= 0.0      # head up top, nothing under the ice
