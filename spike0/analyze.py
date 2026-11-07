"""Spike 0 analysis: two controllers in the hands as a virtual stick. How steady is the blade?

    uv run python analyze.py data/<run>            # report.md + plots in data/<run>/report/
    uv run python analyze.py data/<run> --no-plots

Everything is measured at the virtual blade's heel, because that is where the puck is: the puck
is 25 mm tall and 76 mm wide. Four stick models (see stickmath.py) are compared on the same data.
"Tracked" means the runtime is optically tracking the controller rather than guessing from its IMU.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import recfmt
import stickmath as sm

PUCK_H_MM = 25.4
PUCK_D_MM = 76.2
FRAME_RATES = (72, 90, 120)
JITTER_WINDOW_S = 0.05

# my heuristics for "steady enough to handle a virtual puck" (mm, %)
THRESHOLDS = {
    #  metric                    good   ok     higher_is_better
    "rest_heel_std_mm":         (3.0,  8.0,   False),
    "hold_heel_std_mm":         (6.0,  15.0,  False),
    "jitter_mm":                (3.0,  8.0,   False),
    "on_ice_pct":               (90.0, 70.0,  True),
    "heads_up_tracked_pct":     (99.0, 95.0,  True),
    "shot_tracked_pct":         (99.0, 90.0,  True),
}
RATING_WORD = {"good": "GO", "ok": "MARGINAL", "bad": "NO-GO"}
MODEL_METRICS = ("rest_heel_std_mm", "hold_heel_std_mm", "jitter_mm", "on_ice_pct")
TRACK_METRICS = ("heads_up_tracked_pct", "shot_tracked_pct")


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


def base(label: str) -> str:
    return label.split("#")[0]


def phase_masks(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Phase name -> mask of its LAST attempt (a redone stance replaces the first)."""
    labels = df["phase"].astype(str).to_numpy()
    out = {}
    for lab in pd.unique(labels):
        if lab != recfmt.GAP:
            out[base(lab)] = labels == lab
    return out


def middle(mask: np.ndarray, trim: float = 0.1) -> np.ndarray:
    idx = np.flatnonzero(mask)
    k = int(len(idx) * trim)
    out = np.zeros_like(mask)
    out[idx[k:len(idx) - k]] = True
    return out


def fd_speed(pos: np.ndarray, t: np.ndarray, half_window_s: float = 0.005) -> np.ndarray:
    """Speed from positions over a short centred window (robust to sample-and-hold)."""
    rate_ = (len(t) - 1) / (t[-1] - t[0]) if len(t) > 1 else 1000
    k = max(1, int(round(half_window_s * rate_)))
    v = np.full(len(t), np.nan)
    if len(t) > 2 * k:
        v[k:-k] = np.linalg.norm(pos[2 * k:] - pos[:-2 * k], axis=1) / (t[2 * k:] - t[:-2 * k])
    return v


