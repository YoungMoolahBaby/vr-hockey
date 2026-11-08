"""Hockey-sense drills in the headset.

    uv run python drill.py                    # retrieval: scan, retrieve, first pass (retrieval.py)
    uv run python drill.py --drill pp         # the power-play point: shoot or set one up (powerplay.py)
    uv run python drill.py --free 1.5         # start the pressure here instead of where you left off

retrieval   Face a clear direction in your play space: that becomes the end boards. Hold your
            stick with the blade on the ice; the zone is laid out so your blade sits at the boards
            just left of our net. A puck is dumped in and rims around to you. Before it gets to
            you, check over your shoulder: your winger is up the left wall, your D partner behind
            the net on the right, your center in the slot. F1 commits about a second and a half
            before the puck arrives and F2 takes one man away. Pass to the open one.

pp          Face the direction you want the net in; your blade becomes the left point. Your winger
            on the half wall passes you the puck while the penalty-kill box commits. Shoot through
            the screen, go D-to-D to your partner for his one-timer, or hit the seam to your
            shooter in the far circle. The goalie tracks the puck, loses it behind a screen and
            slides across on passes. Goals are real: the puck has to beat him.

After each rep the voice gives the result and the right play; a map appears in front of you
(looking down): green is the best play, white the puck's path, orange where the defenders went.
The next rep starts after a few seconds while you hold the stick. The first 5 reps of each
session are a warm-up; then the pressure adapts to you.

Controls
  grip buttons                  hold the stick (as in the sandbox)
  A                             start; after a rep, go on to the next one now
  B                             say the last result again
  X                             skip to a new rep
  Y                             fit the stick (as in the sandbox)
  left thumbstick               tune the settings (as in the sandbox; saved only there)
  hold the left thumbstick in   (1 s) lay the zone out around you again

Recorded to data/drill-<timestamp>/ like the sandbox, plus every rep in events.jsonl ("rep") and
a summary in meta.json. The pressure and what the drill learned about your passing and shooting
carry over between sessions (drill_state.json).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import xr

import figures
import goalie as gl
import grab
import powerplay as pp
import puck as pk
import record
import retrieval as rt
import sandbox
import stickspec
import zone as zn
from contacts import Contact

HERE = Path(__file__).resolve().parent
STATE_PATH = HERE / "drill_state.json"
GREEN, WHITE, DIM_ORANGE, GREY = (0.2, 1.0, 0.35), (0.92, 0.92, 0.92), (0.7, 0.35, 0.1), (0.55, 0.58, 0.62)
MAP_SCALE = 1 / 30


# ----------------------------------------------------------------------------- the drills


class Retrieval:
    name, kind = "retrieval", "drill-retrieval"
    blade, facing = rt.JON_BLADE, (0.0, -1.0)
    options = rt.OPTIONS
    stairs_key, you_key, you_cls = "staircase", "you", rt.You
    rep_dt = 0.005           # s: the rep's checks at 200 Hz (a pass moves 5 cm between them)
    outcomes = ("complete", "intercepted", "caught", "loose", "cleared", "own_goal", "missed")

    @staticmethod
    def intro(warmup: int) -> str:
        return ("Retrieval drill. Face the end boards with your stick on the ice and press A. The puck rims "
                "around to you. Before it gets there, check over your shoulder: winger up the wall, partner "
                "behind the net, center in the middle. Read the forecheck and pass to the open man. "
                f"The first {warmup} reps are a warm-up.")

    @staticmethod
    def scenario(rng, level, head, params, you, want):
        return rt.make_scenario(rng, free_time=level, blade=rt.JON_BLADE, head=head, ice_mu=params.ice_mu,
                                board_bounce=params.board_bounce, want=want, pass_speed=you.pass_speed,
                                decide_s=you.decide_s, pause_s=0.002)

    @staticmethod
    def rep(sc, puck, number, rng):
        return rt.Rep(sc, puck, number=number)

    @staticmethod
    def target(rep, best):
        """Where the best play goes (zone x, z), for the green line."""
        return rep.sc.mates[rt.RECEIVER[best]] if best in rt.RECEIVER else None

    @staticmethod
    def line(res, level) -> str:
        return (f"  rep {res['rep']}: {res['outcome']:<11} chose {res.get('choice')!s:<8} best {res.get('best')!s:<8}"
                f" looks {res['looks']} (after commit {res['looks_after_commit']})  free {res['free_time']:.2f}s"
                f" -> {level:.2f}s")


class PowerPlay:
    name, kind = "powerplay", "drill-powerplay"
    blade, facing = pp.JON_BLADE, pp.FACING
    options = pp.OPTIONS
    stairs_key, you_key, you_cls = "powerplay", "you_pp", pp.You
    rep_dt = 0.001           # s: every tick: a shot crosses the goalie in a few ms
    outcomes = ("goal", "save", "blocked", "miss", "intercepted", "caught", "reset", "loose", "cleared", "missed")

    @staticmethod
    def intro(warmup: int) -> str:
        return ("Power play. You're on the left point, facing the net: press A. Your winger passes it up to you "
                "while the box commits. Shoot through the screen, go D to D for the one-timer, or hit the seam "
                f"to the far circle. The first {warmup} reps are a warm-up.")

    @staticmethod
    def scenario(rng, level, head, params, you, want):
        return pp.make_scenario(rng, free_time=level, blade=pp.JON_BLADE, head=head, ice_mu=params.ice_mu,
                                want=want, pass_speed=you.pass_speed, shot_speed=you.shot_speed,
                                decide_s=you.decide_s, pause_s=0.002)

    @staticmethod
    def rep(sc, puck, number, rng):
        return pp.Rep(sc, puck, number=number, rng=rng)

    @staticmethod
    def target(rep, best):
        if best == "shoot":
            return gl.NET_C
        return rep.sc.mates[pp.RECEIVER[best]] if best in pp.RECEIVER else None

    @staticmethod
    def line(res, level) -> str:
        xg = res.get("xg") or {}
        xs = " ".join(f"{k} {100 * v:.1f}%" for k, v in xg.items())
        return (f"  rep {res['rep']}: {res['outcome']:<11} chose {res.get('choice')!s:<8} best {res.get('best')!s:<8}"
                f" xG [{xs}]  looks {res['looks']}  free {res['free_time']:.2f}s -> {level:.2f}s")


DRILLS = {"retrieval": Retrieval, "pp": PowerPlay, "powerplay": PowerPlay}


# ----------------------------------------------------------------------------- the app


class DrillPhysics(sandbox.Physics):
    """The sandbox's stick and puck, with a drill instead of free play."""

    def __init__(self, mode: "DrillMode"):
        super().__init__(mode.play, mode.voice, mode.log)
        self.mode = mode
        self.blade = None
        self.gripping = False

    def __call__(self, t: float, tick: dict) -> None:
        before = getattr(self, "errors", 0)
        super().__call__(t, tick)                       # catches and logs physics errors
        if before == 0 and getattr(self, "errors", 0) > 0:
            self.voice.say("Something broke in the drill. Tell Claude.", key="error")

    def _world(self, t: float, R, p, held: bool) -> None:
        self.blade = (R @ self.sweet + p) if held else None
        # a let-go stick stays in your last hand (LOOSE): that is not playing
        self.gripping = self.play.stick_state in (grab.BOTH, grab.TOP, grab.BOTTOM)
        self.mode.place_if_asked(t, self.blade)

    def _game(self, t: float, imp: float) -> None:
        pl, pz = self.play, self.play.sim.puck
        now = time.perf_counter()
        for kind, speed in pz.events:
            pl.bus.publish(Contact(now, kind, speed))          # the boards thud plays from the bus
            if kind in ("net", "cleared"):
                self.log.event(t, kind, ms=round(speed, 2))
        pz.events.clear()
        self.mode.tick(t, self.blade, self.gripping)


