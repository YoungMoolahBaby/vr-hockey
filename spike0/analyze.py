"""Spike 0 analysis: the virtual stick held with the grip buttons. Tracking, blade control, speed.

    uv run python analyze.py data/<run>            # report.md + plots in data/<run>/report/
    uv run python analyze.py data/<run> --no-plots

The stick is rebuilt from the recording with the same grab rules the headset used (grab.py),
at the full 1 kHz. Everything is measured at the blade, because that is where the puck is:
the puck is 25 mm tall and 76 mm wide. "Tracked" means the runtime is optically tracking the
controller rather than guessing from its IMU.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import grab
import recfmt
import stickmath as sm
from stickspec import INCH, StickSpec

PUCK_H_MM = 25.4
PUCK_D_MM = 76.2
FRAME_RATES = (72, 90, 120)
JITTER_WINDOW_S = 0.05
SHOT_MIN_SPEED = 8.0     # m/s at the blade: slower peaks are stick movements, not shots
STICK_PHASES = ("stickhandle", "heads_up", "one_hand")
SHOT_PHASES = ("wrist_shots", "slap_shots")
EXPECTED = {"stickhandle": (grab.BOTH,), "heads_up": (grab.BOTH,), "one_hand": (grab.BOTTOM, grab.LOOSE_BOTTOM),
            "wrist_shots": (grab.BOTH,), "slap_shots": (grab.BOTH,)}

# my heuristics (good, ok, higher_is_better)
THRESHOLDS = {
    "heads_up_tracked_pct": (99.0, 95.0, True),
    "shot_tracked_pct":     (99.0, 90.0, True),
    "jitter_mm":            (3.0,  8.0,  False),
}
RATING_WORD = {"good": "GO", "ok": "MARGINAL", "bad": "NO-GO"}


def rate(metric: str, value) -> str | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    good, ok, higher = THRESHOLDS[metric]
    if higher:
        return "good" if value >= good else "ok" if value >= ok else "bad"
    return "good" if value <= good else "ok" if value <= ok else "bad"


def worst(ratings) -> str:
    r = [x for x in ratings if x]
    return "bad" if "bad" in r else "ok" if "ok" in r else "good"


def phase_masks(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Phase name -> mask of its last attempt."""
    labels = df["phase"].astype(str).to_numpy()
    out = {}
    for lab in pd.unique(labels):
        if lab not in (recfmt.GAP, "fit"):
            out[lab.split("#")[0]] = labels == lab
    return out


def fd_speed(pos: np.ndarray, t: np.ndarray, half_window_s: float = 0.005) -> np.ndarray:
    """Speed from positions over a short centred window."""
    rate_ = (len(t) - 1) / (t[-1] - t[0]) if len(t) > 1 else 1000
    k = max(1, int(round(half_window_s * rate_)))
    v = np.full(len(t), np.nan)
    if len(t) > 2 * k:
        v[k:-k] = np.linalg.norm(pos[2 * k:] - pos[:-2 * k], axis=1) / (t[2 * k:] - t[:-2 * k])
    return v


def jitter_residual(pos: np.ndarray, rate_hz: float) -> np.ndarray:
    """Position minus a local quadratic fit (Savitzky-Golay, 50 ms): tracking noise and stepping,
    which a quadratic cannot follow, while real stickhandling (a few Hz) it follows almost exactly."""
    k = max(2, int(round(JITTER_WINDOW_S * rate_hz / 2)))
    x = np.arange(-k, k + 1, dtype=float)
    coef = np.linalg.pinv(np.stack([np.ones_like(x), x, x * x], axis=1))[0]
    out = np.full_like(pos, np.nan)
    for j in range(pos.shape[1]):
        out[k:-k, j] = pos[k:-k, j] - np.convolve(pos[:, j], coef[::-1], mode="valid")
    return out


def pick_peaks(t, speed, min_speed=3.0, min_gap_s=1.0, max_peaks=12):
    order = np.argsort(np.nan_to_num(speed, nan=-1))[::-1]
    picked = []
    for i in order:
        if not speed[i] >= min_speed or len(picked) >= max_peaks:
            break
        if all(abs(t[i] - t[j]) >= min_gap_s for j in picked):
            picked.append(i)
    return sorted(picked)


