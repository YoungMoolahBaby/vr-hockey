"""Hockey-sense drill: the power-play point. Shoot, or set up a teammate to score.

You are on the left point (blue line, near the left boards), facing the net. Your winger on the
left half wall passes the puck up to you. While it comes, the penalty kill's box commits:

    F1 (high, your side)   pressures you (into your shooting lane, and onto you if you wait:
                           that opens the seam), or shades the seam (your lane stays open)
    F2 (high, far side)    takes away the D-to-D lane (which opens the seam), or drops into the
                           seam (which opens D-to-D)
    D1 (low, your side)    boxes out your net-front man, standing in your shooting lane, or
                           plays beside him (your lane open, his screen on)
    D2 (low, far side)     steps up on your seam shooter, or stays home in front

Your outs:

    shoot     your own shot, through the screen
    partner   D-to-D across to your partner on the right point, for his one-timer
    seam      hard across the box to your shooter in the far circle, for his one-timer

Each is valued in expected goals with the goalie model in goalie.py (the same goalie then plays
the rep): can the pass get there, can the shot get through the box, and does it beat a goalie who
tracks the puck, loses it behind a screen, and slides across on passes. Your own shot is valued
at your shot speed (learned as you play). Each out is the best one equally often. F1's pressure
(the time from the puck reaching you to F1 reaching you) adapts like the retrieval drill's free
time.

Pure logic, no XR: drill.py runs it in the headset; tests/test_powerplay.py drives it with a bot.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

import goalie as gl
import puck as pk
import retrieval as rt
import zone as zn
from retrieval import (BODY_R, CONTACT_R, CONTROL_R, REACH, REACTION, READY_S, RECEIVE_R, ScanTracker, Skater,
                       Track, angle_deg, arrival, option_value, unit)

OPTIONS = ("shoot", "partner", "seam")
RECEIVER = {"partner": "P", "seam": "S"}
SAY = {"shoot": "your shot", "partner": "D to D", "seam": "the seam", "other": "that"}

JON_BLADE = np.array([-8.3, 20.5])        # the left point: your blade, just inside the blue line
FACING = tuple(unit(np.array([0.0, zn.GOAL_Z]) - JON_BLADE))    # you face the net
SHOT_SPEED = 20.0        # m/s: your shot until the drill has learned it (~45 mph)
PASS_SPEED = 12.0        # m/s: your power-play pass until it has learned it (a seam pass is hard)
REACH_SHOT = 0.45        # m: a body or stick this close to a shot's line blocks it
SHOOTERS = {"P": (22.0, 0.25, 0.8), "S": (20.0, 0.25, 0.8), "N": (14.0, 0.30, 0.7)}   # speed, release s, clean
N_DEPTH = 5.25           # z of your net-front man: on the puck's line to the net, screening

TEAMMATES = {"W": ((-11.6, 12.0), (0.3, 1.0)),       # left half wall: passes you the puck
             "P": ((8.3, 20.5), (0.8, 0.6)),          # your partner on the right point
             "S": ((6.4, 9.8), (0.4, 0.6))}           # your shooter in the far circle
PK_START = {"F1": ((-5.0, 13.0), (0.5, 0.6)), "F2": ((3.5, 14.5), (0.6, 0.8)),
            "D1": ((-2.3, 6.0), (0.4, 0.4)), "D2": ((2.3, 6.3), (0.4, 0.4))}
BEHAVIOURS = {"F1": ("pressure", "middle"), "F2": ("high", "low"), "D1": ("box", "side"), "D2": ("up", "home")}
# what usually makes each out the best (found by tabulating all 16 box reads): when an out is
# wanted, each penalty killer does this with the given chance, else either at random
LEANS = {"shoot": {"F1": ("middle", 0.85), "D1": ("side", 0.9), "D2": ("home", 0.75)},
         "partner": {"D1": ("side", 0.9), "D2": ("up", 0.85)},
         "seam": {"F1": ("pressure", 0.9), "F2": ("high", 0.85), "D2": ("home", 0.9)}}


def n_spot(puck_xz, boxed: bool) -> np.ndarray:
    """Your net-front man: on the line from the puck to the middle of the net, screening; or
    pushed a metre off it when he is boxed out."""
    p = np.asarray(puck_xz, dtype=float)
    d = p - gl.NET_C
    f = (N_DEPTH - zn.GOAL_Z) / max(d[1], 1e-6)
    spot = gl.NET_C + d * min(f, 1.0)
    if boxed:
        spot = spot + np.array([-1.0, 0.35])
    return spot


def through(p0, speed: float, opps, target=None) -> float:
    """The chance a shot from p0 at `speed` gets through the box to the net (bodies and sticks)."""
    target = gl.NET_C if target is None else np.asarray(target, dtype=float)
    L = float(np.linalg.norm(target - p0))
    d = (target - p0) / max(L, 1e-9)
    lane = math.inf
    for pos, vel in opps:
        for s in np.linspace(0.5, L - 1.0, 10):
            lane = min(lane, arrival(pos, vel, p0 + s * d, REACH_SHOT) - s / speed)
    return float(gl.sig(lane / 0.08))


def values(p0, mates, opps, boxed: bool, goalie_c, shot_speed: float, pass_speed: float) -> dict:
    """Each out's expected goals for a puck at p0 now: {out: (xG, details)}. Your net-front man
    screens whoever shoots (he follows the puck), unless he is boxed out."""
    p0 = np.asarray(p0, dtype=float)
    them = [pos for pos, _ in opps]
    out = {}
    sees = not gl.blocks_sight(goalie_c, p0, them + [n_spot(p0, boxed)])
    xg, aim = gl.shot_xg(p0, shot_speed, goalie_c, sees)
    thr = through(p0, shot_speed, opps)
    out["shoot"] = (thr * xg, {"through": round(thr, 3), "beat": round(xg, 3), "screened": not sees})
    for o, who in RECEIVER.items():
        q = np.asarray(mates[who], dtype=float)
        p_pass, lane, _ = option_value(p0, q, opps, pass_speed)
        speed, release, clean = SHOOTERS[who]
        t_pass = float(np.linalg.norm(q - p0)) / pass_speed
        g_c = gl.after_tracking(goalie_c, q, t_pass + release)
        b_sees = not gl.blocks_sight(g_c, q, them + [n_spot(q, boxed)])
        xg_r, _ = gl.shot_xg(q, speed, g_c, b_sees, clean)
        thr_r = through(q, speed, opps)
        p_complete = float(gl.sig(lane / 0.12))
        out[o] = (p_complete * thr_r * xg_r, {"pass": round(p_complete, 3), "through": round(thr_r, 3),
                                             "beat": round(xg_r, 3), "goalie_gap": round(float(np.linalg.norm(gl.home(q) - g_c)), 2)})
    return out


class You(rt.You):
    """Your power-play passing and shooting, learned as you play (medians of the last 20): long
    passes are firmer than the retrieval drill's, so they are learned on their own."""

    def __init__(self, speeds=(), decides=(), shots=(), keep: int = 20):
        super().__init__(speeds, decides, keep)
        self.shots = list(shots)[-keep:]

    def add(self, res: dict) -> None:
        v = res.get("release_speed")
        if res.get("choice") == "shoot":
            if v is not None and 6.0 <= v <= 45.0:
                self.shots = (self.shots + [float(v)])[-self.keep:]
            d = res.get("latency")
            if d is not None and 0.0 <= d <= 4.0:
                self.decides = (self.decides + [float(d)])[-self.keep:]
            return
        super().add(res)

    @property
    def pass_speed(self) -> float:
        return float(np.clip(np.median(self.speeds), 9.0, 18.0)) if len(self.speeds) >= 3 else PASS_SPEED

    @property
    def shot_speed(self) -> float:
        return float(np.clip(np.median(self.shots), 12.0, 35.0)) if len(self.shots) >= 3 else SHOT_SPEED

    def to_dict(self) -> dict:
        return {**super().to_dict(), "shots": [round(v, 2) for v in self.shots]}

    @classmethod
    def load(cls, path, key: str = "you_pp") -> "You":
        import json
        from pathlib import Path
        try:
            d = json.loads(Path(path).read_text())[key]
            return cls(d.get("speeds", ()), d.get("decides", ()), d.get("shots", ()))
        except (OSError, ValueError, KeyError, TypeError):
            return cls()


