"""The defensive zone for drills: regulation (NHL) geometry, boards with rounded corners, our net.

Zone frame (metres): x across the rink, POSITIVE = the defending team's LEFT (looking up ice);
y up; z from the end boards (z = 0) up ice to the blue line. Placed in the world so that a
chosen zone spot sits under the player and a chosen zone direction is where he faces.
"""

from __future__ import annotations

import numpy as np

import puck as pk
import theme

FT = 0.3048
WIDTH = 85 * FT              # 25.9 m
CORNER_R = 28 * FT           # 8.53 m
GOAL_Z = 11 * FT             # goal line, 3.35 m from the end boards
BLUE_Z = 75 * FT             # blue line, 22.86 m from the end boards
CIRCLE_X, CIRCLE_Z, CIRCLE_R = 22 * FT, GOAL_Z + 20 * FT, 15 * FT   # face-off circles
NET_HALF_W, NET_DEPTH, NET_H = 0.915, 1.12, 1.22
POST_R = 0.03
CREASE_R = 6 * FT
BOARDS_H = 1.07
BOARD_MU = 0.12              # puck on the boards (Coulomb): a rim loses speed around the corners
UP = np.array([0.0, 1.0, 0.0])


class Zone:
    def __init__(self, origin: np.ndarray, z_dir: np.ndarray):
        """origin: the world point of zone (0, 0, 0); z_dir: the world direction of zone +z (up ice)."""
        z = np.array([z_dir[0], 0.0, z_dir[2]], dtype=float)
        self.Z = z / np.linalg.norm(z)
        self.X = np.cross(UP, self.Z)                   # the defending team's left
        self.origin = np.array([origin[0], 0.0, origin[2]], dtype=float)

    @classmethod
    def placed(cls, spot_zone, spot_world, facing_world, facing_zone) -> "Zone":
        """A zone where zone point `spot_zone` (x, z) lies under `spot_world` and zone direction
        `facing_zone` (x, z) points along the world direction `facing_world`."""
        a, b = np.array(facing_zone, dtype=float) / np.linalg.norm(facing_zone)
        wx, wz = np.array([facing_world[0], facing_world[2]], dtype=float) / np.hypot(facing_world[0], facing_world[2])
        # with Z = (cos t, 0, sin t), X = UP x Z = (sin t, 0, -cos t): zone (a, b) lands at
        # (a sin t + b cos t, -a cos t + b sin t); solved for t:
        Z = np.array([b * wx - a * wz, 0.0, a * wx + b * wz])
        frame = cls(np.zeros(3), Z)
        origin = np.asarray(spot_world, dtype=float) - (spot_zone[0] * frame.X + spot_zone[1] * frame.Z)
        return cls(origin, Z)

    def to_zone(self, p) -> np.ndarray:
        p = np.asarray(p, dtype=float)
        d = p - self.origin
        return np.array([d @ self.X, p[1], d @ self.Z])

    def xz(self, p) -> np.ndarray:
        """World point -> zone (x, z)."""
        d = np.asarray(p, dtype=float) - self.origin
        return np.array([d @ self.X, d @ self.Z])

    def to_world(self, x: float, y: float, z: float) -> np.ndarray:
        return self.origin + x * self.X + z * self.Z + np.array([0.0, y, 0.0])

    def world_many(self, xz, y: float = 0.0) -> np.ndarray:
        """Zone (x, z) points (n, 2) -> world points (n, 3) at height y."""
        xz = np.asarray(xz, dtype=float).reshape(-1, 2)
        return self.origin + xz[:, :1] * self.X + xz[:, 1:] * self.Z + np.array([0.0, y, 0.0])

    def dir_to_world(self, dx: float, dz: float) -> np.ndarray:
        return dx * self.X + dz * self.Z

    def dir_to_zone(self, v) -> np.ndarray:
        v = np.asarray(v, dtype=float)
        return np.array([v @ self.X, v @ self.Z])

    def to_dict(self) -> dict:
        return {"origin": self.origin.round(4).tolist(), "z_dir": self.Z.round(5).tolist()}


