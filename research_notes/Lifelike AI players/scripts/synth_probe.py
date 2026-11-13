"""Baseline probe for the round-4 synthesis: the current 3v3 AI in self-play, all six skaters AI,
the real 1 kHz puck, the AI capped as in the headset (you_ms = 3.0, Jon's skate setting).

Records every AI tick (positions, commanded velocities, facing, targets, marks, chasers, holder)
and every puck event (takes, passes, shots, losses, failed receptions). Changes no code: it wraps
methods on the Game instance only.

Run from prototype/:  uv run python <this> <seed> <seconds> <out prefix>
Writes <prefix>_s<seed>.npz (ticks) and <prefix>_s<seed>.json (events).
"""
import json
import math
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "tests")

import numpy as np  # noqa: E402

import threes as th  # noqa: E402
from test_threes import make  # noqa: E402

seed, seconds, prefix = int(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
YOU_MS = 3.0

sim, g = make(seed=seed, to_goals=99)
g.you_ms = YOU_MS
ids = [p.id for p in g.players]
idx = {pid: i for i, pid in enumerate(ids)}

ev = {"passes": [], "takes": [], "shots": [], "loses": [], "miss_roll": [], "poss": []}
st = {"pass": None, "cur": None, "targets": {}, "chaser": {}}


def hkey():
    h = g.holder
    if isinstance(h, th.Player):
        return idx[h.id]
    if isinstance(h, th.Keeper):
        return -2 if h.end == "home" else -3
    return -1


# ---------------------------------------------------------------- wrappers (instance only)
o_targets, o_take, o_pass, o_shoot, o_lose, o_loose = g._targets, g._take, g._pass, g._shoot, g._lose, g._loose
o_cover, o_goal, o_faceoff = g._cover, g._goal, g.faceoff


import os  # noqa: E402

DELAY = os.environ.get("DELAY") == "1"
dl = {"key": None, "react_at": {}, "held": {}, "rng": np.random.default_rng(1000 + seed)}


def delayed_targets(pxz, pv):
    """Scratch experiment only: after a change of who has the puck, each AI skater keeps his old
    target until his own reaction time has passed: 0.18 s + an exponential tail (mean 0.1 s), +0.1 s
    if the puck is more than 50 deg off his facing, +0.2 s more if more than 110 deg (behind). The
    new carrier, the passer and the pass's receiver react at once."""
    out = o_targets_orig(pxz, pv)
    key = hkey()
    if dl["key"] is not None and key != dl["key"]:
        for p in g.players:
            if p is g.holder or p.id == g.pass_to or p.id == g.last_touch:
                dl["react_at"][p.id] = g.t
                continue
            a = math.degrees(math.acos(max(-1.0, min(1.0, float(th.unit(pxz - p.pos) @ p.facing)))))
            extra = (0.1 if a > 50 else 0.0) + (0.2 if a > 110 else 0.0)
            dl["react_at"][p.id] = g.t + 0.18 + dl["rng"].exponential(0.1) + extra
    dl["key"] = key
    for pid in list(out):
        if g.t < dl["react_at"].get(pid, -1.0) and pid in dl["held"]:
            out[pid] = dl["held"][pid]
        else:
            dl["held"][pid] = np.asarray(out[pid], dtype=float).copy()
    return out


o_targets_orig = o_targets
if DELAY:
    o_targets = delayed_targets


def targets(pxz, pv):
    out = o_targets(pxz, pv)
    st["targets"] = {k: np.asarray(v, dtype=float).copy() for k, v in out.items()}
    st["chaser"] = {}
    h = g.holder
    if not (isinstance(h, th.Player) or g.yours or isinstance(h, th.Keeper)):
        path = g._path(pxz, pv)                      # _chase's own pick (deterministic, no rng)
        for team in ("us", "them"):
            cands = [p for p in g.players if p.team == team]
            times = {p.id: g._reach(p, path) for p in cands}
            ch = min(cands, key=lambda p: times[p.id][0])
            if g.pass_to in times:
                ch = g.by_id[g.pass_to]
            st["chaser"][team] = idx[ch.id]
    return out


def end_poss(how):
    c = st["cur"]
    if c is None:
        return
    c["t1"], c["how"] = g.t, how
    ev["poss"].append(c)
    st["cur"] = None


def resolve_pass(result):
    pp = st["pass"]
    if pp is not None:
        pp["outcome"] = result
        pp["t_done"] = g.t
        ev["passes"].append(pp)
        st["pass"] = None


def take(p):
    pp = st["pass"]
    from_pass = pp is not None and pp["to"] == p.id
    if pp is not None:
        resolve_pass("same" if p.id == pp["to"] else ("team" if p.team == pp["team"] else "picked"))
    end_poss("?")
    turnover = g.last_team is not None and g.last_team != p.team
    ev["takes"].append({"t": g.t, "id": p.id, "team": p.team, "from_pass": from_pass, "turnover": turnover})
    st["cur"] = {"id": p.id, "team": p.team, "t0": g.t, "from_pass": from_pass, "away": 0.0, "carry": 0.0}
    return o_take(p)


def pss(origin, m, team, by):
    if st["pass"] is not None:
        resolve_pass("superseded")
    rec = {"t": g.t, "by": by, "to": m.id, "team": team, "outcome": None, "missed_roll": 0}
    if by in g.by_id:
        h = g.by_id[by]
        q = m.stick()
        d = th.unit(q - origin)
        rec["face_angle"] = math.degrees(math.acos(max(-1.0, min(1.0, float(d @ h.facing)))))
        opps = g.team(th.OTHER[team])
        rec["pressure"] = min(float(np.linalg.norm(o.pos - h.pos)) for o in opps)
        rec["dist"] = float(np.linalg.norm(q - origin))
        rec["hold"] = g.t - st["cur"]["t0"] if st["cur"] is not None else None
        end_poss("pass")
    else:
        rec["keeper"] = True
    st["pass"] = rec
    return o_pass(origin, m, team, by)


def shoot(h, k, o_f, aim):
    c = st["cur"]
    ev["shots"].append({"t": g.t, "by": h.id, "hold": g.t - c["t0"] if c else None,
                        "from_pass": bool(c and c["from_pass"]),
                        "dist": float(np.linalg.norm(np.asarray(o_f) - np.array([0.0, th.zn.GOAL_Z])))})
    end_poss("shot")
    return o_shoot(h, k, o_f, aim)


def lose(h, by=None):
    kind = "poke" if by in g.by_id else ("keeper" if by in ("home", "far") else "knocked")
    ev["loses"].append({"t": g.t, "id": h.id, "kind": kind})
    end_poss("lost:" + kind)
    return o_lose(h, by)


def loose(pxz, pv, y):
    pp = st["pass"]
    before = {p.id: p.cool_until for p in g.players}
    r = o_loose(pxz, pv, y)
    if pp is not None and g.holder is None and pp["to"] in g.by_id:
        rv = g.by_id[pp["to"]]
        if rv.cool_until != before[rv.id] and abs(rv.cool_until - (g.t + 0.3)) < 1e-9:
            pp["missed_roll"] += 1
            ev["miss_roll"].append(g.t)
    return r


def cover(k):
    resolve_pass("keeper")
    end_poss("keeper")
    return o_cover(k)


def goal(team):
    resolve_pass("goal")
    end_poss("goal")
    return o_goal(team)


def faceoff(say=None):
    resolve_pass("reset")
    end_poss("reset")
    return o_faceoff(say)


g._targets, g._take, g._pass, g._shoot, g._lose, g._loose = targets, take, pss, shoot, lose, loose
g._cover, g._goal, g.faceoff = cover, goal, faceoff

# ---------------------------------------------------------------- the run
T, LIVE, H, P, V, F, TG, MK, CH, PK, PV, CAR = [], [], [], [], [], [], [], [], [], [], [], []
g.start()
last = -1.0
w0 = time.time()
for i in range(int(seconds * 1000)):
    t = i * 0.001
    sim.step(0.001, None, None)
    sim.puck.events.clear()
    st["targets"] = None
    g.update(t, None, None)
    g.outbox.clear()
    if g._last_ai == last:
        continue
    last = g._last_ai
    live = g.state == "live"
    T.append(t)
    LIVE.append(live)
    H.append(hkey())
    P.append([p.pos.copy() for p in g.players])
    V.append([p.vel.copy() for p in g.players])
    F.append([p.facing.copy() for p in g.players])
    tg = st["targets"] or {}
    TG.append([tg.get(pid, np.array([np.nan, np.nan])) for pid in ids])
    MK.append([idx.get(g.marks.get(pid), -1) for pid in ids])
    CH.append([st["chaser"].get("us", -1), st["chaser"].get("them", -1)] if st["targets"] is not None else [-1, -1])
    pxz, pv = g._puck()
    PK.append(pxz.copy())
    PV.append(pv.copy())
    row = [np.nan] * 6                                # carrier: nearest body, nearest stick, open mates, toward net, speed, in poke range
    h = g.holder
    if live and isinstance(h, th.Player):
        origin = g._carry_point(h)
        opps = g.team(th.OTHER[h.team])
        body = min(float(np.linalg.norm(o.pos - h.pos)) for o in opps)
        stick = min(float(np.linalg.norm(o.stick() - origin)) for o in opps)
        n_open = 0
        for m in g.team(h.team):
            if m is h:
                continue
            q = m.stick()
            lead = q + th._cap(m.vel * (float(np.linalg.norm(q - origin)) / th.PASS_MS), th.LEAD_MAX)
            n_open += g._lane(origin, lead, opps, th.PASS_MS, 1.0) > 0.55
        net = g.arena.net(th.attack_end(h.team))
        toward = float(h.vel @ th.unit(net - h.pos))
        row = [body, stick, n_open, toward, float(np.linalg.norm(h.vel)), float(stick < th.POKE_R)]
        c = st["cur"]
        if c is not None:
            c["carry"] += 0.02
            if toward < -0.5:
                c["away"] += 0.02
    CAR.append(row)
end_poss("end")
resolve_pass("end")

np.savez_compressed(f"{prefix}_s{seed}.npz", t=np.array(T), live=np.array(LIVE), holder=np.array(H), pos=np.array(P),
                    vel=np.array(V), facing=np.array(F), target=np.array(TG), marks=np.array(MK), chaser=np.array(CH),
                    puck=np.array(PK), puckv=np.array(PV), carrier=np.array(CAR), vmax=g.vmax,
                    teams=np.array([p.team for p in g.players]))
with open(f"{prefix}_s{seed}.json", "w") as f:
    json.dump({"seed": seed, "seconds": seconds, "score": g.score, "stats": {k: v for k, v in g.stats.items() if k != "goals"},
               "vmax": g.vmax, **ev}, f, default=float)
print(f"seed {seed}: {seconds:.0f} s in {time.time() - w0:.0f} s wall; score {g.score}; passes {len(ev['passes'])}"
      f" shots {len(ev['shots'])} poss {len(ev['poss'])}; vmax {g.vmax:.2f}", flush=True)
