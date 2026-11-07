"""Replay a sandbox session's hands through the physics and measure every blade-puck touch:
how fast the hands' blade was moving vs how fast the puck left. A puck leaving much faster than
the blade (while stickhandling) is the physics adding energy: the "puck explodes off the blade".

    uv run python touches.py data/sandbox-<timestamp>
    uv run python touches.py data/sandbox-<timestamp> --pop 0.1 --flex 90

Pucks are dropped where and when the session dropped them (events.jsonl); the settings are the
session's final ones unless overridden.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import grab
import puck as pk
import recfmt
import sandbox
from stickspec import StickSpec


class _Quiet:
    def say(self, *a, **k):
        pass

    def event(self, *a, **k):
        pass

    def puck_row(self, *a, **k):
        pass


def touches(run_dir, overrides: dict | None = None, until_s: float | None = None, verbose=True) -> dict:
    run_dir = Path(run_dir)
    df, meta = recfmt.load(run_dir)
    spec = StickSpec.from_dict(meta["spec"])
    values = sandbox.Tuning.defaults(spec, grab.Fit.from_dict(meta["fit"]), pk.Params())
    values.update(meta["settings_end"])                 # older sessions lack newer settings
    values.update(overrides or {})
    play = sandbox.Play(sandbox.Tuning(spec.with_(length_m=spec.length_m), values))
    play.retune()
    phys = sandbox.Physics(play, _Quiet(), _Quiet())
    ev = [json.loads(line) for line in open(run_dir / "events.jsonl")]
    drops = [(e["t"], np.array(e["at"])) for e in ev if e["event"] == "puck"]
    rinks = [(e["t"], e) for e in ev if e["event"] == "rink"]
    t = df["t"].to_numpy()
    tr = {d: recfmt.Track(df, d) for d in recfmt.CONTROLLERS}
    sim = play.sim
    out = []          # (blade speed, puck speed before, puck speed after, flex rel speed, bend)
    di = ri = 0
    last_sweet = None
    n = len(t) if until_s is None else int(np.searchsorted(t, until_s))
    for i in range(n):
        while ri < len(rinks) and rinks[ri][0] <= t[i]:
            e = rinks[ri][1]
            sim.puck.rink = pk.Rink(origin=np.array(e["origin"]), fwd=np.array(e["fwd"]))
            ri += 1
        while di < len(drops) and drops[di][0] <= t[i]:
            sim.puck.spawn(drops[di][1][[0, 2]])
            di += 1
        tick = {d: (tr[d].R[i], tr[d].p[i]) for d in recfmt.CONTROLLERS if tr[d].valid[i]}
        for d in recfmt.CONTROLLERS:
            play.squeeze[d] = tr[d].grip[i]
        v_before = sim.puck.speed
        phys._tick(t[i], tick)
        g = phys.grab
        if g.R is not None:
            sweet = g.R @ spec.sweet + g.p
            blade_v = 0.0 if last_sweet is None else float(np.linalg.norm(sweet - last_sweet) / max(t[i] - t[i - 1], 1e-4))
            last_sweet = sweet
        else:
            blade_v, last_sweet = 0.0, None
        if phys.last_impulse > 0.15:
            out.append((blade_v, v_before, sim.puck.speed, float(np.linalg.norm(sim.bend)) * 1000))
    a = np.array(out) if out else np.zeros((0, 4))
    res = {"touches": len(a)}
    if len(a):
        slow = a[a[:, 0] < 3.0]                       # stickhandling-speed touches
        if len(slow):
            gain = slow[:, 2] / np.maximum(slow[:, 0], 0.5)
            res.update(
                slow_touches=len(slow),
                exploded=int(np.sum((slow[:, 2] > 2.0 * np.maximum(slow[:, 0], 0.5)) & (slow[:, 2] > 3.0))),
                puck_after_p50=float(np.median(slow[:, 2])), puck_after_p95=float(np.percentile(slow[:, 2], 95)),
                blade_p50=float(np.median(slow[:, 0])), gain_p95=float(np.percentile(gain, 95)),
                bend_at_explosions_mm=float(np.median(slow[(slow[:, 2] > 2.0 * np.maximum(slow[:, 0], 0.5)) & (slow[:, 2] > 3.0), 3]))
                if np.any((slow[:, 2] > 2.0 * np.maximum(slow[:, 0], 0.5)) & (slow[:, 2] > 3.0)) else 0.0)
    if verbose:
        print(json.dumps(res, indent=2))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--pop", type=float)
    ap.add_argument("--flex", type=float)
    ap.add_argument("--until", type=float, help="only the first N seconds")
    args = ap.parse_args()
    over = {k: v for k, v in (("pop", args.pop), ("flex", args.flex)) if v is not None}
    touches(args.run_dir, over, args.until)


if __name__ == "__main__":
    main()
