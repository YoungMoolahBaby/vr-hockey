"""AI tick cost on the unmodified Game (no wrappers): you_ms 3.0, AI only. Run from prototype/."""
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "tests")
import numpy as np  # noqa: E402

from test_threes import make  # noqa: E402

costs, phys = [], []
for seed in (0, 1):
    sim, g = make(seed=seed, to_goals=99)
    g.you_ms = 3.0
    g.start()
    last = -1.0
    for i in range(120_000):
        t = i * 0.001
        a = time.perf_counter()
        sim.step(0.001, None, None)
        b = time.perf_counter()
        sim.puck.events.clear()
        g.update(t, None, None)
        c = time.perf_counter()
        g.outbox.clear()
        phys.append(b - a)
        if g._last_ai != last:
            last = g._last_ai
            if g.state == "live":
                costs.append(c - b)
costs = np.array(costs) * 1000
print(f"AI tick (live): mean {costs.mean():.2f} ms, median {np.median(costs):.2f}, p99 {np.percentile(costs, 99):.2f};"
      f" at 50 Hz that is {costs.mean() * 50 / 10:.1f}% of a core")
print(f"puck sim.step with no blade: mean {np.mean(phys) * 1e6:.1f} us")
