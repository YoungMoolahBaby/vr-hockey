"""Baseline measures for the synthesis acceptance table, from synth_probe.py runs.

Usage: uv run python <this> <prefix>     (reads <prefix>_s*.npz / .json)
Skater-minutes and game-minutes use the true tick times (the AI ticks about every 20.5 ms)."""
import glob
import json
import sys
from collections import Counter

import numpy as np

pre = sys.argv[1]
files = sorted(glob.glob(pre + "_s*.npz"))
ACCEL = 5.0


def ang(u, v):
    return np.arctan2(u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0], (u * v).sum(1))


def pct(x, q):
    x = np.asarray(x, dtype=float)
    return float(np.percentile(x, q)) if len(x) else float("nan")


A = Counter()
L = {k: [] for k in ["speed_frac", "face_rate", "face_off", "jerk", "lat", "react_lat", "press", "stick_in",
                     "open0", "puck_behind", "carry_speed"]}
skmin = 0.0
gmin = 0.0
loose_min = {"us": 0.0, "them": 0.0}
settled_def_min = 0.0
carry_s = 0.0
for f in files:
    d = np.load(f)
    t, live, H, P, V, F, TG, MK, CH, PK = (d[k] for k in ["t", "live", "holder", "pos", "vel", "facing", "target",
                                                           "marks", "chaser", "puck"])
    CAR = d["carrier"]
    teams = d["teams"]
    vmax = float(d["vmax"])
    n, J = len(t), P.shape[1]
    dt = np.r_[np.diff(t), 0.02]
    ok = np.zeros(n, bool)                      # live, skipping 0.5 s after each drop
    start = None
    for i in range(n):
        if live[i] and start is None:
            start = t[i]
        if not live[i]:
            start = None
        if start is not None and t[i] - start > 0.5:
            ok[i] = True
    gmin += float(dt[ok].sum()) / 60
    okk = ok[1:] & ok[:-1]
    # holder changes (any change of who has it: a player, a goalie, or loose)
    hch = np.r_[False, (H[1:] != H[:-1]) & okk]
    A["holder_changes"] += int(hch.sum())
    ci = np.flatnonzero(hch)
    if len(ci) > 1:
        A["spells_under_0.3"] += int(np.sum(np.diff(t[ci]) < 0.3))
        A["spells"] += len(ci) - 1
    near_h = np.zeros(n, bool)
    for i in ci:
        near_h[max(0, i - 1):i + 2] = True
    # attacking team per tick (team of a player or keeper holder; kept through loose spells), for marks
    att = np.empty(n, dtype=object)
    cur, flip_t = None, -9.0
    flip_at = np.zeros(n)
    for i in range(n):
        if not live[i]:
            cur, flip_t = None, t[i]
        else:
            if H[i] >= 0:
                tm = teams[H[i]]
            elif H[i] == -2:
                tm = "us"
            elif H[i] == -3:
                tm = "them"
            else:
                tm = None
            if tm is not None and tm != cur:
                cur, flip_t = tm, t[i]
        att[i], flip_at[i] = cur, flip_t
    for j in range(J):
        p, vc, fc, tg = P[:, j], V[:, j], F[:, j], TG[:, j]
        s = np.linalg.norm(vc, axis=1)
        skmin += float(dt[ok].sum()) / 60
        L["speed_frac"].append(s[ok] / vmax)
        A["standing"] += int(np.sum(ok & (s < 0.3)))
        A["ticks"] += int(ok.sum())
        A["ge90"] += int(np.sum(ok & (s >= 0.9 * vmax)))
        A["ge98"] += int(np.sum(ok & (s >= 0.98 * vmax)))
        A["under60"] += int(np.sum(ok & (s < 0.6 * vmax)))
        # commanded acceleration
        dvc = np.diff(vc, axis=0)
        ac = np.linalg.norm(dvc, axis=1) / np.diff(t)
        A["at_cap"] += int(np.sum((ac > 0.98 * ACCEL) & okk))
        big = (np.linalg.norm(dvc[1:], axis=1) > 0.9 * ACCEL * 0.02) & (np.linalg.norm(dvc[:-1], axis=1) > 0.9 * ACCEL * 0.02)
        flip = np.abs(ang(dvc[:-1], dvc[1:])) > np.radians(90)
        A["cap_flip"] += int(np.sum(big & flip & okk[1:] & okk[:-1]))
        acv = dvc / np.diff(t)[:, None]
        jk = np.linalg.norm(np.diff(acv, axis=0), axis=1) / 0.02
        L["jerk"].append(jk[okk[1:] & okk[:-1]])
        # hard bouts from commanded speed (0.25 s smoothing, >= 0.3 s above 2 m/s^2)
        ds = np.gradient(np.convolve(s, np.ones(13) / 13, "same"), t)
        for sign, name in ((1, "acc_bouts"), (-1, "dec_bouts")):
            m = (sign * ds > 2.0) & ok
            e = np.flatnonzero(np.diff(np.r_[0, m.astype(int), 0]))
            A[name] += int(sum(1 for a0, a1 in zip(e[::2], e[1::2]) if a1 - a0 >= 15))
        # facing
        fr = np.degrees(np.abs(ang(fc[:-1], fc[1:])) / np.diff(t))
        L["face_rate"].append(fr[okk])
        mv = ok & (s > 1.0)
        L["face_off"].append(np.degrees(np.abs(ang(fc[mv], vc[mv]))))
        # shoves: moved more than its velocity says
        resid = np.linalg.norm(np.diff(p, axis=0) - vc[1:] * np.diff(t)[:, None], axis=1)
        A["shove"] += int(np.sum((resid > 0.03) & okk))
        # target jumps
        tj = np.nan_to_num(np.linalg.norm(np.diff(tg, axis=0), axis=1))
        jumps = np.flatnonzero((tj > 2.0) & okk) + 1
        A["target_jump"] += len(jumps)
        A["target_jump_settled"] += int(np.sum(~near_h[jumps]))
        # role reaction: after each holder change, when does this skater's target first move > 1.5 m?
        for i in ci:
            if i < 1 or np.isnan(tg[i - 1]).any():
                continue
            ref = tg[i - 1]
            for k in range(i, min(n, i + 50)):
                if not ok[k]:
                    break
                if not np.isnan(tg[k]).any() and np.linalg.norm(tg[k] - ref) > 1.5:
                    L["react_lat"].append(t[k] - t[i])
                    break
        # off the puck: the puck behind him (> 90 deg from facing)
        off = ok & (H != j)
        to_p = PK[off] - p[off]
        L["puck_behind"].append(np.degrees(np.abs(ang(fc[off], to_p))) > 90)
        # marks: changes for the defending team, split settled / within 0.65 s of a change of attacker
        mk = MK[:, j]
        for i in range(1, n):
            if not (ok[i] and ok[i - 1]) or att[i] is None or teams[j] == att[i]:
                continue
            if i == 1 or True:
                pass
            if mk[i] != mk[i - 1] and mk[i - 1] >= 0 and mk[i] >= 0:
                if t[i] - flip_at[i] <= 0.65:
                    A["mark_after_flip"] += 1
                else:
                    A["mark_settled"] += 1
        dm = ok & np.array([a is not None and a != teams[j] for a in att])
        settled_def_min += float(dt[dm & (t - flip_at > 0.65)].sum()) / 60
    # chasers: per team, during loose time (puck not held by anyone)
    loose = ok & (H == -1)
    for k, team in enumerate(("us", "them")):
        c = CH[:, k]
        loose_min[team] += float(dt[loose].sum()) / 60
        chg = np.flatnonzero(loose[1:] & loose[:-1] & (c[1:] != c[:-1]) & (c[1:] >= 0) & (c[:-1] >= 0)) + 1
        A["chaser_changes"] += len(chg)
        for i in chg:                                 # back to the previous chaser within 1 s?
            prev = c[i - 1]
            w = np.flatnonzero((t > t[i]) & (t <= t[i] + 1.0))
            if len(w) and np.any(c[w] == prev):
                A["chaser_back"] += 1
    # carrier rows
    cr = CAR[ok & (H >= 0)]
    cr = cr[~np.isnan(cr[:, 0])]
    L["press"].append(cr[:, 0])
    L["stick_in"].append(cr[:, 5])
    L["open0"].append(cr[:, 2] == 0)
    L["carry_speed"].append(cr[:, 4] / (0.85 * vmax))
    carry_s += len(cr) * float(np.median(dt))

