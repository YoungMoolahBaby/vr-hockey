"""3 on 3 with two goalies, in the headset: you and two teammates against three, first to five.

    uv run python game.py                    # first to 5
    uv run python game.py --to 3 --level 0.8 # a shorter game against a slower team
    uv run python game.py --skate 3.5        # your top speed (m/s at full stick; default 4)
    uv run python game.py --free             # free skate: you, a puck and a goalie in each net
    uv run python game.py --free --empty     # ... with both nets empty

Free skate is the same rink with no skaters but you, to get used to skating with the thumbsticks.
The goalies save what they get a piece of, cover a slow puck, and pass it back out to you; you
can't carry it through one (go round him). Its buttons are the sandbox's: X puts a puck on your
stick (one also comes back after a goal), B says the setting, A saves the settings (the comfort
ones too: the game uses them).

You start at centre ice, facing the far net: that's the one you attack; your goalie is behind
you. Press A to drop the puck. Your teammates (blue) pass to you when you're open; the other
team (orange) marks you, goal side, and pokes at the puck when you carry it. Skate into their
carrier to knock it off him, or knock it off his stick with yours. After a goal everyone lines up
at centre again (you're moved there).

Controls
  grip buttons                  hold the stick (as in the sandbox)
  left thumbstick               skate (forward is where you look), up to your cruising speed
  left trigger                  sprint: the harder you squeeze, the faster, up to "sprint speed"
  right trigger                 shoot: firm hands (released, soft hands that give with the puck)
  right thumbstick              turn (the "snap turn" setting turns you in steps instead; 0 = smooth)
  A                             drop the puck (a new game when one is over)
  B                             say the score
  X                             faceoff at centre now
  hold the left thumbstick in   (1 s) lay the rink out around you again (the score stays)
  Y                             fit the stick (as in the sandbox)
  click the left thumbstick     switch it to tuning the settings, and back (as in the sandbox):
                                soft hands, shot release, skate speed and turn speed are among them

Soft hands are off by default, as everywhere (Jon, 2026-11-09: with the ice assist, honest physics
feels right; the soft hands' pull within 4 cm of the blade felt like a magnetic field). --magnet 0.7
turns them back on: while your blade moves at handling speed, a puck on it rides the blade instead
of flying off; swing faster than the shot release speed (relative to you, so skating doesn't count)
and it comes off as hit. The other team is never faster than 95% of your skate speed.

The game is threes.py (the AI and the rules), arena.py (the rink), goalie.py (the goalies).
Recorded to data/game-<timestamp>/ like the sandbox: every pass, shot, save and goal in
events.jsonl, the score and stats in meta.json.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import time
from pathlib import Path

import glfast  # noqa: F401  (first: PyOpenGL's error checking off, read when xr loads it)
import numpy as np
import xr

import arena as ar
import figures
import grab
import puck as pk
import record
import sandbox
import stickspec
import threes
import zone as zn
from contacts import Contact

HERE = Path(__file__).resolve().parent
GAME_MAGNET = 0.0        # soft hands: off (Jon prefers honest physics, with the ice assist); 0.7 was on


class GamePhysics(sandbox.Physics):
    """The sandbox's stick and puck, with the game instead of free play."""

    def __init__(self, mode: "GameMode"):
        super().__init__(mode.play, mode.voice, mode.log)
        self.mode = mode
        self.blade = None
        self.gripping = False

    def __call__(self, t: float, tick: dict) -> None:
        before = getattr(self, "errors", 0)
        super().__call__(t, tick)
        if before == 0 and getattr(self, "errors", 0) > 0:
            self.voice.say("Something broke in the game. Tell Claude.", key="error")

    def _world(self, t: float, R, p, held: bool) -> None:
        self.blade = (R @ self.sweet + p) if held else None
        self.gripping = self.play.stick_state in (grab.BOTH, grab.TOP, grab.BOTTOM)
        self.mode.place_if_asked(t, self.blade)

    def _game(self, t: float, imp: float) -> None:
        pl, pz = self.play, self.play.sim.puck
        if pz.events:
            now = time.perf_counter()
            for kind, speed in pz.events:
                pl.bus.publish(Contact(now, kind, speed))          # boards and posts play from the bus
            pz.events.clear()
        self.mode.tick(t, self.blade, self.gripping)


