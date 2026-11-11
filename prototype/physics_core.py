"""The puck physics, compiled: the same maths as puck.py's Sim.step (with zone.py's ZonePuck),
on plain arrays, built by numba with nogil=True.

Why: the 1 kHz physics thread shares Python's lock (the GIL) with drawing, building reps and
(soon) the audio mixer. The Python physics took ~370 us of every 1000 us tick holding that lock,
and the headset sessions ran at 750-930 samples/s. Compiled, a tick takes a few microseconds and
lets go of the lock while it runs.

puck.py keeps the Python version as the reference; Sim.step uses this when puck.FAST is on, and
tests/test_physics_core.py steps both from identical states and checks they agree.

Event codes in `ev` (code, speed): see EVENT_NAMES.
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit

import puck as pk
import zone as zn

R, H, G = pk.R, pk.H, pk.G
GOAL_HALF_W, GOAL_H, GOAL_DEPTH, POST_R = pk.GOAL_HALF_W, pk.GOAL_H, pk.GOAL_DEPTH, pk.POST_R
ICE_BEND = pk.ICE_BEND
HOLD_JUMP = pk.HOLD_JUMP
Z_WIDTH, Z_CORNER_R, Z_GOAL_Z, Z_BLUE_Z = zn.WIDTH, zn.CORNER_R, zn.GOAL_Z, zn.BLUE_Z
Z_NET_HALF_W, Z_NET_DEPTH, Z_NET_H, Z_POST_R, BOARD_MU = zn.NET_HALF_W, zn.NET_DEPTH, zn.NET_H, zn.POST_R, zn.BOARD_MU

EV_ICE, EV_GOAL, EV_POST, EV_BOARDS, EV_NET, EV_CLEARED, EV_NET2 = 1, 2, 3, 4, 5, 6, 7
EVENT_NAMES = {EV_ICE: "ice", EV_GOAL: "goal", EV_POST: "post", EV_BOARDS: "boards", EV_NET: "net",
               EV_CLEARED: "cleared", EV_NET2: "net2"}
# prm: ice_mu, blade_pop, puck_mass, blade_grip, blade_thickness, forgiveness, soft_hands, ice_bounce,
#      board_bounce, net_bounce, magnet, release, air_k, ease_off
# pf (puck flags): in_net, goals, cleared, nets
# rk: origin x, origin z, direction x, direction z (sandbox: fwd; zone, arena: +z up ice), then
#     sandbox: goal_dist, half_width, back, end; arena: length
# con (the strongest blade contact this step): impulse, approach speed, slide speed, heel(0)-toe(1),
#     x, z, contacts this step
# scr (the blade on the ice): press depth (m, deepest this step), blade speed along the ice (m/s)


@njit(cache=True, inline="always")
def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


@njit(cache=True, inline="always")
def _norm(a):
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


@njit(cache=True, inline="always")
def _speed(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


@njit(cache=True, inline="always")
def _event(ev, nev, code, speed):
    k = nev[0]
    if k < ev.shape[0]:
        ev[k, 0] = code
        ev[k, 1] = speed
        nev[0] = k + 1


@njit(cache=True)
def integrate(h, pos, vel, pf, prm):
    p0, p1, p2 = pos[0], pos[1], pos[2]
    v0, v1, v2 = vel[0], vel[1], vel[2]
    on_ice = p1 <= H / 2 + 1e-4 and v1 <= 1e-6
    k = prm[12]
    if on_ice:
        p1, v1 = H / 2, 0.0
        s = math.sqrt(v0 * v0 + v2 * v2)
        dec = (prm[0] * G + k * s * s) * h        # the ice (Coulomb), and the air
        if s <= dec:
            v0 = 0.0
            v2 = 0.0
        else:
            f = 1 - dec / s
            v0 *= f
            v2 *= f
    else:
        v1 -= G * h
        if k > 0:                                  # the air, on a puck in flight
            f = 1 - min(k * math.sqrt(v0 * v0 + v1 * v1 + v2 * v2) * h, 1.0)
            v0 *= f
            v1 *= f
            v2 *= f
    if pf[0]:
        v0 *= 0.97
        v1 *= 0.97
        v2 *= 0.97
    p0 += v0 * h
    p1 += v1 * h
    p2 += v2 * h
    if p1 < H / 2:
        p1 = H / 2
        v1 = -prm[7] * v1 if v1 < -0.5 else 0.0
    pos[0], pos[1], pos[2] = p0, p1, p2
    vel[0], vel[1], vel[2] = v0, v1, v2


@njit(cache=True)
def collide_blade(pos, vel, normal, bot, top, vb, vt, blade_mass, prm, out_dv, cinfo):
    """The blade (bottom and top edge points, and their velocities) against the puck. Returns the
    puck's change of velocity (m/s), 0 for a touch with no push, -1 for no contact."""
    yc = pos[1]
    n = bot.shape[0]
    lo_min, hi_max = 1e30, -1e30
    for i in range(n):
        b, t = max(bot[i, 1], 0.0), max(top[i, 1], 0.0)
        lo_min = min(lo_min, min(b, t))
        hi_max = max(hi_max, max(b, t))
    if lo_min > yc + H / 2 or hi_max < yc - H / 2:
        return -1.0
    c = np.empty((n, 3))
    vc = np.empty((n, 3))
    for i in range(n):
        dy = top[i, 1] - bot[i, 1]
        s = (yc - bot[i, 1]) / (dy if abs(dy) > 1e-6 else 1e-6)
        s = min(max(s, 0.0), 1.0)
        for k in range(3):
            c[i, k] = bot[i, k] + s * (top[i, k] - bot[i, k])
            vc[i, k] = vb[i, k] + s * (vt[i, k] - vb[i, k])
    px, pz = pos[0], pos[2]
    best_i, best_d, best_t, qx, qz = 0, 1e30, 0.0, 0.0, 0.0
    for i in range(n - 1):
        ax, az = c[i, 0], c[i, 2]
        abx, abz = c[i + 1, 0] - ax, c[i + 1, 2] - az
        t = ((px - ax) * abx + (pz - az) * abz) / max(abx * abx + abz * abz, 1e-12)
        t = min(max(t, 0.0), 1.0)
        x, z = ax + t * abx, az + t * abz
        d = math.sqrt((px - x) ** 2 + (pz - z) ** 2)
        if d < best_d:
            best_i, best_d, best_t, qx, qz = i, d, t, x, z
    reach = R + prm[4] / 2 + prm[5]
    if best_d >= reach:
        return -1.0
    i = best_i
    e = np.empty(3)
    up = np.empty(3)
    for k in range(3):
        e[k] = c[i + 1, k] - c[i, k]
        up[k] = (top[i, k] - bot[i, k]) + (top[i + 1, k] - bot[i + 1, k])
    nrm = np.empty(3)
    nrm[0] = e[1] * up[2] - e[2] * up[1]
    nrm[1] = e[2] * up[0] - e[0] * up[2]
    nrm[2] = e[0] * up[1] - e[1] * up[0]
    nn = _norm(nrm)
    if nn > 1e-9:
        for k in range(3):
            nrm[k] /= nn
    else:
        for k in range(3):
            nrm[k] = normal[k]
    tx, tz = px - qx, pz - qz
    if math.sqrt(tx * tx + tz * tz) > 1e-6:
        if nrm[0] * tx + nrm[2] * tz < 0:
            for k in range(3):
                nrm[k] = -nrm[k]
    elif _dot(nrm, normal) < 0:
        for k in range(3):
            nrm[k] = -nrm[k]
    for k in range(3):
        normal[k] = nrm[k]
    nhn = math.sqrt(nrm[0] * nrm[0] + nrm[2] * nrm[2])        # push the puck out of the blade, sideways
    if nhn > 1e-6:
        pos[0] += nrm[0] / nhn * (reach - best_d)
        pos[2] += nrm[2] / nhn * (reach - best_d)
    t = best_t
    vrel = np.empty(3)
    for k in range(3):
        vrel[k] = vel[k] - (vc[i, k] + t * (vc[i + 1, k] - vc[i, k]))
    vn = _dot(vrel, nrm)
    cinfo[0], cinfo[1], cinfo[2] = 0.0, max(-vn, 0.0), 0.0
    cinfo[3], cinfo[4], cinfo[5] = (i + t) / max(n - 1, 1), qx, qz
    if vn >= 0:
        for k in range(3):
            out_dv[k] = 0.0
        return 0.0
    m = prm[2]
    inv = 1.0 / m + (0.0 if math.isinf(blade_mass) else 1.0 / blade_mass)
    ee = prm[1]
    if prm[6] > 0.5:                                     # soft hands
        ee *= min(max((-vn - 0.5) / (prm[6] - 0.5), 0.0), 1.0)
    jn = -(1 + ee) * vn / inv
    vt_vec = np.empty(3)
    for k in range(3):
        vt_vec[k] = vrel[k] - vn * nrm[k]
    vt_mag = _norm(vt_vec)
    J = np.empty(3)
    for k in range(3):
        J[k] = jn * nrm[k]
    if vt_mag > 1e-9:
        f = min(vt_mag / inv, prm[3] * jn)
        for k in range(3):
            J[k] -= f * vt_vec[k] / vt_mag
    for k in range(3):
        vel[k] += J[k] / m
    if pos[1] <= H / 2 + 1e-4 and vel[1] < 0:
        vel[1] = 0.0
    for k in range(3):
        out_dv[k] = 0.0 if math.isinf(blade_mass) else -J[k] / blade_mass
    cinfo[0], cinfo[2] = jn / m, vt_mag
    return jn / m


