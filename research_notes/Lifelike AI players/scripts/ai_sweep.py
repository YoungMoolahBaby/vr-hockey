"""A pass or wrist shot made by the AI blade through the contact model: the blade, behind the puck,
sweeps it along a direction with a speed ramp (no setting of the puck's velocity). What leaves?
Run from prototype/: uv run python <this>"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path(__file__).parent))
import physics_core as pc  # noqa: E402
from ai_blade_kin import PRM, R, H, TH, SUB, edges  # noqa: E402


def sweep(target_ms, accel, aim_deg=0.0, skate=0.0, curl=0.0):
    """Puck at rest on the blade (or moving with a skater at `skate` m/s along +z); the blade sweeps
    it toward aim_deg (from +z) at up to target_ms, ramping at `accel` m/s^2. curl: rad/s the face
    turns during the sweep (rolling the wrists)."""
    dt, h = 0.001, 0.001 / SUB
    d = np.array([math.sin(math.radians(aim_deg)), math.cos(math.radians(aim_deg))])
    pos = np.array([0.0, H / 2, 0.0])
    vel = np.array([0.0, 0.0, skate])
    normal = np.array([-d[0], 0.0, -d[1]])
    pf = np.zeros(4, dtype=np.int64)
    out_dv, ci = np.zeros(3), np.zeros(6)
    n = d.copy()
    b = pos[[0, 2]] - n * (R + TH / 2 - 0.001)
    vb = np.array([0.0, skate])
    t_contact, t, left = 0.0, 0.0, None
    travel0 = pos[[0, 2]].copy()
    vmax_reached = 0.0
    for i in range(600):
        t = i * dt
        sp = min(target_ms, skate + accel * t)
        p, u = pos[[0, 2]], vel[[0, 2]]
        behind = float((p - b) @ n)
        gap_err = behind - (R + TH / 2)
        tt = np.array([-n[1], n[0]])
        v_along = sp + float(np.clip(12 * gap_err, -0.5, 0.8))
        v_t = float(u @ tt) + 40 * float((p - b) @ tt)
        if sp >= target_ms and left is None:
            v_along = sp * 0.6                  # follow-through: the blade slows, the puck goes on
        vbn = v_along * n + v_t * tt
        b_old = b.copy()
        b = b + vbn * dt
        if curl:
            a = curl * dt
            n = np.array([math.cos(a) * n[0] - math.sin(a) * n[1], math.sin(a) * n[0] + math.cos(a) * n[1]])
        touched = False
        for k in range(SUB):
            s = (k + 1) / SUB
            bk = b_old + s * (b - b_old)
            bot, top = edges(bk, n, 0.0)
            v3 = np.tile(np.array([vbn[0], 0.0, vbn[1]]), (bot.shape[0], 1))
            pc.integrate(h, pos, vel, pf, PRM)
            if pc.collide_blade(pos, vel, normal, bot, top, v3, v3, np.inf, PRM, out_dv, ci) >= 0:
                touched = True
        if touched:
            t_contact = t
        vmax_reached = max(vmax_reached, float(np.linalg.norm(vel[[0, 2]])))
        if left is None and float(np.linalg.norm(pos[[0, 2]] - b)) > 0.12:
            left = t
            break
    v = vel[[0, 2]]
    ang = math.degrees(math.atan2(v[0], v[1]))
    return dict(target=target_ms, accel=accel, aim=aim_deg, skate=skate, out_ms=round(float(np.linalg.norm(v)), 2),
                out_deg=round(ang, 1), contact_ms=round(1000 * t_contact, 0),
                ride_m=round(float(np.linalg.norm(pos[[0, 2]] - travel0)), 2), vy=round(float(vel[1]), 2))


if __name__ == "__main__":
    for tgt in (10.0, 14.0, 20.0):
        for acc in (60.0, 120.0, 200.0):
            print(sweep(tgt, acc, aim_deg=20.0))
    print(sweep(14.0, 120.0, aim_deg=20.0, skate=4.0))
    print(sweep(14.0, 120.0, aim_deg=-60.0, skate=4.0))