# ----------------------------------------------------------------------------- scenarios


@dataclass
class Scenario:
    seed: int
    behaviours: dict
    free_time: float
    pass_in: float                     # the winger's pass to you, m/s
    t_arrive: float
    t_commit: float
    blade: np.ndarray
    head: np.ndarray
    mates: dict
    tracks: dict                       # PK id -> Track
    shoots: dict
    values: dict                       # {out: xG} when you should be deciding
    best: str
    pass_speed: float = PASS_SPEED
    shot_speed: float = SHOT_SPEED
    decide_s: float = rt.DECIDE_S

    def to_dict(self) -> dict:
        return {"seed": self.seed, "behaviours": self.behaviours, "free_time": round(self.free_time, 3),
                "pass_in": round(self.pass_in, 2), "t_arrive": round(self.t_arrive, 3),
                "t_commit": round(self.t_commit, 3), "blade": self.blade.round(3).tolist(),
                "head": self.head.round(3).tolist(), "mates": {k: v.round(3).tolist() for k, v in self.mates.items()},
                "tracks": {k: v.to_dict() for k, v in self.tracks.items()},
                "values": {k: round(v, 4) for k, v in self.values.items()}, "best": self.best,
                "pass_speed": round(self.pass_speed, 2), "shot_speed": round(self.shot_speed, 2),
                "decide_s": round(self.decide_s, 2)}