@njit(cache=True)
def rink_sandbox(h, pos, vel, pf, prm, rk, ev, nev):
    """puck.Puck._rink: open boards around a rectangle, our net in front with its posts."""
    fx, fz = rk[2], rk[3]
    rx, rz = -fz, fx                                     # right = (-fwd z, 0, fwd x)
    dx, dz = pos[0] - rk[0], pos[2] - rk[1]
    u, y, w = dx * rx + dz * rz, pos[1], dx * fx + dz * fz
    vu, vw = vel[0] * rx + vel[2] * rz, vel[0] * fx + vel[2] * fz
    goal_dist, half_width, back, end = rk[4], rk[5], rk[6], rk[7]
    bb, nb = prm[8], prm[9]
    prev_w = w - vw * h
    bounced = False
    if abs(u) > half_width - R and u * vu > 0:
        vu, bounced = -bb * vu, True
    end_w = goal_dist + GOAL_DEPTH + end
    if (w > end_w - R and vw > 0) or (w < -back + R and vw < 0):
        vw, bounced = -bb * vw, True
    for su in (-GOAL_HALF_W, GOAL_HALF_W):
        du, dw = u - su, w - goal_dist
        dist = math.sqrt(du * du + dw * dw)
        if y < GOAL_H and dist < R + POST_R:
            nu, nw = du / max(dist, 1e-9), dw / max(dist, 1e-9)
            vdot = vu * nu + vw * nw
            if vdot < 0:
                vu -= (1 + bb) * vdot * nu
                vw -= (1 + bb) * vdot * nw
                _event(ev, nev, EV_POST, _speed(vel))
    inside = abs(u) < GOAL_HALF_W and goal_dist <= w <= goal_dist + GOAL_DEPTH and y < GOAL_H
    if inside and not pf[0]:
        if prev_w < goal_dist and abs(u) < GOAL_HALF_W - R and y < GOAL_H - H / 2:
            pf[0] = 1
            pf[1] += 1
            _event(ev, nev, EV_GOAL, _speed(vel))
        elif prev_w < goal_dist:
            vw = -bb * vw
        else:
            if abs(u) > GOAL_HALF_W - 0.1:
                vu = -nb * vu
            else:
                vw = -nb * vw
    if pf[0]:
        if w > goal_dist + GOAL_DEPTH - R and vw > 0:
            vw = -nb * vw
        if abs(u) > GOAL_HALF_W - R and u * vu > 0:
            vu = -nb * vu
        if w < goal_dist + R and vw < 0:
            vw = -nb * vw
    vy = vel[1]
    vel[0] = vu * rx + vw * fx
    vel[1] = vy
    vel[2] = vu * rz + vw * fz
    if bounced:
        _event(ev, nev, EV_BOARDS, _speed(vel))


