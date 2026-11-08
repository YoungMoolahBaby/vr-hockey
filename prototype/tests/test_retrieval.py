"""Module 1 (scan, retrieve, first pass), driven by a bot instead of the headset."""

import inspect
import json
import math

import numpy as np
import pytest

import puck as pk
import retrieval as rt
import sandbox
import zone as zn

HEAD = np.array([3.35, 1.32])


def make(rng, want=None, free=1.5, gap=0.25):
    return rt.make_scenario(rng, free_time=free, blade=rt.JON_BLADE, head=HEAD, ice_mu=0.05,
                            board_bounce=0.55, want=want, min_gap=gap)


def play(sc, choose, look=True, look_at=None, hold_s=0.3, pass_speed=11.0, never_pass=False):
    """A bot behind the net: watches the puck come, checks his shoulder, stops the puck dead on
    his blade, then passes to choose(rep) after hold_s. Returns the rep."""
    zone = zn.Zone(np.zeros(3), np.array([0.0, 0.0, 1.0]))
    puck = zn.ZonePuck(pk.Params(ice_mu=0.05, board_bounce=0.55), zone)
    rep = rt.Rep(sc, puck)
    blade = rt.JON_BLADE
    look_at = sc.t_commit + 0.3 if look_at is None else look_at
    caught_at = passed = None
    t = 0.0
    while rep.state != "done" and t < 20:
        t += 0.001
        tau = t - rep.go_at
        pxz = zone.xz(puck.pos)
        if look and look_at <= tau < look_at + 0.4:          # a shoulder check: up ice, behind him
            fwd = np.array([-0.3, 1.0])
        else:
            fwd = pxz - HEAD
        if rep.state == "live" and caught_at is None and np.linalg.norm(pxz - blade) < 0.3:
            puck.vel = np.zeros(3)                            # soft hands
            caught_at = tau
        if rep.state == "control" and not never_pass and passed is None and tau > caught_at + hold_s:
            to = sc.mates[rt.RECEIVER[choose(rep)]] - pxz
            puck.vel = zone.dir_to_world(*(pass_speed * to / np.linalg.norm(to)))
            passed = tau
        puck.step(0.001)
        rep.update(t, blade, (HEAD, fwd))
        drain(t, rep)
    return rep


def drain(t, rep):
    """What the app does with the outbox: the log calls must fit sandbox.Log.event and be json."""
    for item in rep.outbox:
        if item[0] == "log":
            fake_event(t, item[1], **item[2])
            json.dumps(item[2], default=sandbox._plain)
        else:
            assert item[0] in ("say", "sound", "buzz"), item
    rep.outbox.clear()


def fake_event(t: float, kind: str, **data) -> None:
    """sandbox.Log.event's signature, without the file."""
    assert list(inspect.signature(sandbox.Log.event).parameters)[:3] == ["self", "t", "kind"]


def test_an_opponent_on_the_lane_closes_it_and_our_net_blocks_it():
    p0, target = np.array([0.0, 5.0]), np.array([10.0, 5.0])
    open_v = rt.option_value(p0, target, [(np.array([5.0, 12.0]), np.zeros(2))], pass_speed=10.0)
    shut_v = rt.option_value(p0, target, [(np.array([5.0, 5.5]), np.zeros(2))], pass_speed=10.0)
    assert open_v[0] > 0.8 and open_v[1] > 0.2
    assert shut_v[0] < 0.1 and shut_v[1] < 0
    behind = rt.option_value(np.array([0.0, 6.0]), np.array([0.0, 0.5]), [])   # straight through our net
    assert behind[0] == 0.0
    a, b = np.array([0.0, 4.5]), np.array([0.0, 1.0])                          # in front of it, to behind it
    assert rt.skate_dist(a, b) > np.linalg.norm(b - a) + 0.8


def test_time_to_cover_accelerates_then_cruises():
    assert rt.time_to_cover(0.0) == 0.0
    assert rt.time_to_cover(2.5) == pytest.approx(1.0)               # 2.5 = a t^2 / 2 at 5 m/s^2
    long = rt.time_to_cover(20.0)
    assert long == pytest.approx(rt.VMAX / rt.ACCEL + (20 - rt.VMAX ** 2 / (2 * rt.ACCEL)) / rt.VMAX)
    assert rt.time_to_cover(5.0, v0=7.0) == pytest.approx(5.0 / 7.0)


@pytest.mark.parametrize("z_launch,v_arrive", [(9.0, 3.5), (12.0, 4.5), (14.0, 5.0)])
def test_the_dump_in_reaches_you_about_when_and_how_fast_planned(z_launch, v_arrive):
    v0, t_est = rt.rim_launch(z_launch, rt.JON_BLADE[0], v_arrive, 0.05, rt.corner_keep(0.55))
    zone = zn.Zone(np.zeros(3), np.array([0.0, 0.0, 1.0]))
    p = zn.ZonePuck(pk.Params(ice_mu=0.05, board_bounce=0.55), zone)
    p.place(-(zn.WIDTH / 2) + pk.R, z_launch, 0.0, -v0)
    t = 0.0
    while zone.xz(p.pos)[0] < rt.JON_BLADE[0] and t < 10:
        p.step(0.001)
        t += 0.001
    assert p.speed == pytest.approx(v_arrive, abs=0.6)
    assert t == pytest.approx(t_est, abs=0.4)
    assert zone.xz(p.pos)[1] < 0.15                                   # along the end boards, at your blade


