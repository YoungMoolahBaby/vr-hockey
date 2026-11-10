"""The comfort log and queasiness check (sandbox.Comfort), the boards stopping you (GameMode.confine),
and the skating and puck settings reaching the drive and the physics."""

import numpy as np
import pytest

import grab
import puck as pk
import rig
import sandbox
import stickspec
from test_threes import _Quiet, _Said


class _Events(_Quiet):
    def __init__(self):
        self.events = []

    def event(self, t, kind, **data):
        self.events.append((kind, data))


def test_the_check_asks_and_a_b_x_answer_it(tmp_path):
    voice, log = _Said(), _Events()
    c = sandbox.Comfort(tmp_path / "rig.csv", voice, log)
    d = rig.Drive()
    dt, now = 1 / 72, 0.0

    def play(seconds):
        nonlocal now
        for _ in range(int(seconds * 72)):
            now += dt
            c.frame(now, now, dt, (0.0, 1.0, 0.0), True, d, np.array([3.0, 0.0, 0.0]), 0.0, 0.5, 1.0)
    play(61)                                            # a minute of play, with a check every minute
    assert c.asking and "Press A if you feel fine" in voice.said[-1]
    assert "Y if you need a break" in voice.said[-1]
    assert c.answer("a", now, 1.0) and not c.asking
    assert c.ratings[-1]["answer"] == "fine" and c.ratings[-1]["rating"] == 0
    assert not c.answer("a", now, 1.0)                  # not asking: A does its usual job
    play(61)
    assert not c.answer("x", now, 1.0) and c.asking   # X is a new puck, never an answer
    assert c.answer("y", now, 1.0)
    assert c.ratings[-1]["rating"] >= 4 and "take the headset off" in voice.said[-1]
    assert ("comfort", {"answer": "need a break", "rating": 5}) in log.events
    c.close()
    s = c.summary()
    assert [r["answer"] for r in s["ratings"]] == ["fine", "need a break"]
    assert s["moving_min"] > 1.9 and s["vignette_min"] > 1.9
    lines = (tmp_path / "rig.csv").read_text().splitlines()
    assert lines[0].startswith("t,lx,ly") and len(lines) > 8000


def test_an_unanswered_check_times_out():
    voice, log = _Said(), _Events()
    c = sandbox.Comfort(None, voice, log)
    d = rig.Drive()
    dt, now = 1 / 72, 0.0
    for _ in range(int(61 * 72) + int(31 * 72)):
        now += dt
        c.frame(now, now, dt, (0.0, 0.0, 0.0), True, d, np.zeros(3), 0.0, 0.0, 1.0)
    assert not c.asking and ("comfort", {"answer": None, "rating": None}) in log.events


def test_off_never_asks():
    voice = _Said()
    c = sandbox.Comfort(None, voice, _Events())
    for i in range(72 * 600):
        c.frame(i / 72, i / 72, 1 / 72, (0.0, 0.0, 0.0), True, rig.Drive(), np.zeros(3), 0.0, 0.0, 0.0)
    assert not c.asking and not voice.said


def test_the_boards_stop_a_glide_gently():
    from test_threes import _free_skate
    play, voice, mode, physics, hand, run = _free_skate(ends=())
    run(0, 50)
    zone, arena = mode.arena.zone, mode.arena
    import zone as zn
    x_wall = zn.WIDTH / 2
    toward = zone.dir_to_world(1.0, 0.0)                # +x: toward the right-hand boards
    far = zone.to_world(0.0, 0.0, arena.mid)
    v = 3.0 * toward
    assert np.allclose(mode.confine(far, v, 1 / 72), v)  # mid-ice: untouched
    near = zone.to_world(x_wall - 0.8, 0.0, arena.mid)
    out = mode.confine(near, v, 1 / 72)
    assert float(out @ toward) == pytest.approx(mode.BOARD_EASE * (0.8 - mode.BOARD_GAP), abs=1e-6)
    away = -3.0 * toward
    assert np.allclose(mode.confine(near, away, 1 / 72), away)   # skating away: untouched
    along = 3.0 * zone.dir_to_world(0.0, 1.0)
    assert np.allclose(mode.confine(near, along, 1 / 72), along)  # along the boards: untouched
    at = zone.to_world(x_wall - mode.BOARD_GAP, 0.0, arena.mid)
    assert float(mode.confine(at, v, 1 / 72) @ toward) == pytest.approx(0.0, abs=1e-6)


def test_the_settings_reach_the_drive_and_the_physics():
    spec = stickspec.from_height(1.73, "left")
    values = sandbox.Tuning.defaults(spec, grab.Fit(), pk.Params())
    sandbox.set_values(values, ["push=6", "glide=1.5", "stop=8", "carve=6", "back=0.8", "side=0.5",
                                "hands=0.45", "handle=1.25", "boards=0.4", "air=0"])
    tu = sandbox.Tuning(spec, values)
    d = rig.Drive()
    tu.drive(d)
    assert (d.push, d.glide, d.stop_ms2, d.carve, d.back, d.side) == (6, 1.5, 8, 6, 0.8, 0.5)
    play = sandbox.Play(tu)
    assert play.params.board_bounce == 0.4 and play.params.air_k == 0.0
    physics = sandbox.Physics(play, _Quiet(), _Quiet())
    assert play.sim.flex.damping == 1.25                     # stickhandling hands (trigger released)
    play.shoot = 1.0
    physics._firmness()
    assert play.sim.flex.damping == 0.45                     # shooting hands (trigger squeezed)
    with pytest.raises(SystemExit):
        sandbox.set_values(values, ["nope=1"])
    tu.i = [s.key for s in sandbox.SETTINGS].index("glide")
    values["glide"] = 0.0
    assert tu.describe() == "glide, off"


def test_the_defaults_skate_as_before_and_the_puck_as_the_research_says():
    spec = stickspec.from_height(1.73, "left")
    values = sandbox.Tuning.defaults(spec, grab.Fit(), pk.Params())
    assert values["push"] == sandbox.PUSH > 0                   # on: the old easing made Jon sick in seconds
    assert values["glide"] == sandbox.GLIDE > 0 and values["stop"] == sandbox.STOP > 0   # both felt good
    assert values["carve"] == sandbox.CARVE > 0                 # 6 felt good; 9 left him a little sick
    assert values["back"] == values["side"] == 1.0
    p = pk.Params()
    assert (p.ice_mu, p.board_bounce, p.ice_bounce, p.air_k, p.soft_hands) == (0.085, 0.30, 0.20, 0.0043, 0.0)
    assert rig.MOVE_MS == 3.0