@njit(cache=True)
def _boards_contact(x, z, r):
    """zone.boards_contact: (hit, penetration, nx, nz)."""
    half = Z_WIDTH / 2
    if z < Z_CORNER_R and abs(x) > half - Z_CORNER_R:
        cx = (1.0 if x > 0 else -1.0) * (half - Z_CORNER_R)
        dx, dz = x - cx, z - Z_CORNER_R
        d = math.sqrt(dx * dx + dz * dz)
        if d > Z_CORNER_R - r:
            return True, d - (Z_CORNER_R - r), -dx / d, -dz / d
        return False, 0.0, 0.0, 0.0
    if z < r:
        return True, r - z, 0.0, 1.0
    if abs(x) > half - r:
        return True, abs(x) - (half - r), -(1.0 if x > 0 else -1.0), 0.0
    return False, 0.0, 0.0, 0.0


@njit(cache=True)
def _bounce(vx, vz, nx, nz, e, mu):
    vn = vx * nx + vz * nz
    if vn >= 0:
        return vx, vz
    tx, tz = -nz, nx
    vt = vx * tx + vz * tz
    sgn = 1.0 if vt > 0 else (-1.0 if vt < 0 else 0.0)
    vt = sgn * max(0.0, abs(vt) - mu * (1 + e) * -vn)
    vn = -e * vn
    return vn * nx + vt * tx, vn * nz + vt * tz


@njit(cache=True)
def _sign(x):
    return 1.0 if x > 0 else (-1.0 if x < 0 else 0.0)


