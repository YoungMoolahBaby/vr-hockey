"""Feasibility, take 2: a rigid kinematic AI blade (no flex, infinitely heavy) against the puck with
the sim's own compiled contact and ice functions (physics_core.collide_blade and integrate, 4 substeps
per 1 ms tick, as sim_step). The puck only moves by contact, ice friction and air drag. Open ice (no
boards). The AI hands see the puck every tick. Run from prototype/: uv run python <this>"""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path.cwd()))
import physics_core as pc  # noqa: E402
import puck as pk  # noqa: E402

R, H = pk.R, pk.H
TH = 0.012
HALF = 0.14
NPT = 7
CUP = 0.5
SUB = 4
PRM = np.array([0.085, 0.30, 0.170, 0.35, TH, 0.01, 0.0, 0.20, 0.30, 0.08, 0.0, 4.0, 0.0043, 1.0])


def edges(b, n, lift):
    t = np.array([-n[1], n[0]])
    s = np.linspace(-HALF, HALF, NPT)
    pts = b[None, :] + s[:, None] * t[None, :] + (CUP * s ** 2)[:, None] * n[None, :]
    bot = np.column_stack([pts[:, 0], np.full(NPT, 0.003 + lift), pts[:, 1]])
    top = bot + np.array([0.0, 0.07, 0.0])
    return bot, top