def untracked_gap_ms(tracked: np.ndarray, rate_hz: float) -> float:
    lost = ~tracked
    if not lost.any():
        return 0.0
    edges = np.diff(np.concatenate([[0], lost.astype(int), [0]]))
    return float((np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)).max() / rate_hz * 1000)


def stick_from_recording(df: pd.DataFrame, meta: dict):
    """Replay the grips: (spec, fit, state, R, p) or None if the run has no stick."""
    if "spec" not in meta or "fit" not in meta:
        return None
    spec, fit = StickSpec.from_dict(meta["spec"]), grab.Fit.from_dict(meta["fit"])
    T, B = recfmt.Track(df, spec.top_hand), recfmt.Track(df, spec.bottom_hand)
    state = grab.states(grab.held(T.grip), grab.held(B.grip))
    R, p = grab.replay(spec, fit, state, T.R, T.p, B.R, B.p, T.valid, B.valid)
    return spec, fit, state, R, p


def analyze(run_dir, make_plots: bool = True) -> dict:
    run_dir = Path(run_dir)
    df, meta = recfmt.load(run_dir)
    t = df["t"].to_numpy(dtype=np.float64)
    dur = t[-1] - t[0]
    rate_hz = (len(t) - 1) / dur
    masks = phase_masks(df)
    tracks = {d: recfmt.Track(df, d) for d in recfmt.CONTROLLERS}
    head = recfmt.Track(df, "h")
    dts = np.diff(t)
    S: dict = {
        "run": str(run_dir),
        "meta": {k: meta.get(k) for k in ("created", "runtime", "system", "rate_hz", "lag_ms", "space", "notes",
                                          "fit_source", "completed", "synthetic")},
        "rates": {"query_hz": float(rate_hz), "dt_p50_ms": float(np.median(dts) * 1000),
                  "dt_p99_ms": float(np.percentile(dts, 99) * 1000), "dt_max_ms": float(dts.max() * 1000)},
        "phases_found": sorted(masks),
        "controllers": {}, "stick": {}, "phases": {}, "shots": {}, "verdict": {},
    }

    # ---------------------------------------------------------------- each controller
    for d, tr in tracks.items():
        C = S["controllers"][d] = {}
        C["fresh_pose_hz"] = float((tr.changed() & tr.valid).sum() / max(1e-9, tr.valid.mean() * dur))
        C["tracked_pct"] = float(tr.tracked.mean() * 100)
        for ph in STICK_PHASES:
            if ph not in masks:
                continue
            idx = np.flatnonzero(masks[ph])
            P = C.setdefault(ph, {})
            P["tracked_pct"] = float(tr.tracked[idx].mean() * 100)
            P["longest_untracked_ms"] = untracked_gap_ms(tr.tracked[idx], rate_hz)
            if head.valid[idx].any():
                fwd = -head.R[idx][:, :, 2]
                to = sm.unit(tr.p[idx] - head.p[idx])
                ang = np.degrees(np.arccos(np.clip(np.sum(fwd * to, axis=1), -1, 1)))
                P["gaze_angle_median_deg"] = float(np.nanmedian(ang))
                P["tracked_pct_by_gaze_angle"] = {
                    f"{lo}-{hi}": float(tr.tracked[idx][(ang >= lo) & (ang < hi)].mean() * 100)
                    for lo, hi in ((0, 30), (30, 50), (50, 70), (70, 180)) if ((ang >= lo) & (ang < hi)).sum() > 100}

    # ---------------------------------------------------------------- the stick, replayed
    stick = stick_from_recording(df, meta)
    low = sweet = None
    if stick is not None:
        spec, fit, state, R, p = stick
        S["controllers"][spec.top_hand]["hand"] = "top"
        S["controllers"][spec.bottom_hand]["hand"] = "bottom"
        S["stick"] = {"spec": spec.to_dict(), "fit": fit.to_dict(), "length_in": spec.length_m / INCH}
        edge = spec.edge(8)
        low = (np.einsum("nij,kj->nki", R, edge)[..., 1] + p[:, None, 1]).min(axis=1) * 1000   # lowest blade point
        sweet = np.einsum("nij,j->ni", R, spec.sweet) + p
        for ph in STICK_PHASES + SHOT_PHASES:
            if ph not in masks:
                continue
            idx = np.flatnonzero(masks[ph])
            P = S["phases"][ph] = {}
            st = state[idx]
            P["state_pct"] = {grab.STATE_NAMES[k]: float(np.mean(st == k) * 100) for k in grab.STATE_NAMES}
            P["held_as_expected_pct"] = float(np.mean(np.isin(st, EXPECTED[ph])) * 100)
            if ph in STICK_PHASES:
                h = low[idx]
                hv = h[~np.isnan(h)]
                # against the blade's own low point over the last second: an ice level that follows
                # the player's posture would see this, so it sizes an adaptive ice assist
                base = pd.Series(h).rolling(int(rate_hz), center=True, min_periods=int(rate_hz / 5)).quantile(0.1)
                rel = (pd.Series(h) - base).to_numpy()
                rel = rel[~np.isnan(rel)]
                if len(rel):
                    P["lift_p50_mm"] = float(np.percentile(rel, 50))
                    P["lift_p90_mm"] = float(np.percentile(rel, 90))
                P["grip_changes"] = int(np.count_nonzero(np.diff(st.astype(int))))
                if len(hv):
                    P["height_median_mm"] = float(np.median(hv))
                    P["height_p5_p95_mm"] = [float(np.percentile(hv, 5)), float(np.percentile(hv, 95))]
                    P["near_ice_pct"] = float(np.mean(np.abs(hv) <= PUCK_H_MM) * 100)
                    P["within_50mm_pct"] = float(np.mean(np.abs(hv) <= 50) * 100)
                    P["through_ice_pct"] = float(np.mean(hv < -10) * 100)
                    P["band90_mm"] = float(np.percentile(np.abs(hv), 90))
                jr = np.linalg.norm(jitter_residual(sweet[idx], rate_hz), axis=1) * 1000
                P["jitter_mm"] = float(np.sqrt(np.nanmean(jr ** 2))) if np.isfinite(jr).any() else None

        # ------------------------------------------------------------ shots
        T, B = tracks[spec.top_hand], tracks[spec.bottom_hand]
        for ph in SHOT_PHASES:
            if ph not in masks:
                continue
            idx = np.flatnonzero(masks[ph])
            tt = t[idx]
            spd = fd_speed(sweet[idx], tt)
            # only real swings: the stick in a hand (gripped or riding loose), and not within 50 ms
            # of a grab or release (the stick can jump into the hand then, which is not a swing)
            st = state[idx].astype(int)
            near_change = np.zeros(len(idx), bool)
            k = int(0.05 * rate_hz)
            for c in np.flatnonzero(np.diff(st)) + 1:
                near_change[max(0, c - k):c + k] = True
            spd[~np.isin(st, grab.HELD) | near_change] = np.nan
            peaks = pick_peaks(tt, spd, min_speed=SHOT_MIN_SPEED)
            shots = []
            for i in peaks:
                near = (tt >= tt[i] - 0.02) & (tt <= tt[i] + 0.02)
                swing = (tt >= tt[i] - 0.15) & (tt <= tt[i] + 0.15)
                shots.append({"t": float(tt[i]), "blade_speed_ms": float(np.nanmax(spd[near])),
                              "held": grab.STATE_NAMES[int(state[idx][i])],
                              "tracked_pct": {d: float(tr.tracked[idx][swing].mean() * 100)
                                              for d, tr in ((spec.top_hand, T), (spec.bottom_hand, B))}})
            top_speed = max((s["blade_speed_ms"] for s in shots), default=0.0)
            S["shots"][ph] = {
                "count": len(shots), "shots": shots, "peak_blade_speed_ms": top_speed,
                "peak_hand_speed_ms": {d: float(np.nanmax(np.linalg.norm(tr.v[idx], axis=1))) for d, tr in tracks.items()},
                "blade_travel_per_frame_cm": {str(f): top_speed / f * 100 for f in FRAME_RATES},
                "substep_hz_for_1cm": top_speed / 0.01,
                "tracked_pct_in_swings": {d: float(np.mean([s["tracked_pct"][d] for s in shots])) if shots else None
                                          for d in (spec.top_hand, spec.bottom_hand)},
            }

    # ---------------------------------------------------------------- verdicts
    hu = [S["controllers"][d].get("heads_up", {}).get("tracked_pct") for d in tracks]
    sw = [v for p in S["shots"].values() for v in p["tracked_pct_in_swings"].values()]
    m = {"heads_up_tracked_pct": min([x for x in hu if x is not None], default=None),
         "shot_tracked_pct": min([x for x in sw if x is not None], default=None),
         "jitter_mm": S["phases"].get("stickhandle", {}).get("jitter_mm")}
    r = {k: rate(k, v) for k, v in m.items()}
    S["verdict"] = {"overall": RATING_WORD[worst(r.values())], "metrics": m, "ratings": r}
    lifts = [S["phases"][p]["lift_p90_mm"] for p in ("stickhandle", "heads_up") if "lift_p90_mm" in S["phases"].get(p, {})]
    if lifts:
        S["verdict"]["lift_p90_mm"] = float(max(lifts))

    out = run_dir / "report"
    out.mkdir(exist_ok=True)
    (out / "summary.json").write_text(json.dumps(S, indent=2, default=float))
    (out / "report.md").write_text(render_markdown(S), encoding="utf-8")
    if make_plots and stick is not None:
        plots(t, masks, tracks, stick, low, sweet, out)
    return S


