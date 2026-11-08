"""Contact events: one stream from the 1 kHz physics that the sound and the buzz both play from
(reports/VR hockey stick and puck feel.md, build step 1).

Every contact is published the tick it happens, stamped with time.perf_counter(), and never
merged with others: the audio mixer places each one at its own sample. Consumers subscribe and
get their own queue (collections.deque: append and popleft are thread-safe in CPython).

kinds:
    puck     the blade hits the puck. speed: the puck's change of speed (m/s); slide: how fast
             it slid along the face; where: heel (0) to toe (1)
    ice      the blade lands on the ice. speed: how fast it came down (m/s)
    post, boards, net, goal, cleared
             the puck against the rink. speed: the puck's speed (m/s)
The blade dragging on the ice is a continuous state, not an event: Bus.scrape.
"""

from __future__ import annotations

import collections
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Contact:
    t: float                     # time.perf_counter() when it happened
    kind: str
    speed: float
    slide: float = 0.0
    where: float = 0.5
    hands: tuple = ()            # the controllers holding the stick ("l", "r")


class Bus:
    def __init__(self):
        self._subs: list[collections.deque] = []
        self.scrape = (0.0, 0.0)     # the blade on the ice now: (press depth m, speed along the ice m/s)
        self.published = 0

    def subscribe(self, maxlen: int = 512) -> collections.deque:
        q: collections.deque = collections.deque(maxlen=maxlen)
        self._subs.append(q)
        return q

    def publish(self, c: Contact) -> None:
        self.published += 1
        for q in self._subs:
            q.append(c)