def run(speed=4.2, amp=0.2, hz=1.5, seconds=10.0, curve_r=None, close=0.8, kp=6.0, turn_deg=600.0,
        fwd_off=0.55, trace=0):
    dt, h = 0.001, 0.001 / SUB
    heading = np.array([0.0, 1.0])
    car = np.array([0.0, 0.0])
    P0 = car + fwd_off * heading
    pos = np.array([P0[0], H / 2, P0[1]])
    vel = np.array([0.0, 0.0, speed])
    normal = np.array([0.0, 0.0, -1.0])
    pf = np.zeros(4, dtype=np.int64)
    out_dv, cinfo = np.zeros(3), np.zeros(6)
    n = heading.copy()
    side = 1.0
    b = P0 - n * (R + TH / 2 + 0.002)
    lift = 0.0
    turn = math.radians(turn_deg)
    ang = 0.0
    errs, touches, maxsep, lost_t = [], 0, 0.0, None
    big = 0.0
    t_ctrl = t_phys = 0.0
    vb_prev = np.zeros(2)
    for i in range(int(seconds / dt)):
        t = i * dt
        c0 = time.perf_counter()
        if curve_r:
            ang += speed / curve_r * dt
            heading = np.array([math.sin(ang), math.cos(ang)])
        sv = speed * heading
        car = car + sv * dt
        lat = np.array([-heading[1], heading[0]])
        ph = 2 * math.pi * hz * t
        P = car + fwd_off * heading + amp * math.sin(ph) * lat
        dP = sv + amp * 2 * math.pi * hz * math.cos(ph) * lat
        if curve_r:
            dP = dP + fwd_off * (speed / curve_r) * np.array([math.cos(ang), -math.sin(ang)])
        p, u = pos[[0, 2]], vel[[0, 2]]
        e = P - p
        u_des = dP + kp * e
        dv = u_des - u
        if amp > 0:
            # stickhandling: the blade's faces stay across the sweep (toe forward), the forehand face
            # pushing toward the backhand side and back; tilted forward as much as the puck needs
            # forward speed. side switches with a little hysteresis
            dl = float(dv @ lat)
            if abs(dl) > 0.25:
                side = 1.0 if dl > 0 else -1.0
            elif i == 0:
                side = 1.0
            beta = float(np.clip(0.8 * float(dv @ heading), -0.35, 0.7))
            want = side * lat * math.cos(beta) + heading * math.sin(beta)
        else:
            want = dv / np.linalg.norm(dv) if np.linalg.norm(dv) > 0.4 else (u / max(np.linalg.norm(u), 1e-6) if np.linalg.norm(u) > 0.2 else n)
        if float(n @ want) < -0.2:
            n = -n                                     # the other face: over the puck to its other side
        a = math.atan2(n[0] * want[1] - n[1] * want[0], float(np.clip(n @ want, -1, 1)))
        behind = float((p - b) @ n)
        omega = 0.0
        if behind > R + TH / 2 + 0.012 or lift > 0.02 or (amp > 0 and abs(a) < math.radians(25)):
            da = float(np.clip(a, -turn * dt, turn * dt))
            omega = da / dt
            ca, sa = math.cos(da), math.sin(da)
            n = np.array([ca * n[0] - sa * n[1], sa * n[0] + ca * n[1]])
            behind = float((p - b) @ n)
        if behind < R + TH / 2 - 0.004:
            lift = 0.035
        elif behind > R + TH / 2 + 0.005:
            lift = max(0.0, lift - 1.5 * dt)
        gap = 0.0 if (lift == 0 and abs(a) < math.radians(30)) else (0.015 if lift == 0 else 0.02)
        tt = np.array([-n[1], n[0]])
        contact = R + TH / 2 + gap
        gap_err = behind - contact
        un_des, un = float(u_des @ n), float(u @ n)
        if un < un_des:
            vn = un_des + float(np.clip(12.0 * gap_err, -0.5, close))
        else:
            vn = min(un_des, un) + float(np.clip(12.0 * gap_err, -0.5, 0.0))
        vt = float(u @ tt) + 40.0 * float((p - b) @ tt)
        v_rel = vn * n + vt * tt - sv
        nr = float(np.linalg.norm(v_rel))
        if nr > 4.0:
            v_rel *= 4.0 / nr
        vbl = v_rel + sv
        t_ctrl += time.perf_counter() - c0
        c1 = time.perf_counter()
        b_old, n_old = b.copy(), n.copy()
        b = b + vbl * dt
        # substeps: the blade moves linearly between ticks; its points' velocities include its turn
        for k in range(SUB):
            s = (k + 1) / SUB
            bk = b_old + s * (b - b_old)
            bot, top = edges(bk, n, lift)
            r = bot[:, [0, 2]] - bk[None, :]
            vpt = vbl[None, :] + omega * np.column_stack([-r[:, 1], r[:, 0]])
            vb3 = np.column_stack([vpt[:, 0], np.zeros(NPT), vpt[:, 1]])
            pc.integrate(h, pos, vel, pf, PRM)
            imp = pc.collide_blade(pos, vel, normal, bot, top, vb3, vb3, np.inf, PRM, out_dv, cinfo)
            if imp > 0:
                touches += 1
                big = max(big, imp)
        t_phys += time.perf_counter() - c1
        err = float(np.linalg.norm(e))
        errs.append(err)
        sep = float(np.linalg.norm(p - (car + fwd_off * heading)))
        maxsep = max(maxsep, sep)
        if trace and i % trace == 0:
            print(i, "p", p.round(3), "u", u.round(2), "b", b.round(3), "n", n.round(2), "lift", lift, "behind", round(behind, 3), "y", round(pos[1], 4))
        if sep > 0.8 or pos[1] > 0.2:
            lost_t = t
            break
    e = np.array(errs)
    T = len(e) * dt
    return dict(speed=speed, amp=amp, hz=hz, curve_r=curve_r, held_s=round(T, 2), lost=lost_t is not None,
                err_p50=round(float(np.median(e)), 3), err_p95=round(float(np.percentile(e, 95)), 3),
                touch_substeps_per_s=round(touches / T, 1), biggest_kick=round(big, 2),
                ctrl_us_per_tick=round(1e6 * t_ctrl / len(e), 1), phys_us_per_tick=round(1e6 * t_phys / len(e), 1))


if __name__ == "__main__":
    out = []
    for sp in (0.0, 3.0, 4.2, 5.5):
        for amp, hz in ((0.0, 0.0), (0.1, 1.0), (0.2, 1.5), (0.25, 2.0)):
            r = run(sp, amp, hz)
            print(r, flush=True)
            out.append(r)
    for rr in (4.0, 8.0):
        r = run(4.2, 0.2, 1.5, curve_r=rr)
        print(r, flush=True)
        out.append(r)
    Path(__file__).with_name("ai_blade_kin.json").write_text(json.dumps(out, indent=1))
