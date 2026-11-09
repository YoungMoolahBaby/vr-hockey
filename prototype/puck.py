"""A hockey puck on the ice, hit by a blade, scoring in a net. First physics, for feel-tuning.

World: stage space, metres, y up, ice at y = 0. The puck is a flat disc (no tipping or spin
yet): 76.2 mm wide, 25.4 mm tall, 170 g. The blade is the stick's curved plate, given as its
bottom and top edge points in the world at the start and end of a step; it moves linearly in
between, and each step is cut into substeps so a 30 m/s blade can't pass through the puck.

The ice holds the blade (Jon, 2026-11-07, after the first sandbox session): the blade can't go
below the ice; if the hands go lower, the shaft bends instead (the flex loads, like pressing a
stick into the ice before a slap shot). Only past the flex's limit does the blade go through, and
then any part of it at or below the ice still counts as on the ice for hitting the puck.

Contact: the blade face's 3D normal at the puck's height. An open face (tilted back) lifts the
puck. Impulse with restitution ("pop") and Coulomb friction ("grip": the blade can cup and drag
the puck). The blade is infinitely heavy compared with the puck.
"""

from __future__ import annotations

import math
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
    ice_mu: float = 0.085        # sliding friction on the ice (Jon's pick; the one on-ice measurement found
                                 # 0.07-0.12; 0.02 felt like air hockey). reports/Hockey physics feel.md
    blade_pop: float = 0.30      # restitution off the blade: a frozen puck off a rigid plate is ~0.27. Barely
                                 # matters: the light, damped flex sets the bounce (Flex.damping, "hands")
    puck_mass: float = 0.170     # kg (a regulation puck is 156-170 g; heavier feels heavier)
    blade_grip: float = 0.35     # friction along the blade face (cupping, dragging)
    blade_thickness: float = 0.012
    forgiveness: float = 0.01    # extra reach around the blade for catching the puck (m)
    soft_hands: float = 0.0      # m/s: below this impact speed the bounce fades out (0.5 m/s: none). OFF: rubber
                                 # bounces more at low speed, not less (an assist, and it did nothing measurable)
    ice_bounce: float = 0.20
    board_bounce: float = 0.30   # boards, glass, posts: a frozen puck at 55 mph off a rigid plate e = 0.26
                                 # (0.55 was a warm puck dropped slowly: rebounds came back to the slot)
    net_bounce: float = 0.08
    magnet: float = 0.0          # soft hands, 0-1 (physics_core.cradle): 0 = honest physics (the sandbox, the
                                 # drills); the 3v3 game turns it up
    release: float = 4.0         # m/s: blade or puck faster than this (relative to you) is a shot or pass: no cradle
                                 # (Jon's stickhandling, 3v3 2026-11-09: 99% under 3.2 m/s; shots 10+)
    air_k: float = 0.0043        # 1/m: air drag, dv/dt = -air_k v^2 (1/2 rho Cd A / m, Cd ~0.6 side-on: an
                                 # estimate; no measured puck Cd). Equals the ice's friction at ~14 m/s

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
        k = self.params.air_k
        if on_ice:
            p[1], v[1] = H / 2, 0.0
            s = float(np.hypot(v[0], v[2]))
            dec = (self.params.ice_mu * G + k * s * s) * h  # the ice (Coulomb), and the air
            if s <= dec:
                v[0] = v[2] = 0.0
            else:
                v[[0, 2]] *= 1 - dec / s
        else:
            v[1] -= G * h
            if k > 0:                                       # the air, on a puck in flight
                v *= 1 - min(k * float(np.linalg.norm(v)) * h, 1.0)
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
        reach = R + self.params.blade_thickness / 2 + self.params.forgiveness
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
        m = self.params.puck_mass
        inv = 1.0 / m + (0.0 if np.isinf(blade_mass) else 1.0 / blade_mass)
        e = self.params.blade_pop
        if self.params.soft_hands > 0.5:                  # soft hands: little bounce at stickhandling speeds
            e *= float(np.clip((-vn - 0.5) / (self.params.soft_hands - 0.5), 0.0, 1.0))
        jn = -(1 + e) * vn / inv                         # normal impulse, N s
        vt_vec = vrel - vn * n
        vt_mag = float(np.linalg.norm(vt_vec))
        J = jn * n
        if vt_mag > 1e-9:
            J -= min(vt_mag / inv, self.params.blade_grip * jn) * vt_vec / vt_mag
        self.vel = self.vel + J / m
        if self.pos[1] <= H / 2 + 1e-4 and self.vel[1] < 0:
            self.vel[1] = 0.0                            # the ice holds it up
        blade_dv = np.zeros(3) if np.isinf(blade_mass) else -J / blade_mass
        return Contact(float(jn / m), Q[i], blade_dv)

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
ICE_BEND = 0.12           # m: how far the ice may bow the shaft before the stick slides up through the
                          # hands (Jon: "the top hand slips down"). The bow is drawn but stores NO energy:
                          # when the ice loaded the flex spring, a stick held low fired a resting puck at
                          # 6 m/s once it let go (session 2).
