"""Hockey-sense drills in the headset. Module 1: scan, retrieve, first pass (retrieval.py).

    uv run python drill.py
    uv run python drill.py --free 1.5     # start F1's head start here instead of where you left off

Stand facing a clear direction in your play space: that becomes the end boards. Hold your stick
with the blade on the ice; the zone is laid out so your blade sits on the boards just left of
our net. A puck is dumped in down the far wall and rims around to your forehand. Before it gets
to you, check over your shoulders: your winger is up the left wall, your D partner is behind the
net on the right, your center is in the slot. F1 commits about a second and a half before the
puck arrives (down your wall, around the net after the puck, or down the middle) and F2 takes
one man away. Pass to the open one.

After each rep the voice gives the result and the open out; a map of the play appears in front
of you (looking down): green is the best pass, white is where the puck went, orange is where the
forecheckers skated. The next rep starts after a few seconds while you hold the stick.

Controls
  grip buttons                  hold the stick (as in the sandbox)
  A                             start; after a rep, go on to the next one now
  B                             say the last result again
  X                             skip to a new rep
  Y                             fit the stick (as in the sandbox)
  left thumbstick               tune the settings (as in the sandbox; saved only there)
  hold the left thumbstick in   (1 s) lay the zone out around you again: face the end boards first

Recorded to data/drill-<timestamp>/ like the sandbox, plus every rep in events.jsonl ("rep") and
a summary in meta.json. F1's head start carries over between sessions (drill_state.json).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import threading
import time
from pathlib import Path

import numpy as np
import xr

import figures
import grab
import puck as pk
import record
import retrieval as rt
import sandbox
import stickspec
import zone as zn

HERE = Path(__file__).resolve().parent
STATE_PATH = HERE / "drill_state.json"
GREEN, WHITE, DIM_ORANGE, GOLD = (0.2, 1.0, 0.35), (0.92, 0.92, 0.92), (0.7, 0.35, 0.1), (1.0, 0.85, 0.1)
MAP_SCALE = 1 / 30
REP_DT = 0.005           # s: the rep's checks run at 200 Hz (a 10 m/s pass moves 5 cm between them)


class DrillPhysics(sandbox.Physics):
    """The sandbox's stick and puck, with the drill instead of free play."""

    def __init__(self, mode: "DrillMode"):
        super().__init__(mode.play, mode.voice, mode.log)
        self.mode = mode
        self.blade = None

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
        for kind, speed in pz.events:
            if kind == "boards" and speed > 1:
                pl.sounds.put(("thud", float(np.clip(speed / 12.0, 0, 1))))
            elif kind in ("own_goal", "cleared"):
                self.log.event(t, kind, ms=round(speed, 2))
        pz.events.clear()
        self.mode.tick(t, self.blade, self.gripping)


