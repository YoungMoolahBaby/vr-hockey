"""3 on 3 with two goalies: you and two teammates against three, first to five.

Pure logic, no XR: game.py runs it in the headset (you play it with your stick and the
thumbsticks); tests/test_threes.py lets the AI play itself.

Arena frame as in arena.py: z runs from the home end boards. Your team ("us") defends the home net
and attacks the far one; "them" the other way.

The puck is the real puck of the 1 kHz physics. An AI skater with the puck carries it on his stick
(the game puts it there, just in front of his drawn blade and moving with him, 50 times a second).
Any touch of your blade on it knocks it loose: update()'s `touch` is the physics' contact. An AI
pass or shot is the puck sent off at a speed; a goal is the puck in a net.

What the AI does is logged: ai_row() every AI tick (game.py writes it to ai.csv), and takes,
passes, shots, losses and fumbled catches in the outbox's log items. selfplay_metrics.py scores
both against reports/Lifelike AI players.md.

The AI, 50 times a second:
- possession: the puck is carried (by an AI skater, or by you: near your blade and slow), loose,
  or frozen by a goalie. A loose puck at an AI stick is his to catch, by how fast it comes
  (catch_chance: sure to 6 m/s, half at 12, a tenth at 18; less from the side or mid-turn); a miss
  is a bobble, slowed and knocked off line. A defender at the carrier pokes it loose now and then;
  a hard puck into a body is blocked.
- the carrier skates for the slot, away from defenders. Every quarter second or so he shoots (the
  goal chance from goalie.py, against the real goalie), passes (to the most dangerous open
  teammate, you included, if the lane is clear) or keeps going.
- his teammates support: one to the back door, one high (each keeps his spot unless another is a
  20% shorter skate). The other team marks man to man, goal side, and whoever has the carrier
  pressures him: each picks up the nearest man when the puck changes sides, then keeps him; two
  swap only when their men cross.
- a loose puck: each team's quickest skater goes for it (not yours if you're closer), and keeps
  it unless a teammate gets there clearly sooner.
- reactions: when the puck changes hands, each AI skater keeps going where he was going until his
  own reaction time is up (about a quarter second, longer if the puck was off to his side or
  behind him); the new carrier, whoever made the play and the pass's receiver react at once.
- no snap decisions: a role's side of the rink changes past the middle, not at it, and any jump in
  where a skater is going is blended out over about a quarter second (_smooth).
- skating: your skating model (_drive: push, glide, hockey stop, turn limit, as rig.Drive), its
  push building over about 0.15 s; they steer round each other and round you (_avoid).
- pace: top speed 0.95 of your sprint; they cruise at CRUISE of it and go flat out on a read
  (self.burst: a close race for a loose puck, a pass they can't reach cruising, a man past them,
  open ice for the carrier), never within BURST_CLEAR of your head.
- the goalies (goalie.py; the far one in his end's own frame) track and save: a rebound, or he
  covers it and plays it to a teammate a second later.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field

import numpy as np

import arena as ar
import goalie as gl
import puck as pk
import zone as zn

AI_DT = 0.02             # s: the AI's tick
VMAX, ACCEL = 5.8, 5.0   # rec skaters (and never faster than YOU_FRAC of your sprint speed); ACCEL: the old single cap
CRUISE = 0.55            # of their top: their pace when nothing calls for more (the "AI cruising pace" setting; 1: flat out)
BURST_CLEAR = 1.5        # m: nobody bursts within this of your head (plus half a second of his speed: looking ahead)
BURST_GAP = 6.0          # m: a carrier with no defender goal side of him within this goes for the net flat out
BACKCHECK_M = 1.0        # m: a defender whose man is this much nearer our net than he is gets back flat out
RACE_S = 1.0             # s: a loose puck is a race (flat out) if the two teams' chasers are this close in time
LANE_REACT = 0.15        # s: a defender's start on a pass, before his push (lane_odds)
PUSH, GLIDE, STOP, CARVE = 6.0, 1.5, 8.0, 6.0   # m/s^2: your skating limits (sandbox.py's defaults, rig.Drive): theirs too
ARRIVE = 0.7 * STOP      # m/s^2: a skater slows to arrive where he's going at this (a little gentler than a stop)
JERK = 40.0              # m/s^3: his push (or stop) builds this fast: 6 m/s^2 over 0.15 s, never a step
EASE = 0.1               # s: a push eases into the speed he wants over about this (as rig.EASE)
STOP_ANGLE, STOP_DONE = 120.0, 0.3   # deg, m/s: wanting to go this far from where he's going is a hockey stop, down to this
_COS_STOP = math.cos(math.radians(STOP_ANGLE))
SKATE_LIKE_YOU = True    # change 6 (the "AI skating" setting): on your skating model; off, the old single ACCEL cap
YOU_FRAC = 0.95
CARRY = 0.95             # a carrier skates at this much of VMAX (U16 national-team players: 4-5% slower with the puck)
STICK_R = 0.75           # m: how far ahead of him a skater's stick reaches a loose puck (_reach)
BLADE_AT = (0.94, 0.22)  # m: the middle of a skater's blade on the ice, ahead of him and out to his shooting side (figures.py draws it here)
CARRY_AHEAD = pk.R + 0.01  # m: a carried puck sits this far ahead of the blade's middle (on its forehand face)
TOUCH_MS = 0.15          # m/s: your blade touching an AI's puck this hard (a contact you'd hear) knocks it loose
PICKUP_R = 0.6           # m: a loose puck this close to an AI blade is his to catch (catch_chance)
CATCH_MS = (0.0, 6.0, 12.0, 18.0, 24.0)    # m/s, the puck's speed relative to his stick ...
CATCH_P = (1.0, 1.0, 0.5, 0.1, 0.0)        # ... and the chance he catches it clean (in between: a straight line)
CATCH_OFF = 0.6          # ... times this if it comes from more than CATCH_SIDE_DEG off where he faces, or he's mid-turn
CATCH_SIDE_DEG = 60.0
TURNING_DEG_S = 180.0    # deg/s: turning faster than this is mid-turn
BOBBLE_S = 0.1           # s: a miss is a bobble (the puck goes on, slowed and knocked off line): he can try again after this
YOURS_R = 0.6            # m: the puck this close to your blade, and moving with it, is yours
POKE_R = 1.3             # m: a defender's stick reaches the puck from this close
POKE_RATE = 1.4          # pokes per second at point blank, against an AI carrier
POKE_YOU = 0.8           # ... against you
BODY_R = 0.45            # m: a hard puck into a body is blocked
SKATER_GAP = 0.9         # m: skaters don't overlap
SHOT_MS = 22.0           # m/s: an AI shot (about 50 mph)
PASS_MS = 10.0           # m/s: an AI pass
DECIDE_S = 0.25          # s: a carrier reconsiders this often
REACT_S = 0.18           # s: an AI skater reacts to the puck changing hands after this (over level; 0: at once) ...
REACT_TAIL = 0.1         # s: ... plus a random tail of this mean (reaction times are skewed to the right) ...
REACT_SIDE = 0.1         # s: ... plus this with the puck off to his side (50-110 deg from where he faces) ...
REACT_BEHIND = 0.3       # s: ... or this with it behind him
CHASE_KEEP = 0.2         # s: a loose puck's chaser keeps it unless a teammate gets there this much sooner
SWAP_M = 2.0             # m: two defenders swap men only if it saves each of them this much skating
SIDE_FLIP = 1.25         # m: a role's side of the rink changes this far past the middle (x = 0), not at it
SPOT_BETTER = 0.8        # supporters change spots only for one this much shorter a skate (20% better)
SMOOTH_HALF = 0.25       # s: a jump in where a skater is going is blended out over about this (half-life)
JUMP_M = 0.25            # m: a target moving more than this in one AI tick has jumped (12.5 m/s: no skater)
AVOID_S = 0.5            # s: a skater steers round anyone he'd pass close to within this ...
AVOID_M = 1.0            # m: ... closer than this, for another AI skater ...
AVOID_YOU_M = 2.0        # m: ... or this for you (1 m when he's in your view and closing slowly: showing for a pass)
AVOID_YOU_S = 1.0        # s: ... looking this far ahead for you (and he may slow for you, not only step round)
BODY_MIN = 0.6           # m: AI skaters closer than this are pushed apart; you are never pushed, nor is he snapped off you
AVOID_EASE = 0.15        # s: the steering-round request eases in and out over about this (no chatter)
STEADY = True            # changes 4 and 5 (the "steady AI skaters" setting): roles kept, jumps blended, steering round people
SHOOT_RANGE = 16.0       # m
SHOOT_XG = 0.15          # an AI skater shoots at this chance of a goal (or a bit less, in close)
WILD = 2.2               # his aim, in goalie.py's aim errors (a rec shooter)
SMOTHER_RATE = 2.5       # /s: a carrier in alone on the goalie, within his reach, gets smothered
HOLD_S = 1.0             # s: a goalie holds a covered puck this long, then plays it
GOAL_PAUSE = 3.0         # s: after a goal, before the faceoff
FACEOFF_S = 2.0          # s: lined up, then the drop
STUCK_S = 6.0            # s: a dead puck nobody can reach goes back to centre
WATCH_MS = 1.5           # m/s: a goalie plays any puck at his net faster than this (slower ones he covers)
LEAD_MAX = 2.5           # m: a pass leads its receiver at most this far
OTHER = {"us": "them", "them": "us"}


def _n(v) -> float:
    """A vector's length (math.hypot: several times quicker than np.linalg.norm on 2 numbers)."""
    return math.hypot(*v)


def _cap(v, n: float) -> np.ndarray:
    m = _n(v)
    return v * (n / m) if m > n else v


def unit(v) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    n = _n(v)
    return v / n if n > 1e-9 else np.zeros_like(v)


def attack_end(team: str) -> str:
    return "far" if team == "us" else "home"


def defend_end(team: str) -> str:
    return "home" if team == "us" else "far"


def blade_point(pos, facing, shoots: str) -> np.ndarray:
    """The middle of a skater's blade on the ice: BLADE_AT ahead of him and out to his shooting side
    (a left shot carries it on his left; the left of a facing f is (fz, -fx), as in figures.py)."""
    f = unit(facing)
    k = 1.0 if shoots == "L" else -1.0
    return np.asarray(pos, dtype=float) + BLADE_AT[0] * f + (BLADE_AT[1] * k) * np.array([f[1], -f[0]])


