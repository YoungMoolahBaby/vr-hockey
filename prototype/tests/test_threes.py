"""The 3v3 game, played by the AI alone (no headset): the real puck physics, both goalies."""

import time

import numpy as np
import pytest

import arena as ar
import puck as pk
import threes
import zone as zn


def make(you=False, seed=0, to_goals=99, **kw):
    params = pk.Params()
    rink = ar.Arena(zn.Zone(np.array([3.0, 0.0, -1.0]), np.array([0.6, 0.0, -0.8])))
    sim = pk.Sim(params, pk.Rink(), 70)
    sim.puck = ar.ArenaPuck(params, rink)
    game = threes.Game(rink, sim.puck, np.random.default_rng(seed), to_goals=to_goals, you=you, **kw)
    return sim, game


def play(sim, game, seconds, t0=0.0, blade=None, head=None):
    """The physics at 1 kHz and the game every tick, as in the headset."""
    log = []
    n = int(seconds * 1000)
    for i in range(n):
        t = t0 + i * 0.001
        sim.step(0.001, None, None)
        sim.puck.events.clear()
        b = blade(t) if callable(blade) else blade
        h = head(t) if callable(head) else head
        game.update(t, b, h)
        log += game.outbox
        game.outbox.clear()
    return log


def test_the_ai_plays_a_game():
    sim, game = make(seed=1)
    game.start()
    log = play(sim, game, 180.0)
    kinds = [e[1] for e in log if e[0] == "log"]
    s = game.stats
    print("score", game.score, "shots", s["shots"], "saves", s["saves"], "turnovers", s["turnovers"],
          "blocked", s["blocked"], {k: kinds.count(k) for k in set(kinds)})
    assert kinds.count("pass") > 20                          # they move it
    assert s["shots"]["us"] > 3 and s["shots"]["them"] > 3   # both ends get shots
    assert sum(s["saves"].values()) > 2                      # and both goalies work
    assert sum(game.score.values()) >= 1                     # somebody scores
    assert s["turnovers"] > 5                                # the puck changes hands
    x, z = game.arena.zone.xz(sim.puck.pos)                  # the puck is still in the rink
    assert game.arena.boards_contact(x, z, 0.0) is None
    for p in game.players:                                   # so is everyone
        assert game.arena.boards_contact(*p.pos, 0.0) is None


def test_a_puck_stopped_behind_the_net_gets_dug_out():
    """A shot over the net and off the glass stops just behind it, with skaters in front: they go
    round the net for it (they used to stand pinned against its front for the rest of the game)."""
    sim, game = make(seed=1)
    game.start()
    play(sim, game, 2.5)                                      # faceoff and drop
    for p, x in zip(game.players, (-0.2, -1.0, 0.7, 5.8, -0.1, 5.8)):
        p.pos, p.vel = np.array([x, 3.7]), np.zeros(2)        # in front of the home net
    game.holder, game.yours = None, False
    sim.puck.place(-0.25, 2.0)                                # 0.23 m behind the net's back
    for p in game.players:
        p.cool_until = 0.0
    log = play(sim, game, 6.0, t0=game.t + 0.001)
    assert game.holder is not None or game.state != "live"
    assert not any(e[0] == "say" and "Dead puck" in e[1] for e in log)


def test_a_goal_restarts_at_centre_and_ends_the_game():
    sim, game = make(seed=2, to_goals=1)
    game.start()
    play(sim, game, 3.0)
    assert game.state == "live"
    sim.puck.place(0.3, game.arena.length - zn.GOAL_Z - 0.25, 0.0, 4.0)   # behind the goalie, rolling in
    log = play(sim, game, 1.5, t0=3.0)
    assert game.score == {"us": 1, "them": 0}
    assert game.state == "over"
    assert any(e[0] == "say" and "Game over" in e[1] for e in log)
    game.start()
    log = play(sim, game, 0.5, t0=4.5)
    assert game.score == {"us": 0, "them": 0} and game.state == "faceoff"
    x, z = game.arena.zone.xz(sim.puck.pos)
    assert abs(x) < 0.05 and abs(z - game.arena.mid) < 0.05      # held on the dot


def test_you_get_teleported_to_the_faceoff_and_can_take_a_pass():
    sim, game = make(you=True, seed=3)
    game.start()
    tp = [e for e in game.outbox if e[0] == "teleport"]
    assert tp and np.allclose(tp[0][1], (0.0, game.arena.mid - 1.4))
    you_at = np.array([4.0, 30.0])
    head = (you_at, np.array([0.0, 1.0]))
    blade = you_at + np.array([0.3, 0.9])
    play(sim, game, 2.5, head=head, blade=blade)
    u1 = game.by_id["U1"]                                    # give U1 the puck, in the open
    for o in game.players:
        if o.team == "them":
            o.pos = np.array([0.0, 5.0]) + np.random.default_rng(0).normal(size=2)
    u1.pos = np.array([-4.0, 30.0])
    game.holder, game.yours = u1, False
    game._carry()
    game._pass(u1.stick(), game.you, "us", "U1")
    closest = 9.0
    for k in range(1500):                                    # no stick in this test: it slides on by
        t = 2.5 + k * 0.001
        sim.step(0.001, None, None)
        game.update(t, blade, head)
        closest = min(closest, float(np.linalg.norm(game.arena.zone.xz(sim.puck.pos) - blade)))
    assert game.stats["passes_to_you"] == 1
    assert closest < 0.25                                    # on your tape