def test_each_out_is_made_best_on_request_with_a_clear_gap():
    rng = np.random.default_rng(11)
    for want in rt.OPTIONS * 3:
        sc = make(rng, want=want)
        v = sorted(sc.values.values(), reverse=True)
        assert sc.best == want and v[0] - v[1] >= 0.25 and v[0] > 0.5


def test_f1_commits_before_the_puck_arrives_and_arrives_on_the_free_time():
    rng = np.random.default_rng(4)
    for free in (2.0, 1.0, 0.6):
        sc = make(rng, free=free)
        assert 0.8 < sc.t_arrive - sc.t_commit < 2.2
        assert sc.f1.t_end == pytest.approx(sc.t_arrive + free, abs=1e-6)
        assert 4.0 <= sc.f1.speed <= 8.0


def test_reading_it_right_completes_the_pass():
    rng = np.random.default_rng(21)
    results = [play(make(rng, want=w), lambda rep: rep.sc.best).result for w in rt.OPTIONS * 4]
    assert all(r["choice"] == r["best"] or r["outcome"] != "complete" for r in results)
    done = [r for r in results if r["outcome"] == "complete"]
    assert len(done) >= 10, [(r["best"], r["outcome"], r.get("lanes")) for r in results]
    assert all(r["success"] and r["good_read"] for r in done)
    assert all(r["looks"] >= 1 and r["looks_after_commit"] >= 1 and r["saw_f1_after_commit"] for r in results)


def test_passing_into_the_forecheck_gets_picked_off():
    rng = np.random.default_rng(22)
    results = []
    for w in rt.OPTIONS * 4:
        sc = make(rng, want=w)
        worst = min(sc.values, key=sc.values.get)
        results.append(play(sc, lambda rep, worst=worst: worst).result)
    bad = [r for r in results if r["outcome"] in ("intercepted", "caught")]
    assert len(bad) >= 9, [(r["choice"], r["outcome"]) for r in results]
    assert not any(r["success"] for r in results)
    assert all("open" in rt.verdict(r) or "better play" in rt.verdict(r) for r in results)


def test_holding_on_gets_you_hit():
    rep = play(make(np.random.default_rng(3), free=1.0), None, never_pass=True)
    assert rep.result["outcome"] == "caught" and rep.result["by"] == "F1"
    assert rep.result["choice"] is None and not rep.result["success"]
    assert rep.result["t_done"] == pytest.approx(rep.sc.t_arrive + 1.0, abs=0.5)


def test_no_shoulder_check_is_called_out_and_an_early_one_too():
    rng = np.random.default_rng(5)
    sc = make(rng)
    r = play(sc, lambda rep: rep.sc.best, look=False).result
    assert r["looks"] == 0
    assert rt.verdict(r).endswith("No shoulder check.")
    sc = make(rng)                                       # a look that ends before F1 commits
    r = play(sc, lambda rep: rep.sc.best, look_at=sc.t_commit - 0.7).result
    assert r["looks"] == 1 and r["looks_after_commit"] == 0
    assert rt.verdict(r).endswith("You looked too early.")


def test_scan_tracker_counts_real_turns_only():
    st = rt.ScanTracker()
    head, puck = np.zeros(2), np.array([0.0, -5.0])
    def run(t0, t1, yaw_deg):
        a = math.radians(yaw_deg)
        for t in np.arange(t0, t1, 0.01):
            st.update(t, head, np.array([math.sin(a), -math.cos(a)]), puck, {"F1": np.array([0.0, 8.0])})
    run(0.0, 1.0, 0)          # watching the puck
    run(1.0, 1.05, 120)       # a flick, too short to count
    run(1.05, 1.5, 0)
    run(1.5, 1.9, 175)        # a real shoulder check: F1 in view
    run(1.9, 2.5, 10)
    assert len(st.scans) == 1 and st.scans[0][0] == pytest.approx(1.5, abs=0.02)
    assert st.saw("F1", 1.4, 2.0) and not st.saw("F1", 0.0, 1.4)


def test_staircase_settles_near_75_percent():
    rng = np.random.default_rng(0)
    st = rt.Staircase(level=2.5)
    p_at = lambda free: 1 / (1 + math.exp(-(free - 1.2) / 0.15))      # an observer: 50% at 1.2 s
    wins = []
    for i in range(600):
        ok = rng.random() < p_at(st.level)
        st.update(ok)
        if i > 100:
            wins.append(ok)
    assert 0.68 < np.mean(wins) < 0.82