@njit(cache=True)
def _zone_end(h, x, y, z, vx, vz, inside, prm, ev, nev):
    """One end in its zone frame: the rounded boards, then the net (zone.ZonePuck._rink and _net).
    inside: the puck is already in this net. Returns x, z, vx, vz, and whether it just went in."""
    hit, pen, nx, nz = _boards_contact(x, z, R)
    if hit:
        x, z = x + nx * pen, z + nz * pen
        if -(vx * nx + vz * nz) > 0.5:
            _event(ev, nev, EV_BOARDS, math.sqrt(vx * vx + vz * vz))
        vx, vz = _bounce(vx, vz, nx, nz, prm[8], BOARD_MU)
    r = R
    front, back, hw = Z_GOAL_Z, Z_GOAL_Z - Z_NET_DEPTH, Z_NET_HALF_W
    nb, bb = prm[9], prm[8]
    entered = False
    if inside:
        if abs(x) > hw - r:
            if x * vx > 0:
                vx = -nb * vx
            x = _sign(x) * (hw - r)
        if z < back + r:
            z = back + r
            if vz < 0:
                vz = -nb * vz
    elif not (y > Z_NET_H or not (abs(x) < hw + Z_POST_R + r and back - r < z < front + r)):
        px, pz = x - vx * h, z - vz * h
        if pz >= front + r - 1e-6:
            if abs(x) < hw - r:
                entered = True
            else:
                z = front + r
                if vz < 0:
                    vz = -bb * vz
        elif abs(px) >= hw + Z_POST_R + r - 1e-6:
            x = _sign(px) * (hw + Z_POST_R + r)
            if x * vx < 0:
                vx = -nb * vx
        else:
            z = back - r
            if vz > 0:
                vz = -nb * vz
    return x, z, vx, vz, entered


@njit(cache=True)
def rink_zone(h, pos, vel, pf, prm, rk, ev, nev):
    """zone.ZonePuck._rink and _net: rounded boards, our net, open past the blue line."""
    Zx, Zz = rk[2], rk[3]
    Xx, Xz = Zz, -Zx                                     # X = UP x Z
    dx, dz = pos[0] - rk[0], pos[2] - rk[1]
    x, y, z = dx * Xx + dz * Xz, pos[1], dx * Zx + dz * Zz
    vx, vz = vel[0] * Xx + vel[2] * Xz, vel[0] * Zx + vel[2] * Zz
    x, z, vx, vz, entered = _zone_end(h, x, y, z, vx, vz, pf[0] != 0, prm, ev, nev)
    if entered:
        pf[0] = 1
        pf[3] += 1
        _event(ev, nev, EV_NET, math.sqrt(vx * vx + vz * vz))
    pos[0] = rk[0] + x * Xx + z * Zx
    pos[1] = y
    pos[2] = rk[1] + x * Xz + z * Zz
    vy = vel[1]
    vel[0] = vx * Xx + vz * Zx
    vel[1] = vy
    vel[2] = vx * Xz + vz * Zz
    if not pf[2] and z > Z_BLUE_Z:
        pf[2] = 1
        _event(ev, nev, EV_CLEARED, _speed(vel))


@njit(cache=True)
def rink_arena(h, pos, vel, pf, prm, rk, ev, nev):
    """arena.ArenaPuck._rink: the whole rink, each half its end's zone (the far one turned round).
    rk[4]: the length. pf[0]: 0, 1 (in the home net) or 2 (in the far net)."""
    Zx, Zz, L = rk[2], rk[3], rk[4]
    Xx, Xz = Zz, -Zx
    dx, dz = pos[0] - rk[0], pos[2] - rk[1]
    x, y, z = dx * Xx + dz * Xz, pos[1], dx * Zx + dz * Zz
    vx, vz = vel[0] * Xx + vel[2] * Xz, vel[0] * Zx + vel[2] * Zz
    far = z > L / 2
    if far:
        x, z, vx, vz = -x, L - z, -vx, -vz
    x, z, vx, vz, entered = _zone_end(h, x, y, z, vx, vz, pf[0] != 0, prm, ev, nev)
    if entered:
        pf[0] = 2 if far else 1
        pf[3] += 1
        _event(ev, nev, EV_NET2 if far else EV_NET, math.sqrt(vx * vx + vz * vz))
    if far:
        x, z, vx, vz = -x, L - z, -vx, -vz
    pos[0] = rk[0] + x * Xx + z * Zx
    pos[1] = y
    pos[2] = rk[1] + x * Xz + z * Zz
    vy = vel[1]
    vel[0] = vx * Xx + vz * Zx
    vel[1] = vy
    vel[2] = vx * Xz + vz * Zz