class GameMode(sandbox.SandboxMode):
    kind = "game-3v3"
    app_name = "vr-hockey-3v3"
    to_goals, length, level = 5, ar.LENGTH, 1.0

    def __init__(self, play, voice, log):
        super().__init__(play, voice, log)
        self.arena: ar.Arena | None = None
        self.game: threes.Game | None = None
        self.want_place: str | None = None
        self.rng = np.random.default_rng()
        self._static = (None, sandbox.NO_TRIS, None)            # (key, the rink's triangles, its lines)
        self.games: list[dict] = []

    def make_physics(self) -> GamePhysics:
        self.physics = GamePhysics(self)
        return self.physics

    def intro(self) -> str:
        return (f"Three on three, first to {self.to_goals}. You're at centre ice: you attack the far net, "
                "your goalie is behind you. Left stick skates, right stick turns. Press A to drop the puck.")

    # ---- the rink (physics thread)
    def first_head(self) -> None:
        self.want_place = "head"

    def recenter(self) -> None:
        self.want_place = "again"
        self.voice.say("Rink laid out around you.", key="rink")

    def _lay_out(self, t: float) -> ar.ArenaPuck:
        """The rink around you: you on your faceoff spot at centre ice, facing the far net."""
        Rh, ph = self.play.head
        f = -Rh[:, 2]
        f = np.array([f[0], 0.0, f[2]]) / max(float(np.hypot(f[0], f[2])), 1e-6)
        mid = self.length / 2
        zone = zn.Zone.placed((0.0, mid - 1.4), ph, f, (0.0, 1.0))
        self.arena = ar.Arena(zone, self.length)
        puck = ar.ArenaPuck(self.play.params, self.arena)
        self.play.sim.puck = puck
        self.log.event(t, "rink", how=self.want_place, **self.arena.to_dict())
        return puck

    def place_if_asked(self, t: float, blade_world) -> None:
        if self.want_place is None or self.play.head is None:
            return
        puck = self._lay_out(t)
        old = self.game
        self.game = threes.Game(self.arena, puck, np.random.default_rng(self.rng.integers(1 << 31)),
                                to_goals=self.to_goals, you=True, level=self.level)
        if old is not None and self.want_place == "again" and old.state not in ("ready", "over"):
            self.game.score = dict(old.score)
            self.game.t = t
            self.game.faceoff()
        self.want_place = None

    # ---- the boards stop you (render thread, every frame)
    BOARD_GAP = 0.3          # m: your head stops this far off the boards
    BOARD_EASE = 2.0         # 1/s: near them, your speed into them is held to this times the room left
    BOARD_LOOK = 1.8         # m: ... from this far out

    def confine(self, head_world, vel: np.ndarray, dt: float) -> np.ndarray:
        """Gently: your speed into the boards falls as you near them (from 3 m/s that's about
        6 m/s^2 at most), so a glide ends at the boards, not through them."""
        if self.arena is None or head_world is None:
            return vel
        zone = self.arena.zone
        x, z = zone.xz(head_world)
        hit = self.arena.boards_contact(float(x), float(z), self.BOARD_LOOK)
        if hit is None:
            return vel
        pen, (nx, nz) = hit
        room = self.BOARD_LOOK - pen - self.BOARD_GAP        # m left before you stop
        n = zone.dir_to_world(nx, nz)                        # into the rink
        into = -float(vel @ n)
        allowed = max(0.0, self.BOARD_EASE * room)
        if into > allowed:
            vel = vel + (into - allowed) * n
        return vel

    # ---- the game (physics thread, every tick)
    def tick(self, t: float, blade_world, gripping: bool) -> None:
        g = self.game
        if g is None:
            return
        if t - g._last_ai < threes.AI_DT:                # between the AI's ticks: only shots and goals
            g.update(t)
        else:
            zone = self.arena.zone
            head = None
            if self.play.head is not None:
                Rh, ph = self.play.head
                head = (zone.xz(ph), zone.dir_to_zone(-Rh[:, 2]))
            blade = zone.xz(blade_world) if blade_world is not None and gripping else None
            g.you_ms = self.play.tuning.values["skate"]
            g.update(t, blade, head)
        if g.outbox:
            self._drain(t, g)

    def _drain(self, t: float, g: threes.Game) -> None:
        pl = self.play
        hands = [pl.spec.top_hand, pl.spec.bottom_hand]
        while g.outbox:
            item = g.outbox.pop(0)
            kind = item[0]
            if kind == "say":
                self.voice.say(item[1], key=item[2] if len(item) > 2 else "game")
            elif kind == "sound":
                pl.sounds.put((item[1], item[2]))
            elif kind == "buzz":
                pl.haptics.put((item[1], hands, item[2]))
            elif kind == "teleport":
                zone = self.arena.zone
                at, f = item[1], item[2]
                pl.want_teleport = (zone.to_world(at[0], 0.0, at[1]), zone.dir_to_world(f[0], f[1]))
            elif kind == "log":
                self.log.event(t, item[1], **item[2])
                if item[1] == "goal" and g.state == "over":
                    self.games.append(g.summary())
                    print(f"  game over: us {g.score['us']} them {g.score['them']}", flush=True)
                elif item[1] == "goal":
                    print(f"  goal ({item[2]['team']}, {item[2]['by']}): us {g.score['us']} them {g.score['them']}",
                          flush=True)

    def button(self, name: str, t_sim: float) -> None:
        g = self.game
        if g is None:
            return
        if name == "a" and g.state in ("ready", "over"):
            g.start()
        elif name == "x" and g.state in ("live", "goal"):
            g.faceoff()
        elif name == "b":
            s = g.score
            self.voice.say(f"Us {s['us']}, them {s['them']}.", key="game")

    # ---- drawing (render thread)
    def draw(self, poses: dict, held: dict, stick, state: int) -> sandbox.Frame:
        line = sandbox.Lines()
        arena, g = self.arena, self.game
        static, static_tris = np.zeros((0, 6), dtype=np.float32), sandbox.NO_TRIS
        if arena is not None:
            key = (arena, self.play.tuning.values.get("grid", 0) > 0)
            if self._static[0] != key:                    # the rink only changes when it's laid out
                lines = sandbox.Lines()
                ar.markings(arena, lines, grid=key[1])
                self._static = (key, lines.tri_array(), lines.array())
            static_tris, static = self._static[1], self._static[2]
        if g is not None:
            zone = arena.zone
            for p in g.players:
                figures.skater(line, zone, p.pos, p.facing, figures.US if p.team == "us" else figures.THEM,
                               p.shoots, p.stride, float(np.linalg.norm(p.vel)))
            for k in g.keepers.values():
                figures.goalie(line, zone if k.end == "home" else arena.far, k.g.c, k.g.facing,
                               down=k.g.mode != "track" or k.hold_since is not None,
                               color=figures.US if k.team == "us" else figures.THEM)
            ar.scoreboard(arena, line, g.score["us"], g.score["them"], (figures.US, figures.THEM))
        sandbox.draw_puck(line, self.play.sim.puck)
        sandbox.draw_hands_and_stick(line, self.play, poses, held, stick, state)
        return sandbox.Frame(np.vstack([static_tris, line.tri_array()]), np.vstack([static, line.array()]),
                             line.mesh_list())

    def status(self) -> str:
        g = self.game
        err = getattr(self.physics, "errors", 0)
        return (g.status() if g is not None else "laying out") + (f"  ERRORS {err}" if err else "")

    def meta(self) -> dict:
        g = self.game
        return {"games": self.games + ([g.summary()] if g is not None and g.state != "over" else []),
                "rink": self.arena.to_dict() if self.arena else None, "level": self.level,
                "skate_ms": self.play.tuning.values["skate"], "turn_deg_s": self.play.tuning.values["turn"]}

    def close(self) -> None:
        g = self.game
        if g is not None:
            s = g.stats
            print(f"3v3: us {g.score['us']} them {g.score['them']}  shots {s['shots']}  saves {s['saves']}  "
                  f"passes to you {s['passes_to_you']}  your shots {s['your_shots']}")