def lane_odds(a, b, opps, speed: float, reach: float, vmax: float) -> float:
    """The chance a puck from a to b at `speed` gets past every opponent (at the positions `opps`)
    whose stick reaches `reach` and who skates at up to `vmax`: after LANE_REACT he pushes off
    from standing (your skating model), as time_to."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    p = 1.0
    for o in opps:
        d, s = seg_dist(np.asarray(o, dtype=float), a, b)
        t_puck = s / speed
        t_opp = float(time_to(max(0.0, d - reach), 0.0, vmax)) + LANE_REACT
        p *= float(gl.sig((t_opp - t_puck) / 0.12))
    return p


def time_to(dist, v0, vmax: float, push: float = PUSH, stop: float = STOP) -> np.ndarray:
    """Seconds to skate `dist` m (arrays) going v0 m/s toward it now: a hockey stop first if v0 is
    away from it, then a push up to vmax, then vmax."""
    dist = np.asarray(dist, dtype=float)
    v0 = np.asarray(v0, dtype=float)
    back = np.minimum(v0, 0.0)
    t0 = -back / stop
    dist = dist + back * back / (2 * stop)            # the stop carries him the wrong way first
    v = np.clip(v0, 0.0, vmax)
    d_acc = (vmax * vmax - v * v) / (2 * push)
    short = (np.sqrt(v * v + 2 * push * dist) - v) / push
    long = (vmax - v) / push + (dist - d_acc) / vmax
    return t0 + np.where(dist <= d_acc, short, long)


def catch_chance(rel_ms: float, side_deg: float = 0.0, turn_deg_s: float = 0.0, hands: float = 0.0) -> float:
    """The chance a skater catches a puck coming at rel_ms relative to his stick, from side_deg off
    where he faces, while turning at turn_deg_s (change 8: no flat dice). About sure up to 6 m/s,
    half at 12, a tenth at 18; less from the side or mid-turn; `hands` shifts the curve up."""
    p = float(np.interp(rel_ms - hands, CATCH_MS, CATCH_P))
    if side_deg > CATCH_SIDE_DEG or abs(turn_deg_s) > TURNING_DEG_S:
        p *= 1.0 - (1.0 - CATCH_OFF) * min(max((rel_ms - 2.0) / 4.0, 0.0), 1.0)   # (a slow one he just skates onto)
    return p


def seg_dist(p, a, b) -> tuple[float, float]:
    """(distance from p to segment ab, how far along it the nearest point is, m)."""
    ab = b - a
    L2 = float(ab @ ab)
    s = 0.0 if L2 < 1e-12 else float(np.clip((p - a) @ ab / L2, 0.0, 1.0))
    q = a + s * ab
    return _n(p - q), s * math.sqrt(L2)


@dataclass
class Player:
    id: str
    team: str
    shoots: str
    pos: np.ndarray
    facing: np.ndarray
    vel: np.ndarray = field(default_factory=lambda: np.zeros(2))
    stride: float = 0.0
    acc: np.ndarray = field(default_factory=lambda: np.zeros(2))   # his acceleration (it builds at JERK)
    mode: str = "still"                  # what his skating did last: still, push, coast, stop
    turn: float = 0.0                    # deg/s: how fast he's turning (catch_chance)
    hands: float = 0.0                   # m/s: his catching curve shifted up this much (the elite profile: about 2)
    cool_until: float = 0.0              # can't take the puck before this (just lost it or let it go)
    next_decide: float = 0.0
    blade: np.ndarray | None = None      # you: where your blade really is

    def stick(self) -> np.ndarray:
        return self.blade if self.blade is not None else blade_point(self.pos, self.facing, self.shoots)


class Keeper:
    """A goalie (goalie.Goalie) at one end, playing in that end's own zone frame."""

    def __init__(self, arena: ar.Arena, end: str, team: str):
        self.arena, self.end, self.team = arena, end, team
        self.g = gl.Goalie((0.0, 20.0))
        self.hold_since: float | None = None
        self.saves = 0
        self.calm_until = 0.0            # just played it: no smothering for a moment

    def frame(self, xz) -> np.ndarray:
        """Arena <-> his frame (the same map both ways)."""
        return np.asarray(xz, dtype=float) if self.end == "home" else self.arena.mirror(xz)

    def dir_frame(self, v) -> np.ndarray:
        return np.asarray(v, dtype=float) if self.end == "home" else -np.asarray(v, dtype=float)

    @property
    def pos(self) -> np.ndarray:
        return self.frame(self.g.c)

    @property
    def facing(self) -> np.ndarray:
        return self.dir_frame(self.g.facing)

    def stick(self) -> np.ndarray:
        return self.pos + 0.55 * self.facing

    def reset(self) -> None:
        self.g = gl.Goalie((0.0, 20.0))
        self.hold_since = None


class Goalies:
    """Just the goalies, for free skate: each tracks the puck and saves what he gets a piece of (a
    rebound, or he covers it), covers a slow puck at his feet, and after a cover passes it back
    out to you. update(t, blade, head) every physics tick, as Game; sounds, voice and log items
    collect in `outbox`.

    You can't carry it through him: a puck through his plane in close is checked even on your
    stick (his pads are there), so beat him with a shot or go round him."""

    CLOSE = 2.5              # m: a puck this close to a goalie is checked every tick
    OUTLET_QUIET = 0.5       # s: he doesn't check his own outlet pass

    def __init__(self, arena: ar.Arena, puck: ar.ArenaPuck, rng=None, ends=("home", "far")):
        self.arena, self.puck = arena, puck
        self.rng = rng if rng is not None else np.random.default_rng()
        self.keepers = {e: Keeper(arena, e, "them") for e in ends}
        self.holder: Keeper | None = None
        self.you_pos: np.ndarray | None = None
        self.blade: np.ndarray | None = None
        self.saves = {e: 0 for e in ends}
        self.t = 0.0
        self._last_ai = -1.0
        self._quiet = {e: 0.0 for e in ends}
        self.outbox: list[tuple] = []

    def _puck(self) -> tuple[np.ndarray, np.ndarray]:
        z = self.arena.zone
        return z.xz(self.puck.pos), z.dir_to_zone(self.puck.vel)

    def release(self) -> None:
        """A new puck (on your stick): whoever had the old one hasn't."""
        if self.holder is not None:
            self.holder.hold_since = None
            self.holder.calm_until = self.t + 1.0
        self.holder = None

    def update(self, t: float, blade=None, head=None) -> None:
        self.t = t
        if self.holder is None:                       # every tick: a puck through a goalie
            pxz, pv = self._puck()
            y = float(self.puck.pos[1])
            for k in self.keepers.values():
                q = k.frame(pxz)
                if t >= self._quiet[k.end] and abs(q[0] - k.g.c[0]) + abs(q[1] - k.g.c[1]) < self.CLOSE:
                    self._check(k, pxz, pv, y)
                else:
                    k.g.last_s = None                 # a fresh look when it comes back
        if t - self._last_ai < AI_DT:
            return
        dt = AI_DT if self._last_ai < 0 else min(t - self._last_ai, 0.1)
        self._last_ai = t
        if head is not None:
            self.you_pos = np.asarray(head[0], dtype=float)
        self.blade = None if blade is None else np.asarray(blade, dtype=float)
        pxz, pv = self._puck()
        h = self.holder
        if h is not None:
            if t - h.hold_since >= HOLD_S:
                self._play(h)
            else:
                s = h.stick()
                self.puck.place(s[0], s[1])
        elif float(self.puck.pos[1]) < 0.3 and _n(pv) < 3.0 and not self._yours(pxz):
            for k in self.keepers.values():           # a slow puck at the goalie: he covers it
                if t >= k.calm_until and _n(k.pos - pxz) < 0.9:
                    self._cover(k)
                    break
        pxz, pv = self._puck()
        for k in self.keepers.values():
            if k.hold_since is not None:
                continue
            seen = [] if self.you_pos is None else [k.frame(self.you_pos)]   # you can screen him
            k.g.step(t, dt, k.frame(pxz), k.dir_frame(pv), seen)
            if k.g.mode == "done":
                k.g.mode = "track"

    def _yours(self, pxz) -> bool:
        return self.blade is not None and _n(pxz - self.blade) < YOURS_R

    def _check(self, k: Keeper, pxz, pv, y: float) -> None:
        if k.g.check(k.frame(pxz), y, self.rng) != "save":
            return
        k.g.mode = "track"
        k.saves += 1
        self.saves[k.end] += 1
        speed = _n(pv)
        self.outbox.append(("sound", "thud", 0.8))
        self.outbox.append(("log", "save", {"end": k.end, "speed": round(speed, 1)}))
        self.outbox.append(("say", "Save!", "save"))
        if speed < 12.0 or self.rng.random() < 0.35:
            self._cover(k)
        else:                                         # a rebound off the pads, back out in front
            a = self.rng.uniform(-1.0, 1.0)
            f = k.g.facing
            d = np.array([f[0] * math.cos(a) - f[1] * math.sin(a), f[0] * math.sin(a) + f[1] * math.cos(a)])
            at = k.frame(k.g.c + 0.5 * k.g.facing)
            self.puck.place(*at, *(k.dir_frame(d) * speed * self.rng.uniform(0.12, 0.3)))

    def _cover(self, k: Keeper) -> None:
        self.holder = k
        k.hold_since = self.t
        s = k.stick()
        self.puck.place(s[0], s[1])

    def _play(self, k: Keeper) -> None:
        """He passes it out to you: to your blade, hard enough to get there."""
        k.hold_since = None
        k.calm_until = self.t + 2.0
        self._quiet[k.end] = self.t + self.OUTLET_QUIET
        self.holder = None
        origin = k.stick()
        target = self.blade if self.blade is not None else self.you_pos
        d = (target - origin) if target is not None else k.facing
        dist = _n(d)
        speed = min(14.0, math.sqrt(2 * 0.9 * dist) + 2.5)
        self.puck.place(*origin, *(unit(d) * speed))
        self.outbox.append(("log", "outlet", {"end": k.end, "speed": round(speed, 1)}))