def slide(v0, t, mu: float, k: float):
    """How far a puck sliding at v0 (m/s) goes in t s on ice of friction mu with air drag k (1/m):
    dv/dt = -(mu g + k v^2), to a stop. Arrays broadcast."""
    v0, t = np.asarray(v0, dtype=float), np.asarray(t, dtype=float)
    a = mu * G
    if k <= 0:
        if a <= 0:
            return v0 * t
        tt = np.minimum(t, v0 / a)
        return v0 * tt - 0.5 * a * tt * tt
    if a <= 0:
        return np.log1p(k * v0 * t) / k
    w = math.sqrt(a * k)
    phi0 = np.arctan(v0 * math.sqrt(k / a))
    tt = np.minimum(t, phi0 / w)
    return np.log(np.cos(phi0 - w * tt) / np.cos(phi0)) / k


def slide_stop(v0: float, mu: float, k: float) -> float:
    """Where it stops (m); inf on frictionless ice with no drag."""
    a = mu * G
    if k <= 0:
        return v0 * v0 / (2 * a) if a > 0 else math.inf
    if a <= 0:
        return math.inf
    return math.log1p(k * v0 * v0 / a) / (2 * k)


def speed_after(v0: float, x: float, mu: float, k: float) -> float:
    """Its speed after sliding x m (0 if it stops short)."""
    a = mu * G
    if k <= 0:
        return math.sqrt(max(v0 * v0 - 2 * a * x, 0.0))
    if a <= 0:
        return v0 * math.exp(-k * x)
    return math.sqrt(max((v0 * v0 + a / k) * math.exp(-2 * k * x) - a / k, 0.0))


def launch_speed(v1: float, x: float, mu: float, k: float) -> float:
    """The speed to send it at so it still has v1 after x m."""
    a = mu * G
    if k <= 0:
        return math.sqrt(v1 * v1 + 2 * a * x)
    if a <= 0:
        return v1 * math.exp(k * x)
    return math.sqrt((v1 * v1 + a / k) * math.exp(2 * k * x) - a / k)


def slide_time(v0: float, x: float, mu: float, k: float) -> float:
    """How long it takes to slide x m (inf if it stops short)."""
    a = mu * G
    if x <= 0:
        return 0.0
    if k <= 0:
        if a <= 0:
            return x / v0 if v0 > 0 else math.inf
        d = v0 * v0 - 2 * a * x
        return (v0 - math.sqrt(d)) / a if d >= 0 else math.inf
    if a <= 0:
        return math.expm1(k * x) / (k * v0) if v0 > 0 else math.inf
    phi0 = math.atan(v0 * math.sqrt(k / a))
    c = math.cos(phi0) * math.exp(k * x)
    return (phi0 - math.acos(c)) / math.sqrt(a * k) if c <= 1 else math.inf


ICE_ASSIST = 0.16         # m: a blade this close above the ice rests on it (the "ice assist" setting).
                          # Free skate 2026-11-09: the puck crossed the blade line under a hovering
                          # blade 70% of the time; with 12 cm it would have been 37%, 16 cm 26%, 20 cm 19%
                          # (lifting the blade over the puck takes a hand lift of about the band, though)
ICE_PRESS = 0.002         # m: ... pressed this far in, so it counts as on the ice (a touchdown tick)


def ice_assist(low: float, band: float) -> float:
    """How far to lower the stick whose blade's lowest point is `low` (m above the ice).

    In VR nothing stops your hands at the ice, so you can't feel it: a free blade hovered 2.5 to 30 cm
    over it and a puck slid under it at 70% of its crossings (free skate 2026-11-09). So a blade
    within `band` of the ice rests on it; from band to 2*band it rises back to where your hands
    hold it (continuously: the physics sees no jump), and above that it is where they hold it. A blade
    pressed into the ice is left to ice_rest. 0 for band <= 0 (off)."""
    if band <= 0 or low <= -ICE_PRESS or low >= 2 * band:
        return 0.0
    if low <= band:
        return low + ICE_PRESS
    h = -ICE_PRESS + (low - band) * (2 * band + ICE_PRESS) / band
    return low - h
BLADE_MASS = 0.15         # kg: a light composite blade and lower shaft (Jon: "a rubber heavy puck against
                          # a light flexible composite stick"); the damping keeps it from bouncing back
                          # into the puck


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
    DAMPING = 0.60            # the damping ratio: hands damp a stick. This, not blade_pop, sets how hard a
                              # puck comes back off a still blade (0.6: 0.13-0.17 of its speed; 0.3: 0.27)

    def __init__(self, flex: float, mass: float = BLADE_MASS, damping: float = DAMPING):
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


