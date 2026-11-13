"""Feasibility: can an AI blade carry and stickhandle the puck through the REAL contact model
(puck.Sim.step at 1 kHz, the same kernel as Jon's stick: flex, blade mass, restitution, grip)?
No placing, no magnet: the puck only moves when the blade hits it.

The AI "hands": every tick they see the puck (pos, vel) and move a cupped blade smoothly (speed and
turn limited) to sit just behind the puck on the side it must be pushed from, lifting over the puck
to switch sides. Run from prototype/:  uv run python <this> """
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path.cwd()))
import arena as ar  # noqa: E402
import puck as pk  # noqa: E402
import zone as zn  # noqa: E402

R = pk.R
TH = 0.012
HALF = 0.14                   # m: half the blade's length used
N = 7
TRACE = 0
CLOSE = 0.8                   # m/s: the most the blade closes on the puck (a soft catch, not a hit)


def setup():
    params = pk.Params()
    rink = ar.Arena(zn.Zone(np.array([3.0, 0.0, -1.0]), np.array([0.6, 0.0, -0.8])))
    sim = pk.Sim(params, pk.Rink(), 70)
    sim.puck = ar.ArenaPuck(params, rink)
    return sim, rink


def blade_world(rink, b, n, lift):
    """Bottom and top edge points (world) of a cupped blade whose face centre is at zone b, facing
    zone direction n (toward the puck), bottom lift m above the ice."""
    t = np.array([-n[1], n[0]])
    s = np.linspace(-HALF, HALF, N)
    cup = 0.5 * s ** 2                                # toe and heel curl 1.8 cm toward the puck
    pts = b[None, :] + s[:, None] * t[None, :] + cup[:, None] * n[None, :]
    z = rink.zone
    bot = np.array([z.to_world(p[0], 0.003 + lift, p[1]) for p in pts])
    top = bot + np.array([0.0, 0.07, 0.0])
    return bot, top