def _pk_tracks(r, beh: dict, starts: dict, mates: dict, head, t_commit: float, t_arrive: float,
               free_time: float) -> dict:
    """Each penalty killer holds his box spot, then at t_commit heads where his behaviour takes him."""
    tracks = {}
    for k, b in beh.items():
        s = starts[k]
        if k == "F1" and b == "pressure":
            to = head + 0.8 * unit(s - head)
            t_end = t_arrive + free_time
        else:
            to = {("F1", "middle"): np.array([-2.6, 15.7]),             # shading the seam
                  ("F2", "high"): 0.5 * (JON_BLADE + mates["P"]) + np.array([0.0, -2.2]),
                  ("F2", "low"): np.array([1.5, 11.5]),                # in the seam
                  ("D1", "box"): n_spot(JON_BLADE, False) + np.array([0.15, 0.55]),
                  ("D1", "side"): n_spot(JON_BLADE, False) + np.array([0.9, 0.4]),
                  ("D2", "up"): mates["S"] + np.array([-1.2, -0.6]),
                  ("D2", "home"): np.array([1.2, 5.5])}[(k, b)] + r.uniform(-0.3, 0.3, 2)
            t_end = t_commit + r.uniform(0.7, 1.1)
        move = float(np.linalg.norm(to - s))
        speed = max(move / max(t_end - t_commit, 0.3), 0.5)
        tracks[k] = _HeldTrack(s, to, speed, t_commit)
    return tracks


class _HeldTrack(Track):
    """Stand at `start` until t_hold, then skate straight to `end` at `speed`."""

    def __init__(self, start, end, speed: float, t_hold: float):
        super().__init__([start, end], speed)
        self.t_hold = t_hold
        self.t_end = t_hold + self.length / self.speed

    def at(self, t: float) -> np.ndarray:
        return super().at(t - self.t_hold)

    def vel(self, t: float) -> np.ndarray:
        return super().vel(t - self.t_hold)

    def to_dict(self) -> dict:
        return {**super().to_dict(), "t_hold": round(self.t_hold, 3)}