class DrillMode(sandbox.SandboxMode):
    """A drill as a sandbox mode: lays the zone out from your blade, prepares reps in the
    background, runs them, draws them, and keeps score. `drill` says which one."""

    app_name = "vr-hockey-drill"
    drill = Retrieval
    kind = Retrieval.kind
    free_start: float | None = None                       # --free

    def __init__(self, play, voice, log):
        super().__init__(play, voice, log)
        self.zone: zn.Zone | None = None
        self.head_zone = np.asarray(self.drill.blade, dtype=float) + 1.1 * -np.asarray(self.drill.facing)
        self.want_place: str | None = None                 # "head" (provisional) or "blade"
        self.rep = None
        self.rep_t0 = 0.0
        self.started = False
        self.want_next = False
        self.next_sc = None
        self._preparing = False
        self.rng = np.random.default_rng()
        self._bag: list[str] = []
        self.stairs = rt.Staircase.load(STATE_PATH, self.drill.stairs_key)
        if self.free_start is not None:
            self.stairs.level = self.free_start
        self.you = self.drill.you_cls.load(STATE_PATH, self.drill.you_key)
        self.results: list[dict] = []
        self.last_verdict = ""
        self._static = (None, None)                          # (zone, its markings' vertices)
        self._last_update = -1.0

    def make_physics(self) -> DrillPhysics:
        self.physics = DrillPhysics(self)
        return self.physics

    def intro(self) -> str:
        return self.drill.intro(self.stairs.warmup)

    # ---- the zone (physics thread)
    def first_head(self) -> None:
        self.want_place = "head"

    def recenter(self) -> None:
        self.want_place = "blade"
        self.voice.say("Zone set around you.", key="zone")

    def place_if_asked(self, t: float, blade_world) -> None:
        if self.want_place is None or self.play.head is None:
            return
        Rh, ph = self.play.head
        f = -Rh[:, 2]
        f = np.array([f[0], 0.0, f[2]]) / max(float(np.hypot(f[0], f[2])), 1e-6)
        spot = ph + 1.1 * f
        if blade_world is not None and 0.5 < float(np.hypot(*(blade_world - ph)[[0, 2]])) < 2.2:
            spot = blade_world
        b = np.asarray(self.drill.blade, dtype=float)
        self.zone = zn.Zone.placed(tuple(b), spot, f, self.drill.facing)
        self.head_zone = self.zone.xz(ph)
        puck = zn.ZonePuck(self.play.params, self.zone)
        side = np.array([self.drill.facing[1], -self.drill.facing[0]])      # your left
        puck.place(*(b + 0.6 * side + 0.2 * -np.asarray(self.drill.facing)))  # beside your blade, to play with
        self.play.sim.puck = puck
        self.rep = None
        self.next_sc = None
        self.log.event(t, "zone", drill=self.drill.name, how=self.want_place,
                       head=self.head_zone.round(3).tolist(), **self.zone.to_dict())
        self.want_place = None
        self._prepare()

    # ---- reps
    def _prepare(self) -> None:
        """Build the next rep in the background (a few to a few hundred ms)."""
        if self._preparing or self.zone is None:
            return
        self._preparing = True
        want = self._next_want()
        level, head, params = self.stairs.level, self.head_zone.copy(), self.play.params
        you = SimpleNamespace(pass_speed=self.you.pass_speed, decide_s=self.you.decide_s,
                              shot_speed=getattr(self.you, "shot_speed", None))

        def work():
            try:
                self.next_sc = self.drill.scenario(self.rng, level, head, params, you, want)
            finally:
                self._preparing = False
        threading.Thread(target=work, daemon=True, name="prepare-rep").start()

    def _next_want(self) -> str:
        """Each of this drill's options the best one equally often, shuffled in blocks."""
        if not self._bag:
            self._bag = [str(o) for o in self.rng.permutation(self.drill.options)]
        return self._bag.pop()

    def button(self, name: str, t_sim: float) -> None:
        if name == "a":
            if not self.started:
                self.started = True
                self.want_place = "blade"                      # lay it out from your blade now
            self.want_next = True
        elif name == "x" and self.started:
            if self.rep is not None and self.rep.state != "done":
                self.log.event(t_sim, "rep_skipped", rep=self.rep.number)
            self.rep = None
            self.want_next = True
        elif name == "b":
            self.voice.say(self.last_verdict or "No reps yet.", key="verdict")

    def tick(self, t: float, blade_world, gripping: bool = True) -> None:
        """Every physics tick: run the rep, start the next one (only while you grip the stick and
        the drill is in front in the headset)."""
        if self.zone is None:
            return
        rep = self.rep
        if rep is None or rep.state == "done":
            focused = time.time() - self.play.last_focus < 1.5
            ready = self.started and self.next_sc is not None and blade_world is not None and gripping and focused
            waited = rep is None or t - self.rep_t0 - rep.go_at - (rep.t_done or 0.0) >= rt.RESULT_S
            if ready and (self.want_next or waited):
                self.want_next = False
                self.rep_t0 = t
                self.rep = self.drill.rep(self.next_sc, self.play.sim.puck, len(self.results) + 1,
                                          np.random.default_rng(self.rng.integers(1 << 31)))
                self.next_sc = None
                self._prepare()
                rep = self.rep
            if rep is None:
                return
        if t - self._last_update < self.drill.rep_dt:         # the stick and puck run at 1 kHz
            return
        self._last_update = t
        head = None
        if self.play.head is not None:
            Rh, ph = self.play.head
            head = (self.zone.xz(ph), self.zone.dir_to_zone(-Rh[:, 2]))
        blade = self.zone.xz(blade_world) if blade_world is not None else None
        rep.update(t - self.rep_t0, blade, head)
        self._drain(t, rep)

    def _drain(self, t: float, rep) -> None:
        pl = self.play
        hands = [pl.spec.top_hand, pl.spec.bottom_hand]
        while rep.outbox:
            item = rep.outbox.pop(0)
            kind = item[0]
            if kind == "say":
                self.last_verdict = item[1]
                self.voice.say(item[1], key="verdict")
            elif kind == "sound":
                pl.sounds.put((item[1], item[2]))
            elif kind == "buzz":
                pl.haptics.put((item[1], hands, item[2]))
            elif kind == "log":
                self.log.event(t, item[1], **item[2])
                if item[1] == "rep":
                    self._done(item[2])

    def _done(self, res: dict) -> None:
        self.results.append(res)
        if res["outcome"] == "caught":                         # you got hit
            self.play.haptics.put((1.0, [self.play.spec.top_hand, self.play.spec.bottom_hand], 140))
            self.play.sounds.put(("thud", 1.0))
        self.you.add(res)
        if res["counts"]:
            self.stairs.update(res["success"])
            if self.stairs.session == self.stairs.warmup:
                self.voice.say("Warm-up done. From here it adapts to you.", key="warmup")
        try:
            self.stairs.save(STATE_PATH, self.drill.stairs_key, **{self.drill.you_key: self.you.to_dict()})
        except OSError:
            pass
        print(self.drill.line(res, self.stairs.level), flush=True)

    # ---- drawing (render thread)
    def draw(self, poses: dict, held: dict, stick, state: int) -> np.ndarray:
        line = sandbox.Lines()
        zone, rep = self.zone, self.rep
        static = np.zeros((0, 6), dtype=np.float32)
        if zone is not None:
            if self._static[0] is not zone:                    # the rink only changes when it's laid out
                lines = sandbox.Lines()
                zn.markings(zone, lines, near=tuple(self.head_zone))
                self._static = (zone, lines.array())
            static = self._static[1]
            if rep is not None:
                for s in rep.skaters:
                    figures.skater(line, zone, s.pos, s.facing, figures.US if s.team == "us" else figures.THEM,
                                   s.shoots, s.stride, float(np.linalg.norm(s.vel)))
                g = getattr(rep, "goalie", None)
                if g is not None:
                    figures.goalie(line, zone, g.c, g.facing, down=g.mode != "track")
                if rep.state == "done" and rep.result is not None:
                    self._replay(line, zone, rep)
        sandbox.draw_puck(line, self.play.sim.puck)
        sandbox.draw_hands_and_stick(line, self.play, poses, held, stick, state)
        return np.vstack([static, line.array()])

    def _replay(self, line, zone: zn.Zone, rep) -> None:
        """After a rep: the best play and the puck's path on the ice, and a map in front of you
        (looking down): the zone, where the defenders actually skated, the puck, the best play,
        and for the power play each option's chance of a goal as a bar (green: the best)."""
        res = rep.result
        start = np.asarray(res.get("release_at") or self.drill.blade, dtype=float)
        best = res.get("best")
        best_to = self.drill.target(rep, best)
        if best_to is not None:
            for dy in (0.01, 0.03):
                line.many(zone.world_many(start, dy), zone.world_many(best_to, dy), GREEN)
        trail = np.array(rep.trail) if len(rep.trail) > 1 else None
        if trail is not None:
            P = zone.world_many(trail, 0.02)
            line.many(P[:-1], P[1:], WHITE)
        if self.play.head is None:
            return
        Rh, ph = self.play.head                               # the map: a model of the zone, waist high
        f = -Rh[:, 2]
        f = np.array([f[0], 0.0, f[2]]) / max(float(np.hypot(f[0], f[2])), 1e-6)
        centre = ph + 0.55 * f + np.array([0.0, -0.5, 0.0])
        mid = np.array([0.0, zn.BLUE_Z / 2])

        def at(pts):
            xz = np.asarray(pts, dtype=float).reshape(-1, 2) - mid
            return centre + (xz[:, :1] * zone.X + xz[:, 1:] * zone.Z) * MAP_SCALE

        def poly(pts, col):
            P = at(pts)
            line.many(P[:-1], P[1:], col)

        poly(zn.outline(8), zn.BOARDS)
        poly([(-zn.WIDTH / 2, zn.BLUE_Z), (zn.WIDTH / 2, zn.BLUE_Z)], zn.BLUE)
        g = zn.side_boards_x(zn.GOAL_Z)
        poly([(-g, zn.GOAL_Z), (g, zn.GOAL_Z)], zn.RED)
        x0, x1, z0, z1 = rt.NET_SOLID
        poly([(x0, z1), (x0, z0), (x1, z0), (x1, z1)], zn.RED)
        for path in rep.paths.values():                       # where the defenders went
            pts = [p for p in path if p[1] < zn.BLUE_Z + 3]
            if len(pts) > 1:
                poly(pts, DIM_ORANGE)
        if trail is not None:
            poly(trail, WHITE)
        if best_to is not None:
            poly([start, best_to], GREEN)
        ring = 0.45 * np.stack([np.cos(np.linspace(0, 2 * np.pi, 9)), np.sin(np.linspace(0, 2 * np.pi, 9))], axis=1)
        for s in rep.skaters:
            poly(ring + s.pos, figures.US if s.team == "us" else figures.THEM)
        poly(ring + self.head_zone, figures.YOU)
        if getattr(rep, "goalie", None) is not None:
            poly(ring * 0.8 + rep.goalie.c, figures.GOALIE)
        xg = res.get("xg")
        if xg:                                                # each option's goal chance, as a bar
            spots = {"shoot": start, **{o: rep.sc.mates[w] for o, w in pp.RECEIVER.items()}}
            for o, v in xg.items():
                base = at(spots[o])[0]
                top = base + np.array([0.0, 0.01 + 1.5 * min(v, 0.4), 0.0])
                for dx in (-0.004, 0.0, 0.004):
                    off = dx * zone.X
                    line.many((base + off)[None], (top + off)[None], GREEN if o == best else GREY)

    def status(self) -> str:
        rep = self.rep
        st = "waiting" if rep is None else rep.state
        wins = sum(r["success"] for r in self.results)
        err = getattr(self.physics, "errors", 0)
        return f"{self.drill.name} rep {len(self.results) + (rep is not None and rep.state != 'done')} {st:<8} " \
               f"free {self.stairs.level:.2f}s  wins {wins}/{len(self.results)}" + (f"  ERRORS {err}" if err else "")

    def meta(self) -> dict:
        res = [r for r in self.results if r["counts"]]
        summary = {
            "reps": len(self.results), "counted": len(res),
            "success_pct": round(100 * np.mean([r["success"] for r in res]), 1) if res else None,
            "good_read_pct": round(100 * np.mean([r["good_read"] for r in res]), 1) if res else None,
            "outcomes": {o: sum(r["outcome"] == o for r in self.results) for o in self.drill.outcomes},
            "looks_mean": round(float(np.mean([r["looks"] for r in res])), 2) if res else None,
            "looked_after_commit_pct": round(100 * np.mean([r["looks_after_commit"] > 0 for r in res]), 1) if res else None,
            "free_time_end": round(self.stairs.level, 3)}
        you = {"pass_speed": round(self.you.pass_speed, 2), "decide_s": round(self.you.decide_s, 2)}
        if hasattr(self.you, "shot_speed"):
            you["shot_speed"] = round(self.you.shot_speed, 2)
        return {"drill": self.drill.name, "summary": summary, "staircase": self.stairs.__dict__, "you": you,
                "zone": self.zone.to_dict() if self.zone else None}

    def close(self) -> None:
        s = self.meta()["summary"]
        goals = f", goals {s['outcomes'].get('goal')}" if "goal" in s["outcomes"] else ""
        print(f"drill {self.drill.name}: {s['reps']} reps, success {s['success_pct']}%, good reads "
              f"{s['good_read_pct']}%{goals}, looks/rep {s['looks_mean']}, free time now {s['free_time_end']} s")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--drill", choices=sorted(DRILLS), default="retrieval")
    ap.add_argument("--height", default="5'8\"")
    ap.add_argument("--shoots", choices=("left", "right"), default="left")
    ap.add_argument("--free", type=float, help="the pressure (s) to begin with")
    ap.add_argument("--no-voice", action="store_true")
    ap.add_argument("--no-sound", action="store_true")
    ap.add_argument("--audio-device", default="Oculus", help="part of the output device's name (default: the Quest over Link)")
    ap.add_argument("--notes", default="")
    args = ap.parse_args()

    base = stickspec.from_height(stickspec.parse_height(args.height), args.shoots)
    fit = grab.Fit.load(record.FIT_PATH) or grab.Fit()
    values = sandbox.Tuning.defaults(base, fit, pk.Params())
    if sandbox.SETTINGS_PATH.exists():
        values.update(json.loads(sandbox.SETTINGS_PATH.read_text())["values"])
    play = sandbox.Play(sandbox.Tuning(base, values))
    drill = DRILLS[args.drill]
    mode_cls = type(f"{drill.__name__}Mode", (DrillMode,), {"drill": drill, "kind": drill.kind,
                                                            "free_start": args.free})
    run_dir = HERE / "data" / (f"drill-{drill.name}-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    lock = record.take_lock()
    try:
        sandbox.run(args, play, run_dir, mode_cls)
    except xr.FormFactorUnavailableError:
        raise SystemExit("Headset not connected: put it on, start Link, then run again (xrcheck.py tells you).")
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