class Game:
    """One game. update(t, blade, head, touch) every physics tick; t in seconds.

    blade: arena (x, z) of your blade's sweet spot, or None (not holding the stick);
    head: (arena (x, z) of your head, arena direction you face), or None;
    touch: your blade's biggest contact with the puck this physics tick (m/s, the physics' impulse).
    Voice, sounds, buzz, log items and teleports collect in `outbox`."""

    def __init__(self, arena: ar.Arena, puck: ar.ArenaPuck, rng=None, to_goals: int = 5, you: bool = True,
                 level: float = 1.0):
        self.arena, self.puck = arena, puck
        self.rng = rng if rng is not None else np.random.default_rng()
        self.to_goals, self.level = to_goals, level
        self.you_ms: float | None = None         # your cruising speed (the skate speed setting) ...
        self.you_sprint: float | None = None     # ... and your sprint (the sprint speed setting): they're never faster
        self.cruise = CRUISE                     # their pace, as a share of their top (the "AI cruising pace" setting)
        self.burst: set[str] = set()             # who is going flat out this tick (a read: _targets)
        self.keep: set[str] = set()              # who keeps pace with a moving target (a man, the carrier)
        self._held_go: dict[str, bool] = {}      # ... as each was when his target was last taken in (_react)
        self._tvel: dict[str, np.ndarray] = {}   # how fast each one's target is moving (_smooth)
        self.react = REACT_S                     # their reaction time (the "AI reaction" setting; 0: at once)
        self.steady = STEADY                     # the "steady AI skaters" setting (off: as before changes 4-5)
        self.skate_like_you = SKATE_LIKE_YOU     # the "AI skating" setting (off: the old single 5 m/s^2 cap)
        ours = ["U1", "U2"] if you else ["U0", "U1", "U2"]
        self.players = [Player(i, "us", "L" if k % 2 == 0 else "R", np.zeros(2), np.array([0.0, 1.0]))
                        for k, i in enumerate(ours)]
        self.players += [Player(i, "them", "L" if k % 2 else "R", np.zeros(2), np.array([0.0, -1.0]))
                         for k, i in enumerate(("T0", "T1", "T2"))]
        self.by_id = {p.id: p for p in self.players}
        self.you = Player("you", "us", "L", np.zeros(2), np.array([0.0, 1.0])) if you else None
        self.keepers = {"home": Keeper(arena, "home", "us"), "far": Keeper(arena, "far", "them")}
        self.score = {"us": 0, "them": 0}
        self.state = "ready"             # ready -> faceoff -> live -> goal -> faceoff ... -> over
        self.state_t = 0.0
        self.holder = None               # an AI Player or a Keeper with the puck
        self.yours = False               # you have it
        self.pass_to: str | None = None  # the receiver of a pass on its way
        self.last_touch: str | None = None   # who touched it last (an id, "you", or a keeper's end)
        self.last_team: str | None = None
        self.marks: dict[str, str] = {}  # defender id -> the attacker he has
        self._watch: str | None = None   # the end whose goalie is facing a shot (checked every tick)
        self._last_ai = -1.0
        self._you_prev = None
        self._dead_since: float | None = None
        self._slow_since: float | None = None
        self._you_had = False
        self._touch = 0.0                # your blade's biggest touch on the puck since the last AI tick (m/s)
        self.targets: dict[str, np.ndarray] = {}     # where each AI skater was steering, last AI tick
        self.chasers: dict[str, str] = {}            # a loose puck: who each team sent for it
        self._actor: str | None = None   # who just made the play (passed, shot, poked): he reacts at once
        self._poss_key = "?"             # who had the puck at the last AI tick, as _react saw it ("?": nobody yet)
        self._react_at: dict[str, float] = {}        # when each AI skater takes in the last change of possession
        self._held: dict[str, np.ndarray] = {}       # ... and the target he keeps till then
        self.raw_targets: dict[str, np.ndarray] = {}  # where each was going before the smoothing (self.targets: after)
        self._roles_reset()
        self._ai_header: str | None = None
        self._top: float | None = None       # this tick's vmax and puck (arena x, z), while the skaters skate
        self._pxz: np.ndarray | None = None
        self.t = 0.0
        self.outbox: list[tuple] = []
        self.stats = {"shots": {"us": 0, "them": 0}, "goals": [], "saves": {"home": 0, "far": 0},
                      "turnovers": 0, "passes_to_you": 0, "your_shots": 0, "blocked": 0}
        self._line_up()

    @property
    def vmax(self) -> float:
        you = None if self.you_ms is None else max(self.you_ms, self.you_sprint or 0.0)
        top = VMAX if you is None else min(VMAX, YOU_FRAC * you)
        return top * (0.85 + 0.15 * self.level)

    # ------------------------------------------------------------------ the tick
    def update(self, t: float, blade=None, head=None, touch: float = 0.0) -> None:
        self.t = t
        self._touch = max(self._touch, touch)
        if self.state == "live":                      # every tick: shots at a goalie, goals
            if self._watch is not None:
                self._check_keeper(self.keepers[self._watch])
            n = self.puck.in_net
            if n and self.state == "live":
                self._goal("us" if n == 2 else "them")
        if t - self._last_ai < AI_DT:
            return
        dt = AI_DT if self._last_ai < 0 else min(t - self._last_ai, 0.1)
        self._last_ai = t
        touch, self._touch = self._touch, 0.0
        self._prev_chasers = self.chasers
        self.targets, self.raw_targets, self.chasers = {}, {}, {}
        self._you_update(blade, head, dt)
        pxz, pv = self._puck()
        if self.state in ("ready", "faceoff"):
            self.puck.place(0.0, self.arena.mid)      # held on the dot
            if self.state == "faceoff" and t - self.state_t >= FACEOFF_S:
                self._drop()
        elif self.state == "goal":
            if t - self.state_t >= GOAL_PAUSE:
                self.faceoff()
        elif self.state == "live":
            self._possession(pxz, pv, dt, touch)
            pxz, pv = self._puck()
            self.raw_targets = self._react(self._targets(pxz, pv), pxz)
            targets = self.targets = self._smooth(self.raw_targets, dt)
            avoid = self._avoid()
            self._top, self._pxz = self.vmax, self._puck()[0]   # this tick's, for every skater
            for p in self.players:
                self._skate(p, targets.get(p.id), dt, avoid.get(p.id))
            self._top = self._pxz = None
            self._separate()
            self._carry()
            pxz, pv = self._puck()
            self._keepers(pxz, pv, dt)
            self._watch = self._shot_watch(pxz, pv)
            self._dead(pxz, pv)

    def _puck(self) -> tuple[np.ndarray, np.ndarray]:
        z = self.arena.zone
        return z.xz(self.puck.pos), z.dir_to_zone(self.puck.vel)

    def _you_update(self, blade, head, dt: float) -> None:
        y = self.you
        if y is None:
            return
        if head is not None:
            pos = np.asarray(head[0], dtype=float)
            if self._you_prev is not None:
                v = (pos - self._you_prev) / dt
                y.vel = y.vel + (v - y.vel) * min(1.0, dt / 0.08) if _n(v) < 15 else y.vel
            self._you_prev = pos
            y.pos = pos
            f = unit(head[1])
            if np.any(f):
                y.facing = f
        y.blade = None if blade is None else np.asarray(blade, dtype=float)

    def skaters(self) -> list[Player]:
        """Everyone on the ice but the goalies: the AI, and you."""
        return self.players + ([self.you] if self.you is not None else [])

    def team(self, team: str) -> list[Player]:
        return [p for p in self.skaters() if p.team == team]

    # ------------------------------------------------------------------ faceoffs, goals
    def _spots(self) -> dict[str, tuple]:
        m = self.arena.mid
        spots = {"you": ((0.0, m - 1.4), (0.0, 1.0)), "U0": ((0.0, m - 1.4), (0.0, 1.0)),
                 "U1": ((-6.0, m - 3.0), (0.0, 1.0)), "U2": ((6.0, m - 3.0), (0.0, 1.0)),
                 "T0": ((0.0, m + 1.4), (0.0, -1.0)), "T1": ((6.0, m + 3.0), (0.0, -1.0)),
                 "T2": ((-6.0, m + 3.0), (0.0, -1.0))}
        return spots

    def _line_up(self) -> None:
        spots = self._spots()
        for p in self.players:
            pos, f = spots[p.id]
            p.pos, p.facing, p.vel, p.acc = np.array(pos), np.array(f), np.zeros(2), np.zeros(2)
            p.cool_until = 0.0
        for k in self.keepers.values():
            k.reset()
        self.holder, self.yours, self.pass_to, self._watch = None, False, None, None
        self._actor, self._poss_key, self._react_at, self._held = None, "?", {}, {}
        self._roles_reset()
        self.puck.place(0.0, self.arena.mid)

    def start(self) -> None:
        """A new game."""
        self.score = {"us": 0, "them": 0}
        self.stats["goals"] = []
        self.faceoff(say="Three on three. First to {}.".format(self.to_goals))

    def faceoff(self, say: str | None = None) -> None:
        self._line_up()
        self.state, self.state_t = "faceoff", self.t
        if self.you is not None:
            pos, f = self._spots()["you"]
            self.outbox.append(("teleport", np.array(pos), np.array(f)))
        self.outbox.append(("say", (say + " " if say else "") + "Faceoff.", "game"))

    def _drop(self) -> None:
        self.state, self.state_t = "live", self.t
        self.puck.place(0.0, self.arena.mid)
        for p in self.players:                        # the centres react to the drop
            p.cool_until = self.t + (self.rng.uniform(0.25, 0.6) if p.id in ("T0", "U0") else 0.0)
        self.outbox.append(("sound", "go", 0.8))
        self.outbox.append(("log", "drop", {"score": dict(self.score)}))

    def _goal(self, team: str) -> None:
        self.score[team] += 1
        who = self.last_touch if self.last_team == team else None
        self.stats["goals"].append({"team": team, "by": who, "t": round(self.t, 2)})
        self.state, self.state_t = "goal", self.t
        self.holder, self.yours, self._watch = None, False, None
        us, them = self.score["us"], self.score["them"]
        if us == them:
            tally = f"Tied {us} all."
        else:
            lead, a, b = ("You lead", us, them) if us > them else ("They lead", them, us)
            tally = f"{lead} {a} to {b}."
        if team == "us":
            head = "You scored!" if who == "you" else ("Goal! Off one of theirs." if who is None else "Goal!")
            self.outbox += [("sound", "go", 1.0), ("buzz", 1.0, 120)]
        else:
            head = "Their goal." if who is not None else "Their goal, off one of ours."
            self.outbox.append(("sound", "whistle", 0.7))
        if max(us, them) >= self.to_goals:
            self.state = "over"
            won = "You win" if us > them else "They win"
            self.outbox.append(("say", f"{head} Game over. {won}, {max(us, them)} to {min(us, them)}. "
                                       "Press A for another.", "game"))
        else:
            self.outbox.append(("say", f"{head} {tally}", "game"))
        self.outbox.append(("log", "goal", {"team": team, "by": who, "score": dict(self.score)}))

    def _dead(self, pxz, pv) -> None:
        """A puck nobody can get to (on top of a net, stuck) goes back to centre: nobody near it for
        STUCK_S, or nobody playing it for twice that, near or not (sticks pinned against a net)."""
        if self.holder is not None or self.yours or _n(pv) > 0.3:
            self._dead_since = self._slow_since = None
            return
        self._slow_since = self._slow_since if self._slow_since is not None else self.t
        if self.t - self._slow_since > 2 * STUCK_S:
            self._dead_since = self._slow_since = None
            self.faceoff(say="Dead puck.")
            return
        near = min(_n(p.stick() - pxz) for p in self.skaters())
        if near < 2.0:
            self._dead_since = None
            return
        self._dead_since = self._dead_since if self._dead_since is not None else self.t
        if self.t - self._dead_since > STUCK_S:
            self._dead_since = None
            self.faceoff(say="Dead puck.")

    # ------------------------------------------------------------------ who has the puck
    def _possession(self, pxz, pv, dt: float, touch: float = 0.0) -> None:
        h, t, rng = self.holder, self.t, self.rng
        y = float(self.puck.pos[1])
        if isinstance(h, Keeper):
            if t - h.hold_since >= HOLD_S:
                self._keeper_plays(h)
            return
        if isinstance(h, Player):
            if touch > TOUCH_MS:                      # your blade touched it: it's loose
                self._lose(h, by="you")
            elif (_n(pxz - self._carry_point(h)) > 0.5
                    or _n(pv - h.vel) > 3.0):     # knocked off his stick (the boards, a net)
                self._lose(h, by=None)
            else:
                k = self.keepers[attack_end(h.team)]          # in alone on the goalie: he smothers it
                if (t >= k.calm_until and _n(self._carry_point(h) - k.pos) < 0.8
                        and rng.random() < SMOTHER_RATE * dt):
                    self._lose(h, by=k.end)
                    self._cover(k)
                    k.saves += 1
                    self.stats["saves"][k.end] += 1
                    return
                for o in self.team(OTHER[h.team]):
                    if o is self.you:
                        continue
                    d = _n(o.stick() - pxz)
                    if d < POKE_R and rng.random() < POKE_RATE * self.level * dt * (1 - d / POKE_R):
                        self._knock(h, o, pxz)
                        return
                y_ = self.you
                if y_ is not None and h.team == "them":   # you skate into him
                    d = _n(y_.pos - h.pos)
                    if d < SKATER_GAP and _n(y_.vel - h.vel) > 3.0:
                        self._knock(h, y_, pxz)
                        self.outbox += [("sound", "thud", 1.0), ("buzz", 0.9, 90)]
                        return
                if t >= h.next_decide:
                    self._decide(h, pxz)
                return
        # nobody has it: is it yours?
        y_ = self.you
        was = self.yours
        self.yours = (y_ is not None and y_.blade is not None and y < 0.3
                      and _n(pxz - y_.blade) < YOURS_R
                      and _n(pv - y_.vel) < 6.0)
        if self.yours:
            if self.last_team != "us":
                self.stats["turnovers"] += 1
            self.last_touch, self.last_team, self.pass_to = "you", "us", None
            for o in self.team("them"):
                d = _n(o.stick() - pxz)
                if d < POKE_R and rng.random() < POKE_YOU * self.level * dt * (1 - d / POKE_R):
                    d = unit(pxz - o.pos)               # clear of your blade, and past soft hands' release
                    v = d * rng.uniform(5.0, 6.5)
                    self.puck.place(*(pxz + 0.12 * d), *v)
                    self.yours = False
                    o.cool_until = t
                    self.outbox.append(("log", "poked", {"from": "you", "by": o.id}))
                    return
            return
        if was:                                       # it just left your stick
            speed = _n(pv)
            kf = self.keepers["far"]
            if speed > 9.0 and self._at_net(kf, pxz, pv):
                self.stats["shots"]["us"] += 1
                self.stats["your_shots"] += 1
        self._loose(pxz, pv, y)

    def _loose(self, pxz, pv, y: float) -> None:
        t, rng = self.t, self.rng
        speed = _n(pv)
        if speed > 10.0 and y < 1.6 and self.last_team is not None:   # a hard one into a body
            for o in self.team(OTHER[self.last_team]):
                if o is self.you:
                    continue
                if _n(o.pos - pxz) < BODY_R:
                    v = unit(rng.normal(size=2)) * speed * rng.uniform(0.1, 0.25)
                    self.puck.place(*(o.pos + unit(pxz - o.pos) * (BODY_R + 0.05)), *v)
                    self.stats["blocked"] += 1
                    self.outbox.append(("sound", "thud", 0.6))
                    self.last_touch, self.last_team = o.id, o.team
                    self._watch = None
                    return
        for k in self.keepers.values():               # a slow puck at the goalie: he covers it
            if y < 0.3 and speed < 3.0 and _n(k.pos - pxz) < 0.9:
                self._cover(k)
                return
        if y > 0.3:
            return
        best, best_d = None, PICKUP_R
        for p in self.players:
            if t < p.cool_until:
                continue
            d = _n(p.stick() - pxz)
            if d < best_d:
                best, best_d = p, d
        if best is None:
            return
        rel_v = pv - best.vel
        rel = _n(rel_v)
        side = math.degrees(math.acos(max(-1.0, min(1.0, float(unit(-rel_v) @ best.facing))))) if rel > 0.3 else 0.0
        if rng.random() < catch_chance(rel, side, best.turn, best.hands):
            self._take(best)
        else:                                         # a bobble: on it goes, slowed and knocked off line
            a = math.radians(rng.uniform(-35.0, 35.0))
            c, s_ = math.cos(a), math.sin(a)
            keep = rng.uniform(0.4, 0.7)
            v = np.array([c * pv[0] - s_ * pv[1], s_ * pv[0] + c * pv[1]]) * keep
            self.puck.place(pxz[0], pxz[1], v[0], v[1])
            best.cool_until = t + BOBBLE_S
            self.outbox.append(("log", "fumble", {"by": best.id, "rel_ms": round(rel, 1)}))

    def _take(self, p: Player) -> None:
        turnover = self.last_team is not None and self.last_team != p.team
        if turnover:
            self.stats["turnovers"] += 1
        self.outbox.append(("log", "take", {"by": p.id, "pass": self.pass_to == p.id, "turnover": turnover}))
        self.holder, self.pass_to, self._watch = p, None, None
        self.last_touch, self.last_team = p.id, p.team
        p.next_decide = self.t + self.rng.uniform(0.15, 0.35)
        self._carry()

    def _lose(self, h: Player, by=None) -> None:
        self.holder = None
        h.cool_until = self.t + 0.6
        self.outbox.append(("log", "lost", {"from": h.id, "by": by}))

    def _knock(self, h: Player, o: Player, pxz) -> None:
        """o knocks the puck off h's stick."""
        v = unit(pxz - o.pos) * self.rng.uniform(2.0, 4.0) + 0.5 * h.vel
        self.puck.place(*pxz, *v)
        self._lose(h, by=o.id)
        o.cool_until = self.t
        self._actor = o.id

    def _carry_point(self, h: Player) -> np.ndarray:
        """Where a carrier's puck sits: on his blade's forehand, but never in the boards or a net."""
        at = h.stick() + CARRY_AHEAD * unit(h.facing)
        return self._off_nets(self.arena.keep_on_ice(at, pk.R + 0.02), pk.R + 0.02)

    def _carry(self) -> None:
        h = self.holder
        if isinstance(h, Player):
            s = self._carry_point(h)
            self.puck.place(s[0], s[1], h.vel[0], h.vel[1])
        elif isinstance(h, Keeper):
            s = h.stick()
            self.puck.place(s[0], s[1])

    # ------------------------------------------------------------------ the goalies
    def _keepers(self, pxz, pv, dt: float) -> None:
        bodies = [p.pos for p in self.skaters()]
        for k in self.keepers.values():
            if k.hold_since is not None:
                continue
            k.g.step(self.t, dt, k.frame(pxz), k.dir_frame(pv), [k.frame(b) for b in bodies])
            if k.g.mode == "done":
                k.g.mode = "track"

    def _at_net(self, k: Keeper, pxz, pv) -> bool:
        """A puck moving toward k's net on a line that ends near it."""
        p, v = k.frame(pxz), k.dir_frame(pv)
        if v[1] >= -1e-6 or p[1] < zn.GOAL_Z or p[1] > 30.0:
            return False
        x_at = p[0] + v[0] * (zn.GOAL_Z - p[1]) / v[1]
        return abs(x_at) < zn.NET_HALF_W + 2.0

    def _shot_watch(self, pxz, pv) -> str | None:
        if self.holder is not None or self.yours or _n(pv) < WATCH_MS:
            return None
        for end, k in self.keepers.items():
            if self._at_net(k, pxz, pv):
                if self._watch != end:
                    k.g.last_s = None                 # a fresh look at this puck's crossing
                return end
        return None

    def _check_keeper(self, k: Keeper) -> None:
        pxz, pv = self._puck()
        if k.g.check(k.frame(pxz), float(self.puck.pos[1]), self.rng) != "save":
            return
        k.g.mode = "track"
        k.saves += 1
        self.stats["saves"][k.end] += 1
        self._watch = None
        speed = _n(pv)
        self.last_touch, self.last_team = k.end, k.team
        self.outbox.append(("sound", "thud", 0.8))
        self.outbox.append(("log", "save", {"end": k.end, "speed": round(speed, 1)}))
        if speed < 12.0 or self.rng.random() < 0.35:
            self._cover(k)
        else:                                         # a rebound off the pads, back out in front
            a = self.rng.uniform(-1.0, 1.0)
            f = k.g.facing
            d = np.array([f[0] * math.cos(a) - f[1] * math.sin(a), f[0] * math.sin(a) + f[1] * math.cos(a)])
            at = k.frame(k.g.c + 0.5 * k.g.facing)
            self.puck.place(*at, *(k.dir_frame(d) * speed * self.rng.uniform(0.12, 0.3)))

    def _cover(self, k: Keeper) -> None:
        self.holder, self.yours, self.pass_to, self._watch = k, False, None, None
        k.hold_since = self.t
        self.last_touch, self.last_team = k.end, k.team
        self._carry()

    def _keeper_plays(self, k: Keeper) -> None:
        """He plays it to the teammate with the most room and a clear lane: a clean outlet (the
        forecheckers give him a moment)."""
        opps = self.team(OTHER[k.team])
        origin = k.stick()

        def value(m):
            room = min((_n(o.pos - m.pos) for o in opps), default=9.0)
            return self._lane(origin, m.stick(), opps, PASS_MS, 0.6) * min(room, 6.0) - 0.05 * _n(m.pos - k.pos)
        m = max(self.team(k.team), key=value)
        k.hold_since = None
        k.calm_until = self.t + 2.0
        self.holder = None
        for o in opps:
            if o is not self.you:
                o.cool_until = max(o.cool_until, self.t + 0.6)
        self._pass(origin, m, k.team, k.end)

    # ------------------------------------------------------------------ the carrier's choices
    def _decide(self, h: Player, pxz) -> None:
        t, rng = self.t, self.rng
        end = attack_end(h.team)
        k = self.keepers[end]
        net = self.arena.net(end)
        origin = self._carry_point(h)
        opps = self.team(OTHER[h.team])
        dist = _n(net - origin)
        o_f = k.frame(origin)
        xg, aim = 0.0, None
        if dist < SHOOT_RANGE and o_f[1] > zn.GOAL_Z + 0.8 and abs(o_f[0]) < 0.9 * (o_f[1] - zn.GOAL_Z) + 3.0:
            sees = not gl.blocks_sight(k.g.c, o_f, [k.frame(p.pos) for p in self.skaters() if p is not h])
            xg, aim = gl.shot_xg(o_f, SHOT_MS, k.g.c, sees)
            xg *= self._lane(origin, net, opps, SHOT_MS, BODY_R + 0.2)
        pressure = min((_n(o.pos - h.pos) for o in opps), default=9.0)
        best = None
        for m in self.team(h.team):
            if m is h:
                continue
            q = m.stick()
            lead = q + _cap(m.vel * (_n(q - origin) / PASS_MS), LEAD_MAX)
            ok = self._lane(origin, lead, opps, PASS_MS, 1.0) * math.exp(-_n(lead - origin) / 40)
            v = ok * self._threat(lead, end, opps) * (1.3 if m is self.you else 1.0)
            if best is None or v > best[0]:
                best = (v, ok, m)
        own = self._threat(origin, end, opps)
        if xg > SHOOT_XG or (dist < 7.0 and xg > 0.6 * SHOOT_XG):
            return self._shoot(h, k, o_f, aim)
        if best is not None:
            v, ok, m = best
            if (v > max(own * 1.2, xg) + 0.02 and ok > 0.55) or (pressure < 1.6 and ok > 0.5 and rng.random() < 0.5):
                self.holder = None
                h.cool_until = t + 0.4
                return self._pass(origin, m, h.team, h.id)
        h.next_decide = t + DECIDE_S * rng.uniform(0.8, 1.3)

    def _threat(self, q, end: str, opps) -> float:
        """How dangerous a puck at q is (about an xG): close, central, and with room."""
        k = self.keepers[end]
        f = k.frame(q)
        d = _n(f - gl.NET_C)
        if f[1] < zn.GOAL_Z + 0.5:
            return 0.01
        cosang = (f[1] - zn.GOAL_Z) / max(d, 1e-6)
        room = min(1.0, min((_n(o.pos - q) for o in opps), default=9.0) / 3.5)
        return 0.35 * max(0.0, 1 - d / 20.0) * cosang ** 0.7 * (0.3 + 0.7 * room)

    def _lane(self, a, b, opps, speed: float, reach: float) -> float:
        """The chance a puck from a to b at `speed` gets past every opponent's stick."""
        return lane_odds(a, b, [o.pos for o in opps], speed, reach, self.vmax)

    def _shoot(self, h: Player, k: Keeper, o_f, aim) -> None:
        a = gl.aimed(self.rng, aim, o_f, WILD / max(self.level, 0.3))
        v = gl.launch(o_f, a, SHOT_MS * self.rng.uniform(0.85, 1.1))
        vx, vz = k.dir_frame(v[[0, 2]])
        s = self._carry_point(h)
        self.holder = None
        h.cool_until = self.t + 0.5
        self.puck.place(s[0], s[1], vx, vz)
        self.puck.vel = self.puck.vel + np.array([0.0, v[1], 0.0])
        self.stats["shots"][h.team] += 1
        self.last_touch, self.last_team = h.id, h.team
        self._watch = k.end
        self._actor = h.id
        k.g.last_s = None
        self.outbox.append(("log", "shot", {"by": h.id, "end": k.end}))

    def _pass(self, origin, m: Player, team: str, by: str) -> None:
        q = m.stick()
        speed = PASS_MS * (0.9 if m is self.you else 1.0)
        lead = q + _cap(m.vel * (_n(q - origin) / speed), LEAD_MAX)
        v = unit(lead - origin) * speed
        self.puck.place(origin[0], origin[1], v[0], v[1])
        self.pass_to = m.id
        self._actor = by
        self.last_touch, self.last_team = by, team
        if m is self.you:
            self.stats["passes_to_you"] += 1
        self.outbox.append(("log", "pass", {"by": by, "to": m.id}))

    # ------------------------------------------------------------------ where everyone skates
    def _roles_reset(self) -> None:
        """Forget the roles (a faceoff): who chases, who marks whom, sides, spots, the smoothing."""
        self._prev_chasers: dict[str, str] = {}
        self._back: dict[str, str] = {}              # a loose puck: who stays back, per team
        self._def_team: str | None = None            # the team the marks are for
        self._marks_t = -1.0                         # (not steady: marks picked afresh every 0.6 s, as before)
        self._sides: dict[str, float] = {}           # a role's side of the rink (_side)
        self._spot_of: dict[str, str] = {}           # supporter id -> his spot's name
        self._raw_prev: dict[str, np.ndarray] = {}   # the smoothing (_smooth): last raw target,
        self._steer: dict[str, np.ndarray] = {}      # ... last steering point,
        self._off: dict[str, np.ndarray] = {}        # ... and the jump still being blended out (and its rate)
        self._offv: dict[str, np.ndarray] = {}
        self._avoid_f: dict[str, np.ndarray] = {}    # each skater's steering-round request, eased (_skate)

    def _side(self, key: str, x: float) -> float:
        """Which side of the rink's long axis (x = 0) a role is on: it changes only once x is
        SIDE_FLIP past the middle on the other side, so a skater near the middle doesn't flip it."""
        s = self._sides.get(key)
        if s is None or x * s < -(SIDE_FLIP if self.steady else 0.0):
            s = self._sides[key] = 1.0 if x >= 0 else -1.0
        return s

    def _smooth(self, targets: dict, dt: float) -> dict:
        """Where each skater steers: his target, with any jump in it blended out (a critically damped
        spring with a SMOOTH_HALF half-life on the jump). A target that moves smoothly (a man he
        marks, a spot moving with the carrier) is followed exactly, with no lag. (Plain floats: it
        runs for every skater every tick.)"""
        out = {}
        if not self.steady:
            for pid, tg in targets.items():
                rx, rz = float(tg[0]), float(tg[1])
                prev = self._steer.get(pid)
                if prev is not None and math.hypot(rx - prev[0], rz - prev[1]) <= JUMP_M:
                    self._tvel[pid] = ((rx - prev[0]) / dt, (rz - prev[1]) / dt)
                else:
                    self._tvel[pid] = (0.0, 0.0)
                self._steer[pid] = (rx, rz)
                out[pid] = np.array([rx, rz])
            self._raw_prev, self._off, self._offv = {}, {}, {}
            return out
        y = 2.0 * math.log(2.0) / SMOOTH_HALF
        e = math.exp(-y * dt)
        for pid, tg in targets.items():
            rx, rz = float(tg[0]), float(tg[1])
            prev = self._raw_prev.get(pid)
            ox, oz = self._off.get(pid, (0.0, 0.0))
            vx, vz = self._offv.get(pid, (0.0, 0.0))
            if prev is None:                          # no target last tick: blend in from where he was steering
                last = self._steer.get(pid)
                ox, oz = (last[0] - rx, last[1] - rz) if last is not None else (0.0, 0.0)
                self._tvel[pid] = (0.0, 0.0)
            else:
                jx, jz = rx - prev[0], rz - prev[1]
                if math.hypot(jx, jz) > JUMP_M:
                    ox, oz = ox - jx, oz - jz         # it jumped: start from where he was going
                    self._tvel[pid] = (0.0, 0.0)
                else:
                    self._tvel[pid] = (jx / dt, jz / dt)
            j1x, j1z = vx + ox * y, vz + oz * y
            ox, oz, vx, vz = e * (ox + j1x * dt), e * (oz + j1z * dt), e * (vx - j1x * y * dt), e * (vz - j1z * y * dt)
            self._raw_prev[pid], self._off[pid], self._offv[pid] = (rx, rz), (ox, oz), (vx, vz)
            self._steer[pid] = (rx + ox, rz + oz)
            out[pid] = np.array([rx + ox, rz + oz])
        for pid in list(self._raw_prev):              # no target this tick (he coasts): start afresh next time
            if pid not in targets:
                del self._raw_prev[pid]
        return out

    def _react(self, targets: dict, pxz) -> dict:
        """Staggered reactions (reports/Lifelike AI players.md, change 3). When the puck changes hands
        (a take, a pass, a shot, a poke, a cover), each AI skater keeps skating where he was going
        until he has taken it in: REACT_S over level, plus a random tail, plus more if the puck is
        off to his side or behind him. The new carrier, whoever made the play and a pass's receiver
        react at once. Only where they skate waits: the puck on a stick is still instant."""
        h = self.holder
        key = h.id if isinstance(h, Player) else (h.end if isinstance(h, Keeper) else ("you" if self.yours else ""))
        if self.react <= 0:
            self._poss_key, self._react_at, self._held, self._actor = key, {}, {}, None
            return targets
        if key != self._poss_key and self._poss_key != "?":
            base = self.react / max(self.level, 0.3)
            side, behind = math.cos(math.radians(50)), math.cos(math.radians(110))
            for p in self.players:
                if p is h or p.id in (self.pass_to, self._actor):
                    self._react_at[p.id] = self.t
                    continue
                c = float(unit(pxz - p.pos) @ p.facing)
                extra = REACT_BEHIND if c < behind else (REACT_SIDE if c < side else 0.0)
                self._react_at[p.id] = self.t + base + float(self.rng.exponential(REACT_TAIL)) + extra
        self._poss_key, self._actor = key, None
        go = set()
        for pid, tg in targets.items():
            if self.t < self._react_at.get(pid, -1.0) and pid in self._held:
                targets[pid] = self._held[pid]        # (and his pace, as it was)
                if self._held_go.get(pid):
                    go.add(pid)
            else:
                self._held[pid] = np.asarray(tg, dtype=float).copy()
                self._held_go[pid] = pid in self.burst
                if pid in self.burst:
                    go.add(pid)
        self.burst = go
        return targets

    def _targets(self, pxz, pv) -> dict[str, np.ndarray]:
        """Where each AI skater's role sends him; self.burst: who goes flat out (cruise and burst,
        change 7): a loose puck's chasers, a pass's receiver, a defender beaten by his man, and a
        carrier with nobody goal side of him. Everyone else cruises."""
        h = self.holder
        self.burst, self.keep = set(), set()
        out: dict[str, np.ndarray] = {}
        if isinstance(h, Player) or self.yours:
            carrier = h if isinstance(h, Player) else self.you
            att = carrier.team
            if isinstance(h, Player):
                out[h.id] = self._carry_to(h)
            self._support(carrier, out)
            self._defend(OTHER[att], carrier, out)
        elif isinstance(h, Keeper):
            self._support(None, out, team=h.team, near=h.pos)
            self._defend(OTHER[h.team], None, out)
        else:
            self._chase(pxz, pv, out)
        return out

    def _carry_to(self, h: Player) -> np.ndarray:
        end = attack_end(h.team)
        net = self.arena.net(end)
        toward = 1.0 if end == "far" else -1.0
        side = self._side("carry:" + h.id, float(h.pos[0]))
        slot = net + np.array([side * 2.0, -toward * 6.5])
        if _n(slot - h.pos) < 2.0:             # in the slot: cut across
            slot = net + np.array([-side * 2.5, -toward * 5.0])
        push = np.zeros(2)
        mine = _n(h.pos - net)
        open_ice = True
        for o in self.team(OTHER[h.team]):
            d = o.pos - h.pos
            n = _n(d)
            if n < 3.5:
                push -= unit(d) * (3.5 - n) * 1.4
            if n < BURST_GAP and _n(o.pos - net) < mine:
                open_ice = False                  # a defender goal side of him: patience
        if open_ice:
            self.burst.add(h.id)                  # he has beaten them: go
        return slot + push

    def _support(self, carrier, out: dict, team: str | None = None, near=None) -> None:
        team = carrier.team if carrier is not None else team
        c = carrier.pos if carrier is not None else np.asarray(near, dtype=float)
        end = attack_end(team)
        net = self.arena.net(end)
        toward = 1.0 if end == "far" else -1.0
        side = self._side("support:" + team, float(c[0]))
        deep = abs(float(net[1] - c[1])) < 15.0
        door = net + np.array([-side * 1.8, -toward * 3.0])
        high = net + np.array([-side * 5.0, -toward * 12.0]) if deep else c + np.array([-side * 7.0, toward * 5.0])
        trail = c + np.array([side * 3.0, -toward * 5.0])
        mates = [p for p in self.players if p.team == team and p is not carrier]
        spots = {"door": door, "high": high} if deep else {"high": high, "trail": trail}
        if len(mates) == 3:
            spots["trail" if deep else "trail2"] = trail
        if not mates:
            return
        names = list(spots)

        def cost(assign) -> float:
            return sum(_n(p.pos - spots[n]) for p, n in zip(mates, assign))
        best = min(itertools.permutations(names, len(mates)), key=cost)
        now = tuple(self._spot_of.get(p.id) for p in mates)        # keep the spots they have, unless
        if (self.steady and len(set(now)) == len(now) and all(n in spots for n in now)
                and cost(best) > SPOT_BETTER * cost(now)):
            best = now                                             # ... another way is 20% shorter
        if carrier is not None:
            self.keep.update(p.id for p in mates)
        for p, n in zip(mates, best):
            self._spot_of[p.id] = n
            out[p.id] = spots[n]

    def _defend(self, team: str, carrier, out: dict) -> None:
        """Man to man, goal side; whoever has the carrier pressures him. When the puck changes sides
        each picks up the nearest man (the carrier first); then he keeps his man. Two swap only when
        their men cross and it saves both of them SWAP_M of skating; a carrier nobody has (you're
        one of us, so we're a defender short) is taken by the nearest."""
        mine = [p for p in self.players if p.team == team]
        theirs = self.team(OTHER[team])
        net = self.arena.net(defend_end(team))
        by = {a.id: a for a in theirs}
        held = [self.marks.get(d.id) for d in mine]
        if (team != self._def_team or not all(a in by for a in held) or len(set(held)) < len(held)
                or (not self.steady and self.t - self._marks_t > 0.6)):
            self._def_team, self._marks_t = team, self.t
            pairs = sorted(((_n(d.pos - a.pos), d.id, a.id) for d in mine for a in theirs))
            if carrier is not None:                   # the carrier is taken first, by the nearest
                pairs.sort(key=lambda x: (x[2] != carrier.id, x[0]))
            marks, used = {}, set()
            for _, d, a in pairs:
                if d not in marks and a not in used:
                    marks[d], used = a, used | {a}
            self.marks.update(marks)
        elif self.steady:
            for d1, d2 in itertools.combinations(mine, 2):
                a1, a2 = by[self.marks[d1.id]], by[self.marks[d2.id]]
                if (_n(d1.pos - a2.pos) < _n(d1.pos - a1.pos) - SWAP_M and
                        _n(d2.pos - a1.pos) < _n(d2.pos - a2.pos) - SWAP_M):
                    self.marks[d1.id], self.marks[d2.id] = a2.id, a1.id
                    self.outbox.append(("log", "switch", {"team": team, "a": d1.id, "b": d2.id}))
            if carrier is not None and mine and carrier.id not in {self.marks[d.id] for d in mine}:
                d = min(mine, key=lambda d: _n(d.pos - carrier.pos))
                self.marks[d.id] = carrier.id
                self.outbox.append(("log", "switch", {"team": team, "a": d.id, "to": carrier.id}))
        for d in mine:
            a = by.get(self.marks.get(d.id))
            if a is not None:
                self.keep.add(d.id)
            if a is not None and _n(a.pos - net) < _n(d.pos - net) - BACKCHECK_M:
                self.burst.add(d.id)                  # his man is past him: get back
            if a is None:
                out[d.id] = net + unit(np.array([0.0, self.arena.mid]) - net) * 4.0
                continue
            to_net = net - a.pos
            if carrier is not None and a is carrier:
                out[d.id] = a.stick() + 0.6 * unit(to_net)          # on him, goal side
            else:
                gap = float(np.clip(0.35 * _n(to_net), 1.5, 6.0))
                out[d.id] = a.pos + gap * unit(to_net)

    def _chase(self, pxz, pv, out: dict) -> None:
        """A loose puck: each team's quickest skater goes for it; the others pick up a man or
        get to the back door."""
        path = self._path(pxz, pv)
        when: dict[str, float] = {}                   # each team's chaser: how soon he gets there
        for team in ("us", "them"):
            cands = [p for p in self.players if p.team == team]
            if not cands:
                continue
            times = self._reach_all(cands, path)
            chaser = min(cands, key=lambda p: times[p.id][0])
            was = self._prev_chasers.get(team)        # he keeps it unless a teammate is clearly sooner
            if self.steady and was in times and was != chaser.id and times[was][0] <= times[chaser.id][0] + CHASE_KEEP:
                chaser = self.by_id[was]
            if self.pass_to in times:                 # a pass on its way: the receiver goes to it
                chaser = self.by_id[self.pass_to]
            if team == "us" and self.you is not None and self.you.blade is not None and self.pass_to != chaser.id:
                t_you = _n(self.you.blade - pxz) / self.vmax
                if t_you < 0.9 * times[chaser.id][0] or self.pass_to == "you":
                    chaser = None
            if chaser is not None:
                out[chaser.id] = times[chaser.id][1]
                self.chasers[team] = chaser.id
                when[team] = times[chaser.id][0]
                if self.pass_to == chaser.id:         # a pass to him: flat out only if his cruise won't get him there
                    tau, q = times[chaser.id]
                    rel = q - chaser.pos
                    d = _n(rel)
                    v0 = float(rel @ chaser.vel) / max(d, 1e-6)
                    if float(time_to(max(0.0, d - STICK_R), v0, self.cruise * self.vmax)) + 0.1 > tau + 0.05:
                        self.burst.add(chaser.id)
            rest = [p for p in cands if p is not chaser]
            net_own = self.arena.net(defend_end(team))
            net_att = self.arena.net(attack_end(team))
            home = {p.id: _n(p.pos - net_own) for p in rest}
            back = min(rest, key=lambda p: home[p.id]) if rest else None
            was = self._back.get(team)                # he stays back unless a teammate is 2 m nearer home
            if self.steady and back is not None and was in home and home[was] <= home[back.id] + 2.0:
                back = self.by_id[was]
            if back is not None:
                self._back[team] = back.id
            open_x = -6.0 * self._side("open:" + team, float(pxz[0]))
            for p in rest:
                if p is back:                         # the one nearest home stays between it and our net
                    out[p.id] = pxz + 0.45 * (net_own - pxz)
                else:                                 # the other gets open up ice
                    out[p.id] = pxz + 0.35 * (net_att - pxz) + np.array([open_x, 0.0])
        self._races(when)

    def _races(self, when: dict) -> None:
        """A loose puck is a race only if the two chasers are close in time (RACE_S): then both go
        flat out. One clearly first, or one alone, gets there at his cruise."""
        if len(when) == 2 and abs(when["us"] - when["them"]) < RACE_S:
            self.burst.update(self.chasers.values())

    TAUS = np.arange(0.0, 2.01, 0.1)

    def _path(self, pxz, pv) -> np.ndarray:
        """Where a loose puck will be over the next 2 s (sliding to a stop, ice and air; held off the boards)."""
        pr = self.puck.params
        speed = _n(pv)
        s = pk.slide(speed, self.TAUS, pr.ice_mu, pr.air_k)
        P = pxz + unit(pv)[None, :] * s[:, None]
        return np.array([self.arena.keep_on_ice(q, 0.3) for q in P]) if speed > 0.3 else np.repeat(pxz[None], len(self.TAUS), 0)

    def _reach_all(self, ps: list, path: np.ndarray) -> dict:
        """_reach for several skaters at once: {id: (how soon, where)}."""
        if not self.skate_like_you:
            return {p.id: self._reach(p, path) for p in ps}
        P = np.array([p.pos for p in ps])
        V = np.array([p.vel for p in ps])
        rel = path[None, :, :] - P[:, None, :]       # (n, 21, 2)
        d = np.sqrt((rel * rel).sum(-1))
        v0 = (rel * V[:, None, :]).sum(-1) / np.maximum(d, 1e-6)
        T = time_to(np.maximum(0.0, d - STICK_R), v0, self.vmax) + 0.1
        out = {}
        for i, p in enumerate(ps):
            ok = np.flatnonzero(T[i] <= self.TAUS)
            out[p.id] = (float(self.TAUS[ok[0]]), path[ok[0]]) if len(ok) else (2.0 + float(T[i, -1]), path[-1])
        return out

    def _reach(self, p: Player, path: np.ndarray) -> tuple[float, np.ndarray]:
        """(how soon p can get a stick on the puck, where). On your skating model: from the way
        he's going now, stopping first if it's away from the puck, then pushing up to speed."""
        rel = path - p.pos
        d = np.linalg.norm(rel, axis=1)
        if self.skate_like_you:
            v0 = (rel @ p.vel) / np.maximum(d, 1e-6)
            t_p = time_to(np.maximum(0.0, d - STICK_R), v0, self.vmax) + 0.1
        else:
            t_p = np.maximum(0.0, d - STICK_R) / self.vmax + 0.15
        ok = np.flatnonzero(t_p <= self.TAUS)
        if len(ok):
            return float(self.TAUS[ok[0]]), path[ok[0]]
        return 2.0 + float(t_p[-1]), path[-1]

    def _skate(self, p: Player, target, dt: float, avoid=None) -> None:
        """Toward his target, inside his skating limits; `avoid`: requests to go round other AI
        skaters and round you (_avoid), inside the same limits. (Plain floats: it runs for every
        skater every tick.)"""
        top = self._top if self._top is not None else self.vmax      # (this tick's: update works it out once)
        px, pz = float(p.pos[0]), float(p.pos[1])
        vx, vz = float(p.vel[0]), float(p.vel[1])
        live = target is not None and self.state == "live"
        wx = wz = 0.0
        arriving = False
        if live:
            vmax = top * (CARRY if p is self.holder else 1.0)
            pace = vmax                               # flat out on a read; else his cruise, or what keeps up with his man
            y = self.you
            near_you = y is not None and math.hypot(px - y.pos[0], pz - y.pos[1]) < BURST_CLEAR + 0.5 * math.hypot(vx, vz)
            if p.id not in self.burst or near_you:
                pace = self.cruise * top
                if p.id in self.keep:                 # following someone: his speed, a little more if behind
                    gap = math.hypot(target[0] - px, target[1] - pz)
                    tv = self._tvel.get(p.id, (0.0, 0.0))
                    pace = max(pace, math.hypot(tv[0], tv[1]) + 0.3 * min(1.0, gap / 2.0))
                pace = min(vmax, pace)
            tg = self._round_nets(p.pos, self._off_nets(np.asarray(target, dtype=float)))
            tox, toz = float(tg[0]) - px, float(tg[1]) - pz
            dist = math.hypot(tox, toz)
            if self.skate_like_you:                   # his braking takes ARRIVE/JERK to build: start that early
                lead = math.hypot(vx, vz) * ARRIVE / JERK
                arrive = math.sqrt(2 * 0.8 * ARRIVE * max(dist - lead, 0.0))
            else:
                arrive = math.sqrt(2 * ACCEL * dist)
            arriving = arrive < pace
            if dist > 1e-9:
                w = min(pace, arrive) / dist
                wx, wz = tox * w, toz * w
            if self.steady:                           # going round people, eased in and out
                if avoid is None:
                    ax = az = bx = bz = 0.0
                else:
                    ax, az = float(avoid[0][0]) * vmax, float(avoid[0][1]) * vmax
                    bx, bz = float(avoid[1][0]) * vmax, float(avoid[1][1]) * vmax
                wn = math.hypot(wx, wz)
                ux, uz = (wx / wn, wz / wn) if wn > 1e-9 else (0.0, 0.0)
                back = ax * ux + az * uz
                if back < 0:                          # another AI: never brake against where he's going, step round
                    ax, az = ax - back * ux, az - back * uz
                ax, az = ax + bx, az + bz             # you: he may also slow for you
                fx, fz = self._avoid_f.get(p.id, (0.0, 0.0))
                k = min(1.0, dt / AVOID_EASE)
                fx, fz = fx + (ax - fx) * k, fz + (az - fz) * k
                self._avoid_f[p.id] = (fx, fz)
                wx, wz = wx + fx, wz + fz
                m = math.hypot(wx, wz)
                if m > pace:                          # (going round someone is no reason to go faster)
                    wx, wz = wx * (pace / m), wz * (pace / m)
        if self.skate_like_you:
            vx, vz = self._drive(p, vx, vz, wx, wz, arriving, GLIDE if self.state == "live" else STOP, dt)
        elif not live:
            k = max(0.0, 1 - 4 * dt)
            vx, vz = vx * k, vz * k
        else:                                         # the old way: one 5 m/s^2 cap, any direction
            dvx, dvz = wx - vx, wz - vz
            n = math.hypot(dvx, dvz)
            if n > ACCEL * dt:
                dvx, dvz = dvx * (ACCEL * dt / n), dvz * (ACCEL * dt / n)
            vx, vz = vx + dvx, vz + dvz
        fx, fz = px + vx * dt, pz + vz * dt
        pos = self._off_nets(self.arena.keep_on_ice((fx, fz), 0.45))
        nx, nz = float(pos[0]), float(pos[1])
        if self.steady:                               # the boards or a net stopped him: no pushing on into them
            cx, cz = nx - fx, nz - fz
            n = math.hypot(cx, cz)
            if n > 1e-9:
                into = (vx * cx + vz * cz) / n
                if into < 0:
                    vx, vz = vx - into * cx / n, vz - into * cz / n
        p.pos, p.vel = pos, np.array([vx, vz])
        p.stride += math.hypot(nx - px, nz - pz)
        speed = math.hypot(vx, vz)
        ffx, ffz = float(p.facing[0]), float(p.facing[1])
        if p is self.holder or speed > 1.0:
            gx, gz = (vx / speed, vz / speed) if speed > 0.5 else (ffx, ffz)
        else:
            q = self._pxz if self._pxz is not None else self._puck()[0]
            dx, dz = float(q[0]) - nx, float(q[1]) - nz
            n = math.hypot(dx, dz)
            gx, gz = (dx / n, dz / n) if n > 1e-9 else (0.0, 0.0)
        if gx or gz:
            k = min(1.0, 8.0 * dt)
            hx, hz = ffx + k * (gx - ffx), ffz + k * (gz - ffz)
            n = math.hypot(hx, hz)
            hx, hz = (hx / n, hz / n) if n > 1e-9 else (0.0, 0.0)
            p.facing = np.array([hx, hz])
            p.turn = math.degrees(math.atan2(ffx * hz - ffz * hx, ffx * hx + ffz * hz)) / dt

    @staticmethod
    def _crosses(a, b, x0: float, x1: float, z0: float, z1: float) -> bool:
        """Does the segment a-b pass through the inside of the box [x0, x1] x [z0, z1]?"""
        t0, t1 = 0.0, 1.0
        d = (b[0] - a[0], b[1] - a[1])
        for p, q in ((-d[0], a[0] - x0), (d[0], x1 - a[0]), (-d[1], a[1] - z0), (d[1], z1 - a[1])):
            if abs(p) < 1e-12:
                if q <= 1e-9:
                    return False
                continue
            r = q / p
            if p < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t1 - t0 <= 1e-6:
                return False
        return True

    def _round_nets(self, q, target, m: float = 0.35) -> np.ndarray:
        """The way to target: straight, or by a corner of a net in the way (a puck behind the net:
        go round it, not into its front)."""
        hw, front, back = zn.NET_HALF_W + zn.POST_R + m, zn.GOAL_Z + m, zn.GOAL_Z - zn.NET_DEPTH - m
        c = 0.3
        L = self.arena.length
        qx, qz, tx, tz = float(q[0]), float(q[1]), float(target[0]), float(target[1])
        for k in self.keepers.values():
            if k.end == "home":
                ax, az, bx, bz = qx, qz, tx, tz
            else:
                ax, az, bx, bz = -qx, L - qz, -tx, L - tz
            if (max(az, bz) <= back or min(az, bz) >= front or max(ax, bx) <= -hw or min(ax, bx) >= hw):
                continue                              # nowhere near this net
            a, b = k.frame(q), k.frame(target)
            if not self._crosses(a, b, -hw, hw, back, front):
                continue
            corners = [np.array([sx * (hw + c), sz]) for sx in (-1.0, 1.0) for sz in (back - c, front + c)]
            best, best_len = None, math.inf
            for cn in corners:                        # one corner that sees both ends, or the nearest step
                if self._crosses(a, cn, -hw, hw, back, front):
                    continue
                hop = 0.0 if not self._crosses(cn, b, -hw, hw, back, front) else 5.0
                n = float(np.linalg.norm(cn - a) + np.linalg.norm(b - cn)) + hop
                if n < best_len:
                    best, best_len = cn, n
            if best is not None:
                return k.frame(best)
        return np.asarray(target, dtype=float)

    def _off_nets(self, q, m: float = 0.35) -> np.ndarray:
        """A point pushed out of both nets (by m): skaters go round them, not through."""
        front, back, hw = zn.GOAL_Z, zn.GOAL_Z - zn.NET_DEPTH, zn.NET_HALF_W + zn.POST_R
        L = self.arena.length
        for k in self.keepers.values():
            qx, qz = float(q[0]), float(q[1])
            fx, fz = (qx, qz) if k.end == "home" else (-qx, L - qz)
            if not (abs(fx) < hw + m and back - m < fz < front + m):
                continue                              # not in this net
            f = k.frame(q)
            if abs(f[0]) < hw + m and back - m < f[1] < front + m:
                dx, dfront, dback = hw + m - abs(f[0]), front + m - f[1], f[1] - (back - m)
                least = min(dx, dfront, dback)
                if least == dfront:
                    f = np.array([f[0], front + m])
                elif least == dx:
                    f = np.array([math.copysign(hw + m, f[0] if f[0] else 1.0), f[1]])
                else:
                    f = np.array([f[0], back - m])
                q = k.frame(f)
        return np.asarray(q, dtype=float)

    def _drive(self, p: Player, vx: float, vz: float, wx: float, wz: float, arriving: bool, rest: float,
               dt: float) -> tuple[float, float]:
        """Your skating model for an AI skater (change 6; rig.Drive's rules): from his velocity
        (vx, vz) toward the velocity (wx, wz) he wants, he pushes at up to PUSH, easing in over EASE,
        and bends his path at up to CARVE (with the edges' grip shared between the two); slowing to
        arrive he brakes at up to ARRIVE, and wanting to go more than STOP_ANGLE from where he's
        going is a hockey stop at STOP. With nothing to go for he slows at `rest` (GLIDE: coasting;
        STOP: play has stopped). His acceleration builds at JERK, so a push never starts as a step.
        Returns his new velocity; sets p.acc and p.mode."""
        speed = math.hypot(vx, vz)
        want_s = math.hypot(wx, wz)
        ux, uz = (vx / speed, vz / speed) if speed > 1e-9 else (0.0, 0.0)
        if want_s < 1e-9:                             # nothing to go for (or he's there): slow to rest
            rate = ARRIVE if arriving else rest
            p.mode = "coast" if rate == GLIDE else "stop"
            a = min(rate, speed / dt)
            ax, az = -ux * a, -uz * a
        elif speed > STOP_DONE and wx * vx + wz * vz < _COS_STOP * want_s * speed:
            p.mode = "stop"
            ax, az = -ux * STOP, -uz * STOP
        elif speed < STOP_DONE:                       # from (nearly) still: straight at it
            p.mode = "push"
            dvx, dvz = wx - vx, wz - vz
            n = math.hypot(dvx, dvz)
            if n > 1e-9:
                a = min(PUSH, n / EASE) / n
                ax, az = dvx * a, dvz * a
            else:
                ax = az = 0.0
        else:
            p.mode = "push"
            dvx, dvz = wx - vx, wz - vz
            along = dvx * ux + dvz * uz
            cx, cz = dvx - along * ux, dvz - along * uz
            if along >= 0:
                a_al = min(PUSH, along / EASE)
            elif arriving:                            # slowing to get there
                a_al = -min(ARRIVE, -along / EASE)
            elif wx * vx + wz * vz > 0:               # wants a little less speed: coasts down to it
                a_al = -min(GLIDE, -along / EASE)
                p.mode = "coast"
            else:
                a_al = -min(PUSH, -along / EASE)
            n_x = math.hypot(cx, cz)
            a_x = min(CARVE, n_x / EASE)
            grip = max(PUSH, CARVE)
            a_al = math.copysign(min(abs(a_al), math.sqrt(max(grip * grip - a_x * a_x, 0.0))), a_al)
            ax, az = ux * a_al, uz * a_al
            if n_x > 1e-9:
                ax, az = ax + cx / n_x * a_x, az + cz / n_x * a_x
        cax, caz = float(p.acc[0]), float(p.acc[1])
        dax, daz = ax - cax, az - caz
        n = math.hypot(dax, daz)
        if n > JERK * dt:
            dax, daz = dax * (JERK * dt / n), daz * (JERK * dt / n)
        cax, caz = cax + dax, caz + daz
        nvx, nvz = vx + cax * dt, vz + caz * dt
        if p.mode in ("stop", "coast") and nvx * vx + nvz * vz <= 0.0:   # a stop ends at rest; it doesn't push him back
            nvx = nvz = cax = caz = 0.0
        if nvx == 0.0 and nvz == 0.0 and want_s < 1e-9:
            p.mode = "still"
        p.acc = np.array([cax, caz])
        return nvx, nvz

    def _avoid(self) -> dict[str, np.ndarray]:
        """Steering round people (change 5): for each AI skater, (from the other AI, from you): a
        request (in units of his top speed) away from anyone he'd pass closer than AVOID_M (another
        AI, in the next AVOID_S) or AVOID_YOU_M (you, in the next AVOID_YOU_S), harder the closer
        and sooner. Both of two AI skaters give way; you don't, so they go round you, starting 2 m
        out (1 m when he's in your view and closing slowly). _skate keeps it inside his skating
        limits."""
        sk = self.players
        if not self.steady or self.state != "live" or len(sk) < 1:
            return {}
        P = np.array([p.pos for p in sk])
        V = np.array([p.vel for p in sk])
        n = len(sk)
        Q, W = P, V
        Rm = np.full((n, n), AVOID_M)
        y = self.you
        if y is not None:
            Q, W = np.vstack([P, y.pos]), np.vstack([V, y.vel])
            rel = P - y.pos                           # from you to each of them
            dist = np.maximum(np.linalg.norm(rel, axis=1), 1e-6)
            seen = (rel @ y.facing) / dist > math.cos(math.radians(60))
            closing = -((V - y.vel) * rel).sum(1) / dist
            Rm = np.hstack([Rm, np.where(seen & (closing < 1.0), 1.0, AVOID_YOU_M)[:, None]])
        r = Q[None, :, :] - P[:, None, :]            # (n, m, 2): to each other body
        w = W[None, :, :] - V[:, None, :]
        ww = np.maximum((w * w).sum(-1), 1e-9)
        H = np.full(Rm.shape[1], AVOID_S)
        if y is not None:
            H[-1] = AVOID_YOU_S
        tc = np.clip(-(r * w).sum(-1) / ww, 0.0, H)
        c = r + w * tc[..., None]                    # where he'll be from me when we're closest
        d = np.linalg.norm(c, axis=-1)
        s = np.clip((Rm - d) / (Rm - BODY_MIN), 0.0, 1.0) * (1.0 - 0.5 * tc / H)
        s[np.arange(n), np.arange(n)] = 0.0
        head_on = d < 1e-3                           # straight at each other: each keeps to his right
        away = np.where(head_on[..., None], np.stack([r[..., 1], -r[..., 0]], -1), -c)
        away = away / np.maximum(np.linalg.norm(away, axis=-1, keepdims=True), 1e-9)
        push = s[..., None] * away
        ai = push[:, :n].sum(1)
        you = push[:, n] if y is not None else np.zeros_like(ai)
        return {p.id: (ai[i], you[i]) for i, p in enumerate(sk) if s[i].any()}

    def _separate(self) -> None:
        if self.steady:
            return self._separate_steady()
        sk = self.players
        for i in range(len(sk)):
            for j in range(i + 1, len(sk)):
                a, b = sk[i], sk[j]
                d = b.pos - a.pos
                n = _n(d)
                if n < SKATER_GAP:
                    push = unit(d if n > 1e-6 else self.rng.normal(size=2)) * (SKATER_GAP - n) / 2
                    a.pos, b.pos = a.pos - push, b.pos + push
        y = self.you
        if y is not None:                             # you don't get pushed: they go round you
            for a in sk:
                d = a.pos - y.pos
                n = _n(d)
                if n < SKATER_GAP:
                    a.pos = y.pos + unit(d if n > 1e-6 else np.array([1.0, 0.0])) * SKATER_GAP

    def _separate_steady(self) -> None:
        """Bodies closer than BODY_MIN (only when steering round failed): two AI skaters are eased
        apart and stop closing; one on you is never moved, but turns to go away from you at least
        as fast as you come on (no jump beside your head)."""
        sk = self.players
        for i in range(len(sk)):
            for j in range(i + 1, len(sk)):
                a, b = sk[i], sk[j]
                d = b.pos - a.pos
                n = _n(d)
                if n < BODY_MIN:
                    u = unit(d if n > 1e-6 else self.rng.normal(size=2))
                    push = u * (BODY_MIN - n) / 2
                    a.pos, b.pos = a.pos - push, b.pos + push
                    closing = float((a.vel - b.vel) @ u)
                    if closing > 0:
                        a.vel, b.vel = a.vel - 0.5 * closing * u, b.vel + 0.5 * closing * u
        y = self.you
        if y is not None:
            for a in sk:
                d = a.pos - y.pos
                n = _n(d)
                if n < BODY_MIN:
                    u = unit(d if n > 1e-6 else np.array([1.0, 0.0]))
                    need = float(y.vel @ u) + 0.5
                    along = float(a.vel @ u)
                    if along < need:
                        a.vel = a.vel + (need - along) * u

    # ------------------------------------------------------------------ for the app
    AI_COLS = ("x", "z", "vx", "vz", "fx", "fz", "bx", "bz", "tx", "tz", "rx", "rz", "mark", "mode", "go")

    def ai_header(self) -> str:
        """ai.csv's header: the game, the puck, you, then each AI skater (position, velocity,
        facing, blade, where he's steering (t) and where his role says to go before the smoothing
        (r), and the man he marks), then the goalies. Arena (x, z)."""
        if self._ai_header is None:
            cols = ["t", "state", "holder", "pass_to", "vmax", "px", "py", "pz", "pvx", "pvz",
                    "you_x", "you_z", "you_fx", "you_fz", "you_bx", "you_bz", "chase_us", "chase_them"]
            for p in self.players:
                cols += [f"{p.id}_{c}" for c in self.AI_COLS]
            cols += ["home_x", "home_z", "far_x", "far_z"]
            self._ai_header = ",".join(cols) + "\n"
        return self._ai_header

    def ai_row(self) -> str:
        """This AI tick as a row of ai.csv (an empty field: none, or not known)."""
        def f(*v) -> list[str]:
            return [f"{float(x):.3f}" for x in v]
        h = self.holder
        who = h.id if isinstance(h, Player) else (h.end if isinstance(h, Keeper) else ("you" if self.yours else ""))
        pxz, pv = self._puck()
        row = [f"{self.t:.4f}", self.state, who, self.pass_to or "", f"{self.vmax:.3f}",
               *f(pxz[0], self.puck.pos[1], pxz[1], pv[0], pv[1])]
        y = self.you
        row += f(*y.pos, *y.facing) if y is not None else [""] * 4
        row += f(*y.blade) if y is not None and y.blade is not None else ["", ""]
        row += [self.chasers.get("us", ""), self.chasers.get("them", "")]
        for p in self.players:
            row += f(*p.pos, *p.vel, *p.facing, *p.stick())
            for tg in (self.targets.get(p.id), self.raw_targets.get(p.id)):
                row += f(*tg) if tg is not None else ["", ""]
            row.append(self.marks.get(p.id, "") if self.state == "live" else "")
            row += [p.mode, "1" if p.id in self.burst else ""]
        for k in (self.keepers["home"], self.keepers["far"]):
            row += f(*k.pos)
        return ",".join(row) + "\n"

    def status(self) -> str:
        h = self.holder
        who = h.id if isinstance(h, Player) else (f"goalie {h.end}" if isinstance(h, Keeper) else
                                                   ("you" if self.yours else "loose"))
        return f"3v3 {self.state:<7} us {self.score['us']} them {self.score['them']}  puck: {who}"

    def summary(self) -> dict:
        return {"score": dict(self.score), "to": self.to_goals, **self.stats}