def test_an_ai_tick_is_cheap():
    sim, game = make(seed=4)
    game.start()
    play(sim, game, 5.0)
    t = time.perf_counter()
    play(sim, game, 10.0, t0=5.0)
    per_s = time.perf_counter() - t
    # 10 s of game (10,000 physics ticks and 500 AI ticks) should take well under 10 s on top of the physics
    assert per_s < 5.0, per_s


class _Quiet:
    def say(self, *a, **k):
        pass

    def event(self, *a, **k):
        pass

    def puck_row(self, *a, **k):
        pass


def test_the_app_runs_headless():
    """game.py's mode and physics, driven like the headset would: a head, a right hand holding the
    stick, A to drop the puck; then a frame drawn."""
    import game as gm
    import grab
    import sandbox
    import stickspec
    spec = stickspec.from_height(1.73, "left")
    play = sandbox.Play(sandbox.Tuning(spec, sandbox.Tuning.defaults(spec, grab.Fit(), pk.Params())))
    mode = gm.GameMode(play, _Quiet(), _Quiet())
    physics = mode.make_physics()
    play.head = (np.eye(3), np.array([0.0, 1.6, 0.0]))       # looking down -z
    mode.first_head()
    hand = (np.eye(3), np.array([0.25, 1.0, -0.3]))
    play.squeeze["r"] = 1.0
    t = 0.0
    for i in range(3000):
        if i == 500:
            mode.button("a", t)
        t = i * 0.001
        physics(t, {"r": hand})
    assert getattr(physics, "errors", 0) == 0
    g = mode.game
    assert g is not None and g.state == "live"
    assert play.want_teleport is not None                    # you were put on your faceoff spot
    at, facing = play.want_teleport
    assert np.allclose(at[[0, 2]], [0.0, 0.0], atol=1e-6)    # ... which is where you stood
    assert np.allclose(facing[[0, 2]], [0.0, -1.0], atol=1e-6)
    drawn = mode.draw({"r": hand}, {"r": True}, (None, None), grab.TOP)
    verts = drawn.lines
    assert drawn.tris.shape[1] == 6 and len(drawn.tris) > 1000           # the solid rink
    assert verts.shape[1] == 6 and len(verts) > 1000


class _Said(_Quiet):
    def __init__(self):
        self.said = []

    def say(self, text, **k):
        self.said.append(text)


def _free_skate(ends=("home", "far"), seed=1):
    """game.py --free, headless: a head at the origin looking down -z, the right hand holding the stick."""
    import game as gm
    import grab
    import sandbox
    import stickspec
    spec = stickspec.from_height(1.73, "left")
    play = sandbox.Play(sandbox.Tuning(spec, sandbox.Tuning.defaults(spec, grab.Fit(), pk.Params())))
    voice = _Said()
    mode = type("Free", (gm.FreeSkateMode,), {"goalie_ends": ends})(play, voice, _Quiet())
    mode.rng = np.random.default_rng(seed)
    physics = mode.make_physics()
    play.head = (np.eye(3), np.array([0.0, 1.6, 0.0]))
    mode.first_head()
    hand = (np.eye(3), np.array([0.25, 1.0, -0.3]))
    play.squeeze["r"] = 1.0

    def run(a, b):
        for i in range(a, b):
            physics(i * 0.001, {"r": hand})
    return play, voice, mode, physics, hand, run


