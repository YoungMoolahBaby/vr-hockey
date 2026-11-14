"""How the 3v3 AI plays, in numbers: the acceptance table of reports/Lifelike AI players.md
(section 4), from self-play or from a game you played in the headset.

    uv run python selfplay_metrics.py                        # 4 self-play games of 600 s (seeds 0-3), in parallel
    uv run python selfplay_metrics.py --seconds 120 --seeds 0 1
    uv run python selfplay_metrics.py --set CARRY=0.85       # an A/B: a constant of threes.py changed for the run
    uv run python selfplay_metrics.py data/game-20261114-101500    # a game you played (its ai.csv, events.jsonl)
    uv run python selfplay_metrics.py data/selfplay-20261113-160000 --json out.json   # read again; save the numbers

Self-play: all six skaters are AI, with the real 1 kHz puck, and the AI is capped as in the headset
(0.95 of your sprint speed, --you-sprint, default 4.5 m/s: Jon's setting). Each game is written the way
game.py records one (ai.csv every AI tick, the game's log items in events.jsonl) to
data/selfplay-<time>/s<seed>/, then read back, so self-play and your games are scored by the same code.

The table: the report's baseline (measured 2026-11-13 on the AI before any of its changes, with
its own probe; this script reproduces it within the spread between seeds), this run, and the
report's target. Definitions as in the report: a target jump is a skater's steering target moving
more than 2 m in one AI tick (where he steers, and where his role says to go before
change 4's smoothing); a shove, a skater moved more than 3 cm beyond his velocity in one tick;
a role reaction, the time from a change of who has the puck to a skater's role target (before the
smoothing) first moving more than 1.5 m. The first 0.5 s after each faceoff is left out.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

import arena as ar
import puck as pk
import threes as th
import zone as zn

HERE = Path(__file__).resolve().parent
YOU_MS = 3.0             # m/s: Jon's skate setting (his cruise) ...
YOU_SPRINT = 4.5         # m/s: ... and his sprint: the AI's top is 0.95 of the faster, as in the headset

# reports/Lifelike AI players.md, section 4: (baseline, target). The baseline is four 600 s self-play
# games (seeds 0-3) at an AI top of 2.85 m/s, level 1, on main at 7d9ad8c.
TABLE = [
    # key, label, baseline, target, format
    ("role_same_tick", "Role changes on the same tick as a possession change", 0.951, "<= 25%", "pct"),
    ("role_median_s", "... median role reaction (s)", 0.0, "0.2-0.3", "f2"),
    ("target_jumps", "Target jumps > 2 m (where they steer), per skater-min", 48.1, "< 2", "f1"),
    ("raw_jumps", "... before the smoothing (their roles)", 48.1, "", "f1"),
    ("raw_jumps_settled", "... of those, in settled play", 9.3, "", "f1"),
    ("chaser_changes", "Chaser changes, per team per loose-puck min", 4.3, "< 1", "f1"),
    ("chaser_back", "... back to the first chaser within 1 s", 0.392, "< 5%", "pct"),
    ("marks_settled", "Mark changes in settled play, per skater per game-min", 2.14, "< 0.5", "f2"),
    ("shoves", "Shoves, per skater-min", 27.1, "< 1", "f1"),
    ("you_jumps", "... within 2 m of you, per min (a game you played)", None, "0", "f1"),
    ("you_closest", "Closest an AI skater comes to you, median minute (m)", None, "", "f2"),
    ("cap_flips", "Acceleration reversals at the limit, per skater-min", 35.6, "< 2", "f1"),
    ("jerk_p99", "Jerk p99 (m/s^3)", 458, "< 100", "f0"),
    ("hard_acc", "Hard speed-ups, per skater-min", 12.2, "3-6", "f1"),
    ("hard_dec", "Hard slow-downs, per skater-min", 12.1, "3-6, >= speed-ups", "f1"),
    ("mean_speed", "Mean speed / top", 0.844, "0.40-0.55", "f2"),
    ("ge90", "Time at >= 90% of top", 0.638, "<= 10%", "pct"),
    ("standing", "Standing (< 0.3 m/s)", 0.018, "10-20%", "pct"),
    ("gliding", "Gliding (coasting: no push)", 0.0, "20-30%", "pct"),
    ("bursting", "Going flat out on a read", None, "", "pct"),
    ("backward", "Skating backward (facing > 120 deg off travel, moving)", 0.0039, "8-15%", "pct1"),
    ("carry_p90", "Carry speed p90 / top", 0.85, "0.95", "f2"),
    ("missed_catch", "Intercepted passes after a missed catch", 0.427, "< 15%", "pct"),
    ("completion", "Pass completion (intended receiver next)", 0.45, "65-80%", "pct"),
    ("opp_1m", "Passes with an opponent within 1 m", 0.658, "< 25%", "pct"),
    ("over_90", "Passes > 90 deg from the passer's facing", 0.498, "< 15%", "pct"),
    ("pass_len", "Median pass length (m)", 7.3, "9-12", "f1"),
    ("losses_per_s", "Losses per second of carrying", 0.339, "0.05-0.10", "f2"),
    ("poke_touches", "Touches ending in a poke", 0.344, "< 15%", "pct"),
    ("nearest_def", "Nearest defender to the carrier, median (m)", 1.17, "2-4", "f2"),
    ("stick_in_reach", "Defender's stick in poke reach (of carrier time)", 0.579, "20-35%", "pct"),
    ("no_open_mate", "Carrier time with no open teammate", 0.29, "< 10%", "pct"),
    ("away_touches", "Touches with >= 1 s skating away from the net", 0, "some", "int"),
    ("min_release", "Fastest release (s)", 0.161, "~0.1", "f3"),
    ("quick_shots", "Shots within 0.5 s of a received pass", 0.149, "10-20%", "pct"),
    ("puck_behind", "Off-puck time with the puck behind him", 0.162, "~same, seen", "pct"),
    ("to_you", "AI teammates' passes that go to you", 0.175, "35-50% when open", "pct"),
    ("tick_mean_ms", "AI tick, mean (ms)", 0.90, "<= 1.5", "f2"),
    ("tick_p99_ms", "AI tick, p99 (ms)", 1.96, "<= 2.5", "f2"),
]
WATCH = [
    ("goals_per_min", "Goals per live game-min", 0.67, "f2"),
    ("shots_per_min", "Shots per game-min", 2.5, "f2"),
    ("touch_mean", "AI touch, mean (s)", 1.0, "f2"),
    ("touch_median", "AI touch, median (s)", 0.6, "f2"),
    ("touches_per_min", "Touches per game-min", 20.3, "f1"),
]


def _plain(x):
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, np.ndarray):
        return x.tolist()
    return str(x)


# ----------------------------------------------------------------------------- self-play

def make_game(seed: int, you_ms: float = YOU_MS, you_sprint: float = YOU_SPRINT):
    """All six skaters AI, the real puck physics (as tests/test_threes.py's make())."""
    params = pk.Params()
    rink = ar.Arena(zn.Zone(np.array([3.0, 0.0, -1.0]), np.array([0.6, 0.0, -0.8])))
    sim = pk.Sim(params, pk.Rink(), 70)
    sim.puck = ar.ArenaPuck(params, rink)
    game = th.Game(rink, sim.puck, np.random.default_rng(seed), to_goals=99, you=False)
    game.you_ms, game.you_sprint = you_ms, you_sprint
    return sim, game


def _value(s: str):
    """A --set value: a number, or numbers separated by commas (a tuple)."""
    parts = [float(p) for p in s.split(",")]
    return parts[0] if len(parts) == 1 else tuple(parts)


def play_one(job: tuple) -> dict:
    """One self-play game, recorded to `out` as ai.csv, events.jsonl and meta.json."""
    seed, seconds, out, you_ms, sets, *rest = job
    you_sprint = rest[0] if rest else YOU_SPRINT
    for name, _ in sets:
        if not hasattr(th, name):
            raise SystemExit(f"threes.py has no {name}")
    old = {name: getattr(th, name) for name, _ in sets}
    try:
        for name, value in sets:
            setattr(th, name, value)
        return _play(seed, seconds, Path(out), you_ms, sets, you_sprint)
    finally:
        for name, value in old.items():                # as it was (this may be the caller's process)
            setattr(th, name, value)


def _play(seed: int, seconds: float, out: Path, you_ms: float, sets: list, you_sprint: float = YOU_SPRINT) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    sim, g = make_game(seed, you_ms, you_sprint)
    ticks = []
    wall = time.perf_counter()
    with open(out / "ai.csv", "w", encoding="utf-8") as ai, open(out / "events.jsonl", "w", encoding="utf-8") as ev:
        ev.write(json.dumps({"t": 0.0, "event": "rink", **g.arena.to_dict()}) + "\n")
        g.start()
        ai.write(g.ai_header())
        last = g._last_ai
        for i in range(int(seconds * 1000)):
            t = i * 0.001
            sim.step(0.001, None, None)
            sim.puck.events.clear()
            w = time.perf_counter()
            g.update(t)
            if g._last_ai != last:
                ticks.append(time.perf_counter() - w)
                last = g._last_ai
                ai.write(g.ai_row())
            for item in g.outbox:
                if item[0] == "log":
                    ev.write(json.dumps({"t": round(t, 4), "event": item[1], **item[2]}, default=_plain) + "\n")
            g.outbox.clear()
    ms = np.array(ticks) * 1000
    meta = {"kind": "selfplay", "seed": seed, "seconds": seconds, "you_ms": you_ms, "you_sprint": you_sprint,
            "set": {k: v for k, v in sets}, "score": g.score, "stats": {k: v for k, v in g.stats.items() if k != "goals"},
            "ai_tick_ms": [round(float(ms.mean()), 3), round(float(np.percentile(ms, 99)), 3)],
            "wall_s": round(time.perf_counter() - wall, 1)}
    (out / "meta.json").write_text(json.dumps(meta, indent=1, default=_plain))
    return meta


# ----------------------------------------------------------------------------- reading a game

class Run:
    """One recorded game: ai.csv as arrays, events.jsonl as a list."""

    def __init__(self, d: Path):
        self.dir = d
        with open(d / "ai.csv", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        head, rows = rows[0], [r for r in rows[1:] if len(r) == len(rows[0])]
        self.col = {c: i for i, c in enumerate(head)}
        self.rows = rows
        self.ids = [c[:-2] for c in head if c.endswith("_x") and c[:-2] not in ("you", "home", "far")]
        self.n = len(rows)
        self.events = []
        if (d / "events.jsonl").exists():
            with open(d / "events.jsonl", encoding="utf-8") as f:
                self.events = [json.loads(line) for line in f if line.strip()]
        rink = [e for e in self.events if e.get("event") == "rink" and "length" in e]
        self.length = float(rink[-1]["length"]) if rink else ar.LENGTH
        meta = d / "meta.json"
        self.meta = json.loads(meta.read_text()) if meta.exists() else {}

    def s(self, name: str) -> np.ndarray:
        i = self.col[name]
        return np.array([r[i] for r in self.rows], dtype=object)

    def f(self, *names: str) -> np.ndarray:
        """Numeric columns, (n,) or (n, k); an empty field is NaN."""
        idx = [self.col[c] for c in names]
        a = np.array([[float(r[i]) if r[i] != "" else np.nan for i in idx] for r in self.rows], dtype=float)
        return a[:, 0] if len(names) == 1 else a

    def net(self, team: str) -> np.ndarray:
        """The net `team` attacks."""
        return np.array([0.0, self.length - zn.GOAL_Z if team == "us" else zn.GOAL_Z])


def team_of(pid: str) -> str:
    return "us" if pid.startswith("U") or pid == "you" else "them"


def _ang(u, v) -> np.ndarray:
    """Unsigned angles (deg) between rows of u and v."""
    return np.degrees(np.abs(np.arctan2(u[..., 0] * v[..., 1] - u[..., 1] * v[..., 0], (u * v).sum(-1))))


def _pct(x, q) -> float:
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    return float(np.percentile(x, q)) if len(x) else float("nan")


class Score:
    """The table's measures, summed over games."""

    def __init__(self):
        self.A = Counter()
        self.L: dict[str, list] = {}
        self.passes, self.shots, self.touches = [], [], []
        self.ticks_ms = []
        self.vmax = []

    def add(self, key: str, x) -> None:
        self.L.setdefault(key, []).append(np.atleast_1d(np.asarray(x, dtype=float)))

    def cat(self, key: str) -> np.ndarray:
        v = self.L.get(key)
        return np.concatenate(v) if v else np.array([])

    # ------------------------------------------------------------------ one game
    def game(self, r: Run) -> None:
        A = self.A
        t = r.f("t")
        if r.n < 3:
            return
        state, holder = r.s("state"), r.s("holder")
        live = state == "live"
        ids = r.ids
        J = len(ids)
        jx = {pid: j for j, pid in enumerate(ids)}
        H = np.array([jx.get(h, {"home": -2, "far": -3, "you": -4}.get(h, -1)) for h in holder])
        vm = r.f("vmax")
        self.vmax.append(float(np.nanmedian(vm)))
        PK = r.f("px", "pz")
        P = np.stack([r.f(f"{p}_x", f"{p}_z") for p in ids], 1)
        V = np.stack([r.f(f"{p}_vx", f"{p}_vz") for p in ids], 1)
        F = np.stack([r.f(f"{p}_fx", f"{p}_fz") for p in ids], 1)
        B = np.stack([r.f(f"{p}_bx", f"{p}_bz") for p in ids], 1)
        TG = np.stack([r.f(f"{p}_tx", f"{p}_tz") for p in ids], 1)
        RT = (np.stack([r.f(f"{p}_rx", f"{p}_rz") for p in ids], 1) if f"{ids[0]}_rx" in r.col
              else TG)                               # where their roles said to go (logs before change 4: = TG)
        MK = np.stack([r.s(f"{p}_mark") for p in ids], 1)
        teams = [team_of(p) for p in ids]
        YP, YB = r.f("you_x", "you_z"), r.f("you_bx", "you_bz")
        you_in = not np.all(np.isnan(YP[:, 0]))
        YV = np.gradient(YP, t, axis=0) if you_in else None
        self.A["with_you"] += int(you_in)

        n = r.n
        dt_ = np.r_[np.diff(t), np.median(np.diff(t))]
        ok = np.zeros(n, bool)                       # live, but not the first 0.5 s after a drop
        start = None
        for i in range(n):
            if live[i] and start is None:
                start = t[i]
            if not live[i]:
                start = None
            ok[i] = start is not None and t[i] - start > 0.5
        okk = ok[1:] & ok[:-1]
        gmin = float(dt_[ok].sum()) / 60
        A["game_min"] += gmin
        live_min = float(dt_[live].sum()) / 60
        A["live_min"] += live_min

        # who has it: changes, short spells
        hch = np.r_[False, (H[1:] != H[:-1]) & okk]
        ci = np.flatnonzero(hch)
        A["holder_changes"] += len(ci)
        near_h = np.zeros(n, bool)
        for i in ci:
            near_h[max(0, i - 1):i + 2] = True

        # the attacking team, tick by tick (kept through loose spells), for marks
        att = np.empty(n, dtype=object)
        flip_at = np.zeros(n)
        cur, flip_t = None, -9.0
        for i in range(n):
            if not live[i]:
                cur, flip_t = None, t[i]
            else:
                h = holder[i]
                tm = (team_of(h) if h in jx or h == "you" else
                      ("us" if h == "home" else "them" if h == "far" else None))
                if tm is not None and tm != cur:
                    cur, flip_t = tm, t[i]
            att[i], flip_at[i] = cur, flip_t

        for j in range(J):
            p, v, fc, tg, rt = P[:, j], V[:, j], F[:, j], TG[:, j], RT[:, j]
            s = np.linalg.norm(v, axis=1)
            A["skater_min"] += gmin
            self.add("speed_frac", s[ok] / vm[ok])
            A["ticks"] += int(ok.sum())
            A["standing"] += int(np.sum(ok & (s < 0.3)))
            A["ge90"] += int(np.sum(ok & (s >= 0.9 * vm)))
            if f"{ids[j]}_mode" in r.col:
                A["coast"] += int(np.sum(ok & (r.s(f"{ids[j]}_mode") == "coast")))
                A["burst"] += int(np.sum(ok & (r.s(f"{ids[j]}_go") == "1")))
                A["mode_ticks"] += int(ok.sum())
            dv = np.diff(v, axis=0)
            gap = np.diff(t)
            acc = np.linalg.norm(dv, axis=1) / gap
            big = acc > 0.9 * th.ACCEL
            flip = _ang(dv[:-1], dv[1:]) > 90
            A["cap_flips"] += int(np.sum(big[1:] & big[:-1] & flip & okk[1:] & okk[:-1]))
            av = dv / gap[:, None]
            jerk = np.linalg.norm(np.diff(av, axis=0), axis=1) / gap[1:]
            self.add("jerk", jerk[okk[1:] & okk[:-1]])
            ds = np.gradient(np.convolve(s, np.ones(13) / 13, "same"), t)
            for sign, name in ((1, "hard_acc"), (-1, "hard_dec")):
                m = (sign * ds > 2.0) & ok
                e = np.flatnonzero(np.diff(np.r_[0, m.astype(int), 0]))
                A[name] += sum(1 for a0, a1 in zip(e[::2], e[1::2]) if a1 - a0 >= 15)
            mv = ok & (s > 1.0)
            self.add("face_off", _ang(fc[mv], v[mv]))
            resid = np.linalg.norm(np.diff(p, axis=0) - v[1:] * gap[:, None], axis=1)
            A["shoves"] += int(np.sum((resid > 0.03) & okk))
            if you_in:
                near = np.nan_to_num(np.linalg.norm(p - YP, axis=1), nan=9.0)[1:] < 2.0
                A["you_jumps"] += int(np.sum((resid > 0.03) & okk & near))
            tj = np.nan_to_num(np.linalg.norm(np.diff(tg, axis=0), axis=1))
            A["target_jumps"] += int(np.sum((tj > 2.0) & okk))
            rj = np.nan_to_num(np.linalg.norm(np.diff(rt, axis=0), axis=1))
            jumps = np.flatnonzero((rj > 2.0) & okk) + 1
            A["raw_jumps"] += len(jumps)
            A["raw_jumps_settled"] += int(np.sum(~near_h[jumps]))
            for i in ci:                              # role reactions: when his role first moves him
                if i < 1 or np.isnan(rt[i - 1]).any():
                    continue
                ref = rt[i - 1]
                for k in range(i, min(n, i + 50)):
                    if not ok[k]:
                        break
                    if not np.isnan(rt[k]).any() and np.linalg.norm(rt[k] - ref) > 1.5:
                        self.add("react", t[k] - t[i])
                        break
            off = ok & (H != j)
            self.add("behind", _ang(fc[off], PK[off] - p[off]) > 90)
            mk = MK[:, j]
            defending = np.array([a is not None and a != teams[j] for a in att])
            for i in np.flatnonzero(defending[1:] & ok[1:] & ok[:-1]) + 1:
                if mk[i] != mk[i - 1] and mk[i] and mk[i - 1]:
                    A["marks_after_flip" if t[i] - flip_at[i] <= 0.65 else "marks_settled"] += 1

        if you_in:                                   # the closest any AI skater came to you, minute by minute
            gapsy = np.nanmin(np.linalg.norm(P - YP[:, None, :], axis=2), axis=1)
            for m0 in np.arange(t[0], t[-1], 60.0):
                w = ok & (t >= m0) & (t < m0 + 60.0) & ~np.isnan(gapsy)
                if w.sum() > 100:
                    self.add("you_closest", float(gapsy[w].min()))
            A["you_min"] += gmin
        loose = ok & (H == -1)                        # chasers
        A["loose_min"] += 2 * float(dt_[loose].sum()) / 60
        for team in ("us", "them"):
            c = r.s(f"chase_{team}")
            chg = np.flatnonzero(loose[1:] & loose[:-1] & (c[1:] != c[:-1]) & (c[1:] != "") & (c[:-1] != "")) + 1
            A["chaser_changes"] += len(chg)
            for i in chg:
                w = np.flatnonzero((t > t[i]) & (t <= t[i] + 1.0))
                if len(w) and np.any(c[w] == c[i - 1]):
                    A["chaser_back"] += 1

        # the carrier, tick by tick
        carrying = np.flatnonzero(ok & (H >= 0))
        A["carry_s"] += len(carrying) * float(np.median(dt_))
        for i in carrying:
            j = H[i]
            tm = teams[j]
            origin = PK[i]
            opp_pos = [P[i, k] for k in range(J) if teams[k] != tm]
            opp_blade = [B[i, k] for k in range(J) if teams[k] != tm]
            mates = [(B[i, k], V[i, k]) for k in range(J) if teams[k] == tm and k != j]
            if you_in and not np.isnan(YP[i, 0]):
                yb = YB[i] if not np.isnan(YB[i, 0]) else YP[i]
                if tm == "us":
                    mates.append((yb, YV[i]))
                else:
                    opp_pos.append(YP[i])
                    opp_blade.append(yb)
            body = min(float(np.linalg.norm(o - P[i, j])) for o in opp_pos)
            stick = min(float(np.linalg.norm(o - origin)) for o in opp_blade)
            n_open = 0
            for q, mv_ in mates:
                lead = q + th._cap(mv_ * (float(np.linalg.norm(q - origin)) / th.PASS_MS), th.LEAD_MAX)
                n_open += th.lane_odds(origin, lead, opp_pos, th.PASS_MS, 1.0, vm[i]) > 0.55
            self.add("press", body)
            self.add("stick_in", float(stick < th.POKE_R))
            self.add("no_open", float(n_open == 0))
            self.add("carry_speed", float(np.linalg.norm(V[i, j])) / vm[i])

        # touches (an AI skater's spells with the puck), passes, shots
        ev = [e for e in r.events if e.get("event") in ("take", "pass", "shot", "lost", "fumble", "goal")]
        ev_t = np.array([e["t"] for e in ev]) if ev else np.zeros(0)

        def at(ti: float, kind: str, **match):
            for k in np.flatnonzero(np.abs(ev_t - ti) < 0.0015):
                e = ev[k]
                if e["event"] == kind and all(e.get(a) == b for a, b in match.items()):
                    return e
            return None

        spell_start = {}                              # (j, end index) -> start index
        i = 0
        while i < n:
            if H[i] >= 0 and live[i]:
                j, s0 = H[i], i
                while i < n and H[i] == j and live[i]:
                    i += 1
                pid = ids[j]
                spell_start[(j, i)] = s0
                if i >= n:
                    how = "end"
                elif not live[i]:
                    how = "reset"
                elif at(t[i], "pass", by=pid):
                    how = "pass"
                elif at(t[i], "shot", by=pid):
                    how = "shot"
                else:
                    lost = at(t[i], "lost", **{"from": pid})
                    by = lost.get("by") if lost else None
                    how = ("lost:" + ("poke" if by in jx else "you" if by == "you" else "keeper" if by in ("home", "far")
                                      else "knocked")) if lost else "?"
                if how in ("end", "reset", "?"):
                    continue
                take = at(t[s0], "take", by=pid)
                away = 0.0
                net = r.net(teams[j])
                for k in range(s0, i):
                    if float(V[k, j] @ th.unit(net - P[k, j])) < -0.5:
                        away += float(dt_[k])
                self.touches.append({"id": pid, "t0": float(t[s0]), "t1": float(t[i]), "how": how,
                                     "from_pass": bool(take and take.get("pass")), "away": away})
                if how == "shot":
                    self.shots.append({"hold": float(t[i] - t[s0]), "from_pass": bool(take and take.get("pass"))})
            else:
                i += 1

        for e in ev:
            if e["event"] != "pass" or e.get("by") not in jx:
                continue
            k = int(np.searchsorted(t, e["t"] - 0.0005))
            if k < 1 or k >= n:
                continue
            i, jp = k - 1, jx[e["by"]]
            to = e.get("to")
            tm = teams[jp]
            if to in jx:
                q = B[i, jx[to]]
            elif to == "you" and you_in:
                q = YB[i] if not np.isnan(YB[i, 0]) else YP[i]
            else:
                continue
            origin = PK[i]
            opp = [P[i, m] for m in range(J) if teams[m] != tm]
            if you_in and tm == "them" and not np.isnan(YP[i, 0]):
                opp.append(YP[i])
            outcome, t_done = None, None
            for m in range(k, n):
                if not live[m]:
                    outcome = "reset"
                    break
                if H[m] != -1:
                    hm = holder[m]
                    outcome = ("same" if hm == to else "keeper" if hm in ("home", "far")
                               else "team" if team_of(hm) == tm else "picked")
                    t_done = t[m]
                    break
            if outcome in (None, "reset"):
                continue
            fumbled = any(f["event"] == "fumble" and f.get("by") == to and e["t"] <= f["t"] < t_done for f in ev)
            s0 = spell_start.get((jp, k))
            self.passes.append({
                "by": e["by"], "to": to, "outcome": outcome, "fumbled": fumbled,
                "face": float(_ang(th.unit(q - origin), F[i, jp])),
                "pressure": min(float(np.linalg.norm(o - P[i, jp])) for o in opp),
                "dist": float(np.linalg.norm(q - origin)),
                "hold": float(t[k] - t[s0]) if s0 is not None else None})
        A["goals"] += sum(1 for e in r.events if e.get("event") == "goal")
        A["shots"] += sum(1 for e in r.events if e.get("event") == "shot" and e.get("by") in jx)
        tick = r.meta.get("ai_tick_ms")
        if tick:
            self.ticks_ms.append(tick)

    # ------------------------------------------------------------------ the numbers
    def result(self) -> dict:
        A = self.A
        sk, gm = max(A["skater_min"], 1e-9), max(A["game_min"], 1e-9)
        react = self.cat("react")
        passes = self.passes
        npass = max(len(passes), 1)
        picked = [p for p in passes if p["outcome"] == "picked"]
        holds = [p["hold"] for p in passes if p["hold"] is not None] + [s["hold"] for s in self.shots]
        touches = self.touches
        ends = Counter(c["how"] for c in touches)
        dur = [c["t1"] - c["t0"] for c in touches]
        ai_us = [p for p in passes if p["by"].startswith("U")]
        R = {
            "games": len(self.vmax), "game_min": round(A["game_min"], 1), "skater_min": round(A["skater_min"], 1),
            "vmax": round(float(np.median(self.vmax)), 3) if self.vmax else None,
            "role_same_tick": float(np.mean(react <= 0.025)) if len(react) else None,
            "role_median_s": _pct(react, 50),
            "target_jumps": A["target_jumps"] / sk,
            "raw_jumps": A["raw_jumps"] / sk,
            "raw_jumps_settled": A["raw_jumps_settled"] / sk,
            "chaser_changes": A["chaser_changes"] / max(A["loose_min"], 1e-9),
            "chaser_back": A["chaser_back"] / max(A["chaser_changes"], 1),
            "marks_settled": A["marks_settled"] / sk,
            "shoves": A["shoves"] / sk,
            "you_jumps": A["you_jumps"] / A["you_min"] if A["you_min"] else None,
            "you_closest": _pct(self.cat("you_closest"), 50),
            "cap_flips": A["cap_flips"] / sk,
            "jerk_p99": _pct(self.cat("jerk"), 99),
            "hard_acc": A["hard_acc"] / sk,
            "hard_dec": A["hard_dec"] / sk,
            "mean_speed": float(np.mean(self.cat("speed_frac"))),
            "ge90": A["ge90"] / max(A["ticks"], 1),
            "standing": A["standing"] / max(A["ticks"], 1),
            "gliding": A["coast"] / A["mode_ticks"] if A["mode_ticks"] else None,
            "bursting": A["burst"] / A["mode_ticks"] if A["mode_ticks"] else None,
            "backward": float(np.mean(self.cat("face_off") > 120)),
            "carry_p90": _pct(self.cat("carry_speed"), 90),
            "missed_catch": sum(1 for p in picked if p["fumbled"]) / max(len(picked), 1),
            "completion": sum(1 for p in passes if p["outcome"] == "same") / npass,
            "opp_1m": float(np.mean([p["pressure"] < 1.0 for p in passes])) if passes else None,
            "over_90": float(np.mean([p["face"] > 90 for p in passes])) if passes else None,
            "pass_len": _pct([p["dist"] for p in passes], 50),
            "losses_per_s": sum(v for k, v in ends.items() if k.startswith("lost")) / max(A["carry_s"], 1e-9),
            "poke_touches": ends.get("lost:poke", 0) / max(len(touches), 1),
            "nearest_def": _pct(self.cat("press"), 50),
            "stick_in_reach": float(np.mean(self.cat("stick_in"))),
            "no_open_mate": float(np.mean(self.cat("no_open"))),
            "away_touches": sum(1 for c in touches if c["away"] >= 1.0),
            "min_release": min(holds) if holds else None,
            "quick_shots": sum(1 for s in self.shots if s["from_pass"] and s["hold"] < 0.5) / max(len(self.shots), 1),
            "puck_behind": float(np.mean(self.cat("behind"))),
            "to_you": (sum(1 for p in ai_us if p["to"] == "you") / max(len(ai_us), 1)) if A["with_you"] else None,
            "tick_mean_ms": float(np.mean([x[0] for x in self.ticks_ms])) if self.ticks_ms else None,
            "tick_p99_ms": float(np.max([x[1] for x in self.ticks_ms])) if self.ticks_ms else None,
            "goals_per_min": A["goals"] / max(A["live_min"], 1e-9),
            "shots_per_min": A["shots"] / gm,
            "touch_mean": float(np.mean(dur)) if dur else None,
            "touch_median": _pct(dur, 50),
            "touches_per_min": len(touches) / gm,
            "counts": {"passes": len(passes), "picked": len(picked), "shots": len(self.shots), "touches": len(touches),
                       "touch_ends": dict(ends)},
        }
        return R


def _fmt(x, how: str) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "-"
    if how == "pct":
        return f"{100 * x:.0f}%"
    if how == "pct1":
        return f"{100 * x:.1f}%"
    if how == "int":
        return str(int(x))
    return f"{x:.{int(how[1])}f}"


def table(R: dict) -> str:
    lines = [f"{R['games']} game(s), {R['game_min']} game-min, {R['skater_min']} skater-min, AI top {R['vmax']} m/s",
             "", f"{'measure':<58} {'baseline':>9} {'now':>9}   target"]
    for key, label, base, target, how in TABLE:
        lines.append(f"{label:<58} {_fmt(base, how):>9} {_fmt(R.get(key), how):>9}   {target}")
    lines += ["", "watch (no target; a change that moves these more than ~30% needs a look):"]
    for key, label, base, how in WATCH:
        lines.append(f"{label:<58} {_fmt(base, how):>9} {_fmt(R.get(key), how):>9}")
    c = R["counts"]
    lines += ["", f"passes {c['passes']} (picked off {c['picked']}), shots {c['shots']}, touches {c['touches']} "
                  f"ending {c['touch_ends']}"]
    return "\n".join(lines)


def runs_in(path: Path) -> list[Path]:
    """A recorded game (a folder with ai.csv), or a folder of them (self-play's s<seed>/)."""
    if (path / "ai.csv").exists():
        return [path]
    return sorted(p.parent for p in path.glob("*/ai.csv"))


def score(paths: list[Path]) -> dict:
    sc = Score()
    for d in paths:
        sc.game(Run(d))
    return sc.result()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="*", type=Path, help="recorded games to score (default: play self-play games)")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3])
    ap.add_argument("--seconds", type=float, default=600.0, help="each self-play game's length (default 600)")
    ap.add_argument("--you-ms", type=float, default=YOU_MS, help="your skate speed (default 3)")
    ap.add_argument("--you-sprint", type=float, default=YOU_SPRINT,
                    help="your sprint speed: the AI's top is 0.95 of the faster of the two (default 4.5)")
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE",
                    help="a threes.py constant for the self-play, e.g. --set CARRY=0.85 or --set BLADE_AT=0.75,0")
    ap.add_argument("--out", type=Path, help="where self-play games go (default data/selfplay-<time>)")
    ap.add_argument("--json", type=Path, help="also write the numbers here")
    args = ap.parse_args()

    if args.runs:
        paths = [p for r in args.runs for p in runs_in(r)]
        if not paths:
            raise SystemExit("no ai.csv found (games recorded before 2026-11-13 don't have one)")
    else:
        sets = [(k, _value(v)) for k, v in (s.split("=", 1) for s in args.set)]
        out = args.out or HERE / "data" / ("selfplay-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
        jobs = [(seed, args.seconds, str(out / f"s{seed}"), args.you_ms, sets, args.you_sprint) for seed in args.seeds]
        print(f"self-play: {len(jobs)} game(s) of {args.seconds:.0f} s -> {out}" + (f"  set {dict(sets)}" if sets else ""),
              flush=True)
        workers = max(1, min(len(jobs), (os.cpu_count() or 4) - 2))
        with ProcessPoolExecutor(workers) as ex:
            for meta in ex.map(play_one, jobs):
                print(f"  seed {meta['seed']}: score {meta['score']}, AI tick {meta['ai_tick_ms'][0]:.2f} ms "
                      f"(p99 {meta['ai_tick_ms'][1]:.2f}), {meta['wall_s']:.0f} s", flush=True)
        paths = [Path(j[2]) for j in jobs]
    R = score(paths)
    print()
    print(table(R))
    if args.json:
        args.json.write_text(json.dumps(R, indent=1, default=_plain))


if __name__ == "__main__":
    main()