class FreeSkatePhysics(GamePhysics):
    """Free skate: the stick, a puck and the whole rink, and no game. Shot speeds and goals are
    called as in the sandbox; X (or a goal, after a moment) puts a puck on your stick."""

    def _world(self, t: float, R, p, held: bool) -> None:
        super()._world(t, R, p, held)                       # lays the rink out when asked
        pl = self.play
        if not isinstance(pl.sim.puck, ar.ArenaPuck):
            return
        if pl.want_puck or (self.respawn_at is not None and t >= self.respawn_at):
            spot = self._blade_spot(R, p) if held else self._front_spot()
            if spot is not None:
                self.mode.drop(t, spot)
                pl.want_puck, self.respawn_at, self.shot = False, None, None

    def _game(self, t: float, imp: float) -> None:
        pl, pz = self.play, self.play.sim.puck
        if not isinstance(pz, ar.ArenaPuck):
            return
        self._call_shot(t, imp)
        now = time.perf_counter()
        for kind, speed in pz.events:
            pl.bus.publish(Contact(now, kind, speed))      # boards, posts and the net play from the bus
            if kind == "post" and speed > 2:
                self.voice.say("Post!", key="post")
        pz.events.clear()
        if pz.in_net and self.respawn_at is None:
            self.mode.goal(t, "far" if pz.in_net == 2 else "home")
            self.respawn_at = t + 2.0
        self.mode.tick(t, self.blade, self.gripping)        # the goalies


