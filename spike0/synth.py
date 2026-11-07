"""Synthetic Spike 0 recordings with known truth, to test analyze.py without a headset.

    uv run python synth.py data/synth            # writes rec.csv, meta.json, truth.json

Two hands hold a virtual stick (heel at the origin of its frame, blade along +x, shaft up at
a 45 degree lie): the right hand on top (a left shot), the left hand down the shaft. Each
controller sees its own update rate (sample-and-hold), white noise, slow drift, and tracking
dropouts where the runtime would dead-reckon on the IMU.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import protocol
import recfmt
import stickmath as sm

RATE = 1000.0
GAP_S = 4.0
LIE = np.radians(45)
U = np.array([-np.cos(LIE), np.sin(LIE), 0.0])    # shaft direction in the stick frame (heel at origin)
TOP, BOT = "r", "l"                                # left shot: right hand on top
S_TOP, S_BOT = 1.40, 0.85                          # grips, metres up the shaft from the heel
SHOTS = {"wrist_shots": dict(v=14.0, T=0.22, n=6), "slap_shots": dict(v=22.0, T=0.28, n=5)}
NOISE = {  # pos sigma m, rot sigma deg, drift m, update Hz
    TOP: (0.0005, 0.05, 0.002, 500),
    BOT: (0.0006, 0.06, 0.002, 500),
}
X, Y, Z = np.eye(3)


def expmap(r: np.ndarray) -> np.ndarray:
    """(N, 3) rotation vectors -> (N, 3, 3) matrices."""
    r = np.atleast_2d(r)
    th = np.linalg.norm(r, axis=1)
    k = np.where(th[:, None] > 1e-12, r / np.maximum(th, 1e-12)[:, None], 0.0)
    K = np.zeros((len(r), 3, 3))
    K[:, 0, 1], K[:, 0, 2] = -k[:, 2], k[:, 1]
    K[:, 1, 0], K[:, 1, 2] = k[:, 2], -k[:, 0]
    K[:, 2, 0], K[:, 2, 1] = -k[:, 1], k[:, 0]
    s, c = np.sin(th)[:, None, None], np.cos(th)[:, None, None]
    return np.eye(3) + s * K + (1 - c) * (K @ K)


def rot(axis, angles) -> np.ndarray:
    return expmap(np.outer(angles, axis))


def ease(x):
    x = np.clip(x, 0, 1)
    return (1 - np.cos(np.pi * x)) / 2


def gen_stick(name: str, tau: np.ndarray):
    """Stick pose (R_ws, p_ws = world position of the heel) and the bottom grip's place on the shaft."""
    n = len(tau)
    two_pi = 2 * np.pi
    s_bot = np.full(n, S_BOT)
    if name == "stance":
        R = rot(Y, 0.004 * np.sin(two_pi * 0.3 * tau))
        p = np.stack([0.002 * np.sin(two_pi * 0.2 * tau), np.zeros(n), np.full(n, -0.3)], axis=1)
        return R, p, s_bot
    if name in ("stickhandle", "heads_up"):
        T = tau[-1] if n > 1 else 1.0
        f = 0.8 + 2.2 * tau / T
        phi = two_pi * np.cumsum(f) / RATE
        R = rot(Y, 0.35 * np.sin(phi)) @ rot(X, 0.25 * np.sin(phi + 0.5))
        m = np.mod(tau, 3.7)
        lift = np.where(m < 0.15, 0.02 * np.sin(np.pi * m / 0.15), 0.0)
        p = np.stack([0.1 + 0.05 * np.sin(phi), lift, -0.2 + 0.30 * np.sin(phi)], axis=1)
        return R, p, S_BOT + 0.08 * np.sin(phi + 1.0)          # the bottom hand slides on the shaft
    if name in SHOTS:
        sp = SHOTS[name]
        H_s = 1.8 * U                                           # the swing turns about the shoulders
        r = np.linalg.norm(H_s[1:])                             # heel's arc radius about the x axis through H
        th_tot = sp["v"] * sp["T"] / (2 * r)
        cycle = (tau[-1] + 1e-3) / sp["n"]
        k = np.minimum((tau // cycle).astype(int), sp["n"] - 1)
        tc = tau - k * cycle
        T = sp["T"]
        th = np.where(tc < 1.5, -th_tot / 2 * ease(tc / 1.5),
             np.where(tc < 1.5 + T,
                      th_tot * ((tc - 1.5) / T - np.sin(two_pi * (tc - 1.5) / T) / two_pi) - th_tot / 2,
                      th_tot / 2 * (1 - ease((tc - 1.5 - T) / 1.5))))
        R = rot(X, th)
        c = np.array([0.0, 0.0, -0.3])
        p = (c + H_s) - R @ H_s
        return R, p, s_bot
    raise ValueError(name)


def angular_velocity(R, t):
    """World-frame angular velocity from a rotation sequence (central differences)."""
    W = np.gradient(R, t, axis=0) @ np.transpose(R, (0, 2, 1))
    return np.stack([(W[:, 2, 1] - W[:, 1, 2]) / 2, (W[:, 0, 2] - W[:, 2, 0]) / 2,
                     (W[:, 1, 0] - W[:, 0, 1]) / 2], axis=1)


def head_pose(n, target, forward_only):
    pos = np.array([-0.9, 1.65, 0.35])
    f = np.array([1.0, -0.05, 0.0]) if forward_only else target - pos
    f = f / np.linalg.norm(f)
    right = np.cross(f, [0, 1, 0])
    right /= np.linalg.norm(right)
    up = np.cross(right, f)
    R = np.stack([right, up, -f], axis=1)
    return np.repeat(sm.mat_to_quat(R)[None], n, axis=0), np.tile(pos, (n, 1))


def blend(R0, p0, R1, p1, n):
    """Smooth move between two poses (the gaps between phases)."""
    s = ease(np.linspace(0, 1, n))
    q0, q1 = sm.mat_to_quat(R0), sm.mat_to_quat(R1)
    if np.dot(q0, q1) < 0:
        q1 = -q1
    q = (1 - s)[:, None] * q0 + s[:, None] * q1
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    return sm.quat_to_mat(q), (1 - s)[:, None] * p0 + s[:, None] * p1


def synthesize(out_dir: Path, seed: int = 1) -> dict:
    rng = np.random.default_rng(seed)
    grip = {TOP: expmap(rng.normal(size=(1, 3)) * 1.0)[0], BOT: expmap(rng.normal(size=(1, 3)) * 1.0)[0]}
    wobble_axis = sm.unit(rng.normal(size=3))
    start = {TOP: (expmap(rng.normal(size=(1, 3)))[0], np.array([-0.6, 0.9, 0.3])),     # hands at the sides
             BOT: (expmap(rng.normal(size=(1, 3)))[0], np.array([-0.6, 0.9, -0.2]))}
    phases = protocol.select()

    hands = {d: {"R": [], "p": []} for d in (TOP, BOT)}
    heel_true, labels, heads_q, heads_p, phase_log = [], [], [], [], []
    lead = int(GAP_S * RATE)
    last = {d: start[d] for d in (TOP, BOT)}             # each hand's last pose (R, p)
    t_cursor = 0.0
    for ph in phases:
        n = int(ph.seconds * RATE)
        tau = np.arange(n) / RATE
        R_ws, p_ws, s_bot = gen_stick(ph.name, tau)
        wob = rot(wobble_axis, 0.12 * np.sin(2 * np.pi * 0.4 * tau))          # the bottom hand is not glued on
        cur = {TOP: (R_ws @ grip[TOP], p_ws + R_ws @ (S_TOP * U)),
               BOT: (R_ws @ grip[BOT] @ wob, p_ws + np.einsum("nij,nj->ni", R_ws, s_bot[:, None] * U))}
        heel = p_ws
        for d in (TOP, BOT):
            gR, gp = blend(last[d][0], last[d][1], cur[d][0][0], cur[d][1][0], lead)
            hands[d]["R"] += [gR, cur[d][0]]
            hands[d]["p"] += [gp, cur[d][1]]
            last[d] = (cur[d][0][-1], cur[d][1][-1])
        heel_true += [np.full((lead, 3), np.nan), heel]
        labels += [recfmt.GAP] * lead + [ph.name] * n
        for lab, m in ((recfmt.GAP, lead), (ph.name, n)):
            hq, hp = head_pose(m, np.array([0.1, 0.0, -0.2]), lab == "heads_up")
            heads_q.append(hq)
            heads_p.append(hp)
        start = t_cursor + lead / RATE
        phase_log.append({"label": ph.name, "name": ph.name, "start_t": start, "end_t": start + n / RATE})
        t_cursor = start + n / RATE
    heel_true = np.concatenate(heel_true)
    N = len(heel_true)
    t = np.arange(N) / RATE
    labels = np.array(labels, dtype=object)
    clean = {d: (np.concatenate(hands[d]["R"]), np.concatenate(hands[d]["p"])) for d in (TOP, BOT)}

    cols: dict[str, np.ndarray] = {"t": t, "xr_ns": (t * 1e9).astype(np.int64) + 10**14, "phase": labels}
    truth: dict = {"top": TOP, "length_m": S_TOP, "hand_sep_m": S_TOP - S_BOT, "rate_hz": RATE,
                   "controllers": {}, "shots": {}, "models": {}}

    speed = np.full(N, np.nan)
    ok = ~np.isnan(heel_true[:, 0])
    speed[ok] = np.linalg.norm(np.gradient(heel_true[ok], t[ok], axis=0), axis=1)
    for name, sp in SHOTS.items():
        sel = np.flatnonzero(labels == name)
        truth["shots"][name] = [float(c.max()) for c in np.array_split(speed[sel], sp["n"])]

    noisy = {}
    for d in (TOP, BOT):
        pos_sigma, rot_sigma, drift_amp, hz = NOISE[d]
        R_c, p_c = clean[d]
        v_c = np.gradient(p_c, t, axis=0)
        w_c = angular_velocity(R_c, t)
        src = np.clip(np.floor(np.floor(t * hz) / hz * RATE + 1e-6).astype(int), 0, N - 1)
        noise_p = rng.normal(scale=pos_sigma, size=(N, 3))[src]
        noise_r = expmap(rng.normal(scale=np.radians(rot_sigma), size=(N, 3)))[src]
        k = int(N / 100) + 2
        a = np.exp(-0.1 / 2.0)
        dr = np.zeros((k, 3))
        e = rng.normal(size=(k, 3)) * drift_amp * np.sqrt(1 - a * a)
        for i in range(1, k):
            dr[i] = a * dr[i - 1] + e[i]
        drift = np.stack([np.interp(t, np.arange(k) * 0.1, dr[:, j]) for j in range(3)], axis=1)
        lost = np.zeros(N, dtype=bool)
        if d == BOT:   # the lower hand drops out heads-up and through each shot's fast part
            lost |= (labels == "heads_up") & (np.mod(t, 2.0) < 0.6)
            for name in SHOTS:
                sel = np.flatnonzero(labels == name)
                lost[sel[speed[sel] > 0.7 * np.nanmax(speed[sel])]] = True
        err = np.zeros((N, 3))
        if lost.any():
            starts = np.flatnonzero(lost & ~np.concatenate([[False], lost[:-1]]))
            ends = np.flatnonzero(lost & ~np.concatenate([lost[1:], [False]]))
            for s0, s1 in zip(starts, ends):
                acc = sm.unit(rng.normal(size=3)) * 1.0                       # 1 m/s^2 of IMU bias
                dt_ = t[s0:s1 + 1] - t[s0]
                err[s0:s1 + 1] = 0.5 * np.outer(dt_ ** 2, acc)
        R_n = noise_r @ R_c[src]
        p_n = p_c[src] + noise_p + drift[src] + err[src]
        noisy[d] = (R_n, p_n)
        q_n = sm.mat_to_quat(R_n)
        cols[f"{d}_flags"] = np.where(lost, recfmt.FLAG_POS_VALID | recfmt.FLAG_ORI_VALID, 0xF)
        for j, ax in enumerate("xyz"):
            cols[f"{d}_p{ax}"] = p_n[:, j]
        for j, ax in enumerate("xyzw"):
            cols[f"{d}_q{ax}"] = q_n[:, j]
        cols[f"{d}_vflags"] = np.full(N, 3)
        for j, ax in enumerate("xyz"):
            cols[f"{d}_v{ax}"] = v_c[src][:, j] + rng.normal(scale=0.01, size=N)
            cols[f"{d}_w{ax}"] = w_c[src][:, j] + rng.normal(scale=0.01, size=N)
        truth["controllers"][d] = {"hand": "top" if d == TOP else "bottom", "update_hz": hz}

    # truth for the stick models: the true fit (clean stance) and the analysis' own statistics
    def mid(name):
        e = next(x for x in phase_log if x["name"] == name)
        span = e["end_t"] - e["start_t"]
        return (t >= e["start_t"] + 0.1 * span) & (t < e["end_t"] - 0.1 * span)

    st, sh = mid("stance"), labels == "stickhandle"
    cal = sm.calibrate_stance(clean[TOP][0][st], clean[TOP][1][st], clean[BOT][0][st], clean[BOT][1][st], TOP)
    truth["stick"] = cal.to_dict()
    for model in sm.MODELS:
        hs = sm.blade_heel(model, cal, noisy[TOP][0][st], noisy[TOP][1][st], noisy[BOT][0][st], noisy[BOT][1][st])
        hh = sm.blade_heel(model, cal, noisy[TOP][0][sh], noisy[TOP][1][sh], noisy[BOT][0][sh], noisy[BOT][1][sh])
        truth["models"][model] = {
            "hold_heel_std_mm": float(np.sqrt(np.sum(np.var(hs, axis=0))) * 1000),
            "stickhandle_height_median_mm": float(np.median(hh[:, 1]) * 1000),
        }

    hq, hp = np.concatenate(heads_q), np.concatenate(heads_p)
    cols["h_flags"] = np.full(N, 0xF)
    for j, ax in enumerate("xyz"):
        cols[f"h_p{ax}"] = hp[:, j]
    for j, ax in enumerate("xyzw"):
        cols[f"h_q{ax}"] = hq[:, j]

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(cols)[recfmt.COLUMNS].to_csv(out_dir / "rec.csv", index=False, float_format="%.7g")
    recfmt.write_meta(out_dir, {"synthetic": True, "seed": seed, "rate_hz": RATE, "lag_ms": 0, "space": "stage",
                                "runtime": "synth", "system": "synth", "shoots": None, "stick_length_arg": None,
                                "notes": "synthetic: right hand on top (left shot)", "phases": phase_log,
                                "completed": True})
    (out_dir / "truth.json").write_text(json.dumps(truth, indent=2))
    return truth


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", nargs="?", default=str(Path(__file__).parent / "data" / "synth"))
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    print(json.dumps(synthesize(Path(args.out), seed=args.seed), indent=2))


if __name__ == "__main__":
    main()