def make_scenario(rng: np.random.Generator, *, free_time: float, blade, head, ice_mu: float,
                  air_k: float = 0.0, want: str | None = None, pass_speed: float = PASS_SPEED, shot_speed: float = SHOT_SPEED,
                  decide_s: float = rt.DECIDE_S, tries: int = 300, pause_s: float = 0.0,
                  ratio: float = 1.6, min_gap: float = 0.01) -> Scenario:
    """A rep where `want` (or any out) is clearly the best: worth at least `ratio` times the next
    one and at least min_gap expected goals more."""
    import time as _time
    blade, head = np.asarray(blade, dtype=float), np.asarray(head, dtype=float)
    fallback = None
    for _ in range(tries):
        if pause_s:
            _time.sleep(pause_s)
        seed = int(rng.integers(1 << 31))
        r = np.random.default_rng(seed)
        mates = {k: np.array(c) + r.uniform(-1, 1, 2) * np.array(j) for k, (c, j) in TEAMMATES.items()}
        starts = {k: np.array(c) + r.uniform(-1, 1, 2) * np.array(j) for k, (c, j) in PK_START.items()}
        lean = LEANS.get(want, {})
        beh = {k: (lean[k][0] if k in lean and r.random() < lean[k][1] else str(r.choice(v)))
               for k, v in BEHAVIOURS.items()}
        v_in = r.uniform(6.5, 8.0)
        d_in = float(np.linalg.norm(blade - mates["W"]))
        t_arr = pk.slide_time(v_in, d_in, ice_mu, air_k)          # the pass in: ice and air
        if not math.isfinite(t_arr):
            continue
        t_commit = r.uniform(0.3, 0.7)
        tracks = _pk_tracks(r, beh, starts, mates, head, t_commit, t_arr, free_time)
        t_dec = t_arr + float(np.clip(decide_s, 0.3, max(0.3, 0.8 * free_time)))
        opps = [(tr.at(t_dec), tr.vel(t_dec)) for tr in tracks.values()]
        vals = {o: v[0] for o, v in values(blade, mates, opps, beh["D1"] == "box", gl.home(blade), shot_speed,
                                             pass_speed).items()}
        ranked = sorted(vals, key=vals.get, reverse=True)
        top, second = vals[ranked[0]], vals[ranked[1]]
        sc = Scenario(seed, beh, free_time, v_in, t_arr, t_commit, blade, head, mates, tracks,
                      {k: str(r.choice(["L", "R"])) for k in tracks}, vals, ranked[0], pass_speed, shot_speed,
                      decide_s)
        clear = top >= ratio * second and top - second >= min_gap
        if (want is None or ranked[0] == want) and clear:
            return sc
        if (want is None or ranked[0] == want) and (fallback is None or top / max(second, 1e-4) > fallback[0]):
            fallback = (top / max(second, 1e-4), sc)
    if fallback is not None:
        return fallback[1]
    return make_scenario(rng, free_time=free_time, blade=blade, head=head, ice_mu=ice_mu, air_k=air_k, want=None,
                         pass_speed=pass_speed, shot_speed=shot_speed, decide_s=decide_s, tries=tries,
                         pause_s=pause_s, ratio=1.2, min_gap=0.005)


# ----------------------------------------------------------------------------- one rep