class FreeSkateMode(GameMode):
    """You and a puck on the 3v3 rink, a goalie in each net (threes.Goalies; or none, --empty): to
    get used to skating with the thumbsticks before a game. The buttons do what they do in the
    sandbox."""

    kind = "freeskate"
    app_name = "vr-hockey-freeskate"
    goalie_ends: tuple = ("home", "far")

    def __init__(self, play, voice, log):
        super().__init__(play, voice, log)
        self.goals = {"far": 0, "home": 0}
        self.goalies: threes.Goalies | None = None

    def make_physics(self) -> FreeSkatePhysics:
        self.physics = FreeSkatePhysics(self)
        return self.physics

    def intro(self) -> str:
        who = "a goalie in each net" if self.goalie_ends else "both nets empty"
        return (f"Free skate. You, a puck, and {who}. Left stick skates, left trigger sprints, right "
                "stick turns. X puts a puck on your stick. Click the left stick to tune the settings, A saves them.")

    def place_if_asked(self, t: float, blade_world) -> None:
        if self.want_place is None or self.play.head is None:
            return
        puck = self._lay_out(t)
        self.goalies = (threes.Goalies(self.arena, puck, np.random.default_rng(self.rng.integers(1 << 31)),
                                       ends=self.goalie_ends) if self.goalie_ends else None)
        self.want_place = None
        self.play.want_puck = True                          # and a puck to play with

    def tick(self, t: float, blade_world, gripping: bool) -> None:
        gs = self.goalies
        if gs is None:
            return
        if t - gs._last_ai < threes.AI_DT:
            gs.update(t)
        else:
            zone = self.arena.zone
            head = None
            if self.play.head is not None:
                Rh, ph = self.play.head
                head = (zone.xz(ph), zone.dir_to_zone(-Rh[:, 2]))
            gs.update(t, zone.xz(blade_world) if blade_world is not None and gripping else None, head)
        if gs.outbox:
            self._drain(t, gs)

    def drop(self, t: float, spot_world) -> None:
        """A puck at rest at a world spot (pushed inside the boards)."""
        zone = self.arena.zone
        x, z = self.arena.keep_on_ice(zone.xz(spot_world), pk.R + 0.05)
        self.play.sim.puck.place(float(x), float(z))
        if self.goalies is not None:
            self.goalies.release()
        self.log.event(t, "puck", at=[round(float(x), 3), round(float(z), 3)])

    def goal(self, t: float, net: str) -> None:
        self.goals[net] += 1
        n = sum(self.goals.values())
        self.voice.say(f"Goal! {n}", key="goal")
        spec = self.play.spec
        self.play.haptics.put((1.0, [spec.top_hand, spec.bottom_hand], 80))
        self.log.event(t, "goal", net=net, goals=dict(self.goals))
        print(f"  goal ({net} net): {n}", flush=True)

    def button(self, name: str, t_sim: float) -> None:
        sandbox.SandboxMode.button(self, name, t_sim)       # X a puck, B the setting, A save the settings

    def draw(self, poses: dict, held: dict, stick, state: int) -> sandbox.Frame:
        line = sandbox.Lines()
        static, static_tris = np.zeros((0, 6), dtype=np.float32), sandbox.NO_TRIS
        if self.arena is not None:
            key = (self.arena, self.play.tuning.values.get("grid", 0) > 0)
            if self._static[0] != key:
                lines = sandbox.Lines()
                ar.markings(self.arena, lines, grid=key[1])
                self._static = (key, lines.tri_array(), lines.array())
            static_tris, static = self._static[1], self._static[2]
        if self.goalies is not None:
            for k in self.goalies.keepers.values():
                figures.goalie(line, self.arena.zone if k.end == "home" else self.arena.far, k.g.c, k.g.facing,
                               down=k.g.mode != "track" or k.hold_since is not None)
        sandbox.draw_puck(line, self.play.sim.puck)
        sandbox.draw_hands_and_stick(line, self.play, poses, held, stick, state)
        return sandbox.Frame(np.vstack([static_tris, line.tri_array()]), np.vstack([static, line.array()]),
                             line.mesh_list())

    def status(self) -> str:
        err = getattr(self.physics, "errors", 0)
        saves = f"  saves {sum(self.goalies.saves.values())}" if self.goalies is not None else ""
        return (f"free skate  puck {self.play.sim.puck.speed:5.1f} m/s  goals {sum(self.goals.values())}{saves}"
                + (f"  ERRORS {err}" if err else ""))

    def meta(self) -> dict:
        v = self.play.tuning.values
        return {"goals": self.goals, "shots_mph": self.physics.shots if self.physics else [],
                "saves": self.goalies.saves if self.goalies is not None else None,
                "rink": self.arena.to_dict() if self.arena else None,
                **{k: v.get(k) for k in ("skate", "turn", "snap", "vignette", "magnet", "release")}}

    def close(self) -> None:
        shots = self.physics.shots if self.physics else []
        print(f"free skate: {sum(self.goals.values())} goals, {len(shots)} shots"
              + (f", hardest {max(shots):.0f} mph" if shots else "")
              + (f", {sum(self.goalies.saves.values())} saves" if self.goalies is not None else ""))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--free", action="store_true", help="free skate: you, a puck and a goalie in each net")
    ap.add_argument("--empty", action="store_true", help="free skate with both nets empty (no goalies)")
    ap.add_argument("--to", type=int, default=5, help="goals to win (default 5)")
    ap.add_argument("--level", type=float, default=1.0, help="the AI: speed, pokes, aim (1 = rec; 0.7 easier)")
    ap.add_argument("--skate", type=float, help="your top speed, m/s at full stick (default: the skate speed setting, 4)")
    ap.add_argument("--turn", type=float, help="your turn speed, deg/s at full stick (default: the turn speed setting, 150)")
    ap.add_argument("--magnet", type=float, default=GAME_MAGNET,
                    help=f"soft hands, 0-1: a puck on your blade rides it while you handle (default {GAME_MAGNET}; 0 = honest physics)")
    ap.add_argument("--release", type=float, default=pk.Params.release,
                    help=f"blade speed (m/s, relative to you) that counts as a shot: the puck comes off as hit (default {pk.Params.release})")
    ap.add_argument("--length", type=float, default=ar.LENGTH, help="rink length, m (regulation 61)")
    ap.add_argument("--height", default="5'8\"")
    ap.add_argument("--shoots", choices=("left", "right"), default="left")
    ap.add_argument("--no-voice", action="store_true")
    ap.add_argument("--no-sound", action="store_true")
    ap.add_argument("--audio-device", default="Oculus", help="part of the output device's name (default: the Quest over Link)")
    ap.add_argument("--notes", default="")
    ap.add_argument("--set", action="append", metavar="KEY=VALUE",
                    help="a setting for this run, e.g. --set push=6 --set glide=1.5 (keys as in sandbox_settings.json)")
    ap.add_argument("--tune", metavar="KEY", help="open the tuning menu on this setting (e.g. push), for an A/B")
    args = ap.parse_args()

    base = stickspec.from_height(stickspec.parse_height(args.height), args.shoots)
    fit = grab.Fit.load(record.FIT_PATH) or grab.Fit()
    values = sandbox.Tuning.defaults(base, fit, pk.Params())
    if sandbox.SETTINGS_PATH.exists():
        values.update(json.loads(sandbox.SETTINGS_PATH.read_text())["values"])
    for key, v in (("skate", args.skate), ("turn", args.turn), ("magnet", args.magnet), ("release", args.release)):
        if v is not None:
            values[key] = v
    sandbox.set_values(values, args.set)
    play = sandbox.Play(sandbox.Tuning(base, values))
    sandbox.tune_first(play.tuning, args.tune)
    base_cls = FreeSkateMode if args.free else GameMode
    mode_cls = type("ThreesMode", (base_cls,), {"to_goals": args.to, "level": args.level, "length": args.length,
                                                "goalie_ends": () if args.empty else ("home", "far")})
    run_dir = HERE / "data" / (("freeskate-" if args.free else "game-") + dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    lock = record.take_lock()
    try:
        sandbox.run(args, play, run_dir, mode_cls)
    except xr.FormFactorUnavailableError:
        raise SystemExit("Headset not connected: put it on, start Link, then run again (xrcheck.py tells you).")
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