def test_free_skate_runs_headless():
    """game.py --free --empty: the rink and a puck on your stick, nobody else; a goal is called
    once and a puck comes back to you; X gives you one any time."""
    import grab
    play, voice, mode, physics, hand, run = _free_skate(ends=())
    run(0, 500)
    assert getattr(physics, "errors", 0) == 0
    assert mode.game is None and isinstance(play.sim.puck, ar.ArenaPuck)
    pz, zone = play.sim.puck, mode.arena.zone
    blade = physics.grab.R @ physics.sweet + physics.grab.p
    assert np.linalg.norm((pz.pos - blade)[[0, 2]]) < 0.2     # a puck on your stick
    far = mode.arena.net("far")
    pz.place(0.3, far[1] - 3.0, 0.0, 15.0)                  # a shot at the far net
    run(500, 1500)
    assert mode.goals == {"far": 1, "home": 0} and "Goal! 1" in voice.said
    assert pz.in_net == 2                                    # still in: called once
    run(1500, 3000)                                          # 2 s on: a puck back on your stick
    assert not pz.in_net and np.linalg.norm((pz.pos - blade)[[0, 2]]) < 0.2
    pz.place(5.0, 10.0)
    mode.button("x", 3.0)
    run(3000, 3010)
    assert np.linalg.norm((pz.pos - blade)[[0, 2]]) < 0.2
    assert mode.goals == {"far": 1, "home": 0}
    drawn = mode.draw({"r": hand}, {"r": True}, (None, None), grab.TOP)
    verts = drawn.lines
    assert drawn.tris.shape[1] == 6 and len(drawn.tris) > 1000           # the solid rink
    assert verts.shape[1] == 6 and len(verts) > 500
    assert mode.meta()["goals"] == {"far": 1, "home": 0}
    assert "goals 1" in mode.status()


def test_free_skate_goalies_save_cover_and_pass_it_back_to_you():
    import grab
    play, voice, mode, physics, hand, run = _free_skate()
    run(0, 500)
    assert getattr(physics, "errors", 0) == 0
    gs, pz = mode.goalies, play.sim.puck
    assert set(gs.keepers) == {"home", "far"}
    far = mode.arena.net("far")
    pz.place(0.0, far[1] - 6.0, 0.0, 15.0)                  # a shot right at the far goalie
    run(500, 1500)
    assert getattr(physics, "errors", 0) == 0
    assert not pz.in_net and gs.saves["far"] == 1 and "Save!" in voice.said
    assert mode.goals == {"far": 0, "home": 0}
    # a slow puck at his feet: he covers it, then passes it out to you
    k = gs.keepers["far"]
    gs.release()                                              # (whatever became of the shot)
    k.calm_until = 0.0
    at = k.pos + 0.5 * k.facing
    pz.place(at[0], at[1], *(-0.5 * k.facing))
    run(1500, 1700)
    assert gs.holder is k
    blade = physics.grab.R @ physics.sweet + physics.grab.p
    run(1700, 2800)                                           # he holds it a second, then plays it
    assert gs.holder is None
    zone = mode.arena.zone
    to_you = zone.xz(blade) - zone.xz(pz.pos)
    v = zone.dir_to_zone(pz.vel)
    assert float(np.linalg.norm(v)) > 4.0
    assert float(v @ to_you) / (np.linalg.norm(v) * np.linalg.norm(to_you)) > 0.95     # at your blade
    drawn = mode.draw({"r": hand}, {"r": True}, (None, None), grab.TOP)
    verts = drawn.lines
    assert drawn.tris.shape[1] == 6 and len(drawn.tris) > 1000           # the solid rink
    assert verts.shape[1] == 6
    assert "saves" in mode.status() and mode.meta()["saves"]["far"] >= 1


def test_a_snap_turn_takes_the_puck_on_your_blade_with_you():
    """The stick jumps 30 degrees round your head in one tick: no sweep through the puck (no hit),
    and a puck resting on the blade turns with you."""
    import grab
    import sandbox
    import stickspec
    spec = stickspec.from_height(1.73, "left")
    play = sandbox.Play(sandbox.Tuning(spec, sandbox.Tuning.defaults(spec, grab.Fit(), pk.Params())))
    physics = sandbox.Physics(play, _Quiet(), _Quiet())
    play.squeeze["r"] = 1.0
    hand = (np.eye(3), np.array([0.25, 1.0, -0.3]))
    for i in range(300):                                     # hold it; let the stick settle on the ice
        physics(i * 0.001, {"r": hand})
    blade = physics.grab.R @ physics.sweet + physics.grab.p
    n = physics.grab.R @ spec.z_forehand
    n = np.array([n[0], 0.0, n[2]]) / np.hypot(n[0], n[2])
    play.sim.puck.spawn((blade + (pk.R + 0.01) * n)[[0, 2]])  # resting against the forehand
    for i in range(300, 400):
        physics(i * 0.001, {"r": hand})
    before = play.sim.puck.pos - blade
    a = np.radians(30)                                       # snap: hands turned about the head (0, 1.7, 0)
    Ry = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    turned = (Ry @ hand[0], Ry @ hand[1])
    play.rig_yaw = a
    hits = 0
    for i in range(400, 700):
        physics(i * 0.001, {"r": turned})
        hits += getattr(physics, "last_impulse", 0.0) > 1.0
    blade2 = physics.grab.R @ physics.sweet + physics.grab.p
    after = play.sim.puck.pos - blade2
    assert hits == 0                                          # not swept through
    assert play.sim.puck.speed < 0.5
    assert np.linalg.norm((after - Ry @ before)[[0, 2]]) < 0.05   # still on the blade, turned with you