def jitter_residual(pos: np.ndarray, rate_hz: float) -> np.ndarray:
    """Position minus a local quadratic fit (Savitzky-Golay, 50 ms): what is left is jitter.

    A quadratic follows real stickhandling (a few Hz) almost exactly, so the residual is
    tracking noise, update-rate stepping and tremor: the part a game would have to smooth.
    """
    k = max(2, int(round(JITTER_WINDOW_S * rate_hz / 2)))
    x = np.arange(-k, k + 1, dtype=float)
    A = np.stack([np.ones_like(x), x, x * x], axis=1)
    coef = np.linalg.pinv(A)[0]
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
    runs = np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)
    return float(runs.max() / rate_hz * 1000)


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
                                          "shoots", "stick_length_arg", "show_model", "completed", "synthetic")},
        "rates": {"query_hz": float(rate_hz), "dt_p50_ms": float(np.median(dts) * 1000),
                  "dt_p99_ms": float(np.percentile(dts, 99) * 1000), "dt_max_ms": float(dts.max() * 1000)},
        "phases_found": sorted(masks),
        "controllers": {}, "stick": {}, "models": {}, "shots": {}, "verdict": {},
    }

    # ---------------------------------------------------------------- each controller on its own
    for d, tr in tracks.items():
        C = S["controllers"][d] = {}
        ch = tr.changed() & tr.valid
        C["fresh_pose_hz"] = float(ch.sum() / max(1e-9, tr.valid.mean() * dur))
        C["valid_pct"] = float(tr.valid.mean() * 100)
        C["tracked_pct"] = float(tr.tracked.mean() * 100)
        if "rest" in masks:
            m = middle(masks["rest"]) & tr.valid
            if m.sum() > 100:
                C["rest_pos_std_mm"] = float(np.sqrt(np.sum(np.var(tr.p[m], axis=0))) * 1000)
                dR = sm.mean_rotation(tr.R[m]).T @ tr.R[m]
                C["rest_rot_rms_deg"] = float(np.sqrt(np.mean(sm.rotation_angle_deg(dR) ** 2)))
        for ph in ("stickhandle", "heads_up"):
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
                P["gaze_angle_median_deg"] = float(np.median(ang))
                bins = {}
                for lo, hi in ((0, 30), (30, 50), (50, 70), (70, 180)):
                    sel = (ang >= lo) & (ang < hi)
                    if sel.sum() > 100:
                        bins[f"{lo}-{hi}"] = float(tr.tracked[idx][sel].mean() * 100)
                P["tracked_pct_by_gaze_angle"] = bins

    # ---------------------------------------------------------------- the stick, fitted to the stance
    cal = None
    if "stance" in masks:
        both = tracks["l"].valid & tracks["r"].valid
        m = middle(masks["stance"]) & both
        if m.sum() >= 200:
            pl, pr = tracks["l"].p[m], tracks["r"].p[m]
            top = {"left": "r", "right": "l"}.get(meta.get("shoots") or "") or sm.pick_top(pl, pr)
            bot = "r" if top == "l" else "l"
            T, B = tracks[top], tracks[bot]
            try:
                cal = sm.calibrate_stance(T.R[m], T.p[m], B.R[m], B.p[m], top, 0.0, meta.get("stick_length_arg"))
                heel = sm.blade_heel("two_hand", cal, T.R[m], T.p[m], B.R[m], B.p[m])
                spread = float(np.max(np.linalg.norm(heel - np.median(heel, axis=0), axis=1)))
                S["stick"] = {**cal.to_dict(), "problems": sm.stance_problems(cal, spread)}
            except ValueError as e:
                S["stick"] = {"problems": [str(e)]}
        else:
            S["stick"] = {"problems": ["both controllers were not tracked through the stance"]}
    else:
        S["stick"] = {"problems": ["no stance phase in this run"]}

    heels: dict[str, np.ndarray] = {}
    if cal is not None:
        T, B = tracks[cal.top], tracks[cal.bottom]
        both = T.valid & B.valid
        S["controllers"][cal.top]["hand"] = "top"
        S["controllers"][cal.bottom]["hand"] = "bottom"
        st = middle(masks["stance"]) & both
        Rt_s, pt_s = sm.mean_rotation(T.R[st]), T.p[st].mean(axis=0)
        Rb_s, pb_s = sm.mean_rotation(B.R[st]), B.p[st].mean(axis=0)
        for model in sm.MODELS:
            M = S["models"][model] = {}
            heel = sm.blade_heel(model, cal, T.R, T.p, B.R, B.p)
            heel[~both] = np.nan
            heels[model] = heel
            # pure tracking noise: the rest-phase jitter of each controller, carried onto the stance
            if "rest" in masks:
                rm = middle(masks["rest"]) & both
                if rm.sum() > 100:
                    Rt_n, pt_n = sm.move_noise(T.R[rm], T.p[rm], Rt_s, pt_s)
                    Rb_n, pb_n = sm.move_noise(B.R[rm], B.p[rm], Rb_s, pb_s)
                    hn = sm.blade_heel(model, cal, Rt_n, pt_n, Rb_n, pb_n)
                    M["rest_heel_std_mm"] = float(np.sqrt(np.sum(np.var(hn, axis=0))) * 1000)
            # holding still in the stance: tracking plus the tremor of real hands
            M["hold_heel_std_mm"] = float(np.sqrt(np.sum(np.nanvar(heel[st], axis=0))) * 1000)
            for ph in ("stickhandle", "heads_up"):
                if ph not in masks:
                    continue
                idx = np.flatnonzero(masks[ph])
                h = heel[idx, 1] * 1000
                hv = h[~np.isnan(h)]
                jr = jitter_residual(heel[idx], rate_hz)
                jn = np.linalg.norm(jr, axis=1) * 1000
                P = M.setdefault(ph, {})
                if len(hv):
                    P["height_median_mm"] = float(np.median(hv))
                    P["height_p5_p95_mm"] = [float(np.percentile(hv, 5)), float(np.percentile(hv, 95))]
                    P["near_ice_pct"] = float(np.mean(np.abs(hv) <= PUCK_H_MM) * 100)
                P["jitter_mm"] = float(np.sqrt(np.nanmean(jn ** 2))) if np.isfinite(jn).any() else None

    # ---------------------------------------------------------------- shots
    if cal is not None:
        T, B = tracks[cal.top], tracks[cal.bottom]
        for ph in ("wrist_shots", "slap_shots"):
            if ph not in masks:
                continue
            idx = np.flatnonzero(masks[ph])
            tt = t[idx]
            vok = ((T.vflags[idx] & 3) == 3) & ((B.vflags[idx] & 3) == 3)
            sp = {}
            for model in sm.MODELS:
                v = np.linalg.norm(sm.heel_velocity(model, cal, T.R[idx], T.p[idx], T.v[idx], T.w[idx],
                                                    B.R[idx], B.p[idx], B.v[idx], B.w[idx]), axis=1)
                v[~vok] = np.nan
                sp[model] = {"runtime": v, "positions": fd_speed(heels[model][idx], tt)}
            ref = sp["two_hand"]["positions"]
            peaks = pick_peaks(tt, ref)
            shots = []
            for i in peaks:
                near = (tt >= tt[i] - 0.02) & (tt <= tt[i] + 0.02)
                swing = (tt >= tt[i] - 0.15) & (tt <= tt[i] + 0.15)
                s = {"t": float(tt[i]), "tracked_pct": {}, "speed": {}}
                for d, tr in ((cal.top, T), (cal.bottom, B)):
                    s["tracked_pct"][d] = float(tr.tracked[idx][swing].mean() * 100)
                for model in sm.MODELS:
                    r, p = sp[model]["runtime"][near], sp[model]["positions"][near]
                    s["speed"][model] = {"runtime": float(np.nanmax(r)) if np.isfinite(r).any() else None,
                                         "positions": float(np.nanmax(p)) if np.isfinite(p).any() else None}
                shots.append(s)
            top_speed = max((s["speed"]["two_hand"]["positions"] or 0) for s in shots) if shots else 0.0
            hand_speed = {d: float(np.nanmax(np.linalg.norm(tr.v[idx], axis=1))) for d, tr in tracks.items()}
            S["shots"][ph] = {
                "count": len(shots), "shots": shots, "peak_heel_speed_ms": top_speed,
                "peak_hand_speed_ms": hand_speed,
                "peak_wrist_rotation_deg_s": {d: float(np.degrees(np.nanmax(np.linalg.norm(tr.w[idx], axis=1))))
                                              for d, tr in tracks.items()},
                "blade_travel_per_frame_cm": {str(f): top_speed / f * 100 for f in FRAME_RATES},
                "substep_hz_for_1cm": top_speed / 0.01,
                "tracked_pct_in_swings": {d: float(np.mean([s["tracked_pct"][d] for s in shots])) if shots else None
                                          for d in (cal.top, cal.bottom)},
            }

    # ---------------------------------------------------------------- verdicts
    hu = [S["controllers"][d].get("heads_up", {}).get("tracked_pct") for d in tracks]
    sw = [S["shots"][p]["tracked_pct_in_swings"].get(d) for p in S["shots"] for d in tracks]
    track_m = {"heads_up_tracked_pct": min([x for x in hu if x is not None], default=None),
               "shot_tracked_pct": min([x for x in sw if x is not None], default=None)}
    track_r = {k: rate(k, v) for k, v in track_m.items()}
    S["verdict"]["tracking"] = {"overall": RATING_WORD[worst(track_r.values())], "metrics": track_m,
                                "ratings": track_r}
    order = {"good": 0, "ok": 1, "bad": 2}
    rank = {}
    for model, M in S["models"].items():
        m = {"rest_heel_std_mm": M.get("rest_heel_std_mm"), "hold_heel_std_mm": M.get("hold_heel_std_mm"),
             "jitter_mm": M.get("stickhandle", {}).get("jitter_mm"),
             "on_ice_pct": M.get("stickhandle", {}).get("near_ice_pct")}
        r = {k: rate(k, v) for k, v in m.items()}
        w = worst(r.values())
        S["verdict"][model] = {"overall": RATING_WORD[w], "metrics": m, "ratings": r}
        rank[model] = (order[w], M.get("rest_heel_std_mm") or 1e9)
    S["verdict"]["recommended_model"] = min(rank, key=rank.get) if rank else None
    if cal is None or S["stick"].get("problems"):
        S["verdict"]["stick_fit"] = "check: " + "; ".join(S["stick"].get("problems", []))

    out = run_dir / "report"
    out.mkdir(exist_ok=True)
    (out / "summary.json").write_text(json.dumps(S, indent=2, default=float))
    (out / "report.md").write_text(render_markdown(S), encoding="utf-8")
    if make_plots and cal is not None:
        plots(t, masks, tracks, cal, heels, rate_hz, out)
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

    st = S["stick"]
    L.append("## The stick, fitted to your stance\n")
    if "length_m" in st:
        L.append(f"{hand[st['top']]} hand on top; {st['length_m']:.2f} m from the top grip to the heel"
                 f"{' (fixed by --stick-length)' if st['length_fixed'] else ''}; hands {st['hand_sep_m'] * 100:.0f} cm "
                 f"apart; shaft {st['shaft_angle_deg']:.0f} deg below horizontal."
                 + (f" **Check:** {'; '.join(st['problems'])}." if st["problems"] else ""))
    else:
        L.append(f"No stick: {'; '.join(st.get('problems', []))}.")

    V = S["verdict"]
    L.append("\n## Verdict\n")
    tv = V["tracking"]
    L.append(f"**Controller tracking: {tv['overall']}**: worst hand heads-up "
             f"{rated(tv['metrics']['heads_up_tracked_pct'], tv['ratings']['heads_up_tracked_pct'], 1, '%')}, "
             f"in swings {rated(tv['metrics']['shot_tracked_pct'], tv['ratings']['shot_tracked_pct'], 1, '%')}.\n")
    if S["models"]:
        L.append("| stick model | verdict | blade noise, controllers at rest | holding still (with tremor) | "
                 "jitter while stickhandling | blade near the ice while stickhandling |")
        L.append("|---|---|---|---|---|---|")
        shown = m.get("show_model") or "two_hand"
        for model in S["models"]:
            mv = V[model]
            tags = [x for x, c in (("recommended", model == V.get("recommended_model")),
                                   ("shown in the headset", model == shown)) if c]
            L.append(f"| {model}{' (' + ', '.join(tags) + ')' if tags else ''} | **{mv['overall']}** | "
                     f"{rated(mv['metrics']['rest_heel_std_mm'], mv['ratings']['rest_heel_std_mm'])} | "
                     f"{rated(mv['metrics']['hold_heel_std_mm'], mv['ratings']['hold_heel_std_mm'])} | "
                     f"{rated(mv['metrics']['jitter_mm'], mv['ratings']['jitter_mm'])} | "
                     f"{rated(mv['metrics']['on_ice_pct'], mv['ratings']['on_ice_pct'], 0, '%')} |")
    L.append(f"\nFor scale: the puck is {PUCK_H_MM} mm tall and {PUCK_D_MM} mm wide.\n")

    L.append("## Controllers\n")
    L.append("| controller | hand | fresh poses | at rest: position / rotation | stickhandle tracked | "
             "heads-up tracked | longest heads-up gap | tracked by gaze angle (heads-up) |")
    L.append("|---|---|---|---|---|---|---|---|")
    for d, C in S["controllers"].items():
        hu = C.get("heads_up", {})
        bins = ", ".join(f"{k} deg: {v:.0f}%" for k, v in hu.get("tracked_pct_by_gaze_angle", {}).items())
        L.append(f"| {hand[d]} | {C.get('hand', '-')} | {C['fresh_pose_hz']:.0f}/s | "
                 f"{f(C.get('rest_pos_std_mm'), 2, ' mm')} / {f(C.get('rest_rot_rms_deg'), 3, ' deg')} | "
                 f"{f(C.get('stickhandle', {}).get('tracked_pct'), 1, '%')} | {f(hu.get('tracked_pct'), 1, '%')} | "
                 f"{f(hu.get('longest_untracked_ms'), 0, ' ms')} | {bins} |")

    if S["models"]:
        L.append("\n## Blade height while stickhandling (no ice holds it up: this is your hands alone)\n")
        L.append("| stick model | phase | median height | p5..p95 | within a puck height of the ice | jitter |")
        L.append("|---|---|---|---|---|---|")
        for model, M in S["models"].items():
            for ph in ("stickhandle", "heads_up"):
                P = M.get(ph)
                if not P or "height_median_mm" not in P:
                    continue
                L.append(f"| {model} | {ph} | {P['height_median_mm']:+.0f} mm | "
                         f"{P['height_p5_p95_mm'][0]:+.0f}..{P['height_p5_p95_mm'][1]:+.0f} mm | "
                         f"{P['near_ice_pct']:.0f}% | {f(P['jitter_mm'], 1, ' mm')} |")

    for ph, Sh in S["shots"].items():
        L.append(f"\n## {ph.replace('_', ' ').title()}\n")
        L.append(f"Peak blade (heel) speed: **{Sh['peak_heel_speed_ms']:.1f} m/s** (two_hand model). Per frame the "
                 "blade travels " + ", ".join(f"{v:.0f} cm at {k} Hz" for k, v in Sh["blade_travel_per_frame_cm"].items())
                 + f" (the puck is {PUCK_D_MM / 10:.1f} cm). For at most 1 cm per physics step: "
                 f"**{Sh['substep_hz_for_1cm']:.0f} Hz**. Peak hand speed: "
                 + ", ".join(f"{hand[d]} {v:.1f} m/s" for d, v in Sh["peak_hand_speed_ms"].items())
                 + "; peak wrist rotation: "
                 + ", ".join(f"{hand[d]} {v:.0f} deg/s" for d, v in Sh["peak_wrist_rotation_deg_s"].items()) + ".\n")
        models = list(sm.MODELS)
        L.append("| shot | t | " + " | ".join(f"{mm} (runtime / positions)" for mm in models)
                 + " | tracked in swing |")
        L.append("|---|---|" + "---|" * len(models) + "---|")
        for k, s in enumerate(Sh["shots"], 1):
            cells = " | ".join(f"{f(s['speed'][mm]['runtime'])} / {f(s['speed'][mm]['positions'])} m/s" for mm in models)
            tr = ", ".join(f"{hand[d]} {v:.0f}%" for d, v in s["tracked_pct"].items())
            L.append(f"| {k} | {s['t']:.1f} s | {cells} | {tr} |")

    L.append("\n## What the numbers mean\n")
    L.append("- **Stick models**: two_hand runs the shaft through both grips; top_hand/bottom_hand fix the stick "
             "in one hand; blend averages the two_hand and top_hand directions.")
    L.append("- **blade noise, controllers at rest**: each controller's jitter while lying still, carried onto your "
             "stance and through the stick model. Pure tracking noise at the blade.")
    L.append("- **holding still**: the blade in your stance, held still. Tracking plus real hand tremor.")
    L.append(f"- **jitter**: the blade minus a smooth {JITTER_WINDOW_S * 1000:.0f} ms fit while stickhandling: what a "
             "game would have to smooth away (smoothing costs latency).")
    L.append("- **blade height / near the ice**: with no stick, nothing holds the blade on the ice but your hands. "
             "This shows how much help the game must give (snapping the blade to the ice, or a physics stick that "
             "slides on it). You steered the model shown in the headset, so that one has an edge here; run again "
             "with --show-model to judge another fairly.")
    L.append("- **tracked**: the runtime is optically tracking the controller (not guessing from its IMU).")
    L.append("- **speed (runtime / positions)**: from the runtime's velocities vs from the positions; a big gap "
             "means smoothed or late poses.")
    L.append("- Thresholds are my heuristics (good / ok): " + "; ".join(
        f"{k} {g}/{o}" for k, (g, o, _) in THRESHOLDS.items()) + ".")
    return "\n".join(L) + "\n"


