"""The guided Spike 0 session (controllers in hand, grip buttons hold the virtual stick)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Phase:
    name: str
    seconds: float
    say: str
    optional: bool = False


FIT_SAY = ("Stick fitting. The stick is in your right hand. Push the right thumbstick left and right to turn "
           "the blade, up and down to tilt the stick. Hold B and push left or right to swing it sideways. "
           "Press A when it feels right.")

PHASES = (
    Phase("stickhandle", 30,
          "Stickhandling. Squeeze both grip buttons to hold the stick. Look down at the blade and keep it on "
          "the ice. Slow at first, then faster."),
    Phase("heads_up", 30,
          "Heads up. Same stickhandling, but look straight ahead, not at the stick."),
    Phase("one_hand", 30,
          "Top hand off. Let go with your right hand and play the stick with your left hand only, like "
          "angling an attacker to your left. Grab the top again after the stop sound."),
    Phase("wrist_shots", 40,
          "Wrist shots, both hands on the stick. Take six at full speed. Pause and reset after each one."),
    Phase("slap_shots", 40,
          "Slap shots. Take five at full speed, pausing between each. Keep the wrist straps on.",
          optional=True),
)


def select(skip_optional: bool = False, only: list[str] | None = None) -> list[Phase]:
    phases = [p for p in PHASES if not (skip_optional and p.optional)]
    if only:
        names = {p.name for p in PHASES}
        unknown = [n for n in only if n not in names]
        if unknown:
            raise SystemExit(f"unknown phase(s): {unknown}; known: {sorted(names)}")
        phases = [p for p in PHASES if p.name in only]
    return phases