# ----------------------------------------------------------------------------- report


def f(v, nd=1, unit=""):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "-"
    return f"{v:.{nd}f}{unit}"


def rated(v, r, nd=1, unit=" mm"):
    return f"{f(v, nd, unit)} ({r})" if r else f(v, nd, unit)


def render_markdown(S: dict) -> str:
    L = []
    m = S["meta"]
    hand = {"l": "left", "r": "right"}
    L.append(f"# Spike 0 report: {Path(S['run']).name}\n")
    L.append(f"Runtime: {m.get('runtime')} | headset: {m.get('system')} | space: {m.get('space')} | "
             f"query lag: {m.get('lag_ms')} ms | completed: {m.get('completed')}")
    if m.get("notes"):
        L.append(f"Notes: {m['notes']}")
    r = S["rates"]
    L.append(f"\nQueries: {r['query_hz']:.0f}/s (dt p50 {r['dt_p50_ms']:.2f} ms, p99 {r['dt_p99_ms']:.2f}, "
             f"max {r['dt_max_ms']:.1f}). Phases: {', '.join(S['phases_found'])}.\n")

    if S["stick"]:
        sp, ft = S["stick"]["spec"], S["stick"]["fit"]
        L.append("## The stick\n")
        L.append(f"{S['stick']['length_in']:.1f}\" ({sp['length_m']:.2f} m) heel to top, lie {sp['lie']:g} "
                 f"(shaft {sp['shaft_angle_deg']:.0f} deg above the ice), {sp['shoots']} shot, blade "
                 f"{sp['blade_len_m'] * 100:.0f} cm with a {sp['curve_depth_m'] / INCH:.2f}\" curve. Fit in the top hand: "
                 f"blade turned {ft['roll_deg']:.0f}, tilted {ft['pitch_deg']:.0f}, swung {ft['yaw_deg']:.0f} deg "
                 f"({m.get('fit_source')}).\n")
    else:
        L.append("## The stick\n\nThis run has no grip-held stick (an older recording): tracking only.\n")

    V = S["verdict"]
    L.append("## Verdict\n")
    L.append(f"**Tracking: {V['overall']}**. Worst hand heads-up "
             f"{rated(V['metrics']['heads_up_tracked_pct'], V['ratings']['heads_up_tracked_pct'], 1, '%')}, in swings "
             f"{rated(V['metrics']['shot_tracked_pct'], V['ratings']['shot_tracked_pct'], 1, '%')}, blade jitter "
             f"stickhandling {rated(V['metrics']['jitter_mm'], V['ratings']['jitter_mm'])}.")
    if "lift_p90_mm" in V:
        L.append(f"\n**Ice assist:** measured from its own low point over the last second, the blade rose up to "
                 f"**{V['lift_p90_mm']:.0f} mm** (90th percentile) while stickhandling. An assist that follows your "
                 "height and holds the blade down unless you lift further than that would keep it on the ice.\n")

    if S["phases"]:
        L.append("## How you held the stick, and where the blade was\n")
        L.append("| phase | held as asked | both / top / bottom / loose | grab changes | blade height median | "
                 "p5..p95 | within a puck height | above its 1 s low (p50 / p90) | through the ice | jitter |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        for ph, P in S["phases"].items():
            sp = P["state_pct"]
            states = (f"{sp['both']:.0f} / {sp['top']:.0f} / {sp['bottom']:.0f} / "
                      f"{sp['loose top'] + sp['loose bottom']:.0f}%")
            changes = P.get("grip_changes", "")
            if "height_median_mm" in P:
                L.append(f"| {ph} | {P['held_as_expected_pct']:.0f}% | {states} | {changes} | "
                         f"{P['height_median_mm']:+.0f} mm | "
                         f"{P['height_p5_p95_mm'][0]:+.0f}..{P['height_p5_p95_mm'][1]:+.0f} mm | "
                         f"{P['near_ice_pct']:.0f}% | {f(P.get('lift_p50_mm'), 0)} / {f(P.get('lift_p90_mm'), 0)} mm | "
                         f"{P['through_ice_pct']:.0f}% | {f(P['jitter_mm'], 1, ' mm')} |")
            else:
                L.append(f"| {ph} | {P['held_as_expected_pct']:.0f}% | {states} | | | | | | | |")

    L.append("\n## Controllers\n")
    L.append("| controller | hand | fresh poses | stickhandle tracked | heads-up tracked | one-hand tracked | "
             "longest heads-up gap | tracked by gaze angle (heads-up) |")
    L.append("|---|---|---|---|---|---|---|---|")
    for d, C in S["controllers"].items():
        hu = C.get("heads_up", {})
        bins = ", ".join(f"{k} deg: {v:.0f}%" for k, v in hu.get("tracked_pct_by_gaze_angle", {}).items())
        L.append(f"| {hand[d]} | {C.get('hand', '-')} | {C['fresh_pose_hz']:.0f}/s | "
                 f"{f(C.get('stickhandle', {}).get('tracked_pct'), 1, '%')} | {f(hu.get('tracked_pct'), 1, '%')} | "
                 f"{f(C.get('one_hand', {}).get('tracked_pct'), 1, '%')} | "
                 f"{f(hu.get('longest_untracked_ms'), 0, ' ms')} | {bins} |")

    for ph, Sh in S["shots"].items():
        L.append(f"\n## {ph.replace('_', ' ').title()}\n")
        L.append(f"Peak blade speed: **{Sh['peak_blade_speed_ms']:.1f} m/s**. Per frame the blade travels "
                 + ", ".join(f"{v:.0f} cm at {k} Hz" for k, v in Sh["blade_travel_per_frame_cm"].items())
                 + f" (the puck is {PUCK_D_MM / 10:.1f} cm). For at most 1 cm per physics step: "
                 f"**{Sh['substep_hz_for_1cm']:.0f} Hz**. Peak hand speed: "
                 + ", ".join(f"{hand[d]} {v:.1f} m/s" for d, v in Sh["peak_hand_speed_ms"].items()) + ".\n")
        L.append("| shot | t | blade speed | held | tracked in swing |")
        L.append("|---|---|---|---|---|")
        for k, s in enumerate(Sh["shots"], 1):
            tr = ", ".join(f"{hand[d]} {v:.0f}%" for d, v in s["tracked_pct"].items())
            L.append(f"| {k} | {s['t']:.1f} s | {s['blade_speed_ms']:.1f} m/s | {s['held']} | {tr} |")

    L.append("\n## What the numbers mean\n")
    L.append("- **held as asked**: share of the phase with the stick held the way the step asked (both grips; "
             "top hand off for one_hand). **loose**: no grip pressed, the stick riding in the last hand that held it.")
    L.append("- **blade height**: the lowest point of the blade's bottom edge above the ice. Nothing holds it up "
             "but your hands, so this sizes the ice assist. **90% band**: nine samples in ten are within this "
             "height of the ice.")
    L.append(f"- **jitter**: the blade minus a smooth {JITTER_WINDOW_S * 1000:.0f} ms fit while stickhandling: "
             "what a game would have to smooth away (smoothing costs latency).")
    L.append("- **tracked**: the runtime is optically tracking the controller (not guessing from its IMU).")
    L.append("- Thresholds are my heuristics (good / ok): " + "; ".join(
        f"{k} {g}/{o}" for k, (g, o, _) in THRESHOLDS.items()) + ".")
    return "\n".join(L) + "\n"


def plots(t, masks, tracks, stick, low, sweet, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    spec, fit, state, R, p = stick
    shade = {grab.TOP: "#c05621", grab.BOTTOM: "#6b46c1", grab.LOOSE_TOP: "#d69e2e",
             grab.LOOSE_BOTTOM: "#9f7aea", grab.NONE: "#888888"}
    phs = [ph for ph in STICK_PHASES if ph in masks]
    if phs:
        fig, axes = plt.subplots(len(phs), 1, figsize=(11, 3.2 * len(phs)), squeeze=False)
        for ax, ph in zip(axes[:, 0], phs):
            idx = np.flatnonzero(masks[ph])
            tt = t[idx] - t[idx[0]]
            ax.plot(tt, low[idx], lw=0.6, color="#2b6cb0", label="lowest blade point")
            ax.axhline(0, color="k", lw=0.8)
            ax.axhspan(-PUCK_H_MM, PUCK_H_MM, color="gray", alpha=0.12, label="within a puck height")
            for k, c in shade.items():
                sel = state[idx] == k
                if sel.any():
                    ax.fill_between(tt, 0, 1, where=sel, color=c, alpha=0.12, transform=ax.get_xaxis_transform(),
                                    label=f"held: {grab.STATE_NAMES[k]}")
            ax.set_ylabel("mm above the ice")
            ax.set_title(f"Blade height, {ph.replace('_', ' ')}")
            ax.legend(loc="upper right", fontsize=8)
        axes[-1, 0].set_xlabel("s into phase")
        fig.tight_layout()
        fig.savefig(out / "blade_height.png", dpi=110)
        plt.close(fig)

    shot_phases = [ph for ph in SHOT_PHASES if ph in masks]
    if shot_phases:
        fig, axes = plt.subplots(len(shot_phases), 1, figsize=(11, 3.2 * len(shot_phases)), squeeze=False)
        for ax, ph in zip(axes[:, 0], shot_phases):
            idx = np.flatnonzero(masks[ph])
            tt = t[idx] - t[idx[0]]
            ax.plot(tt, fd_speed(sweet[idx], t[idx]), lw=0.7, color="#2b6cb0", label="blade speed")
            for d, c in ((spec.top_hand, "#c05621"), (spec.bottom_hand, "#6b46c1")):
                lost = ~tracks[d].tracked[idx]
                if lost.any():
                    ax.fill_between(tt, 0, 1, where=lost, color=c, alpha=0.15, transform=ax.get_xaxis_transform(),
                                    label=f"{d} not tracked")
            ax.set_ylabel("m/s")
            ax.set_title(ph.replace("_", " "))
            ax.legend(loc="upper right", fontsize=8)
        axes[-1, 0].set_xlabel("s into phase")
        fig.tight_layout()
        fig.savefig(out / "blade_speed_shots.png", dpi=110)
        plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--no-plots", action="store_true")
    args = ap.parse_args()
    analyze(args.run_dir, make_plots=not args.no_plots)
    print((Path(args.run_dir) / "report" / "report.md").read_text(encoding="utf-8"))
    print(f"plots + summary.json in {Path(args.run_dir) / 'report'}")


if __name__ == "__main__":
    main()
