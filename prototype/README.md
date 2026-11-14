# The Python prototype

Everything runs from here (Python, OpenXR via pyopenxr, a Quest 3 on Link):
- **The Spike 0 tracking recorder:** `record.py`, with `analyze.py` reporting on a recording.
- **The free-play [sandbox](#sandbox):** your stick, a puck and a net.
- **The hockey-sense drills:** [retrieval](#drill-scan-retrieve-first-pass) and the
  [power-play point](#drill-the-power-play-point-shoot-or-set-one-up).

You hold a Quest controller in each hand (no physical stick, ever). The stick is virtual:
- **Sized from your height** (`stickspec.py`): length, lie and a curved blade.
- **Fitted once in your right (top) hand** with the thumbstick.
- **Held with the grip buttons** (the middle-finger squeeze), so either hand can hold it.

The recorder's guided session of about 4 minutes records both controllers, their grip buttons
and the headset at about 1 kHz. The sandbox and drills record the same way, plus the puck and
every event.

## The stick

| | default (5'8", left shot) | change with |
|---|---|---|
| length (heel to top of the shaft) | 0.84 x height = **57.1"** (1.45 m) | `--height`, `--stick-length` |
| lie | **5**: shaft 45 deg above the ice (each step about 2 deg more upright) | `--lie` |
| blade | 29 cm heel to toe, 7.5 cm tall, mid-toe curve 1/2" deep (P92-like), mirrored for a right shot | `--shoots` |
| skate height | **off**: the ice is your floor | the "skate height" setting (cm) |

**Your own stick, on skates.** On the ice, skates lift you a few cm, so your hands sit higher over the
ice than they do in the headset standing on your floor. Set "skate height" to your height in skates
minus your height barefoot and the ice drops that far below your floor (eased in over half a second).
Then set the stick length to your real stick's, and you also see the ice from your height on skates.
With it off, a stick a few inches shorter than your own fits instead: about 1.4x the skate height
shorter at lie 5 (6 cm of skates: 8.5 cm, 3.3"). Jon's stick reaches his nose barefoot (about 62"); his saved
length is 58.5" with skate height off.

Sources:
- [CCM size chart](https://www.scheels.com/size-chart/ccm-hockey-sticks-size-chart): a 57" stick for 5'2"-5'10".
- [Bauer size chart](https://www.scheels.com/size-chart/bauer-hockey-sticks-size-chart): measures from the heel's contact point to the top of the shaft.
- [Lie](https://www.hockeystickman.ca/pages/hockey-stick-lie): lie 5 = 135 deg blade to shaft = 45 deg shaft to ice.
- [P92 curve](https://www.stickmeta.com/curve-compare/p88-kane/p92-matthews): a mid-toe curve with a slightly open face, about 3/8"-1/2" deep.

**Fitting it in your hand** (the first run, or `--refit`): the stick appears in your right hand.
- Right thumbstick left/right turns the blade.
- Up/down tilts the stick.
- Hold B and push left/right to swing it sideways.
- Press A to save. The fit goes to `stick_fit.json` and is reused on every run.

**Holding it** (`grab.py`). Each grab gives a short buzz.

| grips pressed | the stick |
|---|---|
| right only | rigid in your right hand, exactly as fitted |
| both | your right hand holds it and sets the blade's turn; your left hand aims the shaft (and can slide along it) |
| left only (top hand off, e.g. angling an attacker on D) | stays in your left hand exactly where it was when you let go with the right |
| none | **never dropped:** it stays in the last hand that held it, exactly where it was (drawn a little dimmer). Squeezing the right grip snaps it back into the fitted hold; squeezing the left alone takes it where it is |

## What it measures

- **held as asked**: whether the grips were pressed the way each step asks.
- **blade height**: the lowest point of the blade above the ice while stickhandling, heads-up and
  one-handed. Nothing holds the blade on the ice but your hands, so this sizes the **ice assist**:
  the report gives the band that holds the blade nine times in ten.
- **jitter**: what a game would have to smooth away (smoothing costs latency).
- **tracking**: per controller, heads-up, one-handed and mid-swing, and how it depends on where
  you look. "Tracked" means the runtime is optically tracking the controller; otherwise it is
  guessing from the motion sensors. Quest's camera-based hand tracking is not used.
- **blade and hand speeds** in shots: how many cm per frame the blade moves, and what physics
  step rate the puck sim needs.

## Setup

1. Wrist straps on. The recorder's shots want about 3 x 3 m clear; the sandbox and drills work
   standing in place.
2. Draw a room-scale boundary. Its floor becomes the virtual ice.
3. Use a Link cable if you have one.
4. A voice guides you through the default Windows audio device. Set the headset (Oculus Virtual
   Audio Device) as default, or keep the PC speakers loud enough to hear.

## Run

```powershell
cd C:\dev\vr-hockey\prototype
uv run python xrcheck.py          # runtime, extensions, and whether the headset is connected
uv run python record.py --notes "Quest 3, cable Link"
```

**Three low beeps = get ready, high beep = go, two falling beeps = stop.** In the headset you see:
- the ice as a grid, green while a step records
- each controller's axes, with a green cross while that hand grips
- the stick: a white shaft and a yellow blade outline

| step | time | what you do |
|---|---|---|
| fit | until you press A | first run or `--refit`: turn and tilt the stick in your right hand until it feels right |
| stickhandle | 30 s | both grips; look at the blade and keep it on the ice, slow then fast |
| heads_up | 30 s | same, looking straight ahead |
| one_hand | 30 s | top hand off: play the stick with your left hand only, like angling an attacker to your left |
| wrist_shots | 40 s | six full-speed wrist shots, both hands |
| slap_shots | 40 s | five full-speed slap shots (`--no-slap` skips them) |

Ctrl+C stops early and keeps what was recorded. `--only stickhandle one_hand` runs only some steps.

Then:

```powershell
uv run python analyze.py data\<timestamp>
```

This writes `data\<timestamp>\report\report.md`, `summary.json` and two plots. Or just tell
Claude the folder name.

## Sandbox

```powershell
uv run python sandbox.py
uv run python sandbox.py --fresh      # start from the defaults, not your saved settings
```

Your stick, a puck and a net, laid out in front of you. Play, and tune everything as you go.

**Controls:**
- **Grip buttons:** hold the stick (as above).
- **Left stick:** move you around the ice (`rig.py`). Forward is where you look; it eases in
  and out, or skates with hockey limits (push, glide, hockey stop, turn limit) if you turn them on
  (below). Full stick is your cruising speed ("skate speed").
- **Left trigger (index finger):** sprint. The harder you squeeze, the faster you go, from your
  cruising speed up to "sprint speed" (default 4.5 m/s; 0 = off). Like a hockey game's speed
  burst, but how hard you squeeze is how fast. You get there at the push limit, and coast back
  down at the glide when you let go.
- **Right trigger (top hand's index finger):** shoot. Released, your hands are soft and give
  with the puck ("stickhandling hands"). Squeeze it and they firm up for a shot ("shooting
  hands"), the harder the firmer.
- **Right stick left/right:** turn you, about your head (not while fitting), smoothly. Set "snap
  turn" (e.g. 30 degrees) to turn in steps instead, one per flick.
- **X:** a new puck, on your blade.
- **Hold the left stick in (1 s):** put the net straight in front of you again.
- **Menu button (left controller, three lines):** the settings menu, in and out. Nothing outside
  it changes or saves a setting, so nothing changes by accident while you play (Jon asked,
  2026-11-13). The left stick stops skating you while it's open. In the menu:
  - **Left stick left/right:** pick a setting. The voice says which, and its value.
  - **Left stick up/down:** change it (hold to keep changing). It takes effect at once.
  - **B:** say the current setting again.
  - **A:** save the settings (`sandbox_settings.json`, used by the drills and the game too).
  - **Y:** fit the stick in your hand. The right stick turns and tilts it; hold B and push to
    swing it; A saves the fit; Y again (or closing the menu) leaves without saving.

Moving needs no play space: stand or sit, and skate with the stick.
- **Sliding** is continuous in time, so the 1 kHz physics sees your blade glide.
- **A snap turn** (or the game's move to a faceoff) is a deliberate jump. The physics doesn't
  sweep the blade across it, and a puck on your blade turns with you.
- **The recording** (`rec.csv`) holds your hands in the world, so replays line up with the puck.

**Settings** (any of them for one run: `--set KEY=VALUE`, e.g. `--set push=6 --set glide=1.5`; the
keys are those in `sandbox_settings.json`):
- stick length, lie, curve depth, face open, flex
- forgiveness (extra reach for catching the puck)
- puck weight
- **The puck** (`reports/Hockey physics feel.md` has the evidence):
  - ice friction: default 0.085. The one on-ice measurement found 0.07-0.12.
  - air drag (`air`): default 4.3 per km (`Params.air_k` 0.0043 per m), 0 = off. It equals the
    ice's friction at about 14 m/s, so hard passes and shots slow down; stickhandling doesn't
    change.
  - board bounce (`boards`): default 0.30, for the boards, glass and posts. A frozen puck off a
    rigid plate measured 0.26; the old 0.55 sent rebounds back to the slot.
  - stickhandling hands (`handle`) and shooting hands (`hands`): the stick's damping, which sets
    how hard a puck springs off the blade; higher gives a softer catch. With the right trigger
    released your hands are soft (default 1.50). Squeeze it and they firm up toward the shooting
    hands (default 0.60) for a shot, the harder the firmer. On a synthetic blade, a 4 m/s pass into
    a still blade comes back at 0% of its speed with soft hands and 11% with firm ones. A tap sends
    the puck off at 87% of the blade's speed against 98%. A wrist shot with soft hands is about 5%
    slower. `handle` 0 = off (always the shooting hands, as before). This replaces "blade pop",
    which did nothing measurable (the restitution is now the measured 0.30 and not a setting). The
    low-speed bounce fade is gone: rubber bounces more at low speed, not less.
- blade grip, buzz strength
- skate speed (default 3 m/s), snap turn (default 0 = smooth; 30 turns in 30-degree steps) and smooth turn speed
  (default 150 deg/s): the thumbsticks, everywhere
- **The skating model** (`rig.Drive`): push (6 m/s²), glide (1.5), the hockey stop (8) and the
  turn limit (6) are on; the others are off by default.
  Try them one at a time, in this order, with the comfort check on:
  - push (`push`, m/s²): speed up at most this hard, easing in at the top, half as hard
    backwards; with no glide, letting go slows you at this rate too. 6 is a rec skater's first
    strides (95% of 3 m/s in about 0.55 s). Off, the old easing starts and stops every move at
    20 m/s² and more (2 g). In the first A/B (free skate, 2026-11-09), push 6 "was solid" and 6-10
    felt fine at 3 and at 4 m/s; with it off Jon was sick within seconds. In the motion log, push
    6-10 never went over 11 m/s² (5% of the time over 6); off, the worst 5% were over 30 and
    the peak was 47.
  - glide (`glide`, m/s²): let go of the stick, or ease off it, and you coast, slowing at this
    rate. 1.5 (2 s and 3 m from 3 m/s) "felt good"; try 1.0, then 0.5 on later days. Off, letting
    go stops you at the push rate. In the rink, the boards stop a glide gently.
  - hockey stop (`stop`, m/s²): hold the left stick more than 120° against your motion to stop
    at this rate, then push the new way. 8 "felt good" (6 is gentler). The vignette stays closed
    through it.
  - turn limit (`carve`, m/s²): your path can't bend harder than this sideways. A glance doesn't
    whip it round, the right stick's turn is capped at speed (115°/s at 3 m/s for 6), and turning
    carves your path with you. 6 "felt good" (free skate, 2026-11-10). 9, which doesn't cap the
    turn at 3 m/s, left Jon "a little motion sick" after 16 minutes; the session's length wasn't
    ruled out.
  - backward and sideways speed (`back`, `side`): a share of forwards. Try 0.8 and 0.5.
- comfort vignette (default 0.7): the view's edges darken while the thumbsticks move you (0 = off)
- ice grid (`grid`, default off; 1 = on): the old 2 m grid on the ice. A real rink has none, and
  every line sliding by under you is motion your inner ear doesn't feel.
- your skates (`feet`, default off; 1 = on): Jon's custom roller skates under you, where your feet
  would be (nothing tracks them): under your neck, hip width apart. They stay put while you lean or
  glance round, step after you once your head is 25 cm away, come round once it's turned 35°, and
  slide and turn with the thumbsticks exactly. Off until tried: legs that move on their own could
  bother a queasy stomach. The skates' wheels put the bottom of your foot 9.3 cm up, so with them on,
  "skate height" 9 puts the ice where they stand.

**The skates.** Every skater wears Jon's custom roller skate from the custom-skate project next door
(`gear.py`): its 3D viewer build (`../../custom-skate/out/boot_roller/viewer`, or `VR_HOCKEY_SKATES`
for another `out` folder), each part cut to a few thousand triangles (about 23,000 a skate), in his
colourway, cached in `gear_cache/` (not in git: a boot built on his own foot scan carries its shape).
They turn out and tip onto their inside edges as a skater pushes. Without the build there, skaters
get a line for each blade, as before. `gear.KIND = "ice"` puts them on the ice skate instead.
- comfort check (`check`, default every 4 min; 0 = off): the voice asks how you feel. Press A if
  you feel fine, B if you're a bit queasy, Y if you need a break (Y says to take the headset off;
  not X, which is a new puck).
  They're logged as 0, 2 and 5 out of 10. A 0-10 count on the left stick was tried first and was
  too fiddly to answer in the headset. Every frame of the thumbsticks' motion goes to `rig.csv`,
  and a summary to `meta.json` (`comfort`).
- AI reaction time (`react`, default 0.18 s; 0 = off, everyone at once as before): in the 3v3, when
  the puck changes hands each AI skater keeps going where he was going until he's taken it in:
  this, plus a random tail (about 0.1 s), plus 0.1 s with the puck off to his side or 0.3 s with it
  behind him. Steps of 0.06 s, so three presses turn it off for an A/B.
- ice assist (default 16 cm; 0 = off): a blade within this of the ice rests on it, everywhere.
  Nothing stops your hands at the ice, so you can't feel it. In the first free skate the blade
  hovered 2.5-30 cm up, and the puck slid under it at 70% of its crossings. From 16 to 32 cm the
  blade rises back to your hands, smoothly, so the physics never sees a jump. Higher, it's where
  you hold it. To hop the blade over the puck, lift your hands about the band. It's the last
  setting: one push left from the first.
- soft hands and shot release: off (honest physics), everywhere by default

**What you hear and feel:**
- **Sounds:** a tap when the blade lands, a dull "thock" off the puck, a ping off the posts, a
  thud off the boards. Every contact gets its own sound, from the contact bus (`contacts.py`),
  mixed (`audio.py`) straight to the headset's Link audio. The voice plays there too, rendered to
  samples and mixed in (Windows' default output can be a monitor with headphones on a cable too
  short to play in; Jon missed every comfort check that way, 2026-11-13).
  - About 23 ms after the contact, the same every time.
  - Up to 16 at once, 5 variants of each, and louder for harder hits.
  - `--audio-device` picks another output; with no device it falls back to winsound.
- **Buzz:** every puck contact buzzes the hands holding the stick, harder hits for longer.

The voice calls each shot's speed in mph.

## Drill: scan, retrieve, first pass

```powershell
uv run python drill.py
```

**Setup:** face a clear direction in your play space; that becomes the end boards. Put your blade on
the ice and press A. The zone is laid out so your blade sits at the end boards, just left of our net.

**Each rep:**
1. A puck is dumped in down the far wall and rims around toward you from your left.
   - **Rim assist:** boards in VR have no feel, so as the puck leaves the corner it is steered gently
     off the boards to where your blade is (at most 1 m out), as if it had kicked off the corner.
2. F1 commits about 1.5 s before it reaches you. He comes down your wall, chases the puck around
   the net, or comes down the middle. F2 takes away one of your three outs:
   - up the wall to your winger
   - a reverse behind the net to your D partner
   - up the middle to your center
3. Only a shoulder check after F1 commits shows which out is open. Pass to it with your stick.

**After each rep:**
- **The voice gives:** the result, the open out, and whether you checked (none, or too early).
- **A green line on the ice:** the best pass.
- **A map at waist height:** green is the best pass, white is the puck's path, orange is where the
  forecheckers went.

**Scoring and difficulty:**
- Every out is scored by time to intercept: could a forechecker get a stick on the lane, or reach
  the receiver, before the puck?
- **Valued for your passing:** every out is valued at your own pass speed and your own time from
  control to release. These are medians of your last 20 passes, ignoring fans and glitches.
- Each out is the best one equally often.
- **F1's head start adapts** toward about 75% success.
- **Warm-up:** the first 5 reps of each session don't move the difficulty.
- **Saved between sessions:** both the head start and your passing (`drill_state.json`).
- **Reps start only while you grip the stick** and the drill is in front in the headset. A let-go
  stick stays in your hand, but that doesn't count as playing.

**Controls:**
- **A:** next rep now
- **B:** repeat the result
- **X:** skip the rep
- **Hold the left stick in (1 s):** lay the zone out again

The grips, moving and turning, Y fitting and left-stick tuning work as in the sandbox.

## Drill: the power-play point (shoot, or set one up)

```powershell
uv run python drill.py --drill pp
```

**Setup:** face where you want the net and press A. Your blade becomes the left point.

**Each rep:**
1. Your winger on the left half wall passes the puck up to you.
2. While it travels, the penalty-kill box commits:
   - **F1** pressures you, which closes your shooting lane but opens the seam. Or he shades the
     seam, which leaves your lane open.
   - **F2** takes away D-to-D, or drops into the seam.
   - **D1** boxes out your screen, standing in your lane. Or he plays beside your screen.
   - **D2** steps up on your seam shooter, or stays home.
3. Pick your play:
   - **Shoot:** your own shot, through the screen.
   - **D-to-D:** your partner's one-timer from the right point.
   - **The seam:** a hard pass across the box to your shooter in the far circle.

**The goalie** (`goalie.py`) is a rec goalie:
- He plays his angle and follows the puck a beat late.
- A screen means he picks up a shot only about 9 m out.
- He slides across on passes and makes saves in the butterfly. His reach has a soft edge, so it's
  never quite all or nothing.

**Scoring and difficulty:**
- Every play is valued in expected goals with that same goalie: can the pass get there, can the
  shot get through the box, and does it beat him?
- Goals are real. Your actual shot, or your teammate's one-timer, has to beat the goalie and get
  into the net.
- **Learns you:** your power-play pass speed and shot speed are learned separately from the
  retrieval drill's.
- **Pressure** is how soon F1 reaches you. It adapts, with the same warm-up.
- **The map** shows each play's goal chance as a bar; green is the best.

## Game: 3 on 3

```powershell
uv run python game.py                     # first to 5
uv run python game.py --to 3 --level 0.8  # shorter, against a slower team
uv run python game.py --skate 3.5         # your top speed (m/s at full stick; default 4)
uv run python game.py --free              # free skate: you, a puck and a goalie in each net
uv run python game.py --free --empty      # ... with both nets empty
```

**Free skate** (`--free`) is the same rink with no skaters but you, for getting used to skating
with the thumbsticks:
- A goalie in each net (`threes.Goalies`, the game's goalies on their own). He saves what he gets
  a piece of, either as a rebound or by covering it. He covers a slow puck at his feet, then
  passes it back out to your blade. A puck through him in close is checked even on your stick,
  so go round him or shoot.
- Soft hands are off, as in the game.
- Shot speeds and goals are called out, and after a goal a puck comes back to your stick.
- The buttons do what they do in the sandbox: X puts a puck on your stick, and the menu button
  opens the settings (A in the menu saves them, the comfort ones too, and the game uses them).

You and two AI teammates (blue) against three (orange), with a goalie in each net, on a whole rink:
- **The rink** (`arena.py`): regulation width, corners and nets, 46 m long (regulation is 61:
  `--length`).
- **No offside or icing.** The score hangs over centre ice.

**Playing it:**
- You start at centre ice, facing the net you attack. Your goalie is behind you.
- Press A to drop the puck. After a goal, everyone lines up at centre again, and you're moved
  there.
- Skate with the left stick and turn with the right. Your stick is the real physics stick.
- **Soft hands** are off: honest physics, as everywhere. With the ice assist that felt right. On,
  their pull within 4 cm of the blade felt like a magnetic field. `--magnet 0.7` turns them on:
  - While your blade moves at handling speed, a puck on it rides the blade instead of flying off.
  - Swing faster than the shot release speed (`--release`, default 4 m/s) and it comes off as
    hit. Skating doesn't count: speeds are taken relative to you.
  - It is `physics_core.cradle`, inside the 1 kHz step, so it adds no delay.
- **The other team is never faster than 95% of your skate speed** (they were skating 5.8 m/s to
  your 4).
- Your teammates pass to you when you're open (a pass is led to your blade).
- The other team marks you goal side and pokes at the puck while you carry it.
- To get the puck back, get your stick on it or skate into their carrier. His puck rides on the
  blade you see, just off his forehand, and any touch of your blade knocks it loose.

**The AI** (`threes.py`) ticks 50 times a second:
- **The carrier** skates for the slot, away from defenders. Every quarter second or so he shoots,
  passes to the most dangerous open teammate (you included), or keeps going. Shots are valued with
  the goalie model, against the real goalie.
- **His teammates** take the back door and the high slot, and keep their spots unless swapping
  saves a fifth of the skating.
- **The other team** marks man to man, goal side. Whoever has the carrier pressures him. Each picks
  up the nearest man when the puck changes sides, then keeps him; two swap only when their men cross.
- **A loose puck:** each team's quickest skater goes for it (not your teammates, if you're closer),
  and keeps going unless a teammate would get there 0.2 s sooner.
- **No snap decisions:** sides change 1.25 m past the middle of the rink, not at it, and any jump in
  where a skater is going is blended out over about a quarter second.
- **Reactions:** when the puck changes hands, each skater reacts after his own reaction time
  (median about 0.3 s, longer if the puck was behind him). The new carrier, whoever made the play
  and a pass's receiver go at once. The "AI reaction time" setting, 0 = everyone at once.
- **The goalies** are the drills' rec goalie, one per end. After a save there's a rebound, or he
  covers it and plays it out a second later.
- **AI against AI** (no you): about 1.4 goals a minute and 28% shooting. Shots are even between the
  teams over 16 games.

**Measuring the AI** (`selfplay_metrics.py`, from reports/Lifelike AI players.md): every game
records the AI 50 times a second in `ai.csv` (the skaters, the puck, you) and its takes, passes,
shots and losses in `events.jsonl`. The script scores a game against the report's table (baseline,
now, target), or plays the AI against itself and scores that:

```
uv run python selfplay_metrics.py                          # 4 self-play games of 600 s (about a minute)
uv run python selfplay_metrics.py --set CARRY=0.85         # an A/B: one of threes.py's constants changed
uv run python selfplay_metrics.py data/game-<timestamp>    # a game you played
```

**Controls:**
- **A:** drop the puck (a new game when one is over)
- **B:** say the score
- **X:** faceoff at centre now
- **Hold the left stick in (1 s):** lay the rink out around you again (the score stays)

The grips, moving and turning, Y fitting and left-stick tuning work as in the sandbox.

## Findings so far

Run 1 (2026-11-07, Quest 3 on cable Link):
- Controller tracking held 100% heads-up and through every wrist and slap shot.
- Jitter was about 0.5-1 mm.
- The runtime gives a fresh pose on about 900 of every 1000 queries.
- It also freezes a controller's pose a few seconds after it is set down, so a "controllers lying
  still" noise test doesn't work.

That run (and the cancelled run 2) used an earlier stick fitted to a still stance. It was rejected
on feel: the blade's rotation was off. So the analysis gives those recordings a tracking-only report.

**Sandbox:** 5 sessions on 2026-11-07, tuned live. Each fix answered what Jon felt:
- A real blade curve.
- Shaft flex "with forgiveness like golf clubs".
- Ice sounds ("way better with the sounds").
- The blade kept on top of the ice.
- Consistent grips.
- No more exploding puck: the ice no longer loads the flex.
- "A rubber heavy puck against a light flexible composite stick" instead of an air-hockey puck.

**Retrieval drill:**

| | reps | success | good reads | note |
|---|---|---|---|---|
| Session 1 | 57 | 31% | 46% | Most misses were rims along the boards that never touched the blade. The winger stood off the wall. |
| Session 2 | 118 | 59% | 71% | After the fixes: rim assist, winger on the wall, his own pass speed, warm-up. The free time reached 1.35 s. |

**Power-play drill, session 1:** 138 reps, 0 goals.
- 20% of incoming passes not controlled.
- 8 of 17 shots wide.
- All 6 seam passes picked off.

Next: tuning, after the feel research (`../reports/`).

**Physics rate:** the 1 kHz physics shares Python's GIL with drawing and building reps.
- Session 1: 902/s.
- Session 2: 752/s, after a too-short GIL switch interval (reverted).
- Power-play session: about 920/s.
- Off the headset, a contention harness measures 999/s.
- **Since the compiled physics** (`physics_core.py`, numba with nogil):
  - A tick costs 144 us instead of 549.
  - 60 s of real play gives the same 222 touches and identical puck paths.
  - The harness, with drawing, rep building and the headset audio stream all running, holds
    1000/s with 0 audio underruns.

## Files

| file | what |
|---|---|
| `record.py` | OpenXR recorder (pyopenxr + OpenGL). A sampler thread locates both controllers and the head at a fixed rate; the main thread reads the inputs, runs the grab rules and renders; a protocol thread runs the voice and steps |
| `stickspec.py` | the stick sized from height, lie and shot side |
| `grab.py` | the fit in the hand and the grab rules, live (one sample) and replayed (whole recording) |
| `analyze.py` | replays the grips, then metrics, verdict, `report.md`, plots |
| `protocol.py` | the steps and what the voice says |
| `recfmt.py` | the `rec.csv` / `meta.json` format |
| `synth.py` | synthetic recordings with known truth (noise, drift, dropouts, 500 Hz updates, top hand off) |
| `xrcheck.py` | runtime and headset check |
| `sandbox.py` | free play: the stick, a puck and a net, with settings tuned in the headset; its physics tick, drawing and frame loop are reused by the drills |
| `puck.py` | the puck, the blade contact, the shaft flex, the ice (the Python reference; `FAST` runs it compiled) |
| `physics_core.py` | the same physics compiled with numba (nogil): what the app runs; tested against `puck.py` to 1e-9. Also soft hands (`cradle`, off unless `Params.magnet`; the reference runs the same function uncompiled) |
| `contacts.py` | the contact bus: every contact from the 1 kHz physics, which the sound and the buzz play from |
| `audio.py` | the mixer: a low-latency stream to the headset, each contact placed at its own sample |
| `sounds.py` | the synthesized sounds (tap, thock, ping, thud, go, whistle) |
| `stickmath.py` | rotations and quaternions |
| `rig.py` | thumbstick locomotion: where the room sits in the world, moved continuously in time so the physics never sees a jump |
| `replay.py`, `touches.py` | replay a recorded session's hands through the physics; measure every blade-puck touch (does the puck leave faster than the blade?) |
| `session_replay.py` | replay a whole session (free skate, game or sandbox) through today's physics and check how the puck leaves the blade against `reports/Shot release.md`'s targets: shot speeds, launches, lift-offs after a press. `--set ease_off=0` or `--window 0.004` compare with and without a change |
| `shotcall.py` | calling a shot's speed from the puck's free flight, the same in the game and every replay |
| `drill.py` | the drill app (a sandbox mode): lays out the zone, runs reps, draws the skaters and the after-rep map |
| `retrieval.py` | module 1's logic, without XR: scenarios, the time-to-intercept value model, forecheckers, shoulder-check tracking, scoring, the staircase |
| `zone.py` | the defensive zone: regulation boards with rounded corners (rims), our net, markings |
| `figures.py` | line-drawn skaters and the goalie |
| `powerplay.py` | the power-play drill's logic: the box's reads, expected goals per play, the rep with real shots and one-timers |
| `goalie.py` | a rec goalie: angle, screens, saves, and expected goals from the same model |
| `game.py` | the 3-on-3 app (a sandbox mode): lays out the rink, runs the game, draws the skaters, goalies and score; `--free` for free skate on the same rink |
| `threes.py` | the 3-on-3 game's logic, without XR: possession, the AI's choices and positions, both goalies, faceoffs, goals; its log (`ai.csv`) |
| `selfplay_metrics.py` | the AI in numbers: self-play or a recorded game, scored against reports/Lifelike AI players.md |
| `arena.py` | the whole rink: both ends from zone.py (the far one turned round), its puck (both nets), markings, the scoreboard |
| `theme.py` | the look: a white rink aboard a mothership. Solid ice, boards, painted lines, the hull and a ring of light overhead, as triangles under the line drawing; the palette, given as the colours the headset shows |
| `tests/` | `uv run pytest`. They cover: the grab rules, exact and live = replay; the analysis recovering the synthetic truth; the puck physics; the zone (rims, our net); both drills driven by a bot; the goalie and expected goals; the skater drawing; the whole rink's puck (compiled = reference); the 3-on-3 played by the AI (a puck behind the net gets dug out; the carried puck on the drawn blade; your touch knocks it loose; staggered reactions to a pass; jumps blended out, marks held, sides past the middle), its log and metrics, and its app run headless; free skate and its goalies; thumbstick moves without jumps, the teleport, and the skating limits (push, glide, hockey stop, turn limit); the ice assist; air drag against its closed forms; the comfort check and the boards stopping you |