def test_picker_makes_each_out_best_equally_often():
    pk_ = rt.Picker(np.random.default_rng(1))
    seq = [pk_.next() for _ in range(30)]
    assert {o: seq.count(o) for o in rt.OPTIONS} == {o: 10 for o in rt.OPTIONS}


def test_the_wall_winger_takes_a_hard_rim_along_the_boards():
    rng = np.random.default_rng(31)
    sc = make(rng, want="wall")
    sc.f2 = rt.Track([np.array([0.0, 30.0]), np.array([0.0, 29.0])], 1.0)   # nobody on the wall
    zone = zn.Zone(np.zeros(3), np.array([0.0, 0.0, 1.0]))
    puck = zn.ZonePuck(pk.Params(ice_mu=0.05, board_bounce=0.55), zone)
    rep = rt.Rep(sc, puck)
    rep.state, rep.t_control, rep.go_at = "control", 0.0, 0.0
    rep.last_blade = rt.JON_BLADE.copy()
    puck.place(rt.JON_BLADE[0] + 0.3, pk.R, 14.0, 0.0)                     # rimmed hard into the corner
    t = 0.0
    while rep.state != "done" and t < 6:
        t += 0.001
        puck.step(0.001)
        rep.update(t, rt.JON_BLADE, (HEAD, np.array([0.0, 1.0])))
    assert rep.result["outcome"] == "complete" and rep.result["by"] == "W", rep.result["outcome"]


@pytest.mark.parametrize("blade_z,expect_z", [(0.7, 0.7), (0.15, 0.15), (2.5, rt.AIM_MAX_Z)])
def test_the_rim_assist_brings_the_puck_to_your_blade(blade_z, expect_z):
    sc = make(np.random.default_rng(8))
    zone = zn.Zone(np.zeros(3), np.array([0.0, 0.0, 1.0]))
    puck = zn.ZonePuck(pk.Params(ice_mu=0.05, board_bounce=0.55), zone)
    rep = rt.Rep(sc, puck)
    blade = np.array([rt.JON_BLADE[0], blade_z])
    t = 0.0
    while zone.xz(puck.pos)[0] < blade[0] and t < 12:      # no stick: let it run past
        t += 0.001
        puck.step(0.001)
        rep.update(t, blade, (HEAD, np.array([0.0, -1.0])))
        if rep.state == "done":
            break
    x, z = zone.xz(puck.pos)
    assert rep.aimed and abs(z - expect_z) < 0.12, (x, z)


def test_the_value_model_uses_your_pass_speed():
    p0, target = np.array([0.0, 2.0]), np.array([10.0, 2.0])
    opp = [(np.array([6.0, 4.4]), np.zeros(2))]                # 1.2 m off the lane, 6 m along
    fast = rt.option_value(p0, target, opp, pass_speed=12.0)
    slow = rt.option_value(p0, target, opp, pass_speed=5.0)
    assert fast[1] > 0 > slow[1] and fast[0] > slow[0]
    sc = make(np.random.default_rng(9), want="middle")
    sc_slow = rt.make_scenario(np.random.default_rng(9), free_time=2.5, blade=rt.JON_BLADE, head=HEAD,
                               ice_mu=0.05, board_bounce=0.55, want="middle", pass_speed=5.5, decide_s=1.6)
    assert sc_slow.best == "middle" and sc_slow.pass_speed == 5.5 and sc_slow.decide_s == 1.6
    assert sc.pass_speed == rt.PASS_SPEED


def test_you_learns_your_passing_and_ignores_glitches():
    you = rt.You()
    assert you.pass_speed == rt.PASS_SPEED and you.decide_s == rt.DECIDE_S
    for v, d in ((6.0, 1.2), (5.5, 1.9), (33.0, 1.0), (1.0, 0.9), (7.0, 1.5), (6.5, None)):
        you.add({"release_speed": v, "latency": d})
    assert you.speeds == [6.0, 5.5, 7.0, 6.5]                  # not the 33 m/s glitch, not the 1 m/s fan
    assert you.pass_speed == pytest.approx(6.25)
    assert you.decide_s == pytest.approx(1.5)                  # only real passes count
    you.add({"release_speed": 2.0, "latency": None})
    for _ in range(5):
        you.add({"release_speed": 2.5, "latency": None})
    assert you.pass_speed == 5.0                                # clamped: a few soft passes don't spiral


def test_warm_up_reps_dont_move_the_difficulty(tmp_path):
    st = rt.Staircase(level=2.0, warmup=5)
    for _ in range(5):
        assert st.update(False) is False and st.level == 2.0
    assert st.update(False) is True and st.level == pytest.approx(2.45)
    st.save(tmp_path / "s.json", you={"speeds": [6.0]})
    again = rt.Staircase.load(tmp_path / "s.json")
    assert again.level == pytest.approx(2.45) and again.warming_up            # a new session warms up again
    assert rt.You.load(tmp_path / "s.json").speeds == [6.0]