def run(speed=4.2, amp=0.2, hz=1.5, seconds=8.0, curve_r=None, seed=0, verbose=False):
    sim, rink = setup()
    rng = np.random.default_rng(seed)
    z = rink.zone
    c0 = np.array([0.0, 8.0])
    heading = np.array([0.0, 1.0])
    car = c0.copy()
    lat = np.array([heading[1], -heading[0]]) * -1    # his left
    fwd_off = 0.55
    target = car + fwd_off * heading
    sim.puck.place(target[0], target[1], *(speed * heading))
    n = heading.copy()                                 # blade face normal (toward the puck)
    b = target - n * (R + TH / 2 + 0.002)
    lift = 0.0
    v_rel_max = 4.0                                    # m/s: the blade relative to the skater (Lawrie: peaks ~3.5)
    turn_max = math.radians(600)                      # rad/s: how fast the face can turn
    dt = 0.001
    errs, gaps, contacts, lost_t, bspeed = [], [], 0, 0.0, []
    ang = 0.0
    lost = False
    t0 = time.perf_counter()
    kernel = 0.0
    for i in range(int(seconds / dt)):
        t = i * dt
        # the skater: straight, or round a circle
        if curve_r:
            ang += speed / curve_r * dt
            heading = np.array([math.sin(ang), math.cos(ang)])
            vel = speed * heading
        else:
            vel = speed * heading
        car = car + vel * dt
        lat = np.array([-heading[1], heading[0]])
        # where he wants the puck: ahead of him, swept side to side
        ph = 2 * math.pi * hz * t
        P = car + fwd_off * heading + amp * math.sin(ph) * lat
        dP = vel + amp * 2 * math.pi * hz * math.cos(ph) * lat
        if curve_r:
            dP = dP + fwd_off * (speed / curve_r) * np.array([math.cos(ang), -math.sin(ang)])
        p = z.xz(sim.puck.pos)
        u = z.dir_to_zone(sim.puck.vel)
        e = P - p
        u_des = dP + 6.0 * e
        dv = u_des - u
        # push side: the blade sits behind the puck along the change of velocity it needs; when the
        # needed push is small it just rides along behind (along the skating direction)
        want_n = dv / np.linalg.norm(dv) if np.linalg.norm(dv) > 0.4 else (u / max(np.linalg.norm(u), 1e-6))
        # turn the face toward want_n, limited; if it must swing past 100 deg, lift over the puck
        # (the blade has two faces: a push the other way is the other face, so n flips and the blade
        # goes over the puck to its other side: forehand to backhand)
        if float(n @ want_n) < -0.2:
            n = -n
        cross = n[0] * want_n[1] - n[1] * want_n[0]
        dot = float(np.clip(n @ want_n, -1, 1))
        a = math.atan2(cross, dot)
        behind = float((p - b) @ n)
        clear = behind > R + TH / 2 + 0.006 or lift > 0.02
        if clear:                                   # the face turns only off the puck
            da = float(np.clip(a, -turn_max * dt, turn_max * dt))
            ca, sa = math.cos(da), math.sin(da)
            n = np.array([ca * n[0] - sa * n[1], sa * n[0] + ca * n[1]])
            behind = float((p - b) @ n)
        if behind < R + TH / 2 - 0.004:            # on the wrong side, or on top: lift over it
            lift = 0.035
        elif behind > R + TH / 2 + 0.005:
            lift = max(0.0, lift - 1.5 * dt)
        gap = 0.0 if lift == 0 and abs(a) < math.radians(30) else (0.015 if lift == 0 else 0.02)
        # the blade: across n it follows the puck and stays centred on it; along n it moves at the
        # speed the puck should have, closing (gently) on it when behind, so it only ever pushes
        tt = np.array([-n[1], n[0]])
        contact = R + TH / 2 + gap
        gap_err = float((p - b) @ n) - contact
        un_des, un = float(u_des @ n), float(u @ n)
        if un < un_des:
            vn = un_des + float(np.clip(12.0 * gap_err, -0.5, CLOSE))
        else:
            vn = min(un_des, un) + float(np.clip(12.0 * gap_err, -0.5, 0.0))
        vt = float(u @ tt) + 40.0 * float((p - b) @ tt)
        v_b = vn * n + vt * tt - vel
        nb = float(np.linalg.norm(v_b))
        if nb > v_rel_max:
            v_b *= v_rel_max / nb
        b = b + (v_b + vel) * dt
        bspeed.append(float(np.linalg.norm(v_b)))
        bot, top = blade_world(rink, b, n, lift)
        k0 = time.perf_counter()
        imp = sim.step(dt, bot, top)
        kernel += time.perf_counter() - k0
        sim.puck.events.clear()
        sim.events.clear()
        if imp > 0:
            contacts += 1
        d_c = float(np.linalg.norm(p - (car + fwd_off * heading)))
        errs.append(float(np.linalg.norm(e)))
        gaps.append(d_c)
        if TRACE and i % TRACE == 0:
            print(i, "imp", round(imp, 3), "p", p.round(3), "u", u.round(2), "b", b.round(3), "n", n.round(2), "lift", round(lift, 3), "behind", round(behind, 3), "want", want_n.round(2), "y", round(float(sim.puck.pos[1]), 4))
        if d_c > 0.8:
            lost = True
            lost_t = t
            break
    wall = time.perf_counter() - t0
    e = np.array(errs)
    return dict(speed=speed, amp=amp, hz=hz, curve_r=curve_r, lost=lost, lost_t=round(lost_t, 2),
                err_p50=round(float(np.median(e)), 3), err_p95=round(float(np.percentile(e, 95)), 3),
                contacts_per_s=round(contacts / (len(e) * dt), 1), blade_rel_p95=round(float(np.percentile(bspeed, 95)), 2),
                us_per_tick_total=round(1e6 * wall / len(e), 1), us_per_tick_kernel=round(1e6 * kernel / len(e), 1))


if __name__ == "__main__":
    import json
    out = []
    for sp in (0.0, 3.0, 4.2, 5.5):
        for amp, hz in ((0.0, 0.0), (0.15, 1.0), (0.2, 1.5), (0.25, 2.0), (0.3, 2.5)):
            r = run(sp, amp, hz, seconds=8.0)
            print(r, flush=True)
            out.append(r)
    for rr in (4.0, 8.0):
        r = run(4.2, 0.2, 1.5, seconds=8.0, curve_r=rr)
        print(r, flush=True)
        out.append(r)
    Path(__file__).with_name("ai_blade_proto.json").write_text(json.dumps(out, indent=1))