R = {k: (np.concatenate(v) if len(v) else np.array([])) for k, v in L.items() if k != "react_lat"}
R["react_lat"] = np.array(L["react_lat"])

# ---------------------------------------------------------------- events
passes, shots, poss, loses, takes = [], [], [], [], []
for f in sorted(glob.glob(pre + "_s*.json")):
    e = json.load(open(f))
    passes += [p for p in e["passes"] if "face_angle" in p and p["outcome"] not in ("reset", "goal", "end")]
    shots += e["shots"]
    poss += [c for c in e["poss"] if c["how"] not in ("reset", "goal", "end", "?")]
    loses += e["loses"]
    takes += e["takes"]
po = Counter(p["outcome"] for p in passes)
npass = len(passes)
picked = [p for p in passes if p["outcome"] == "picked"]
holds = [p["hold"] for p in passes if p["hold"] is not None] + [s["hold"] for s in shots if s["hold"] is not None]
dur = [c["t1"] - c["t0"] for c in poss]
ends = Counter(c["how"] for c in poss)
q_shots = [s for s in shots if s["from_pass"] and s["hold"] is not None and s["hold"] < 0.5]

out = {
    "files": len(files), "game_min": round(gmin, 1), "skater_min": round(skmin, 1), "vmax": vmax,
    "skate": {
        "mean_speed_over_top": round(float(R["speed_frac"].mean()), 3),
        "time_ge_90pct_top": round(A["ge90"] / A["ticks"], 3),
        "time_ge_98pct_top": round(A["ge98"] / A["ticks"], 3),
        "time_under_60pct_top": round(A["under60"] / A["ticks"], 3),
        "time_standing_lt_0.3": round(A["standing"] / A["ticks"], 3),
        "backward_gt120deg_moving": round(float(np.mean(R["face_off"] > 120)), 4),
        "ticks_on_accel_cap": round(A["at_cap"] / A["ticks"], 3),
        "cap_flips_per_skmin": round(A["cap_flip"] / skmin, 1),
        "jerk_p99": round(pct(R["jerk"], 99)),
        "hard_acc_per_skmin": round(A["acc_bouts"] / skmin, 1),
        "hard_dec_per_skmin": round(A["dec_bouts"] / skmin, 1),
        "facing_rate_p99_deg_s": round(pct(R["face_rate"], 99)),
        "shoves_per_skmin": round(A["shove"] / skmin, 1),
        "target_jumps_per_skmin": round(A["target_jump"] / skmin, 1),
        "target_jumps_settled_per_skmin": round(A["target_jump_settled"] / skmin, 1),
    },
    "possession": {
        "holder_changes_per_game_min": round(A["holder_changes"] / gmin, 1),
        "spells_under_0.3s": round(A["spells_under_0.3"] / max(1, A["spells"]), 3),
        "ai_touch_mean_s": round(float(np.mean(dur)), 2), "ai_touch_median_s": round(pct(dur, 50), 2),
        "touches_per_game_min": round(len(poss) / gmin, 1),
        "touch_ends": {k: round(v / len(poss), 3) for k, v in ends.items()},
        "losses_per_carry_s": round(sum(v for k, v in ends.items() if k.startswith("lost")) / carry_s, 3),
        "poke_losses_per_carry_s": round(ends.get("lost:poke", 0) / carry_s, 3),
        "touches_with_1s_away_from_net": sum(1 for c in poss if c["away"] >= 1.0),
        "touches_n": len(poss),
    },
    "passing": {
        "n": npass, "per_game_min": round(npass / gmin, 2),
        "outcomes": {k: round(v / npass, 3) for k, v in po.items()},
        "completion": round(po["same"] / npass, 3),
        "picked_after_receiver_missed_roll": sum(1 for p in picked if p["missed_roll"] > 0), "picked": len(picked),
        "passes_with_a_missed_roll": sum(1 for p in passes if p["missed_roll"] > 0),
        "over_90deg_from_facing": round(float(np.mean([p["face_angle"] > 90 for p in passes])), 3),
        "opp_within_1m": round(float(np.mean([p["pressure"] < 1.0 for p in passes])), 3),
        "opp_within_1.6m": round(float(np.mean([p["pressure"] < 1.6 for p in passes])), 3),
        "length_median_m": round(pct([p["dist"] for p in passes], 50), 1),
        "hold_before_pass_median": round(pct([p["hold"] for p in passes if p["hold"] is not None], 50), 2),
    },
    "release": {
        "min_release_s": round(min(holds), 3), "under_0.3s": round(float(np.mean(np.array(holds) < 0.3)), 3),
        "shots": len(shots), "shots_within_0.5s_of_pass": len(q_shots),
        "share_quick_shots": round(len(q_shots) / max(1, len(shots)), 3),
        "shots_per_game_min": round(len(shots) / gmin, 2),
    },
    "defence": {
        "nearest_def_body_median_m": round(pct(R["press"], 50), 2),
        "nearest_def_body_p10_p90": [round(pct(R["press"], 10), 2), round(pct(R["press"], 90), 2)],
        "def_stick_in_poke_range": round(float(R["stick_in"].mean()), 3),
        "mark_changes_settled_per_def_min": round(A["mark_settled"] / settled_def_min, 2),
        "mark_changes_after_flip_total": A["mark_after_flip"],
        "mark_changes_settled_total": A["mark_settled"],
        "mark_changes_settled_per_skater_per_game_min": round(A["mark_settled"] / (gmin * 6), 2),
        "mark_changes_after_flip_per_skater_per_game_min": round(A["mark_after_flip"] / (gmin * 6), 2),
        "chaser_changes_per_team_loose_min": round(A["chaser_changes"] / (loose_min["us"] + loose_min["them"]), 2),
        "chaser_back_within_1s": round(A["chaser_back"] / max(1, A["chaser_changes"]), 3),
    },
    "support": {"carrier_time_no_open_mate": round(float(R["open0"].mean()), 3)},
    "person": {
        "role_react_n": len(R["react_lat"]),
        "role_react_within_1_tick": round(float(np.mean(R["react_lat"] <= 0.025)), 3),
        "role_react_median_s": round(pct(R["react_lat"], 50), 3),
        "puck_behind_off_puck": round(float(R["puck_behind"].mean()), 3),
    },
    "carry_speed_p90_over_carry_top": round(pct(R["carry_speed"], 90), 3),
    "goals_per_game_min": None,
}
print(json.dumps(out, indent=1))
