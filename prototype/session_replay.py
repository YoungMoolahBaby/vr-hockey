"""Replay a whole session's hands through today's physics (no headset), and check how the puck
leaves the blade against reports/Shot release.md's targets.

    uv run python session_replay.py data/freeskate-20261110-120859
    uv run python session_replay.py data/<run> --set ease_off=0              # without the ease-off (change 2)
    uv run python session_replay.py data/<run> --window 0.004                # with the 4 ms velocity fit (change 1)
    uv run python session_replay.py data/<run> --until 300 --json out.json

rec.csv holds the hands in the world (with the thumbsticks' motion and any skate height), so they line
up with the rink: free skates and games lay out the arena from their "rink" event, the sandbox its
rink. Pucks are dropped where and when the session dropped them, at rest. No goalies, no other
players. The settings are the session's last ones (sessions before the right trigger's soft hands
replay without them), the right trigger is read back from puck.csv's damping column when it has
one, and the hands' tracking flags from rec.csv.

It reports:
- shots, called as the game calls them (shotcall.py: the puck's free flight);
- launches: the puck going up faster than 6 m/s, each with its peak upward speed and height, and
  whether the stick was still sliding through the hands;
- lift-offs after a press (the hands' blade more than ICE_BEND under the ice): how fast the blade
  rises in its first ms off the ice, against the hands, and whether it stepped.
The targets (reports/Shot release.md, section 4) are printed with each.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import arena as ar
import grab
import puck as pk
import recfmt
import sandbox
import shotcall
import zone as zn
from stickspec import StickSpec


class _Quiet:
    def say(self, *a, **k):
        pass

    def event(self, *a, **k):
        pass

    def puck_row(self, *a, **k):
        pass


def _setup(run_dir: Path, over: dict):
    df, meta = recfmt.load(run_dir)
    spec = StickSpec.from_dict(meta["spec"])
    values = sandbox.Tuning.defaults(spec, grab.Fit.from_dict(meta["fit"]), pk.Params())
    end = meta.get("settings_end") or {}
    values.update(end)
    if "handle" not in end:
        values["handle"] = 0.0                     # recorded before the right trigger's soft hands
    values.update({k: v for k, v in over.items() if k in values})
    play = sandbox.Play(sandbox.Tuning(spec, values))
    play.retune()
    for k, v in over.items():
        if hasattr(play.params, k):
            setattr(play.params, k, v)
    phys = sandbox.Physics(play, _Quiet(), _Quiet())
    phys._game = lambda t, imp: None               # no respawns or calls of its own: ours below
    ev = [json.loads(line) for line in open(run_dir / "events.jsonl")]
    rink = next((e for e in ev if e["event"] == "rink"), None)
    arena = None
    if rink is not None and "z_dir" in rink:
        arena = ar.Arena(zn.Zone(np.array(rink["origin"], float), np.array(rink["z_dir"], float)), rink["length"])
        play.sim.puck = ar.ArenaPuck(play.params, arena)
    elif rink is not None:
        play.sim.puck.rink = pk.Rink(origin=np.array(rink["origin"]), fwd=np.array(rink["fwd"]))
    drops = [(e["t"], e["at"]) for e in ev if e["event"] == "puck"]
    shoot = None
    pc = run_dir / "puck.csv"
    if pc.exists():
        p = pd.read_csv(pc)
        if "hands" in p:                            # the damping in use: the right trigger, read back
            soft, firm = values.get("handle", 0.0), values.get("hands", pk.Flex.DAMPING)
            if soft > 0 and soft != firm:
                s = np.clip((soft - p["hands"].to_numpy()) / (soft - firm), 0.0, 1.0)
                shoot = (p["t"].to_numpy(), 0.05 + 0.9 * s)    # back through rig.TRIGGER_DEAD's mapping
    return df, play, phys, arena, drops, shoot


def replay(run_dir, over: dict | None = None, window: float | None = None, until: float | None = None,
           verbose: bool = True) -> dict:
    run_dir = Path(run_dir)
    df, play, phys, arena, drops, shoot = _setup(run_dir, over or {})
    if window is not None:
        sandbox.VEL_WINDOW_S = window
    sim, spec = play.sim, play.spec
    t = df["t"].to_numpy()
    tr = {d: recfmt.Track(df, d) for d in recfmt.CONTROLLERS}
    val = {d: tr[d].valid for d in tr}
    n = len(t) if until is None else int(np.searchsorted(t, until))
    caller = shotcall.ShotCall()
    shots, launches, lifts = [], [], []
    launch = None                                   # the launch in progress: [t, peak vy, peak y, sliding]
    di, si = 0, 0
    press_deep, was_on, prev = False, False, None   # the lift-off watch
    for i in range(n):
        while di < len(drops) and drops[di][0] <= t[i]:
            at = drops[di][1]
            if arena is not None and len(at) == 2:
                sim.puck.place(float(at[0]), float(at[1]))
            else:
                sim.puck.spawn(np.array(at)[[0, 2]])
            caller.reset()
            launch = None
            di += 1
        if shoot is not None:
            while si + 1 < len(shoot[0]) and shoot[0][si + 1] <= t[i]:
                si += 1
            play.shoot = float(shoot[1][si])
        tick = {d: (tr[d].R[i], tr[d].p[i]) for d in recfmt.CONTROLLERS if val[d][i]}
        for d in recfmt.CONTROLLERS:
            play.squeeze[d] = tr[d].grip[i]
            play.latest_flags[d] = int(tr[d].flags[i])
        phys._tick(t[i], tick)
        pz = sim.puck
        call = caller.tick(t[i], phys.last_impulse, pz.vel)
        if call is not None:
            shots.append({**call, "t": round(float(t[i]), 3)})
        # launches
        vy, y = float(pz.vel[1]), float(pz.pos[1])
        if launch is None and vy > 6.0:
            launch = [float(t[i]), vy, y, bool(np.linalg.norm(sim.slide) > 0)]
        elif launch is not None:
            launch[1], launch[2] = max(launch[1], vy), max(launch[2], y)
            if y <= pk.H / 2 + 1e-3 or t[i] - launch[0] > 4.0:
                launches.append(launch)
                launch = None
        # lift-offs after a press: the blade's first ms off the ice, against the hands
        g = phys.grab
        if g.R is not None and play.stick_state in grab.HELD:
            rig_low = float((phys.edge_b @ g.R.T + g.p)[:, 1].min())
            blade_low = float((phys.edge_b @ g.R.T + g.p + sim.bend + sim.slide)[:, 1].min())
            if rig_low < -pk.ICE_BEND:
                press_deep = True
            if prev is not None and press_deep and was_on and not sim.on_ice:
                dt = max(t[i] - prev[0], 1e-4)
                lifts.append(((blade_low - prev[2]) / dt, (rig_low - prev[1]) / dt))
                press_deep = False
            if rig_low > 0.05:
                press_deep = False
            prev, was_on = (float(t[i]), rig_low, blade_low), sim.on_ice
        else:
            prev, press_deep = None, False
    if launch is not None:
        launches.append(launch)
    return _report(run_dir, shots, launches, lifts, verbose)


def _report(run_dir, shots, launches, lifts, verbose) -> dict:
    mph = np.array([s["mph"] for s in shots])
    med = float(np.median(mph)) if len(mph) else float("nan")
    L = np.array([[lv[1], lv[2], lv[3]] for lv in launches]) if launches else np.zeros((0, 3))
    res = {
        "run": Path(run_dir).name,
        "shots": len(mph),
        "mph_median": round(med, 1),
        "mph_p90": round(float(np.percentile(mph, 90)), 1) if len(mph) else None,
        "mph_max": round(float(mph.max()), 1) if len(mph) else None,
        "p90_over_median": round(float(np.percentile(mph, 90)) / med, 2) if len(mph) else None,
        "max_over_median": round(float(mph.max()) / med, 2) if len(mph) else None,
        "shots_30ms_or_more": int(np.sum(mph >= 30 * shotcall.MPH)),
        "launches_over_6": len(L),
        "launch_share": round(len(L) / max(len(mph), 1), 2),
        "launches_peak_over_8": int(np.sum(L[:, 0] > 8)),
        "launches_over_10_or_3m": int(np.sum((L[:, 0] > 10) | (L[:, 1] > 3.0))),
        "launches_while_sliding": int(np.sum(L[:, 2] > 0)),
        "lift_offs": len(lifts),
    }
    if lifts:
        a = np.array(lifts)
        rising = a[a[:, 1] > 0.5]
        if len(rising):
            ratio = rising[:, 0] / rising[:, 1]
            res["lift_off_speed_over_hands_median"] = round(float(np.median(ratio)), 2)
            res["lift_offs_stepping"] = int(np.sum(ratio > 0.6))
    res["calls"] = shots
    if verbose:
        print(f"{res['run']}: {res['shots']} shots, median {res['mph_median']} mph, p90 {res['mph_p90']}, "
              f"max {res['mph_max']} (targets: p90/median <= 1.45 -> {res['p90_over_median']}, "
              f"max/median <= 1.8 -> {res['max_over_median']}); {res['shots_30ms_or_more']} at 30 m/s or more")
        print(f"  launches over 6 m/s up: {res['launches_over_6']} ({res['launch_share']:.0%} of shots; target <= 5%), "
              f"peaking over 8: {res['launches_peak_over_8']} (<= 1), over 10 m/s or 3 m: {res['launches_over_10_or_3m']} (0), "
              f"while sliding: {res['launches_while_sliding']} (0)")
        if "lift_off_speed_over_hands_median" in res:
            print(f"  lift-offs after a press: {res['lift_offs']}; first ms off the ice at "
                  f"{res['lift_off_speed_over_hands_median']:.0%} of the hands' rise (median); stepping (> 60%): "
                  f"{res['lift_offs_stepping']} (target 0)")
        for lv in sorted(launches, key=lambda x: -x[1])[:5]:
            print(f"    launch at {lv[0]:8.3f} s: up {lv[1]:5.1f} m/s, {lv[2]:4.1f} m high{', sliding' if lv[3] else ''}")
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="a setting (sandbox.SETTINGS key) or a puck.Params field, e.g. ease_off=0")
    ap.add_argument("--window", type=float, help="sandbox.VEL_WINDOW_S in s (0: one sample's difference)")
    ap.add_argument("--until", type=float, help="only the first N seconds")
    ap.add_argument("--json", help="write the results here")
    args = ap.parse_args()
    over = {}
    for kv in args.set:
        k, v = kv.split("=", 1)
        over[k] = float(v)
    res = replay(args.run_dir, over, args.window, args.until)
    if args.json:
        Path(args.json).write_text(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