class Rep:
    """One rep, run by update() every physics tick (rep time t, s, from when it was made).

    blade: zone (x, z) of your blade's sweet spot, or None; head: (zone (x, z), facing) or None.
    Voice, sounds, buzz and log items collect in `outbox`, as in retrieval.Rep."""

    def __init__(self, sc: Scenario, puck: zn.ZonePuck, number: int = 1, rng=None):
        self.sc, self.puck, self.number = sc, puck, number
        self.rng = rng if rng is not None else np.random.default_rng(sc.seed)
        self.skaters = [Skater(k, "them", sc.shoots[k], tr.at(0.0), tr) for k, tr in sc.tracks.items()]
        self.skaters += [Skater(k, "us", "R" if k == "P" else "L", p.copy(), mode="hold") for k, p in sc.mates.items()]
        self.n = Skater("N", "us", "L", n_spot(sc.mates["W"], False), mode="hold")
        self.skaters.append(self.n)
        self.by_id = {s.id: s for s in self.skaters}
        self.goalie = gl.Goalie(sc.mates["W"])
        self.paths = {s.id: [s.pos.copy()] for s in self.skaters if s.team == "them"}
        self.state, self.t, self.go_at = "ready", 0.0, READY_S
        self.scan = ScanTracker()
        self.outbox: list[tuple] = []
        self.trail: list[np.ndarray] = []
        self.t_near = self.t_control = self.t_release = self.t_done = None
        self.control_since = self.slow_since = None
        self.last_blade = None
        self.release = None
        self.shot = None                       # {"by": id, "t": tau, ...}
        self.holder = None                     # teammate with the puck, waiting to shoot
        self.result: dict | None = None
        self._last_skate = -1.0
        w = sc.mates["W"]
        puck.place(w[0] + 0.6, w[1] + 0.3)

    @property
    def tau(self) -> float:
        return self.t - self.go_at

    def _xz(self):
        return self.puck.zone.xz(self.puck.pos), self.puck.zone.dir_to_zone(self.puck.vel)

    def _opps(self):
        return [(s.pos.copy(), s.vel.copy()) for s in self.skaters if s.team == "them"]

    def _values(self, p0) -> dict:
        sc = self.sc
        boxed = self.sc.behaviours["D1"] == "box" and self.tau >= self.sc.t_commit + 0.6
        return values(p0, sc.mates, self._opps(), boxed, self.goalie.c, sc.shot_speed, sc.pass_speed)

    # -- the tick
    def update(self, t: float, blade, head) -> None:
        self.t = t
        if self.state == "done":
            return
        if blade is not None:
            self.last_blade = np.asarray(blade, dtype=float)
        if self.state == "ready":
            if t >= self.go_at:
                self.state = "live"
                w = self.sc.mates["W"]
                p0 = np.array([w[0] + 0.6, w[1] + 0.3])
                to = self.last_blade if self.last_blade is not None else self.sc.blade
                v = self.sc.pass_in * unit(to - p0)
                self.puck.place(p0[0], p0[1], v[0], v[1])
                self.outbox += [("sound", "go", 1.0), ("buzz", 0.4, 40)]
                self.outbox.append(("log", "rep_go", {"rep": self.number, "drill": "powerplay", **self.sc.to_dict()}))
            return
        pxz, pv = self._xz()
        speed = float(np.linalg.norm(pv))
        if t - self._last_skate >= 0.01:
            dt = 0.01 if self._last_skate < 0 else min(t - self._last_skate, 0.05)
            self._last_skate = t
            self._skate(dt, pxz, pv, head)
        y = float(self.puck.pos[1])
        b = self.last_blade
        near = b is not None and float(np.linalg.norm(pxz - b)) < CONTROL_R
        if b is not None and self.t_near is None and float(np.linalg.norm(pxz - b)) < 1.0:
            self.t_near = self.tau
        if self.state == "live":
            self._live(pxz, speed, near, head)
        elif self.state == "control":
            self._control(pxz, pv, speed, near, head)
        elif self.state == "pass":
            self._pass(pxz, speed, y, near)
        elif self.state == "held":
            self._held()
        elif self.state == "shot":
            self._shot(pxz, pv, speed, y)

    def _skate(self, dt, pxz, pv, head) -> None:
        for s in self.skaters:
            if s is self.n:
                boxed = self.sc.behaviours["D1"] == "box" and self.tau >= self.sc.t_commit + 0.6
                want = n_spot(pxz if self.holder is None else self.by_id[self.holder].pos, boxed)
                step = want - s.pos
                d = float(np.linalg.norm(step))
                s.vel = step / dt if d < 3.0 * dt else unit(step) * 3.0
                s.pos = s.pos + s.vel * dt
                s.stride += float(np.linalg.norm(s.vel)) * dt
                s.facing = unit(s.pos - gl.NET_C)              # back to the goalie, facing the play
            else:
                s.step(self.tau, dt, pxz, pv)
            path = self.paths.get(s.id)
            if path is not None and float(np.linalg.norm(s.pos - path[-1])) > 0.25:
                path.append(s.pos.copy())
        bodies = [s.pos for s in self.skaters]
        self.goalie.step(self.tau, dt, pxz, pv, bodies)
        if head is not None:
            self.scan.update(self.tau, head[0], head[1], pxz, {s.id: s.pos for s in self.skaters})
        if not self.trail or np.linalg.norm(pxz - self.trail[-1]) > 0.15:
            self.trail.append(pxz.copy())

    def _hit(self, pxz, head) -> str | None:
        for s in self.skaters:
            if s.team != "them":
                continue
            if head is not None and float(np.linalg.norm(s.pos - np.asarray(head[0]))) < CONTACT_R:
                return s.id
            if self.t_control is not None and float(np.linalg.norm(s.pos - pxz)) < REACH * 0.8:
                return s.id
        return None

    def _live(self, pxz, speed, near, head) -> None:
        if near and speed < 2.5:
            self.control_since = self.control_since if self.control_since is not None else self.tau
            if self.tau - self.control_since >= 0.1:
                self.state, self.t_control = "control", self.control_since
                self.outbox.append(("log", "rep_control", {"rep": self.number, "tau": round(self.t_control, 3)}))
            return
        self.control_since = None
        b = self.last_blade
        gone = b is not None and self.t_near is not None and float(np.linalg.norm(pxz - b)) > 2.5
        if gone or self.puck.cleared or self.tau > self.sc.t_arrive + 3.0:
            self._finish("missed")

    def _control(self, pxz, pv, speed, near, head) -> None:
        who = self._hit(pxz, head)
        if who:
            return self._finish("caught", by=who)
        b = self.last_blade
        gone = float(np.linalg.norm(pxz - b)) if b is not None else 9.0
        if gone > 0.7 and speed > 2.5:
            vals = self._values(pxz)
            choice, kind = self._classify(pxz, pv, speed)
            self.t_release = self.tau
            self.release = {"at": pxz.copy(), "speed": speed, "values": vals, "choice": choice}
            if kind == "shot":
                self._start_shot("you")
            else:
                self.state = "pass"
                for s in self.skaters:
                    if s.team == "them":
                        s.react_at = self.tau + REACTION
            self.slow_since = None
        elif gone > 2.5 and speed < 0.5:
            self._finish("loose")

    def _classify(self, pxz, pv, speed) -> tuple[str, str]:
        if speed > 9.0 and pv[1] < 0:
            x_at = pxz[0] + pv[0] * (zn.GOAL_Z - pxz[1]) / pv[1]
            if abs(x_at) < zn.NET_HALF_W + 2.0:
                return "shoot", "shot"
        best, ang = "other", 25.0
        for o, who in RECEIVER.items():
            a = angle_deg(pv, self.sc.mates[who] - pxz)
            if a < ang:
                best, ang = o, a
        return best, "pass"

    def _pass(self, pxz, speed, y, near) -> None:
        for s in self.skaters:
            if s.team == "them":
                r = REACH if y < pk.H / 2 + 0.12 else BODY_R
                if float(np.linalg.norm(s.pos - pxz)) < r:
                    return self._finish("intercepted", by=s.id)
        for s in self.skaters:
            if s.team == "us" and y < 0.5 and float(np.linalg.norm(s.pos - pxz)) < RECEIVE_R:
                if s.id == "W":
                    return self._finish("reset", by="W")
                self.holder, self.state = s.id, "held"
                self.held_at = self.tau
                self.puck.vel = np.zeros(3)
                self.puck.place(*(s.pos + 0.7 * s.facing))
                if self.release is not None and self.release["choice"] not in RECEIVER:
                    self.release["choice"] = next((o for o, w in RECEIVER.items() if w == s.id), "other")
                return
        if self.puck.cleared:
            return self._finish("cleared")
        if near and speed < 2.5:
            self.state, self.release = "control", None
            return
        if speed < 0.4:
            self.slow_since = self.slow_since if self.slow_since is not None else self.tau
            if self.tau - self.slow_since > 0.8:
                return self._finish("loose")
        else:
            self.slow_since = None

    def _held(self) -> None:
        s = self.by_id[self.holder]
        speed, release, clean = SHOOTERS[self.holder]
        if self.tau - self.held_at < release:
            return
        origin = s.pos + 0.7 * unit(gl.NET_C - s.pos)
        xg, aim = gl.shot_xg(origin, speed, self.goalie.c, self.goalie.sees)
        wild = 1.0 if self.rng.random() < clean else 3.0          # a fanned one-timer goes anywhere
        a = gl.aimed(self.rng, aim, origin, wild)
        v = gl.launch(origin, a, speed)
        zone = self.puck.zone
        self.puck.place(origin[0], origin[1])
        self.puck.vel = zone.dir_to_world(v[0], v[2]) + np.array([0.0, v[1], 0.0])
        self._start_shot(self.holder)

    def _start_shot(self, by: str) -> None:
        self.state = "shot"
        self.shot = {"by": by, "t": self.tau}
        self.goalie.last_s = None

    def _shot(self, pxz, pv, speed, y) -> None:
        shooter = self.shot["by"]
        for s in self.skaters:                                   # blocked by a body or a stick
            if s.team != "them":
                continue
            d = float(np.linalg.norm(s.pos - pxz))
            if (y < 1.6 and d < BODY_R) or (y < 0.15 and d < REACH_SHOT):
                return self._finish("blocked", by=s.id)
        if self.goalie.check(pxz, y, self.rng) == "save":
            self.puck.vel = self.puck.vel * -0.15
            return self._finish("save", by=shooter)
        if self.puck.in_net:
            return self._finish("goal", by=shooter)
        if pxz[1] < zn.GOAL_Z - 0.3 or speed < 2.0 or self.tau - self.shot["t"] > 3.0:
            return self._finish("miss", by=shooter)

    # -- the end of a rep
    def _finish(self, outcome: str, by: str | None = None) -> None:
        self.state, self.t_done = "done", self.tau
        for s in self.skaters:
            s.mode, s.vel = "hold", np.zeros(2)
        if outcome in ("intercepted", "blocked", "reset"):
            self.puck.vel = np.zeros(3)
        rel = self.release
        t_end = self.t_control if self.t_control is not None else self.tau
        looks = self.scan.between(0.0, t_end)
        res = {"rep": self.number, "drill": "powerplay", "outcome": outcome, "by": by,
               "shooter": self.shot["by"] if self.shot else None, "behaviours": self.sc.behaviours,
               "free_time": round(self.sc.free_time, 3), "t_arrive_est": round(self.sc.t_arrive, 3),
               "t_commit": round(self.sc.t_commit, 3), "t_near": rt._r(self.t_near),
               "t_control": rt._r(self.t_control), "t_release": rt._r(self.t_release), "t_done": rt._r(self.tau),
               "looks": len(looks), "looks_after_commit": len([s for s in looks if s[1] >= self.sc.t_commit]),
               "best_planned": self.sc.best, "values_planned": {k: round(v, 4) for k, v in self.sc.values.items()},
               "pass_speed": round(self.sc.pass_speed, 2), "shot_speed_model": round(self.sc.shot_speed, 2)}
        if rel is not None:
            xg = {k: v[0] for k, v in rel["values"].items()}
            best = max(xg, key=xg.get)
            chosen = rel["choice"]
            v_ch = xg.get(chosen, 0.0)
            res.update(choice=chosen, best=best, xg={k: round(v, 4) for k, v in xg.items()},
                       why={k: v[1] for k, v in rel["values"].items()},
                       value_chosen=round(v_ch, 4), value_best=round(xg[best], 4),
                       decision=round(v_ch / max(xg[best], 1e-6), 3), release_speed=round(rel["speed"], 2),
                       release_at=rel["at"].round(3).tolist(),
                       latency=rt._r(self.t_release - self.t_control) if self.t_control is not None else None)
            if chosen == "shoot":
                res["shot_speed"] = round(rel["speed"], 2)
            res["good_read"] = chosen == best or v_ch >= 0.85 * xg[best]
        else:
            res.update(choice=None, best=self.sc.best, good_read=False)
        res["success"] = res["good_read"] and outcome in ("goal", "save")
        res["counts"] = outcome != "missed"
        self.result = res
        self.outbox.append(("say", verdict(res)))
        self.outbox.append(("sound", "go" if outcome == "goal" else "whistle", 1.0 if outcome == "goal" else 0.6))
        if outcome == "goal":
            self.outbox.append(("buzz", 1.0, 120))
        self.outbox.append(("log", "rep", res))


def verdict(res: dict) -> str:
    out, best, ok = res["outcome"], res.get("best"), res["good_read"]
    best_s = SAY.get(best, "")
    if out == "missed":
        return "Missed the pass."
    if out == "goal":
        head = "Goal!" if ok else f"Goal! But {best_s} was the better play."
    elif out == "save":
        head = "Saved. Right play." if ok else f"Saved. {best_s.capitalize()} was the play."
    elif out == "blocked":
        head = "Blocked." if ok else f"Blocked. {best_s.capitalize()} was the play."
    elif out == "miss":
        head = "Wide." if ok else f"Wide. {best_s.capitalize()} was the play."
    elif out == "intercepted":
        head = "Right read, but picked off." if ok else f"Picked off. {best_s.capitalize()} was open."
    elif out == "caught":
        head = f"Pressured off it. {best_s.capitalize()} was there."
    elif out == "reset":
        head = f"Back to the wall. {best_s.capitalize()} was there."
    else:
        head = f"Lost it. {best_s.capitalize()} was there."
    if res["looks"] == 0 and best != "shoot":
        return head + " No look."
    return head
