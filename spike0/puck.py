"""A hockey puck on the ice, hit by a blade, scoring in a net. First physics, for feel-tuning.

World: stage space, metres, y up, ice at y = 0. The puck is a flat disc (no tipping or spin
yet): 76.2 mm wide, 25.4 mm tall, 170 g. The blade is the stick's curved plate, given as its
bottom and top edge points in the world at the start and end of a step; it moves linearly in
between, and each step is cut into substeps so a 30 m/s blade can't pass through the puck.

Soft floor (Jon, 2026-11-07): the stick may go through the ice; any part of the blade at or
below the ice counts as on the ice for hitting the puck.

Contact: the blade face's 3D normal at the puck's height. An open face (tilted back) lifts the
puck. Impulse with restitution ("pop") and Coulomb friction ("grip": the blade can cup and drag
the puck). The blade is infinitely heavy compared with the puck.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

R = 0.0381          # puck radius
H = 0.0254          # puck height
M = 0.170           # puck mass (kg), for reporting impulses
G = 9.81
GOAL_HALF_W = 0.915  # 6 ft opening
GOAL_H = 1.22        # 4 ft
GOAL_DEPTH = 1.0
POST_R = 0.03


@dataclass
class Params:
    ice_mu: float = 0.02         # sliding friction on the ice (lower = faster ice)
    blade_pop: float = 0.30      # restitution off the blade
    blade_grip: float = 0.35     # friction along the blade face (cupping, dragging)
    blade_thickness: float = 0.012
    ice_bounce: float = 0.25
    board_bounce: float = 0.55
    net_bounce: float = 0.08

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Rink:
    """The playing area, laid out from where the player starts: origin under them, `fwd` toward the net."""
    origin: np.ndarray = field(default_factory=lambda: np.zeros(3))
    fwd: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, -1.0]))
    goal_dist: float = 6.0       # goal line, metres in front of the start
    half_width: float = 6.0      # boards to the sides
    back: float = 3.0            # boards behind the start
    end: float = 1.5             # boards behind the net

    @property
    def right(self) -> np.ndarray:
        return np.array([-self.fwd[2], 0.0, self.fwd[0]])

    def to_rink(self, p: np.ndarray) -> tuple[float, float, float]:
        """World point -> (u right, y up, w forward)."""
        d = p - self.origin
        return float(d @ self.right), float(p[1]), float(d @ self.fwd)

    def to_world(self, u: float, y: float, w: float) -> np.ndarray:
        return self.origin * np.array([1, 0, 1]) + u * self.right + w * self.fwd + np.array([0, y, 0])

    def to_dict(self) -> dict:
        return {"origin": self.origin.tolist(), "fwd": self.fwd.tolist(), "goal_dist": self.goal_dist,
                "half_width": self.half_width, "back": self.back, "end": self.end}


@dataclass
class Contact:
    impulse: float               # m/s change of the puck's velocity
    point: np.ndarray
    blade_dv: np.ndarray = field(default_factory=lambda: np.zeros(3))   # the blade's kick back (finite mass)


class Puck:
    def __init__(self, params: Params, rink: Rink):
        self.params = params
        self.rink = rink
        self.pos = np.array([0.0, H / 2, 0.0])
        self.vel = np.zeros(3)
        self.in_net = False
        self.goals = 0
        self.events: list[tuple[str, float]] = []      # ("goal", speed) etc., drained by the app
        self._normal = np.array([1.0, 0.0, 0.0])

    def spawn(self, pos_xz: np.ndarray) -> None:
        self.pos = np.array([pos_xz[0], H / 2, pos_xz[-1]])
        self.vel = np.zeros(3)
        self.in_net = False

    @property
    def speed(self) -> float:
        return float(np.linalg.norm(self.vel))

    # ------------------------------------------------------------------ one step
    def step(self, dt: float, blade0=None, blade1=None, substeps: int = 4) -> float:
        """Advance dt. blade0/blade1: (bottom (n,3), top (n,3)) edge points at the start and end of
        the step, or None. Returns the largest contact impulse (m/s) in the step (0 if none)."""
        h = dt / substeps
        biggest = 0.0
        near = False
        if blade0 is not None and blade1 is not None:
            mid = blade1[0].mean(axis=0)
            reach = np.linalg.norm((blade1[0][-1] - blade1[0][0])[[0, 2]]) / 2 + 0.25
            near = np.linalg.norm((mid - self.pos)[[0, 2]]) < reach + np.linalg.norm((blade1[0] - blade0[0]).mean(axis=0))
        for k in range(substeps):
            self._integrate(h)
            if near:
                a = (k + 1) / substeps
                bot = blade0[0] + a * (blade1[0] - blade0[0])
                top = blade0[1] + a * (blade1[1] - blade0[1])
                vb = (blade1[0] - blade0[0]) / dt
                vt = (blade1[1] - blade0[1]) / dt
                c = self._collide_blade(bot, top, vb, vt)
                if c is not None:
                    biggest = max(biggest, c.impulse)
            self._rink(h)
        return biggest

    def _integrate(self, h: float) -> None:
        p, v = self.pos.copy(), self.vel.copy()
        on_ice = p[1] <= H / 2 + 1e-4 and v[1] <= 1e-6
        if on_ice:
            p[1], v[1] = H / 2, 0.0
            s = float(np.hypot(v[0], v[2]))
            dec = self.params.ice_mu * G * h
            if s <= dec:
                v[0] = v[2] = 0.0
            else:
                v[[0, 2]] *= 1 - dec / s
        else:
            v[1] -= G * h
        if self.in_net:
            v *= 0.97                                   # the mesh soaks it up
        p += v * h
        if p[1] < H / 2:
            p[1] = H / 2
            v[1] = -self.params.ice_bounce * v[1] if v[1] < -0.5 else 0.0
        self.pos, self.vel = p, v

    def _collide_blade(self, bot, top, vb, vt, blade_mass: float = np.inf) -> Contact | None:
        yc = self.pos[1]
        # soft floor: anything below the ice counts as on the ice
        lo = np.minimum(np.maximum(bot[:, 1], 0.0), np.maximum(top[:, 1], 0.0))
        hi = np.maximum(np.maximum(bot[:, 1], 0.0), np.maximum(top[:, 1], 0.0))
        if lo.min() > yc + H / 2 or hi.max() < yc - H / 2:
            return None
        dy = top[:, 1] - bot[:, 1]
        s = np.clip((yc - bot[:, 1]) / np.where(np.abs(dy) > 1e-6, dy, 1e-6), 0.0, 1.0)
        c = bot + s[:, None] * (top - bot)              # the blade at the puck's height
        vc = vb + s[:, None] * (vt - vb)
        A, B = c[:-1][:, [0, 2]], c[1:][:, [0, 2]]
        P = self.pos[[0, 2]]
        AB = B - A
        t = np.clip(np.sum((P - A) * AB, axis=1) / np.maximum(np.sum(AB * AB, axis=1), 1e-12), 0, 1)
        Q = A + t[:, None] * AB
        d = np.linalg.norm(P - Q, axis=1)
        i = int(np.argmin(d))
        reach = R + self.params.blade_thickness / 2
        if d[i] >= reach:
            return None
        # face normal at that segment, pointing at the puck
        e = c[i + 1] - c[i]
        up = (top[i] - bot[i]) + (top[i + 1] - bot[i + 1])
        n = np.cross(e, up)
        nn = np.linalg.norm(n)
        n = n / nn if nn > 1e-9 else self._normal
        toward = np.array([P[0] - Q[i][0], 0.0, P[1] - Q[i][1]])
        if np.linalg.norm(toward) > 1e-6:
            if n @ toward < 0:
                n = -n
        elif n @ self._normal < 0:
            n = -n
        self._normal = n
        # push the puck out of the blade, sideways
        nh = np.array([n[0], 0.0, n[2]])
        nhn = np.linalg.norm(nh)
        if nhn > 1e-6:
            self.pos = self.pos + nh / nhn * (reach - d[i])
        # impulse: restitution along the normal, friction along the face
        vcon = vc[i] + t[i] * (vc[i + 1] - vc[i])
        vrel = self.vel - vcon
        vn = float(vrel @ n)
        if vn >= 0:
            return Contact(0.0, Q[i])
        inv = 1.0 / M + (0.0 if np.isinf(blade_mass) else 1.0 / blade_mass)
        jn = -(1 + self.params.blade_pop) * vn / inv     # normal impulse, N s
        vt_vec = vrel - vn * n
        vt_mag = float(np.linalg.norm(vt_vec))
        J = jn * n
        if vt_mag > 1e-9:
            J -= min(vt_mag / inv, self.params.blade_grip * jn) * vt_vec / vt_mag
        self.vel = self.vel + J / M
        if self.pos[1] <= H / 2 + 1e-4 and self.vel[1] < 0:
            self.vel[1] = 0.0                            # the ice holds it up
        blade_dv = np.zeros(3) if np.isinf(blade_mass) else -J / blade_mass
        return Contact(float(jn / M), Q[i], blade_dv)

    def _rink(self, h: float) -> None:
        rk, pr = self.rink, self.params
        u, y, w = rk.to_rink(self.pos)
        vu, vw = float(self.vel @ rk.right), float(self.vel @ rk.fwd)
        prev_w = w - vw * h
        bounce = None
        # boards
        if abs(u) > rk.half_width - R and u * vu > 0:
            vu, bounce = -pr.board_bounce * vu, pr.board_bounce
        end_w = rk.goal_dist + GOAL_DEPTH + rk.end
        if (w > end_w - R and vw > 0) or (w < -rk.back + R and vw < 0):
            vw, bounce = -pr.board_bounce * vw, pr.board_bounce
        # posts
        for su in (-GOAL_HALF_W, GOAL_HALF_W):
            du, dw = u - su, w - rk.goal_dist
            dist = np.hypot(du, dw)
            if y < GOAL_H and dist < R + POST_R:
                nu, nw = du / max(dist, 1e-9), dw / max(dist, 1e-9)
                vdot = vu * nu + vw * nw
                if vdot < 0:
                    vu -= (1 + pr.board_bounce) * vdot * nu
                    vw -= (1 + pr.board_bounce) * vdot * nw
                    self.events.append(("post", self.speed))
        # the goal mouth and the net box
        inside = abs(u) < GOAL_HALF_W and rk.goal_dist <= w <= rk.goal_dist + GOAL_DEPTH and y < GOAL_H
        if inside and not self.in_net:
            if prev_w < rk.goal_dist and abs(u) < GOAL_HALF_W - R and y < GOAL_H - H / 2:
                self.in_net = True
                self.goals += 1
                self.events.append(("goal", self.speed))
            elif prev_w < rk.goal_dist:
                vw = -pr.board_bounce * vw                  # crossbar or post edge
            else:                                          # into the net from the side or back
                if abs(u) > GOAL_HALF_W - 0.1:
                    vu = -pr.net_bounce * vu
                else:
                    vw = -pr.net_bounce * vw
        if self.in_net:                                    # keep it in the net
            if w > rk.goal_dist + GOAL_DEPTH - R and vw > 0:
                vw = -pr.net_bounce * vw
            if abs(u) > GOAL_HALF_W - R and u * vu > 0:
                vu = -pr.net_bounce * vu
            if w < rk.goal_dist + R and vw < 0:
                vw = -pr.net_bounce * vw
        vy = float(self.vel[1])
        self.vel = vu * rk.right + vw * rk.fwd + np.array([0.0, vy, 0.0])
        if bounce is not None:
            self.events.append(("boards", self.speed))


# ----------------------------------------------------------------------------- shaft flex

INCH = 0.0254
LBF = 4.448
FLEX_SPAN = 1.17          # m between the supports in a flex test (approximate)
FLEX_LEVER = 0.80         # m from the bottom hand to the blade: the bending cantilever
BLADE_MASS = 0.15         # kg: blade plus lower shaft, the part that whips


def tip_stiffness(flex: float) -> float:
    """N/m at the blade, from a flex rating (lbs to bend the shaft 1 inch in a 3-point test).
    3-point: k3 = 48 EI / span^3, so EI = k3 span^3 / 48; cantilever tip: 3 EI / lever^3."""
    k3 = flex * LBF / INCH
    ei = k3 * FLEX_SPAN ** 3 / 48
    return 3 * ei / FLEX_LEVER ** 3


class Flex:
    """The blade as a mass on a spring off the stick the hands hold (bending across the shaft only).

    The hands move the rigid stick; the blade follows through the spring. Accelerating loads the
    shaft (the blade lags), stopping releases it (the blade whips past), and a puck hit pushes
    the blade back. Deflection is measured at the blade, across the shaft."""

    MAX_BEND = 0.15

    def __init__(self, flex: float, mass: float = BLADE_MASS, damping: float = 0.10):
        self.mass = mass
        self.damping = damping
        self.set_flex(flex)
        self.x = None             # where the blade is (world)
        self.v = np.zeros(3)

    def set_flex(self, flex: float) -> None:
        self.flex = flex
        self.k = tip_stiffness(flex)
        self.c = 2 * self.damping * np.sqrt(self.k * self.mass)

    @property
    def hz(self) -> float:
        return float(np.sqrt(self.k / self.mass) / (2 * np.pi))

    def bend(self, x_rigid: np.ndarray) -> np.ndarray:
        return np.zeros(3) if self.x is None else self.x - x_rigid

    def step(self, h: float, x_rigid: np.ndarray, v_rigid: np.ndarray, shaft: np.ndarray) -> None:
        if self.x is None or np.linalg.norm(self.x - x_rigid) > 0.4:    # first step, or the stick jumped
            self.x, self.v = x_rigid.copy(), v_rigid.copy()
            return
        d = self.x - x_rigid
        a = (-self.k * d - self.c * (self.v - v_rigid)) / self.mass
        self.v = self.v + a * h                          # semi-implicit Euler: stable at these steps
        self.x = self.x + self.v * h
        d = self.x - x_rigid                             # the shaft doesn't stretch: bend across it only
        d -= (d @ shaft) * shaft
        if np.linalg.norm(d) > self.MAX_BEND:
            d *= self.MAX_BEND / np.linalg.norm(d)
        self.x = x_rigid + d
        rel = self.v - v_rigid
        self.v = v_rigid + rel - (rel @ shaft) * shaft


# ----------------------------------------------------------------------------- the whole sim


class Sim:
    """The stick (rigid from the hands, plus flex at the blade), the puck, the rink, the net."""

    def __init__(self, params: Params, rink: Rink, flex: float):
        self.puck = Puck(params, rink)
        self.flex = Flex(flex)
        self.bend = np.zeros(3)
        self._last = None

    def step(self, dt: float, rigid_bot: np.ndarray | None, rigid_top: np.ndarray | None,
             anchor: np.ndarray | None = None, shaft: np.ndarray | None = None, substeps: int = 4) -> float:
        """Advance dt with the rigid blade edges at the end of the step (None: no stick).
        anchor: the blade point the flex hangs on (world); shaft: unit shaft direction.
        Returns the biggest puck impulse (m/s) this step."""
        p = self.puck
        if rigid_bot is None:
            self._last = None
            for _ in range(substeps):
                p._integrate(dt / substeps)
                p._rink(dt / substeps)
            return 0.0
        anchor = rigid_bot.mean(axis=0) if anchor is None else anchor
        shaft = np.array([0.0, 1.0, 0.0]) if shaft is None else shaft
        if self._last is None:
            self._last = (rigid_bot, rigid_top, anchor)
        b0, t0, a0 = self._last
        h = dt / substeps
        v_anchor = (anchor - a0) / dt
        vb_r, vt_r = (rigid_bot - b0) / dt, (rigid_top - t0) / dt
        biggest = 0.0
        for k in range(substeps):
            s = (k + 1) / substeps
            a_s = a0 + s * (anchor - a0)
            self.flex.step(h, a_s, v_anchor, shaft)
            bend = self.flex.bend(a_s)
            dv_bend = self.flex.v - v_anchor
            bot = b0 + s * (rigid_bot - b0) + bend
            top = t0 + s * (rigid_top - t0) + bend
            p._integrate(h)
            mid = bot.mean(axis=0)
            if np.linalg.norm((mid - p.pos)[[0, 2]]) < 0.4:
                c = p._collide_blade(bot, top, vb_r + dv_bend, vt_r + dv_bend, self.flex.mass)
                if c is not None and c.impulse > 0:
                    biggest = max(biggest, c.impulse)
                    self.flex.v = self.flex.v + c.blade_dv          # the hit bends the blade back
            p._rink(h)
        self.bend = self.flex.bend(anchor)
        self._last = (rigid_bot, rigid_top, anchor)
        return biggest
