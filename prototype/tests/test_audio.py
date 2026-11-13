"""The mixer, driven by a simulated stream clock (no sound card needed)."""

import numpy as np
import pytest

import audio
from contacts import Bus, Contact


def run_blocks(mx, n_blocks, events, lead=0.010, offset=100.0, block=audio.BLOCK, rate=audio.RATE):
    """Call fill() like the stream would. events: [(perf time, Contact or ('ui', name))].
    The stream clock is perf time - offset; each block is heard `lead` after its callback."""
    out = []
    pending = sorted(events, key=lambda e: e[0])
    cur = 0.0
    for _ in range(n_blocks):
        perf = cur + offset
        while pending and pending[0][0] <= perf:
            t, e = pending.pop(0)
            if isinstance(e, Contact):
                mx.q.append(e)
            else:
                mx.play(e[1], 1.0, t)
        out.append(mx.fill(block, cur, cur + lead, perf))
        cur += block / rate
    return np.concatenate(out)


def onsets(x, thresh=1e-4, gap=600):
    idx = np.flatnonzero(np.abs(x) > thresh)
    starts = [idx[0]] if len(idx) else []
    for a, b in zip(idx, idx[1:]):
        if b - a > gap:
            starts.append(b)
    return starts


def test_every_contact_sounds_the_same_delay_after_it_happened():
    mx = audio.Mixer(Bus())
    rate, offset = audio.RATE, 100.0
    times = [offset + 0.050 + k * 0.137 + (k * 0.0013) for k in range(8)]   # all over the blocks
    out = run_blocks(mx, 300, [(t, Contact(t, "puck", 5.0)) for t in times])
    got = onsets(out)
    assert len(got) == len(times)
    lead = 0.010                                                  # each block is heard this long after it is written
    delays = [s / rate + lead - (t - offset) for s, t in zip(got, times)]
    assert max(delays) - min(delays) < 2.5 / rate, delays          # constant: no jitter
    assert abs(np.mean(delays) - mx.delay) < 2.5 / rate            # exactly the delay the mixer reports
    assert mx.delay < 0.042                                       # inside the ~42 ms people don't notice
    assert mx.stats["late"] == 0


def test_overlapping_contacts_both_sound_and_the_limiter_holds():
    mx = audio.Mixer(Bus())
    t0 = 100.05
    evs = [(t0, Contact(t0, "puck", 8.0)), (t0 + 0.001, Contact(t0 + 0.001, "ice", 2.0)),
           (t0 + 0.0015, Contact(t0 + 0.0015, "boards", 12.0))]
    out = run_blocks(mx, 60, evs)
    assert mx.stats["played"] == 3 and mx.stats["dropped"] == 0
    assert np.max(np.abs(out)) <= 1.0


def test_too_many_at_once_drops_the_quietest():
    mx = audio.Mixer(Bus())
    t0 = 100.05
    evs = [(t0, Contact(t0, "puck", 0.4 + 0.25 * k)) for k in range(30)]
    run_blocks(mx, 20, evs)
    assert len(mx.voices) <= audio.MAX_VOICES
    assert mx.stats["dropped"] >= 30 - audio.MAX_VOICES


def test_sounds_by_name_and_silence_below_the_thresholds():
    assert audio.gain_for(Contact(0, "puck", 0.2)) is None
    assert audio.gain_for(Contact(0, "ice", 0.1)) is None
    assert audio.gain_for(Contact(0, "goal", 30.0)) is None
    soft, hard = audio.gain_for(Contact(0, "puck", 1.0)), audio.gain_for(Contact(0, "puck", 8.0))
    assert soft[0] == hard[0] == "clack" and soft[1] < hard[1] == 1.0
    mx = audio.Mixer(None)
    out = run_blocks(mx, 40, [(100.05, ("ui", "go"))])
    assert len(onsets(out)) >= 1


@pytest.mark.parametrize("kind", audio.KINDS)
def test_variants_differ_but_stay_the_same_sound(kind):
    vs = audio.bank()[kind]
    assert all(np.max(np.abs(v)) == pytest.approx(1.0, abs=1e-6) for v in vs)
    if len(vs) > 1:
        assert len({len(v) for v in vs}) > 1 or not np.allclose(vs[0], vs[1])


def test_a_spoken_line_plays_whole_on_the_mixer_and_a_pile_of_hits_cant_drop_it():
    mx = audio.Mixer(Bus())
    line = (0.5 * np.sin(2 * np.pi * 220 * np.arange(int(1.5 * audio.RATE)) / audio.RATE)).astype(np.float32)
    mx.speak(line)
    hits = [(100.0 + 0.2 + 0.005 * i, Contact(kind="puck", t=100.0 + 0.2 + 0.005 * i, speed=8.0)) for i in range(40)]
    n = int(1.6 * audio.RATE / audio.BLOCK) + 1
    out = run_blocks(mx, n, hits)
    assert np.abs(out[:2 * audio.BLOCK]).max() > 0.1              # starts at once
    assert mx.stats["dropped"] > 0                                # the hits did overflow the voices...
    played = out
    tail = played[int(1.0 * audio.RATE):int(1.45 * audio.RATE)]   # ...but the line is still there at the end
    assert np.abs(tail).max() > 0.2
    assert np.abs(played[int(1.55 * audio.RATE):]).max() < 0.05   # and then it's over