class DrillMode(sandbox.SandboxMode):
    kind = "drill-retrieval"
    app_name = "vr-hockey-drill"
    free_start: float | None = None                       # --free

    def __init__(self, play, voice, log):
        super().__init__(play, voice, log)
        self.zone: zn.Zone | None = None
        self.head_zone = np.array([3.35, 1.3])
        self.want_place: str | None = None                 # "head" (provisional) or "blade"
        self.rep: rt.Rep | None = None
        self.rep_t0 = 0.0
        self.started = False
        self.want_next = False
        self.next_sc: rt.Scenario | None = None
        self._preparing = False
        self.rng = np.random.default_rng()
        self.picker = rt.Picker(self.rng)
        self.stairs = rt.Staircase.load(STATE_PATH)
        if self.free_start is not None:
            self.stairs.level = self.free_start
        self.you = rt.You.load(STATE_PATH)                    # your pass speed and release time
        self.results: list[dict] = []
        self.last_verdict = ""
        self._static = (None, None)                          # (zone, its markings' vertices)
        self._last_update = -1.0

    def make_physics(self) -> DrillPhysics:
        self.physics = DrillPhysics(self)
        return self.physics

    def intro(self) -> str:
        return ("Retrieval drill. Face the end boards with your stick on the ice and press A. The puck rims "
                "around to you. Before it gets there, check over your shoulder: winger up the wall, partner "
                "behind the net, center in the middle. Read the forecheck and pass to the open man. "
                f"The first {self.stairs.warmup} reps are a warm-up.")

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
        self.zone = zn.Zone.placed(tuple(rt.JON_BLADE), spot, f, (0.0, -1.0))
        self.head_zone = self.zone.xz(ph)
        puck = zn.ZonePuck(self.play.params, self.zone)
        puck.place(rt.JON_BLADE[0] - 0.6, rt.JON_BLADE[1] + 0.2)     # beside your blade, to play with
        self.play.sim.puck = puck
        self.rep = None
        self.next_sc = None
        self.log.event(t, "zone", how=self.want_place, head=self.head_zone.round(3).tolist(), **self.zone.to_dict())
        self.want_place = None
        self._prepare()

    # ---- reps
    def _prepare(self) -> None:
        """Build the next rep in the background (it takes ~50 ms)."""
        if self._preparing or self.zone is None:
            return
        self._preparing = True
        want, level, head = self.picker.next(), self.stairs.level, self.head_zone.copy()
        params, you = self.play.params, (self.you.pass_speed, self.you.decide_s)

        def work():
            try:
                self.next_sc = rt.make_scenario(self.rng, free_time=level, blade=rt.JON_BLADE, head=head,
                                                ice_mu=params.ice_mu, board_bounce=params.board_bounce, want=want,
                                                pass_speed=you[0], decide_s=you[1])
            finally:
                self._preparing = False
        threading.Thread(target=work, daemon=True, name="prepare-rep").start()

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
                self.rep = rt.Rep(self.next_sc, self.play.sim.puck, number=len(self.results) + 1)
                self.next_sc = None
                self._prepare()
                rep = self.rep
            if rep is None:
                return
        if t - self._last_update < REP_DT:                   # the stick and puck run at 1 kHz; the
            return                                           # rep's checks need far less
        self._last_update = t
        head = None
        if self.play.head is not None:
            Rh, ph = self.play.head
            head = (self.zone.xz(ph), self.zone.dir_to_zone(-Rh[:, 2]))
        blade = self.zone.xz(blade_world) if blade_world is not None else None
        rep.update(t - self.rep_t0, blade, head)
        self._drain(t, rep)

    def _drain(self, t: float, rep: rt.Rep) -> None:
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
            self.stairs.save(STATE_PATH, you=self.you.to_dict())
        except OSError:
            pass
        print(f"  rep {res['rep']}: {res['outcome']:<11} chose {res.get('choice')!s:<8} best {res.get('best')!s:<8}"
              f" looks {res['looks']} (after commit {res['looks_after_commit']})  free {res['free_time']:.2f}s"
              f" -> {self.stairs.level:.2f}s", flush=True)

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
                if rep.state == "done" and rep.result is not None:
                    self._replay(line, zone, rep)
        sandbox.draw_puck(line, self.play.sim.puck)
        sandbox.draw_hands_and_stick(line, self.play, poses, held, stick, state)
        return np.vstack([static, line.array()])

    def _replay(self, line, zone: zn.Zone, rep: rt.Rep) -> None:
        """After a rep: the best pass and the puck's path on the ice, and a map in front of you
        (looking down): the zone, where the forecheckers actually skated, the puck, the best pass."""
        res = rep.result
        start = np.asarray(res.get("release_at") or rt.JON_BLADE, dtype=float)
        best = res.get("best")
        best_to = rep.sc.mates[rt.RECEIVER[best]] if best in rt.RECEIVER else None
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

        def poly(pts, col):
            xz = np.asarray(pts, dtype=float).reshape(-1, 2) - mid
            P = centre + (xz[:, :1] * zone.X + xz[:, 1:] * zone.Z) * MAP_SCALE
            line.many(P[:-1], P[1:], col)

        poly(zn.outline(8), zn.BOARDS)
        poly([(-zn.WIDTH / 2, zn.BLUE_Z), (zn.WIDTH / 2, zn.BLUE_Z)], zn.BLUE)
        gl = zn.side_boards_x(zn.GOAL_Z)
        poly([(-gl, zn.GOAL_Z), (gl, zn.GOAL_Z)], zn.RED)
        x0, x1, z0, z1 = rt.NET_SOLID
        poly([(x0, z1), (x0, z0), (x1, z0), (x1, z1)], zn.RED)
        for path in rep.paths.values():                       # where the forecheckers went
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

    def status(self) -> str:
        rep = self.rep
        st = "waiting" if rep is None else rep.state
        wins = sum(r["success"] for r in self.results)
        err = getattr(self.physics, "errors", 0)
        return f"rep {len(self.results) + (rep is not None and rep.state != 'done')} {st:<8} " \
               f"free {self.stairs.level:.2f}s  wins {wins}/{len(self.results)}" + (f"  ERRORS {err}" if err else "")

    def meta(self) -> dict:
        res = [r for r in self.results if r["counts"]]
        summary = {
            "reps": len(self.results), "counted": len(res),
            "success_pct": round(100 * np.mean([r["success"] for r in res]), 1) if res else None,
            "good_read_pct": round(100 * np.mean([r["good_read"] for r in res]), 1) if res else None,
            "outcomes": {o: sum(r["outcome"] == o for r in self.results) for o in
                         ("complete", "intercepted", "caught", "loose", "cleared", "own_goal", "missed")},
            "looks_mean": round(float(np.mean([r["looks"] for r in res])), 2) if res else None,
            "looked_after_commit_pct": round(100 * np.mean([r["looks_after_commit"] > 0 for r in res]), 1) if res else None,
            "free_time_end": round(self.stairs.level, 3)}
        return {"drill": "retrieval", "summary": summary, "staircase": self.stairs.__dict__,
                "you": {"pass_speed": round(self.you.pass_speed, 2), "decide_s": round(self.you.decide_s, 2)},
                "zone": self.zone.to_dict() if self.zone else None}

    def close(self) -> None:
        s = self.meta()["summary"]
        print(f"drill: {s['reps']} reps, success {s['success_pct']}%, good reads {s['good_read_pct']}%, "
              f"looks/rep {s['looks_mean']}, free time now {s['free_time_end']} s")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--height", default="5'8\"")
    ap.add_argument("--shoots", choices=("left", "right"), default="left")
    ap.add_argument("--free", type=float, help="F1's head start (s) to begin with")
    ap.add_argument("--no-voice", action="store_true")
    ap.add_argument("--no-sound", action="store_true")
    ap.add_argument("--notes", default="")
    args = ap.parse_args()

    base = stickspec.from_height(stickspec.parse_height(args.height), args.shoots)
    fit = grab.Fit.load(record.FIT_PATH) or grab.Fit()
    values = sandbox.Tuning.defaults(base, fit, pk.Params())
    if sandbox.SETTINGS_PATH.exists():
        values.update(json.loads(sandbox.SETTINGS_PATH.read_text())["values"])
    play = sandbox.Play(sandbox.Tuning(base, values))
    DrillMode.free_start = args.free
    run_dir = HERE / "data" / ("drill-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    lock = record.take_lock()
    try:
        sandbox.run(args, play, run_dir, DrillMode)
    except xr.FormFactorUnavailableError:
        raise SystemExit("Headset not connected: put it on, start Link, then run again (xrcheck.py tells you).")
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