def end_boards_z(x: float) -> float:
    """Where the boards are at this x, at our end (0 on the straight part, more in a corner)."""
    k = abs(x) - (WIDTH / 2 - CORNER_R)
    return 0.0 if k <= 0 else CORNER_R - float(np.sqrt(max(CORNER_R ** 2 - k * k, 0.0)))


def side_boards_x(z: float) -> float:
    """Half the ice's width at this z (narrower in the corners)."""
    if z >= CORNER_R:
        return WIDTH / 2
    return WIDTH / 2 - CORNER_R + float(np.sqrt(max(CORNER_R ** 2 - (CORNER_R - z) ** 2, 0.0)))


def boards_contact(x: float, z: float, r: float):
    """For a disc of radius r at zone (x, z): (penetration, inward normal (nx, nz)) against the
    boards, or None. The zone is open up ice (beyond the blue line is the neutral zone)."""
    half = WIDTH / 2
    if z < CORNER_R and abs(x) > half - CORNER_R:          # rounded corner
        cx = np.sign(x) * (half - CORNER_R)
        dx, dz = x - cx, z - CORNER_R
        d = float(np.hypot(dx, dz))
        if d > CORNER_R - r:
            return d - (CORNER_R - r), (-dx / d, -dz / d)
        return None
    if z < r:                                              # end boards
        return r - z, (0.0, 1.0)
    if abs(x) > half - r:                                  # side boards
        return abs(x) - (half - r), (-float(np.sign(x)), 0.0)
    return None


def bounce(vx: float, vz: float, nx: float, nz: float, e: float, mu: float) -> tuple[float, float]:
    """Velocity after hitting a wall with inward normal n: restitution e on the normal part,
    Coulomb friction mu (times the normal impulse) on the tangential part."""
    vn = vx * nx + vz * nz
    if vn >= 0:
        return vx, vz
    tx, tz = -nz, nx
    vt = vx * tx + vz * tz
    vt = float(np.sign(vt)) * max(0.0, abs(vt) - mu * (1 + e) * -vn)
    vn = -e * vn
    return vn * nx + vt * tx, vn * nz + vt * tz


class ZonePuck(pk.Puck):
    """A puck in the defensive zone: rounded boards (pucks rim around the corners), our net (an
    own goal from the front, solid from the sides and back), open up ice past the blue line."""

    def __init__(self, params: pk.Params, zone: Zone):
        super().__init__(params, pk.Rink())
        self.zone = zone
        self.cleared = False
        self.nets = 0                                   # pucks into the net (whose goal depends on the drill)

    def spawn(self, pos_xz) -> None:
        super().spawn(pos_xz)
        self.cleared = False

    def place(self, x: float, z: float, vx: float = 0.0, vz: float = 0.0) -> None:
        """Put the puck at zone (x, z) on the ice, sliding at zone velocity (vx, vz)."""
        self.spawn(self.zone.to_world(x, 0.0, z)[[0, 2]])
        self.vel = self.zone.dir_to_world(vx, vz)

    def _rink(self, h: float) -> None:
        zn, pr = self.zone, self.params
        x, y, z = zn.to_zone(self.pos)
        vx, vz = float(self.vel @ zn.X), float(self.vel @ zn.Z)
        hit = boards_contact(x, z, pk.R)
        if hit is not None:
            pen, (nx, nz) = hit
            x, z = x + nx * pen, z + nz * pen
            if -(vx * nx + vz * nz) > 0.5:
                self.events.append(("boards", float(np.hypot(vx, vz))))
            vx, vz = bounce(vx, vz, nx, nz, pr.board_bounce, BOARD_MU)
        x, z, vx, vz = self._net(x, y, z, vx, vz, h)
        self.pos = zn.to_world(x, y, z)
        self.vel = vx * zn.X + vz * zn.Z + np.array([0.0, self.vel[1], 0.0])
        if not self.cleared and z > BLUE_Z:
            self.cleared = True
            self.events.append(("cleared", self.speed))

    def _net(self, x, y, z, vx, vz, h):
        pr, r = self.params, pk.R
        front, back, hw = GOAL_Z, GOAL_Z - NET_DEPTH, NET_HALF_W
        if self.in_net:                                     # the mesh keeps it in
            if abs(x) > hw - r:
                if x * vx > 0:
                    vx = -pr.net_bounce * vx
                x = float(np.sign(x)) * (hw - r)
            if z < back + r:
                z, vz = back + r, (-pr.net_bounce * vz if vz < 0 else vz)
            return x, z, vx, vz
        if y > NET_H or not (abs(x) < hw + POST_R + r and back - r < z < front + r):
            return x, z, vx, vz
        px, pz = x - vx * h, z - vz * h                     # where it came from
        if pz >= front + r - 1e-6:                          # from the front
            if abs(x) < hw - r:                             # through the mouth: in our net
                self.in_net = True
                self.nets += 1
                self.events.append(("net", float(np.hypot(vx, vz))))
            else:                                           # a post
                z, vz = front + r, (-pr.board_bounce * vz if vz < 0 else vz)
        elif abs(px) >= hw + POST_R + r - 1e-6:             # a side of the net
            x = float(np.sign(px)) * (hw + POST_R + r)
            vx = -pr.net_bounce * vx if x * vx < 0 else vx
        else:                                               # the back of the net
            z, vz = back - r, (-pr.net_bounce * vz if vz > 0 else vz)
        return x, z, vx, vz