@njit(cache=True)
def _rink(kind, h, pos, vel, pf, prm, rk, ev, nev):
    if kind == 0:
        rink_sandbox(h, pos, vel, pf, prm, rk, ev, nev)
    elif kind == 1:
        rink_zone(h, pos, vel, pf, prm, rk, ev, nev)
    else:
        rink_arena(h, pos, vel, pf, prm, rk, ev, nev)


@njit(cache=True)
def flex_step(h, fx, fv, fs, fk, x_rigid, v_rigid, shaft):
    """puck.Flex.step: the blade as a damped mass on a spring across the shaft."""
    if fs[0] == 0 or math.sqrt((fx[0] - x_rigid[0]) ** 2 + (fx[1] - x_rigid[1]) ** 2
                               + (fx[2] - x_rigid[2]) ** 2) > 0.4:
        for k in range(3):
            fx[k] = x_rigid[k]
            fv[k] = v_rigid[k]
        fs[0] = 1
        return
    kk, cc, mass, max_bend = fk[0], fk[1], fk[2], fk[3]
    for k in range(3):
        d = fx[k] - x_rigid[k]
        a = (-kk * d - cc * (fv[k] - v_rigid[k])) / mass
        fv[k] += a * h
        fx[k] += fv[k] * h
    d = np.empty(3)
    for k in range(3):
        d[k] = fx[k] - x_rigid[k]
    ds = _dot(d, shaft)
    for k in range(3):
        d[k] -= ds * shaft[k]
    dn = _norm(d)
    if dn > max_bend:
        for k in range(3):
            d[k] *= max_bend / dn
    for k in range(3):
        fx[k] = x_rigid[k] + d[k]
    rel = np.empty(3)
    for k in range(3):
        rel[k] = fv[k] - v_rigid[k]
    rs = _dot(rel, shaft)
    for k in range(3):
        fv[k] = v_rigid[k] + rel[k] - rs * shaft[k]


@njit(cache=True)
def ice_rest(bend, low, shaft, max_bend, out_bend, out_slide):
    """puck.ice_rest: lift a blade whose lowest point is `low` back onto the ice."""
    for k in range(3):
        out_bend[k] = bend[k]
        out_slide[k] = 0.0
    if low >= 0:
        return
    need = -low
    sy = shaft[1]
    d0, d1, d2 = -sy * shaft[0], 1.0 - sy * shaft[1], -sy * shaft[2]    # up minus its part along the shaft
    dn = math.sqrt(d0 * d0 + d1 * d1 + d2 * d2)
    if dn > 0.2:
        d0, d1, d2 = d0 / dn, d1 / dn, d2 / dn
        bd = bend[0] * d0 + bend[1] * d1 + bend[2] * d2
        bb = bend[0] * bend[0] + bend[1] * bend[1] + bend[2] * bend[2]
        t_max = -bd + math.sqrt(max(bd * bd - (bb - max_bend * max_bend), 0.0))
        t = min(need / d1, max(t_max, 0.0))
        out_bend[0] += d0 * t
        out_bend[1] += d1 * t
        out_bend[2] += d2 * t
        need -= t * d1
    if need > 1e-6 and sy > 0.2:
        for k in range(3):
            out_slide[k] = shaft[k] * (need / sy)


# Soft hands (Params.magnet; off in the sandbox and drills, on in the 3v3). The feel research says
# no possession magnet, at most "a little damping inside the blade's cup, within the same physics
# step". This is that, and it only ever absorbs: a puck on the blade may not run ahead of the blade
# that pushes it (it slows as the blade slows, instead of flying off), and a retreating blade leaves
# it where it is (no pull: it isn't stuck to the stick). Along the blade, a pressed puck rolls off
# the toe or heel a little less easily. All relative to your body (skating and turning don't
# count), and only at handling speeds: a blade or a puck moving faster than Params.release is a
# shot or a pass, and the puck comes off as hit.
CRADLE_GAP = 0.04        # m: the puck this close to touching the blade's bottom edge is in its cup
CRADLE_TAU = 0.005       # s: at full strength a puck leaving the face is caught within a few ms (inside the cup)
CRADLE_TAU_T = 0.04      # s: along the blade, much gentler


