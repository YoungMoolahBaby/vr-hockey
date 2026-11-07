"""The guided Spike 0 session (controllers in hand, no physical stick)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Phase:
    name: str
    seconds: float
    say: str
    optional: bool = False


PHASES = (
    Phase("stance", 10,
          "Stance. Hold the controllers exactly like you hold your stick, in your normal stance, "
          "with the blade on the ice. You will not see a stick yet. Hold still."),
    Phase("rest", 15,
          "Stillness test. Put both controllers down on a table or a chair so they lie completely still. "
          "Look at them until you hear the stop sound."),
    Phase("stickhandle", 30,
          "Stickhandling. Pick the controllers up, look down at the blade, and keep it on the ice. "
          "Move it side to side, slow at first, then faster."),
    Phase("heads_up", 30,
          "Heads up. Same stickhandling, but look straight ahead, not at the stick."),
    Phase("wrist_shots", 40,
          "Wrist shots. Take six wrist shots at full speed. Pause and reset after each one."),
    Phase("slap_shots", 40,
          "Slap shots. Take five slap shots at full speed, pausing between each. Keep the wrist straps on.",
          optional=True),
)

CALIBRATION = "stance"


def select(skip_optional: bool = False, only: list[str] | None = None) -> list[Phase]:
    phases = [p for p in PHASES if not (skip_optional and p.optional)]
    if only:
        names = {p.name for p in PHASES}
        unknown = [n for n in only if n not in names]
        if unknown:
            raise SystemExit(f"unknown phase(s): {unknown}; known: {sorted(names)}")
        phases = [p for p in PHASES if p.name in only]
    return phases