FAST = True                # Sim.step runs compiled (physics_core.py); False: the Python reference
_NO_EDGE = np.zeros((1, 3))
_NO_VEC = np.zeros(3)
_NO_BODY = np.zeros(5)


class Sim:
    """The stick (rigid from the hands, plus flex at the blade), the puck, the rink, the net."""

    def __init__(self, params: Params, rink: Rink, flex: float):
        self.puck = Puck(params, rink)
        self.flex = Flex(flex)
        self.bend = np.zeros(3)
        self._last = None
        self.on_ice = False
        self.slide = np.zeros(3)                       # the stick slid up its shaft (past the flex's limit)
        self.events: list[tuple[str, float]] = []      # ("ice", touchdown speed m/s), drained by the app

    def _hold_on_ice(self, bot_rigid: np.ndarray, anchor: np.ndarray, shaft: np.ndarray) -> np.ndarray:
        """Keep the blade on top of the ice WITHOUT storing energy: the flex (driven by the hands'
        motion) is left alone; on top of it the shaft bows (energy-free) up to ICE_BEND, and only
        past that does the stick slide up through the hands (self.slide). Returns the total bend."""
        bend = self.flex.bend(anchor)
        low = float((bot_rigid[:, 1] + bend[1]).min())
        self.slide = np.zeros(3)
        if low < 0:
            total, self.slide = ice_rest(bend, low, shaft, ICE_BEND)
            if not self.on_ice:                             # touchdown
                self.events.append(("ice", max(0.0, float(-self.flex.v[1]))))
                self.on_ice = True
            return total
        if low > 0.003:                                     # clearly lifted off
            self.on_ice = False
        return bend

    def step(self, dt: float, rigid_bot: np.ndarray | None, rigid_top: np.ndarray | None,
             anchor: np.ndarray | None = None, shaft: np.ndarray | None = None, substeps: int = 4,
             body=None) -> float:
        """Advance dt with the rigid blade edges at the end of the step (None: no stick).
        anchor: the blade point the flex hangs on (world); shaft: unit shaft direction.
        Returns the biggest puck impulse (m/s) this step.

        With FAST on this runs compiled (physics_core.py, the same maths, without holding Python's
        lock); step_ref is the Python reference it is tested against."""
        if FAST:
            return self._step_fast(dt, rigid_bot, rigid_top, anchor, shaft, substeps, body)
        return self.step_ref(dt, rigid_bot, rigid_top, anchor, shaft, substeps, body)

    def _step_fast(self, dt, rigid_bot, rigid_top, anchor, shaft, substeps, body=None) -> float:
        import physics_core as pc
        p, fl = self.puck, self.flex
        has = rigid_bot is not None
        if has:
            rigid_bot = np.ascontiguousarray(rigid_bot, dtype=float)
            rigid_top = np.ascontiguousarray(rigid_top, dtype=float)
            anchor = rigid_bot.mean(axis=0) if anchor is None else np.asarray(anchor, dtype=float)
            shaft = np.array([0.0, 1.0, 0.0]) if shaft is None else np.asarray(shaft, dtype=float)
            n = len(rigid_bot)
            if self._last is not None and len(self._last[0]) == n:
                lb, lt, la = (np.array(a, dtype=float) for a in self._last)
                has_last = 1
            else:
                lb, lt, la, has_last = np.empty((n, 3)), np.empty((n, 3)), np.empty(3), 0
        else:
            rigid_bot = rigid_top = lb = lt = _NO_EDGE
            anchor = shaft = la = _NO_VEC
            has_last = 0
        ss = np.array([has_last, int(self.on_ice)], dtype=np.int64)
        fx = np.zeros(3) if fl.x is None else np.array(fl.x, dtype=float)
        fv = np.array(fl.v, dtype=float)
        fs = np.array([0 if fl.x is None else 1], dtype=np.int64)
        fk = np.array([fl.k, fl.c, fl.mass, Flex.MAX_BEND])
        bend, slide = np.array(self.bend, dtype=float), np.array(self.slide, dtype=float)
        pos, vel, normal = (np.array(a, dtype=float) for a in (p.pos, p.vel, p._normal))
        zone = getattr(p, "zone", None)
        pf = np.array([int(p.in_net), p.goals, int(getattr(p, "cleared", False)), getattr(p, "nets", 0)],
                      dtype=np.int64)
        pr = p.params
        prm = np.array([pr.ice_mu, pr.blade_pop, pr.puck_mass, pr.blade_grip, pr.blade_thickness,
                        pr.forgiveness, pr.soft_hands, pr.ice_bounce, pr.board_bounce, pr.net_bounce,
                        pr.magnet, pr.release, pr.air_k])
        length = getattr(p, "arena_length", None)          # the whole rink (arena.py)
        if zone is None:
            rk = p.rink
            rkv = np.array([rk.origin[0], rk.origin[2], rk.fwd[0], rk.fwd[2], rk.goal_dist, rk.half_width,
                            rk.back, rk.end])
            kind = 0
        else:
            rkv = np.array([zone.origin[0], zone.origin[2], zone.Z[0], zone.Z[2],
                            0.0 if length is None else length, 0.0, 0.0, 0.0])
            kind = 1 if length is None else 2
        ev, nev = np.zeros((16, 2)), np.zeros(1, dtype=np.int64)
        con, scr = np.zeros(7), np.zeros(2)
        imp = pc.sim_step(dt, substeps, has, rigid_bot, rigid_top, anchor, shaft, lb, lt, la, ss,
                          fx, fv, fs, fk, bend, slide, pos, vel, normal, pf, prm, kind, rkv, ev, nev, con, scr,
                          _NO_BODY if body is None else np.asarray(body, dtype=float))
        p.pos, p.vel, p._normal = pos, vel, normal
        p.in_net, p.goals = (int(pf[0]) if kind == 2 else bool(pf[0])), int(pf[1])
        if zone is not None:
            p.cleared, p.nets = bool(pf[2]), int(pf[3])
        fl.x, fl.v = (fx if fs[0] else None), fv
        self.on_ice = bool(ss[1])
        if has:
            self.bend, self.slide = bend, slide
            self._last = (rigid_bot, rigid_top, anchor)
        else:
            self._last = None
        for k in range(int(nev[0])):
            name = pc.EVENT_NAMES[int(ev[k, 0])]
            (self.events if name == "ice" else p.events).append((name, float(ev[k, 1])))
        self.contact = con if con[6] > 0 else None       # the strongest blade-puck contact this step
        self.scrape = scr                                # the blade on the ice: depth, speed
        return float(imp)

    def step_ref(self, dt: float, rigid_bot: np.ndarray | None, rigid_top: np.ndarray | None,
                 anchor: np.ndarray | None = None, shaft: np.ndarray | None = None, substeps: int = 4,
                 body=None) -> float:
        """The Python reference of step (see step)."""
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
            bot_r = b0 + s * (rigid_bot - b0)
            bend = self._hold_on_ice(bot_r, a_s, shaft) if self.flex.x is not None else np.zeros(3)
            total_bend = bend
            dv_bend = self.flex.v - v_anchor
            bot = bot_r + bend + self.slide
            top = t0 + s * (rigid_top - t0) + bend + self.slide
            p._integrate(h)
            mid = bot.mean(axis=0)
            if np.linalg.norm((mid - p.pos)[[0, 2]]) < 0.4:
                c = p._collide_blade(bot, top, vb_r + dv_bend, vt_r + dv_bend, self.flex.mass)
                if c is not None and c.impulse > 0:
                    biggest = max(biggest, c.impulse)
                    self.flex.v = self.flex.v + c.blade_dv          # the hit bends the blade back
                pr = p.params
                if pr.magnet > 0:                                   # soft hands: the same code, uncompiled
                    import physics_core as pc
                    pc.cradle.py_func(h, p.pos, p.vel, np.asarray(bot, dtype=float), vb_r + dv_bend, pr.magnet,
                                      pr.release, pr.blade_thickness,
                                      _NO_BODY if body is None else np.asarray(body, dtype=float))
            p._rink(h)
        self.bend = total_bend                              # the flex plus the ice's bow, at the step's end
        self._last = (rigid_bot, rigid_top, anchor)
        return biggest


def ice_rest(bend: np.ndarray, low: float, shaft: np.ndarray, max_bend: float = ICE_BEND):
    """Lift a blade whose lowest point is `low` (m, below 0 = in the ice) back onto the ice.

    First bend the shaft further (across it, toward up), up to max_bend in all; whatever is left,
    slide the stick up along its shaft (the hands sliding down it). Returns (bend, slide)."""
    slide = np.zeros(3)
    if low >= 0:
        return bend, slide
    up = np.array([0.0, 1.0, 0.0])
    need = -low
    d = up - (up @ shaft) * shaft
    dn = np.linalg.norm(d)
    if dn > 0.2:
        d /= dn
        bd, bb = float(bend @ d), float(bend @ bend)
        t_max = -bd + np.sqrt(max(bd * bd - (bb - max_bend ** 2), 0.0))   # |bend + d t| = max_bend
        t = min(need / float(d @ up), max(t_max, 0.0))
        bend = bend + d * t
        need -= t * float(d @ up)
    if need > 1e-6 and shaft @ up > 0.2:
        slide = shaft * (need / float(shaft @ up))
    return bend, slide
