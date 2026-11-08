"""The power-play point drill, driven by a bot instead of the headset."""

import json

import numpy as np
import pytest

import goalie as gl
import powerplay as pp
import puck as pk
import sandbox
import zone as zn

HEAD = pp.JON_BLADE + np.array([-0.3, 1.0])


def make(rng, want=None, free=2.0, shot=20.0, pass_speed=12.0):
    return pp.make_scenario(rng, free_time=free, blade=pp.JON_BLADE, head=HEAD, ice_mu=0.05, want=want,
                            pass_speed=pass_speed, shot_speed=shot, decide_s=1.0)


def play(sc, do, hold_s=0.6, shot_speed=20.0, pass_speed=12.0, seed=0, never=False):
    """A bot on the point: stops the winger's pass dead, waits hold_s, then does `do`
    ("shoot": at the model's aim point; "partner" / "seam": a pass to that man)."""
    zone = zn.Zone(np.zeros(3), np.array([0.0, 0.0, 1.0]))
    puck = zn.ZonePuck(pk.Params(ice_mu=0.05), zone)
    rep = pp.Rep(sc, puck, rng=np.random.default_rng(seed))
    blade = pp.JON_BLADE
    caught = done = None
    t = 0.0
    while rep.state != "done" and t < 25:
        t += 0.001
        tau = t - rep.go_at
        pxz = zone.xz(puck.pos)
        if rep.state == "live" and caught is None and np.linalg.norm(pxz - blade) < 0.3:
            puck.vel = np.zeros(3)
            caught = tau
        if rep.state == "control" and not never and done is None and tau > caught + hold_s:
            if do == "shoot":                                    # aimed like a rec shooter: it misses a bit
                _, aim = gl.shot_xg(pxz, shot_speed, rep.goalie.c, rep.goalie.sees)
                v = gl.launch(pxz, gl.aimed(np.random.default_rng(seed + 99), aim, pxz), shot_speed)
                puck.vel = zone.dir_to_world(v[0], v[2]) + np.array([0.0, v[1], 0.0])
            else:
                to = sc.mates[pp.RECEIVER[do]] - pxz
                puck.vel = zone.dir_to_world(*(pass_speed * to / np.linalg.norm(to)))
            done = tau
        puck.step(0.001)
        rep.update(t, blade, (HEAD, np.array([0.3, -1.0])))
        for item in rep.outbox:
            if item[0] == "log":
                json.dumps(item[2], default=sandbox._plain)
        rep.outbox.clear()
    return rep


def test_the_goalie_plays_his_angle_and_loses_a_screened_puck():
    pt = np.array([-8.3, 20.5])
    c = gl.home(pt)
    assert abs(np.linalg.norm(c - gl.NET_C) - gl.DEPTH) < 1e-9
    assert np.allclose(gl.unit(c - gl.NET_C), gl.unit(pt - gl.NET_C))
    screen = gl.NET_C + 0.4 * (pt - gl.NET_C)                  # someone on the line
    assert gl.blocks_sight(c, pt, [screen]) and not gl.blocks_sight(c, pt, [screen + np.array([1.0, 0.0])])


def test_xg_is_higher_for_harder_closer_and_screened_shots_and_an_open_net():
    pt = np.array([-8.3, 20.5])
    c = gl.home(pt)
    soft = gl.shot_xg(pt, 15, c, False)[0]
    hard = gl.shot_xg(pt, 25, c, False)[0]
    seen = gl.shot_xg(pt, 25, c, True)[0]
    assert soft < hard and seen < hard
    slot = gl.shot_xg(np.array([0.0, 11.0]), 18, gl.home([0.0, 11.0]), True)[0]
    assert slot > seen
    open_net = gl.shot_xg(np.array([4.0, 6.0]), 16, gl.home(pt), True)[0]   # goalie still on the far side
    assert open_net > 0.5


def test_a_shot_into_his_body_is_saved_and_one_past_him_goes_in():
    rng = np.random.default_rng(0)
    saves = goals = 0
    for aim, want in (((0.0, 0.5), "save"), ((0.8, 1.05), "goal")):
        for _ in range(20):
            zone = zn.Zone(np.zeros(3), np.array([0.0, 0.0, 1.0]))
            p = zn.ZonePuck(pk.Params(ice_mu=0.05), zone)
            g = gl.Goalie((0.0, 8.0))
            origin = np.array([0.0, 8.0])
            for _ in range(300):                                 # he settles on his angle
                g.step(0.0, 0.01, origin, np.zeros(2), [])
            v = gl.launch(origin, aim, 30.0)
            p.place(*origin)
            p.vel = zone.dir_to_world(v[0], v[2]) + np.array([0.0, v[1], 0.0])
            out = None
            for i in range(600):
                p.step(0.001)
                xz = zone.xz(p.pos)
                if i % 10 == 0:
                    g.step(i * 0.001, 0.01, xz, zone.dir_to_zone(p.vel), [])
                if g.check(xz, float(p.pos[1]), rng) == "save":
                    out = "save"
                    break
                if p.in_net:
                    out = "goal"
                    break
            saves += out == "save" and want == "save"
            goals += out == "goal" and want == "goal"
    assert saves >= 18 and goals >= 15, (saves, goals)


def test_each_out_is_made_best_on_request():
    rng = np.random.default_rng(5)
    for want in pp.OPTIONS * 3:
        sc = make(rng, want=want)
        v = sorted(sc.values.values(), reverse=True)
        assert sc.best == want and v[0] >= 1.6 * v[1], (want, sc.values, sc.behaviours)


def test_the_best_out_scores_more_than_the_others():
    """The value model and the simulated rep agree: playing the best out scores more."""
    rng = np.random.default_rng(12)
    best_goals = other_goals = 0
    best_x = other_x = 0.0
    for i, want in enumerate(pp.OPTIONS * 14):
        sc = make(rng, want=want)
        other = [o for o in pp.OPTIONS if o != want][i % 2]
        best_goals += play(sc, want, seed=i).result["outcome"] == "goal"
        other_goals += play(sc, other, seed=i).result["outcome"] == "goal"
        best_x += sc.values[want]
        other_x += sc.values[other]
    assert best_x > 2 * other_x
    assert best_goals > other_goals, (best_goals, other_goals, best_x, other_x)


def test_holding_on_under_pressure_gets_you_stripped():
    sc = make(np.random.default_rng(3), want="seam", free=1.0)
    assert sc.behaviours["F1"] == "pressure"
    rep = play(sc, None, never=True)
    assert rep.result["outcome"] == "caught" and rep.result["by"] == "F1"


def test_you_learn_your_power_play_passes_and_shots_apart(tmp_path):
    you = pp.You()
    assert you.pass_speed == pp.PASS_SPEED and you.shot_speed == pp.SHOT_SPEED
    for v in (14.0, 12.0, 13.0):
        you.add({"choice": "seam", "release_speed": v, "latency": 0.8})
    for v in (24.0, 26.0, 22.0):
        you.add({"choice": "shoot", "release_speed": v, "latency": 0.5})
    assert you.pass_speed == 13.0 and you.shot_speed == 24.0
    import retrieval as rt
    rt.Staircase().save(tmp_path / "s.json", you_pp=you.to_dict())
    again = pp.You.load(tmp_path / "s.json")
    assert again.shots == [24.0, 26.0, 22.0] and again.speeds == [14.0, 12.0, 13.0]
