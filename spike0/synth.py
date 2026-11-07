"""Synthetic Spike 0 recordings with known truth, to test analyze.py without a headset.

    uv run python synth.py data/synth            # writes rec.csv, meta.json, truth.json

A 5'8" left shot's stick (stickspec) moves through the protocol. The right (top) hand holds
it where the fit says; the left hand sits on the shaft and slides along it. Both grips are
held, except in one_hand where the top hand lets go and the stick rides in the left hand.
Each controller gets its own update rate (sample-and-hold), white noise, slow drift, and
dropouts where the runtime would dead-reckon on the IMU.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import grab
import protocol
import recfmt
import stickmath as sm
import stickspec

RATE = 1000.0
GAP_S = 4.0
SPEC = stickspec.from_height(stickspec.parse_height("5'8\""), "left")
FIT = grab.Fit(roll_deg=20.0, pitch_deg=-10.0, yaw_deg=5.0)
TOP, BOT = SPEC.top_hand, SPEC.bottom_hand
S_BOT = 0.80                                       # bottom grip, metres up the shaft from the heel
SHOTS = {"wrist_shots": dict(v=14.0, T=0.22, n=6), "slap_shots": dict(v=22.0, T=0.28, n=5)}
NOISE = {TOP: (0.0005, 0.05, 0.002, 500),          # pos sigma m, rot sigma deg, drift m, update Hz
         BOT: (0.0006, 0.06, 0.002, 500)}
X, Y, Z = np.eye(3)
expmap = sm.expmap


def rot(axis, angles) -> np.ndarray:
    return expmap(np.outer(angles, axis))


def ease(x):
    x = np.clip(x, 0, 1)
    return (1 - np.cos(np.pi * x)) / 2


def gen_stick(name: str, tau: np.ndarray):
    """Stick pose (R_ws, p_ws = the heel) and the bottom grip's place on the shaft."""
    n = len(tau)
    two_pi = 2 * np.pi
    u = SPEC.u
    s_bot = np.full(n, S_BOT)
    if name in ("stickhandle", "heads_up", "one_hand"):
        T = tau[-1] if n > 1 else 1.0
        f = 0.8 + 2.2 * tau / T
        phi = two_pi * np.cumsum(f) / RATE
        R = rot(Y, 0.35 * np.sin(phi)) @ rot(X, 0.25 * np.sin(phi + 0.5))
        m = np.mod(tau, 3.7)
        lift = np.where(m < 0.15, 0.02 * np.sin(np.pi * m / 0.15), 0.0)
        p = np.stack([0.1 + 0.05 * np.sin(phi), lift, -0.2 + 0.30 * np.sin(phi)], axis=1)
        if name != "one_hand":
            s_bot = S_BOT + 0.08 * np.sin(phi + 1.0)              # the bottom hand slides on the shaft
        return R, p, s_bot
    if name in SHOTS:
        sp = SHOTS[name]
        H_s = 1.8 * u                                           # the swing turns about the shoulders
        r = np.linalg.norm((SPEC.sweet - H_s)[1:])
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
        return R, (c + H_s) - R @ H_s, s_bot
    raise ValueError(name)


def angular_velocity(R, t):
    W = np.gradient(R, t, axis=0) @ np.transpose(R, (0, 2, 1))
    return np.stack([(W[:, 2, 1] - W[:, 1, 2]) / 2, (W[:, 0, 2] - W[:, 2, 0]) / 2,
                     (W[:, 1, 0] - W[:, 0, 1]) / 2], axis=1)


def head_pose(n, forward_only):
    pos = np.array([-0.9, 1.6, 0.35])
    f = np.array([1.0, -0.05, 0.0]) if forward_only else np.array([0.1, 0.0, -0.2]) - pos
    f = f / np.linalg.norm(f)
    right = sm.unit(np.cross(f, [0, 1, 0]))
    R = np.stack([right, np.cross(right, f), -f], axis=1)
    return np.repeat(sm.mat_to_quat(R)[None], n, axis=0), np.tile(pos, (n, 1))


def blend(R0, p0, R1, p1, n):
    s = ease(np.linspace(0, 1, n))
    q0, q1 = sm.mat_to_quat(R0), sm.mat_to_quat(R1)
    if np.dot(q0, q1) < 0:
        q1 = -q1
    q = (1 - s)[:, None] * q0 + s[:, None] * q1
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    return sm.quat_to_mat(q), (1 - s)[:, None] * p0 + s[:, None] * p1