@njit(cache=True)
def cradle(h, pos, vel, bot, vb, strength, release, thickness, body):
    """Absorb a puck leaving the blade's face faster than the blade follows it, at handling speeds
    (see above). body: your body's motion (vx, vz, turn rate, pivot x, pivot z). The Python
    reference (puck.Sim.step_ref) runs this same function uncompiled (cradle.py_func)."""
    if strength <= 0.0 or pos[1] > H / 2 + 0.02:
        return
    n = bot.shape[0]
    px, pz = pos[0], pos[2]
    best_d, best_i, best_t, qx, qz = 1e30, 0, 0.0, 0.0, 0.0
    for i in range(n - 1):
        ax, az = bot[i, 0], bot[i, 2]
        abx, abz = bot[i + 1, 0] - ax, bot[i + 1, 2] - az
        t = ((px - ax) * abx + (pz - az) * abz) / max(abx * abx + abz * abz, 1e-12)
        t = min(max(t, 0.0), 1.0)
        x, z = ax + t * abx, az + t * abz
        d = math.sqrt((px - x) ** 2 + (pz - z) ** 2)
        if d < best_d:
            best_d, best_i, best_t, qx, qz = d, i, t, x, z
    contact = R + thickness / 2
    if best_d > contact + CRADLE_GAP or best_d < 1e-9:
        return
    i, t = best_i, best_t
    bx = body[0] + body[2] * (qz - body[4])               # your body's motion where the blade is
    bz = body[1] - body[2] * (qx - body[3])
    ubx = vb[i, 0] + t * (vb[i + 1, 0] - vb[i, 0]) - bx   # the blade, relative to you
    ubz = vb[i, 2] + t * (vb[i + 1, 2] - vb[i, 2]) - bz
    if math.sqrt(ubx * ubx + ubz * ubz) > release:
        return                                            # shooting: let it go as hit
    upx, upz = vel[0] - bx, vel[2] - bz                   # the puck, relative to you
    if math.sqrt(upx * upx + upz * upz) > release:
        return                                            # it was shot or passed (or a pass is arriving)
    nx, nz = (px - qx) / best_d, (pz - qz) / best_d       # from the blade to the puck
    vbn = ubx * nx + ubz * nz
    vpn = upx * nx + upz * nz
    cap = max(vbn, 0.0)                                   # it may leave the face no faster than the blade follows
    if vpn > cap:
        dv = strength * (1.0 - math.exp(-h / CRADLE_TAU)) * (vpn - cap)
        vel[0] -= dv * nx
        vel[2] -= dv * nz
    if vbn >= 0.0:                                        # pressed on the face: less rolling off the end
        tx, tz = -nz, nx
        rt = (upx - ubx) * tx + (upz - ubz) * tz
        kt = strength * (1.0 - math.exp(-h / CRADLE_TAU_T))
        vel[0] -= kt * rt * tx
        vel[2] -= kt * rt * tz


_NO_RVEL = np.zeros((0, 3))


@njit(cache=True)
def ease_off(h, bend, own, sl, v_hold, hold_prev, fx, fv, fk, v_anchor, shaft):
    """Lifting out of a press (Params.ease_off): while the hands rise out of the ice at u (the blade's
    anchor rising, the hold shrinking), once the whole bend left is no more than c u / k (= 2 zeta u /
    omega), hand the bow to the flex as spring bend, with the blade where it is and moving as it moves.
    Its spring then pulls the blade down no harder than its damper drags it up, so it lifts from rest,
    with no step in its speed (reports/Shot release.md, change 2). Not while the stick slides through the
    hands, nor when the hands aren't rising (a hit bending the blade into the ice and springing back),
    and the rest of a press stays energy-free.
    bend: the total bend (flex + bow); own: the flex's own bend; edits fx, fv and the hold."""
    for k in range(3):
        if sl[k] != 0.0:
            return
    # the bow's direction: up, across the shaft (ice_rest's). u: the hands' rise along it
    su = shaft[1]
    d0, d1, d2 = -su * shaft[0], 1.0 - su * shaft[1], -su * shaft[2]
    dn = math.sqrt(d0 * d0 + d1 * d1 + d2 * d2)
    if dn < 0.2:
        return
    d0, d1, d2 = d0 / dn, d1 / dn, d2 / dn
    u = v_anchor[0] * d0 + v_anchor[1] * d1 + v_anchor[2] * d2
    if u <= 0.0 or v_hold[0] * d0 + v_hold[1] * d1 + v_hold[2] * d2 >= 0.0:
        return
    b2 = 0.0
    for k in range(3):
        b2 += bend[k] ** 2
    lim = fk[1] * u / fk[0]
    if b2 > lim * lim:
        return
    for k in range(3):
        fx[k] += bend[k] - own[k]                     # the flex takes the bow: the blade stays put
        fv[k] += v_hold[k]                            # ... and keeps its motion
        own[k] = bend[k]
        v_hold[k] = 0.0
        hold_prev[k] = 0.0


