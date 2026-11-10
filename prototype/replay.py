"""Replay a recording's shots through the sandbox physics (no headset): how fast does the puck go?

    uv run python replay.py data/<run>                 # every shot in the run
    uv run python replay.py data/<run> --flex 50 --pop 0.4

For each shot that analyze.py finds, a puck is put just off the blade's forehand where the blade
is 30 ms before the peak (where it would meet the puck), and the recorded hands (and grips) swing
the stick through it with exactly the sandbox's physics code. A blade passing above the puck
misses it, as it would in the headset.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

import analyze
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


def replay(run_dir, flex=None, pop=None, grip=None, verbose=True) -> list[dict]:
    df, meta = recfmt.load(run_dir)
    spec, fit = StickSpec.from_dict(meta["spec"]), grab.Fit.from_dict(meta["fit"])
    values = sandbox.Tuning.defaults(spec, fit, pk.Params())
    for k, v in (("flex", flex), ("grip", grip)):
        if v is not None:
            values[k] = v
    play = sandbox.Play(sandbox.Tuning(spec, values))
    play.shoot = 1.0                                     # shots: the right trigger squeezed (firm hands)
    if pop is not None:                                  # no longer a setting (it barely matters): the param
        play.params.blade_pop = pop
    physics = sandbox.Physics(play, _Quiet(), _Quiet())
    S = analyze.analyze(run_dir, make_plots=False)
    peaks = [s["t"] for ph in S["shots"].values() for s in ph["shots"]]
    t = df["t"].to_numpy()
    tr = {d: recfmt.Track(df, d) for d in recfmt.CONTROLLERS}
    out = []
    for tp in peaks:
        i0 = int(np.searchsorted(t, tp - 2.0))         # 2 s run-in so the grab state is right
        i_spawn = int(np.searchsorted(t, tp - 0.03))
        i1 = int(np.searchsorted(t, tp + 0.4))
        physics.last_t = None
        best, blade_low = 0.0, np.inf
        for i in range(i0, i1):
            tick = {d: (tr[d].R[i], tr[d].p[i]) for d in recfmt.CONTROLLERS if tr[d].valid[i]}
            for d in recfmt.CONTROLLERS:
                play.squeeze[d] = tr[d].grip[i]
            if i == i_spawn:
                play.want_puck = True
            physics(t[i], tick)
            if i > i_spawn:
                best = max(best, play.sim.puck.speed)
                g = physics.grab
                if g.R is not None and i < i_spawn + 60:
                    blade_low = min(blade_low, float((physics.edge_b @ g.R.T + g.p)[:, 1].min()))
        row = {"t": round(float(tp), 2), "puck_ms": round(best, 1), "puck_mph": round(best * sandbox.MPH, 1),
               "blade_low_cm": round(blade_low * 100, 1)}
        out.append(row)
        if verbose:
            note = "" if best > 1 else ("  (blade passed over it)" if blade_low > pk.H else "  (missed)")
            print(f"  shot at {row['t']:7.2f} s: puck {row['puck_ms']:5.1f} m/s ({row['puck_mph']:3.0f} mph), "
                  f"blade's lowest point {row['blade_low_cm']:+6.1f} cm{note}")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--flex", type=float)
    ap.add_argument("--pop", type=float)
    ap.add_argument("--grip", type=float)
    args = ap.parse_args()
    print(f"{Path(args.run_dir).name}: puck speeds through the sandbox physics")
    replay(args.run_dir, args.flex, args.pop, args.grip)


if __name__ == "__main__":
    main()