def synthesize(out_dir: Path, seed: int = 1) -> dict:
    rng = np.random.default_rng(seed)
    R_ts, p_ts = grab.hold(SPEC, FIT)
    G_b = expmap(rng.normal(size=(1, 3)))[0]           # how the bottom controller sits on the shaft
    wobble_axis = sm.unit(rng.normal(size=3))
    phases = protocol.select()

    sticks_R, sticks_p, s_bots, labels, grip_top, heads_q, heads_p, phase_log = [], [], [], [], [], [], [], []
    lead = int(GAP_S * RATE)
    prev = None
    t_cursor = 0.0
    for ph in phases:
        n = int(ph.seconds * RATE)
        tau = np.arange(n) / RATE
        R, p, sb = gen_stick(ph.name, tau)
        gR, gp = blend(*(prev or (R[0], p[0] + [0, 0.3, 0])), R[0], p[0], lead)    # the stick moves between steps
        sticks_R += [gR, R]
        sticks_p += [gp, p]
        s_bots += [np.full(lead, sb[0]), sb]
        labels += [recfmt.GAP] * lead + [ph.name] * n
        grip_top += [np.ones(lead), np.zeros(n) if ph.name == "one_hand" else np.ones(n)]
        for lab, m in ((recfmt.GAP, lead), (ph.name, n)):
            hq, hp = head_pose(m, lab == "heads_up")
            heads_q.append(hq)
            heads_p.append(hp)
        start = t_cursor + lead / RATE
        phase_log.append({"label": ph.name, "name": ph.name, "start_t": start, "end_t": start + n / RATE})
        t_cursor = start + n / RATE
        prev = (R[-1], p[-1])
    R_s, p_s = np.concatenate(sticks_R), np.concatenate(sticks_p)
    s_bot = np.concatenate(s_bots)
    labels = np.array(labels, dtype=object)
    N = len(R_s)
    t = np.arange(N) / RATE

    # the hands that hold this stick
    R_t = R_s @ R_ts.T
    p_t = p_s - np.einsum("nij,j->ni", R_t, p_ts)
    wob_angle = np.where(np.isin(labels, ["stickhandle", "heads_up", "wrist_shots", "slap_shots"]),
                         0.12 * np.sin(2 * np.pi * 0.4 * t), 0.0)
    R_b = R_s @ G_b @ rot(wobble_axis, wob_angle)
    p_b = p_s + np.einsum("nij,nj->ni", R_s, s_bot[:, None] * SPEC.u)
    clean = {TOP: (R_t, p_t), BOT: (R_b, p_b)}
    grips = {TOP: np.concatenate(grip_top), BOT: np.ones(N)}

    cols: dict[str, np.ndarray] = {"t": t, "xr_ns": (t * 1e9).astype(np.int64) + 10**14, "phase": labels}
    edge = SPEC.edge(8)
    low_true = (np.einsum("nij,kj->nki", R_s, edge)[..., 1] + p_s[:, None, 1]).min(axis=1) * 1000
    sweet_true = np.einsum("nij,j->ni", R_s, SPEC.sweet) + p_s
    speed = np.linalg.norm(np.gradient(sweet_true, t, axis=0), axis=1)
    truth: dict = {"spec": SPEC.to_dict(), "fit": FIT.to_dict(), "phases": {}, "shots": {}, "controllers": {}}
    for ph in ("stickhandle", "heads_up", "one_hand"):
        h = low_true[labels == ph]
        truth["phases"][ph] = {"height_median_mm": float(np.median(h)),
                               "near_ice_pct": float(np.mean(np.abs(h) <= 25.4) * 100)}
    for name, sp in SHOTS.items():
        sel = np.flatnonzero(labels == name)
        truth["shots"][name] = [float(c.max()) for c in np.array_split(speed[sel], sp["n"])]

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
                lost[sel[speed[sel] > 0.7 * speed[sel].max()]] = True
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
        cols[f"{d}_grip"] = grips[d]
        truth["controllers"][d] = {"hand": "top" if d == TOP else "bottom", "update_hz": hz}

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
                                "runtime": "synth", "system": "synth", "spec": SPEC.to_dict(), "fit": FIT.to_dict(),
                                "fit_source": "synthetic", "notes": "synthetic: 5'8\" left shot",
                                "phases": phase_log, "completed": True})
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