@njit(cache=True, nogil=True)
def sim_step(dt, substeps, has_blade, rigid_bot, rigid_top, anchor, shaft,
             last_bot, last_top, last_anchor, ss,
             fx, fv, fs, fk, bend_out, slide,
             pos, vel, normal, pf, prm, kind, rk, ev, nev, con, scr, body, rvel):
    """puck.Sim.step on arrays. ss: has_last, on_ice. rvel: the rigid blade's velocities, rows
    bottom edge (n), top edge (n), anchor (1), from a short window of samples (Sim.step's rvel), or no
    rows: then each is the last step's position difference. Returns the biggest impulse (m/s)."""
    nev[0] = 0
    for k in range(7):
        con[k] = 0.0
    scr[0], scr[1] = 0.0, 0.0
    h = dt / substeps
    if not has_blade:
        ss[0] = 0
        for _ in range(substeps):
            integrate(h, pos, vel, pf, prm)
            _rink(kind, h, pos, vel, pf, prm, rk, ev, nev)
        return 0.0
    n = rigid_bot.shape[0]
    if ss[0] == 0:
        for i in range(n):
            for k in range(3):
                last_bot[i, k] = rigid_bot[i, k]
                last_top[i, k] = rigid_top[i, k]
        for k in range(3):
            last_anchor[k] = anchor[k]
    # the step's own position differences: a blade the ice holds uses these, as its hold's rate is
    # measured the same way and must cancel the hands' motion exactly; a free blade uses the window's
    va_d = np.empty(3)
    for k in range(3):
        va_d[k] = (anchor[k] - last_anchor[k]) / dt
    vb_d = (rigid_bot - last_bot) / dt
    vt_d = (rigid_top - last_top) / dt
    v_anchor = va_d.copy()
    vb_r = vb_d.copy()
    vt_r = vt_d.copy()
    if rvel.shape[0] == 2 * n + 1:
        vb_r = rvel[:n].copy()
        vt_r = rvel[n:2 * n].copy()
        for k in range(3):
            v_anchor[k] = rvel[2 * n, k]
    sp = 0.0                                             # blade speed along the ice (for the scrape)
    for i in range(n):
        sp += math.sqrt(vb_r[i, 0] ** 2 + vb_r[i, 2] ** 2)
    sp /= n
    biggest = 0.0
    a_s = np.empty(3)
    bot_r = np.empty((n, 3))
    bend = np.zeros(3)
    tot = np.empty(3)
    sl = np.empty(3)
    bot = np.empty((n, 3))
    top = np.empty((n, 3))
    dv_bend = np.empty(3)
    out_dv = np.empty(3)
    cinfo = np.empty(6)
    vbc = np.empty((n, 3))
    vtc = np.empty((n, 3))
    total_bend = np.zeros(3)
    # The ice's hold (its bow plus the slide up the shaft) moves the blade off the hands' path, so the
    # blade's velocity at a contact must include how fast that hold changes: a blade pinned on the ice
    # while the hands lift out of it is not moving up. Without this the hands' lift went into the puck
    # (14-20 m/s launches, free skate 2026-11-09/10). The hold at the last step's end, from its state:
    hold_prev = np.empty(3)
    for k in range(3):
        hold_prev[k] = bend_out[k] - ((fx[k] - last_anchor[k]) if fs[0] else 0.0) + slide[k]
    fresh = ss[0] == 0
    v_hold = np.zeros(3)
    sl_prev = slide.copy()                               # the slide (up the shaft) at the last step's end
    for k_sub in range(substeps):
        s = (k_sub + 1) / substeps
        for k in range(3):
            a_s[k] = last_anchor[k] + s * (anchor[k] - last_anchor[k])
        flex_step(h, fx, fv, fs, fk, a_s, v_anchor, shaft)
        for i in range(n):
            for k in range(3):
                bot_r[i, k] = last_bot[i, k] + s * (rigid_bot[i, k] - last_bot[i, k])
        # hold on the ice (Sim._hold_on_ice)
        for k in range(3):
            bend[k] = fx[k] - a_s[k] if fs[0] else 0.0
            dv_bend[k] = bend[k]                          # (the flex's own bend, for the hold below)
            sl[k] = 0.0
        low = 1e30
        for i in range(n):
            low = min(low, bot_r[i, 1] + bend[1])
        if low < 0:
            ice_rest(bend, low, shaft, ICE_BEND, tot, sl)
            for k in range(3):
                bend[k] = tot[k]
            if ss[1] == 0:
                _event(ev, nev, EV_ICE, max(0.0, -fv[1]))
                ss[1] = 1
            scr[0] = max(scr[0], -low)
        elif low > 0.003:
            ss[1] = 0
        jump = 0.0
        for k in range(3):
            hold = bend[k] - dv_bend[k] + sl[k]
            v_hold[k] = (hold - hold_prev[k]) / h
            jump = max(jump, abs(v_hold[k]))
            hold_prev[k] = hold
        if fresh or jump > HOLD_JUMP:                     # no last step, or the flex was reset: no rate
            for k in range(3):
                v_hold[k] = 0.0
            fresh = False
        else:
            # the slide stands in for hands deeper than a stick can bend: its rate up and down counts
            # (a pinned blade isn't rising), but not its shove along the ice, which no stick makes
            # (it kicked pucks to 100+ mph as a deep press unwound under them)
            v_hold[0] -= (sl[0] - sl_prev[0]) / h
            v_hold[2] -= (sl[2] - sl_prev[2]) / h
        for k in range(3):
            sl_prev[k] = sl[k]
        held = low < 0                                   # the ice holds the blade this substep
        if held and fs[0] and prm[13] > 0:
            ease_off(h, bend, dv_bend, sl, v_hold, hold_prev, fx, fv, fk, va_d, shaft)
        for k in range(3):
            slide[k] = sl[k]
            total_bend[k] = bend[k]
            dv_bend[k] = fv[k] - (va_d[k] if held else v_anchor[k]) + v_hold[k]
        for i in range(n):
            for k in range(3):
                bot[i, k] = bot_r[i, k] + bend[k] + sl[k]
                top[i, k] = last_top[i, k] + s * (rigid_top[i, k] - last_top[i, k]) + bend[k] + sl[k]
        integrate(h, pos, vel, pf, prm)
        mx, mz = 0.0, 0.0
        for i in range(n):
            mx += bot[i, 0]
            mz += bot[i, 2]
        mx, mz = mx / n, mz / n
        if math.sqrt((mx - pos[0]) ** 2 + (mz - pos[2]) ** 2) < 0.4:
            for i in range(n):
                for k in range(3):
                    vbc[i, k] = (vb_d[i, k] if held else vb_r[i, k]) + dv_bend[k]
                    vtc[i, k] = (vt_d[i, k] if held else vt_r[i, k]) + dv_bend[k]
            imp = collide_blade(pos, vel, normal, bot, top, vbc, vtc, fk[2], prm, out_dv, cinfo)
            if imp > 0:
                con[6] += 1
                if imp > biggest:
                    biggest = imp
                    for k in range(6):
                        con[k] = cinfo[k]
                for k in range(3):
                    fv[k] += out_dv[k]
            cradle(h, pos, vel, bot, vbc, prm[10], prm[11], prm[4], body)
        _rink(kind, h, pos, vel, pf, prm, rk, ev, nev)
    for k in range(3):
        bend_out[k] = total_bend[k]
    if scr[0] > 0:
        scr[1] = sp
    for i in range(n):
        for k in range(3):
            last_bot[i, k] = rigid_bot[i, k]
            last_top[i, k] = rigid_top[i, k]
    for k in range(3):
        last_anchor[k] = anchor[k]
    ss[0] = 1
    return biggest