def outline(n: int = 12) -> list[tuple[float, float]]:
    """The boards from the left blue line, around both corners, to the right blue line (zone x, z)."""
    half = WIDTH / 2
    pts = [(half, BLUE_Z)]
    for a in np.linspace(0, np.pi / 2, n):                           # left corner
        pts.append((half - CORNER_R + CORNER_R * np.cos(a), CORNER_R - CORNER_R * np.sin(a)))
    for a in np.linspace(np.pi / 2, np.pi, n):                       # right corner
        pts.append((-(half - CORNER_R) + CORNER_R * np.cos(a), CORNER_R - CORNER_R * np.sin(a)))
    pts.append((-half, BLUE_Z))
    return pts


RED, BLUE, BOARDS, ICE, MESH = theme.RED, theme.BLUE, (0.6, 0.62, 0.68), theme.GRID, theme.MESH
RED_LINE_Z = 100 * FT          # centre ice (regulation): the drills' ice runs on to here


def markings(zone: Zone, line, near: tuple[float, float] | None = None, grid: bool = False) -> None:
    """Draw the zone: solid ice and boards (theme.py) on to the red line, if line takes triangles
    (line.solid); the boards' edges, goal line, net, crease, circles and blue line as lines; the ice
    grid if grid is on. near: a zone (x, z) spot that gets a finer grid (where the player stands)."""
    half = WIDTH / 2
    W = zone.to_world
    end = RED_LINE_Z + 1.0
    rim = [(half, end)] + outline() + [(-half, end)]                 # the boards, from the red line round
    solid = getattr(line, "solid", None)
    if solid is not None:
        s = theme.Surf(solid, zone.origin, zone.X, zone.Z)
        theme.ice(s, rim)
        theme.boards(s, rim, BOARDS_H, closed=False)
        theme.mothership(s, rim)
        P, gl = theme.PAINT_Y, side_boards_x(GOAL_Z)
        s.band((-gl, GOAL_Z), (gl, GOAL_Z), theme.THIN, P, RED)
        s.band((-half, BLUE_Z + 0.15), (half, BLUE_Z + 0.15), theme.WIDE, P, BLUE)
        s.band((-half, RED_LINE_Z), (half, RED_LINE_Z), theme.WIDE, P, RED)
        s.band((-half, end - 0.3), (half, end - 0.3), 0.08, P, theme.GLOW)    # where the ice ends
        s.disc((0.0, GOAL_Z), CREASE_R, P, theme.CREASE, 0.0, np.pi)
        for sx in (-CIRCLE_X, CIRCLE_X):
            s.arc((sx, CIRCLE_Z), CIRCLE_R, theme.THIN, P, RED)
            s.disc((sx, CIRCLE_Z), 0.3, P, RED)
    theme.board_lines(line, W, rim, BOARDS_H)
    if grid:
        for gx in np.arange(-12, 12.1, 2.0):                         # ice grid, every 2 m
            line(W(gx, 0.001, end_boards_z(gx)), W(gx, 0.001, BLUE_Z), ICE)
        for gz in np.arange(2.0, BLUE_Z, 2.0):
            k = side_boards_x(gz)
            line(W(-k, 0.001, gz), W(k, 0.001, gz), ICE)
    if grid and near is not None:                                    # a finer grid around the player
        nx, nz = near
        for gx in np.arange(np.floor(nx) - 3, np.floor(nx) + 3.01, 0.5):
            z0 = max(end_boards_z(gx), nz - 3)
            if z0 < nz + 3:
                line(W(gx, 0.0015, z0), W(gx, 0.0015, nz + 3), ICE)
        for gz in np.arange(max(np.floor(nz) - 3, 0.5), np.floor(nz) + 3.01, 0.5):
            k = side_boards_x(gz)
            line(W(max(nx - 3, -k), 0.0015, gz), W(min(nx + 3, k), 0.0015, gz), ICE)
    gl = side_boards_x(GOAL_Z)                                       # goal line, blue line, red line
    line(W(-gl, 0.003, GOAL_Z), W(gl, 0.003, GOAL_Z), RED)
    for dz in (0.0, 0.3):
        line(W(-half, 0.003, BLUE_Z + dz), W(half, 0.003, BLUE_Z + dz), BLUE)
    for dz in (-0.15, 0.15):
        line(W(-half, 0.003, RED_LINE_Z + dz), W(half, 0.003, RED_LINE_Z + dz), RED)
    line(W(-half, 0.003, end - 0.3), W(half, 0.003, end - 0.3), theme.GLOW)
    a = np.linspace(0, np.pi, 15)                                    # crease
    cr = [W(CREASE_R * np.cos(t), 0.003, GOAL_Z + CREASE_R * np.sin(t)) for t in a]
    for p0, p1 in zip(cr, cr[1:]):
        line(p0, p1, RED)
    net(zone, line)
    a = np.linspace(0, 2 * np.pi, 33)                                # face-off circles and dots
    for sx in (-CIRCLE_X, CIRCLE_X):
        ring = [W(sx + CIRCLE_R * np.cos(t), 0.003, CIRCLE_Z + CIRCLE_R * np.sin(t)) for t in a]
        for p0, p1 in zip(ring, ring[1:]):
            line(p0, p1, RED)
        dot = [W(sx + 0.3 * np.cos(t), 0.004, CIRCLE_Z + 0.3 * np.sin(t)) for t in a[::4]]
        for p0, p1 in zip(dot, dot[1:]):
            line(p0, p1, RED)


def net(zone: Zone, line) -> None:
    W = zone.to_world
    g, hw, d, h = GOAL_Z, NET_HALF_W, NET_DEPTH, NET_H
    for sx in (-hw, hw):
        line(W(sx, 0, g), W(sx, h, g), RED)
        line(W(sx, h, g), W(sx, h * 0.6, g - d), MESH)
        line(W(sx, 0, g), W(sx, 0, g - d), MESH)
        line(W(sx, 0, g - d), W(sx, h * 0.6, g - d), MESH)
    line(W(-hw, h, g), W(hw, h, g), RED)
    line(W(-hw, 0, g - d), W(hw, 0, g - d), MESH)
    line(W(-hw, h * 0.6, g - d), W(hw, h * 0.6, g - d), MESH)
    for x in np.linspace(-hw, hw, 7)[1:-1]:
        line(W(x, 0, g - d), W(x, h * 0.6, g - d), MESH)
        line(W(x, h, g), W(x, h * 0.6, g - d), MESH)