def plots(t, masks, tracks, cal, heels, rate_hz, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"two_hand": "#2b6cb0", "top_hand": "#c05621", "bottom_hand": "#6b46c1", "blend": "#2f855a"}
    hand = {"l": "left", "r": "right"}

    phs = [p for p in ("stickhandle", "heads_up") if p in masks]
    if phs:
        fig, axes = plt.subplots(len(phs), 1, figsize=(11, 3.4 * len(phs)), squeeze=False)
        for ax, ph in zip(axes[:, 0], phs):
            idx = np.flatnonzero(masks[ph])
            for model in ("two_hand", "top_hand"):
                ax.plot(t[idx] - t[idx[0]], heels[model][idx, 1] * 1000, lw=0.6, color=colors[model], label=model)
            ax.axhline(0, color="k", lw=0.8)
            ax.axhspan(-PUCK_H_MM, PUCK_H_MM, color="gray", alpha=0.12, label="within a puck height")
            ax.set_ylabel("blade heel height (mm)")
            ax.set_title(f"Blade height, {ph.replace('_', ' ')}")
            ax.legend(loc="upper right")
        axes[-1, 0].set_xlabel("s into phase")
        fig.tight_layout()
        fig.savefig(out / "blade_height.png", dpi=110)
        plt.close(fig)

    shot_phases = [p for p in ("wrist_shots", "slap_shots") if p in masks]
    if shot_phases:
        fig, axes = plt.subplots(len(shot_phases), 1, figsize=(11, 3.4 * len(shot_phases)), squeeze=False)
        for ax, ph in zip(axes[:, 0], shot_phases):
            idx = np.flatnonzero(masks[ph])
            tt = t[idx] - t[idx[0]]
            ax.plot(tt, fd_speed(heels["two_hand"][idx], t[idx]), lw=0.7, color=colors["two_hand"],
                    label="blade speed (two_hand)")
            for d, c in ((cal.top, "#c05621"), (cal.bottom, "#6b46c1")):
                lost = ~tracks[d].tracked[idx]
                if lost.any():
                    ax.fill_between(tt, 0, 1, where=lost, color=c, alpha=0.15, transform=ax.get_xaxis_transform(),
                                    label=f"{hand[d]} not tracked")
            ax.set_ylabel("m/s")
            ax.set_title(ph.replace("_", " "))
            ax.legend(loc="upper right")
        axes[-1, 0].set_xlabel("s into phase")
        fig.tight_layout()
        fig.savefig(out / "blade_speed_shots.png", dpi=110)
        plt.close(fig)

    if "stickhandle" in masks:
        idx = np.flatnonzero(masks["stickhandle"])
        fig, ax = plt.subplots(figsize=(11, 3.4))
        for model in sm.MODELS:
            jr = np.linalg.norm(jitter_residual(heels[model][idx], rate_hz), axis=1) * 1000
            ax.plot(t[idx] - t[idx[0]], jr, lw=0.5, color=colors[model], label=model, alpha=0.8)
        ax.set_ylabel("jitter (mm)")
        ax.set_xlabel("s into stickhandling")
        ax.set_title("Blade jitter while stickhandling (blade minus a smooth 50 ms fit)")
        ax.legend(loc="upper right")
        fig.tight_layout()
        fig.savefig(out / "blade_jitter.png", dpi=110)
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