def warm() -> float:
    """Compile (first run) or load the cached kernel before the 1 kHz loop needs it, for every rink
    and soft hands on. Seconds taken. (Its arguments must match sim_step's: tests/test_physics_core.py
    runs it.)"""
    import time
    t = time.perf_counter()
    edge = np.zeros((8, 3))
    for kind in (0, 1, 2):
        for has in (True, False):
            sim_step(0.001, 4, has, edge, edge + 0.07, np.zeros(3), np.array([0.0, 1.0, 0.0]),
                     np.zeros((8, 3)), np.zeros((8, 3)), np.zeros(3), np.zeros(2, dtype=np.int64),
                     np.zeros(3), np.zeros(3), np.zeros(1, dtype=np.int64), np.array([1000.0, 10.0, 0.15, 0.15]),
                     np.zeros(3), np.zeros(3), np.array([0.0, H / 2, 0.5]), np.zeros(3), np.array([1.0, 0, 0]),
                     np.zeros(4, dtype=np.int64),
                     np.array([0.085, 0.3, 0.17, 0.35, 0.012, 0.01, 0.0, 0.2, 0.3, 0.08, 0.7, 4.5, 0.0043, 1.0]),
                     kind, np.array([0.0, 0.0, 0.0, -1.0, 46.0 if kind == 2 else 6.0, 6.0, 3.0, 1.5]),
                     np.zeros((16, 2)), np.zeros(1, dtype=np.int64), np.zeros(7), np.zeros(2), np.zeros(5),
                     np.zeros((17, 3)) if has else _NO_RVEL)
    return time.perf_counter() - t
