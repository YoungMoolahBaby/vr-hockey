# Making AI players feel like people: game-AI craft and presence in VR

Research round "Lifelike AI players", 2026-11-13.

Topic: what makes AI teammates and opponents read as people rather than bots, in games generally and in VR in particular: perception and imperfection, commitment, individuality, difficulty, presence (gaze, contingency, intent, voice, personal space, comfort), architecture and testing. How `threes.py` measures up.

Tags: **[M]** measured in the cited study. **[D]** derived by me (arithmetic shown, or my own measurement of the sim). **[E]** estimate or model output, assumptions stated. **[V]** vendor claim, developer talk or postmortem, coaching text, scouting or anecdote. **[S]** secondary (read in a source that cites the primary).

Builds on, and does not repeat: `reports/VR hockey sense training.md` (believable opponents need honest kinematics; scripted plays plus a reactive rule layer), `VR hockey sense training/simulation_and_scoring.md` (ghosting, point-light fidelity, the rink-control model), `reports/Hockey physics feel.md` item 11 (AI skaters on Jon's skating model). The sibling note in this round, `elite skating and body motion.md`, covers how the bodies move: pace, stops, backward skating, gait, a head that leads turns and quick checks, steady targets and soft avoidance. This note covers why the AI looks where it looks, when it reacts, what it decides, what it says, and how Jon can tell whether a change made it more human.

**My self-play measurements [D].** Two AI-only games of 10 minutes (seeds 1 and 2), `level` 1, the AI's top speed capped as in the headset at 0.95 × Jon's skate setting of 3 m/s (2.85 m/s). 547-556 s of live play each. I logged every 50 Hz AI tick: each skater's position, velocity, facing, target, mark, the holder and the puck. No code or tracked file was changed. Scripts and outputs: `C:\Users\jhill\AppData\Local\Temp\claude\d5760a1e5391f178\c9432537-7115-4ab8-897a-637cb1235a5b\scratchpad\ai-round\presence\` (`measure.py`, `analyze.py`, `jumps.py`, `react2.py`, `cost.py`).

## Bottom line

1. **The loudest robotic tell is timing: everyone reacts at once, instantly.** After a change of possession, 96-97% of the AI's target changes happen on the very next AI tick (about 21 ms), and 76-77% of skaters start pushing in a new direction within 40 ms [D]. *Corrected in fact-check:* the 76-77% is a share of the skaters who were already pushing and whose push turned more than 45° within 1 s (about 60% of skater-events), not of all skaters; a re-run gives 76-79% within two AI ticks (about 42 ms) [D]. People need about 0.2 s to react to an expected visual signal and about 0.4 s when they must first tell two signals apart [S]; Olympic sprinters' best reactions to the gun averaged 166 ms [M]. Expert defenders facing VR rugby side-steps waited longer than novices (268 against 193 ms) and so bit on fakes far less (14% against 42% early wrong-way moves) [M]. The fix is a staggered, per-skater perception delay of roughly 0.2-0.45 s, shorter when the event is in front of him and expected [E].
2. **Delays and errors must be legible, or they read as bugs.** Halo's designers added a short pause before enemies recognised the player; playtesters "assumed this Feature was a Bug" and said it made the AI look dumb, so it was removed [V]. A delay works only if the figure shows its cause: a head that is turned away, then snaps to the puck [E]. Game AI books say the same about misses: a deliberate miss must look like a near miss the player can see [V].
3. **The AI is omniscient and never looks.** Every decision uses every player's true position, whichever way the skater faces. Off the puck, a skater has the puck behind him (more than 90° off his facing) 15-17% of the time, yet reacts to it on the next tick [D]. Acting on things not looked at gave Unreal Tournament bots away [S]. A field of view, a remembered picture of the play, and a head that turns to refresh it would make what the AI knows match what Jon sees it see [E].
4. **The AI dithers; people commit.** During loose pucks each team's chaser changes about 5 times a minute, and 39-42% of those changes flip back within 1 s. Defenders change marks 9 times a minute while defending a carrier [D]. In a judged Unreal Tournament contest, bots that went "back and forth" became recognisable after about 3 minutes [M]. *Corrected in fact-check:* this was the organisers' observation during the qualifying rounds ("repetitive and predictable behaviour after 3 minutes, such as going back and forth"), used to set the match length; it is not a judged or measured result, so read it as [V]. UT^2, a 2012 BotPrize winner, was built to copy how people "tenaciously pursue specific opponents without regard for optimality", as with a grudge [V]. It was judged human about 52% of the time, against 40% for the human players [M].
5. **Teammates should talk, briefly, about what Jon cannot see.** In football pairs, 77% of what players said during play was orienting talk (what to do, where, when), usually one or two words [M]. *Corrected in fact-check:* the 77% is [M]; "one or two words" is earlier work the authors cite, so [S]. F.E.A.R.'s developers found that squad coordination was invisible until the AI said it out loud [V]. *Corrected in fact-check:* Orkin argues there is "no point" in squad behaviour the player cannot see and uses dialogue "to cue the player in to the fact that the coordination is intentional"; he does not report testing that it was invisible without the lines [V]. The Last of Us's companion calls out threats the player has not seen [V]. The sim's Windows voice takes 0.34-0.75 s to render a one-word call and pads it to 1.1-1.3 s [D], so calls must be pre-rendered and trimmed.
6. **A few parameters make individuals; a distinct look makes them recognisable.** Five puzzle-game "personas" that differed only in their utility weights showed distinct play styles [M]; EA's NHL 26 claims 22 per-player tendencies, including reaction timing [V]. Viewers spot copied appearances far more easily than copied motions [M], so the five AI need different looks too. In tracking data Kucherov stands out by touching the puck often: 41.5 possessions per 20 minutes at 5v5, against a forward average of 31.3 [M].
7. **Scale difficulty through perception and decision speed, not through speed caps, dice or aim noise.** Google Research Football's built-in opponent scales from easy to hard "by speeding up or slowing down the bot reaction time and decision making" [M]. *Corrected in fact-check:* this is the authors' description of how their bot's difficulty knob works, not a measured result, so [V]. Weakened chess engines match human moves 35-40% of the time, a model trained on human games 46-52% [M]: a strong AI plus noise is not a weaker human. Visible speed rubber-banding looks unfair [V]. In Halo playtests tougher enemies were judged smarter (8% against 43% "very intelligent") [V].
8. **In VR, contingency and personal space matter as much as looks.** People pick out a real partner from a non-responding copy by how it responds to them (65.9% against 23.0% of clicks) [S]. Arousal rose the closer virtual characters approached [M]. Gaze helped a realistic avatar but hurt a "match-stick" one [M]; Jon's figures are match-stick figures, so gaze cues need an A/B test. Unexpected vection was the best predictor of VR sickness (reported by 88% of sick players, 31% of well ones) [M]; whether moving AI bodies cause it is unknown.
9. **Keep the AI hand-built and layered: perception, belief, intent, motion.** Learned policies are out of reach: simulated humanoid football took 8 × 10^10 steps and six weeks of training [M], and Google Research Football's hard level needed 500 million steps for a positive goal difference [M]. The current AI tick costs 0.83 ms on average every 20 ms [D]; each change proposed here adds tens of microseconds [E].
10. **Test with paired A/B choices, short games, and self-play numbers.** Ratings suffer from order and inconsistency effects that pairwise preferences avoid [M]. *Corrected in fact-check:* the review reports that ranks reduce these effects, citing an earlier comparison (Yannakakis & Hallam 2011), so [S], and "reduce" rather than "avoid". Believability may be judged better by watching than by playing [E, authors' argument], so Jon should also watch a replay. Self-play can track each tell above as a number.

## 1. What gives bots away

### 1.1 Turing tests for game bots

- **BotPrize (Unreal Tournament 2004).** Players carried a "judging gun" to tag opponents as human or bot. In 2012, MirrorBot (52.2%) and UT^2 (51.9%) passed the 50% bar; the next bot scored 36.0%. UT^2's rating rested on 27 judgments, MirrorBot's on 23 [M] ([Schrum, Karpov & Miikkulainen poster](https://people.southwestern.edu/~schrum2/AAAI-BotPrizePoster.pdf); [Polceanu 2013](https://doi.org/10.1109/CIG.2013.6633618)). Human players averaged only 40% [M] ([UT Austin news](https://www.cs.utexas.edu/news/2012/artificially-intelligent-game-bots-pass-turing-test-turing%E2%80%99s-centenary)). The samples are small.
- **What UT^2 did** [V, the authors' description]: navigation replayed recorded human traces (which also stopped it getting stuck); its aim got worse with "rapid movements and long distances", since otherwise evolution produced "perfect aim, which is not very human-like"; behaviours "were constrained to prevent super-human levels of performance"; it pursued one opponent tenaciously, as people with a grudge do; and it pretended to play the judging game, as humans did. MirrorBot used "human-inspired mirroring behavior" [V, abstract].
- **A later contest** (60 AI-conference judges, three finalist bots, UT2004 one-on-one) found no bot that passed: humans scored 0.38 on the humanness scale, bots -0.19 to -0.33 (p < 0.001). Humanness did not track winning or score. Some bots became repetitive after about 3 minutes, "going back and forth" or always taking the same path [M] ([Even, Bosser & Buche 2021, Frontiers](https://www.frontiersin.org/articles/10.3389/fcomp.2021.774763/full)). *Corrected in fact-check:* the 3-minute point was seen "during the qualifying process" and led the organisers to make matches longer than 3 minutes; it is an observation, not a measured result [V]. The humanness scores and the p-value are [M].
- **A 2025 survey** of 54 papers lists the recurring tells [S]: pixel-perfect precision; "seemingly unlimited reaction times"; acting on things not looked at (UT2004 bots picked up items "not looking at them"); repeating the same mistake ("quickly judged as non-human-like"); getting stuck on geometry ([Świechowski & Ślęzak, AAMAS 2025](https://arxiv.org/pdf/2505.20011)).

### 1.2 Skill is not human-likeness

- **Chess.** Maia, trained on 12 million human games per 100-point rating band, matched human moves 46-52% of the time. Weakened Stockfish matched "about 35-40%"; even depth-1 Stockfish matched 1900-rated players better than 1100-rated ones. Maia predicted the exact blunder more than 25% of the time, even for hanging a queen [M] ([Microsoft Research](https://www.microsoft.com/en-us/research/?p=708031); [McIlroy-Young et al. 2020](https://arxiv.org/abs/2006.01855v3)). The lesson for a sports AI: a strong AI plus noise does not look like a weaker human; human errors are patterned [E].

### 1.3 What developers learned (talks and postmortems, all [V])

- **Halo (GDC 2002)** ([talk notes](https://halo.bungie.org/misc/gdc.2002.haloai/talk.html?page=19)):
  - Tougher enemies seemed smarter: weak enemies, 36% "too easy" and 8% "very intelligent"; stronger ones, 0% and 43% ([page 16](https://halo.bungie.org/misc/gdc.2002.haloai/talk.html?page=16)). Playtests had 25-35 non-hardcore players.
  - "If it isn't totally obvious, it's too subtle": even after the Grunts' panic was exaggerated, the designers estimated that fewer than a third of players made the connection.
  - The deliberate perception pause looked like a bug and was removed.
  - "The Player assumes the AI has capabilities that are similar to his own"; an AI may have extra abilities only if their limits are predictable ([page 6](https://www.halo.bungie.org/misc/gdc.2002.haloai/talk.html?page=6)).
- **F.E.A.R. (GDC 2006)** ([Orkin](https://pages.cs.wisc.edu/~dyer/cs540/handouts/gdc2006_orkin_jeff_fear.pdf)): "There is no point in spending time and effort implementing squad behaviors if in the end the coordination of the A.I. is not apparent to the player." Dialogue showed that coordination was intentional, sometimes with no behaviour behind the line; flanking was never implemented but emerged from simple moves; a line also explained inaction ("I've got nowhere to go!").
- **The Last of Us (Ellie)** ([Dyckhoff, Game AI Pro 2](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter35_Ellie_Buddy_AI_in_The_Last_of_Us.pdf)): keep the companion close, so her actions "can by definition be no more stupid than what the player is doing"; filter out needless short moves; scale her speed by up to 25% so she stops flicking between run and walk; never teleport; call out threats the player has not seen; make sure the player sees her help. *Corrected in fact-check:* the chapter's rule is that a called-out enemy must be "there for the player to see"; it does not state a general rule that the player must see her help. Her gifts and special moves sit on long timers so they stay memorable.
- **EA NHL.** EA says NHL 26's AI "largely operated as individuals"; NHL 27 adds "Cohesive AI" (a partner covers the high slot when a defenseman pinches), team playbooks "built directly from real-world NHL EDGE positional data", and goalies that "read the play ahead of time" at higher levels ([EA NHL 27 blog](https://www.ea.com/games/nhl/nhl-27/news/nhl-27-gameplay-presentation)). NHL 26 has "22 unique tendencies ... built using NHL EDGE tracking", including reaction timing and defensive spacing ([EA via RMNB](https://russianmachineneverbreaks.com/2025/08/26/nhl-26-alex-ovechkin-office-power-play-tendency/)). Marketing text: I found no readable GDC talk or postmortem with data on EA NHL, FIFA/EA FC, NBA 2K or Rocket League AI.

### 1.4 RoboCup and learned football

- **RoboCup 2D (HELIOS).** Team positions come from a function of the ball position: a designer places example formations for sample ball positions, the field is cut into Delaunay triangles, and each player's spot is linearly interpolated inside the ball's triangle. It is cheap, unique for a given data set and "outputs continuous value" [V, team description] ([HELIOS2008 TDP](https://wrighteagle2d.github.io/robocup/2008/2D_TDP_helios.pdf)). Continuous spots are exactly what `_support` lacks (section 7).
- **Google Research Football.** The opponent is a rule-based bot whose difficulty (0-1) is set "by speeding up or slowing down the bot reaction time and decision making". Learned agents needed up to 500 million steps for the hard level; an agent trained against another agent beat it but did poorly against the built-in AI [M] ([Kurach et al. 2020](https://arxiv.org/pdf/1907.11180)). *Corrected in fact-check:* the difficulty knob is the authors' description of their environment [V]; the training-step and transfer results are [M].
- **Learned humanoid football (DeepMind).** Players were constrained to human-like movement by a controller distilled from about 1 h 45 min of football motion capture. Coordinated 2v2 play emerged after 8 × 10^10 environment steps, about six weeks of training [M] ([Liu et al. 2022](https://ar5iv.labs.arxiv.org/html/2105.12196)).

## 2. Perception and imperfection

### 2.1 How fast people react

- **Lab reaction times** [S, from Rabin's survey] ([Rabin, "Agent Reaction Time", Game AI Pro 2](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter05_Agent_Reaction_Time_How_Fast_Should_An_AI_React.pdf)):
  - simple visual reaction 0.19 s (Kosinski) or 0.22 s (Laming);
  - go/no-go, telling two stimuli apart, 0.38 s (Laming);
  - longer for weak stimuli, for extra aiming movement, and with lapses of attention.
  Rabin's working rule is 0.2-0.4 s [V].
- **The floor.** Olympic sprinters' fastest reactions to the gun averaged 166 ms (men) and 189 ms (women), an auditory, fully expected stimulus [M] ([Lipps et al. 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3198384)). The rink-control model in round 1 used 0.189 s, citing this paper, so its value is a sprint-start floor, not a hockey game reaction [D, from [arXiv 2205.13678](https://ar5iv.labs.arxiv.org/html/2205.13678) §III-A]. That model also gave defenders 0.1 s more than attackers [E, model assumption].
- **Experts wait on purpose.** Against VR rugby side-steps (12 expert, 12 novice), experts started moving at 268 ms (SD 36) against 193 ms (SD 64) for novices. Novices made early wrong-direction moves on about 42% of trials, experts on 14%; *Corrected in fact-check:* these rates are for the deceptive side-step trials only (M = 41.9% against 14.2%); the timing figures are the paper's text values, and its Table 2 prints 285 ms for experts; experts read the honest centre-of-mass cue [M] ([Brault et al. 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3372470/)). A high-IQ defender is not the one who reacts fastest; he reacts to the right cue.
- **The shape of the distribution.** Reaction times are skewed to the right and fitted as a Gaussian plus an exponential tail (ex-Gaussian, mean = μ + τ) [M] ([Gooch, Snowling & Hulme 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3413905)). *Corrected in fact-check:* that study fitted children (with ADHD symptoms, dyslexia, or neither) on a stop-signal task; it shows the method, not adult or athlete values. I found no ex-Gaussian fit for athletes in game situations.

**Starting values for the sim [E].** A delay drawn per event and per skater: 0.18 s plus a lognormal or exponential tail with mean about 0.1 s when the event is in his central view and expected (median about 0.25 s); about 0.1 s more in peripheral view; behind him, no reaction until his next scan or until he hears a call or the puck. Anticipation can cut the delay to about 0.1 s, but only when his own read predicted the event (the pass he was covering).

### 2.2 Seeing, attending, remembering

- **Vision zones.** Game AI commonly replaces a yes/no view cone with zones of identification certainty, best straight ahead, worse with distance and toward the periphery, with a bonus for moving objects. The Last of Us required the player to stay 1-2 s in an enemy's "sweet spot" before being seen [V] ([Rabin, "Vision Zones", Game AI Pro 2](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter04_Vision_Zones_and_Object_Identification_Certainty.pdf)). For hockey, a moving puck is easy to spot in the periphery, while a teammate sneaking in behind is not [E].
- **Scanning.** Soccer players scan about 0.44 times a second before receiving, fewer under close pressure; elite junior hockey scans are brief (fixations about 135 ms) [S, via round 1 and the skating note] ([Jordet et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7573254); [Bespomoshchnov et al. 2026](https://doi.org/10.1080/02640414.2026.2744018)).
- **The head shows the decision.** Rabin argues the head look is the AI programmer's most powerful cheap tool (*Corrected in fact-check:* he calls it a way to add to the AI's "vocabulary" with which a programmer "can wield great power"; he does not rank it "most powerful"): sizing up two targets with the head for a second before attacking one "can telegraph deep intelligence" for a choice made instantly [V] ([Rabin, "The Illusion of Intelligence", Game AI Pro 3](http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter01_The_Illusion_of_Intelligence.pdf)). When walking people turn, their gaze turns toward the new direction about 557 ms before the pelvis does, and the head about 264 ms before it, in the light (n = 10) [M] ([Authié et al. 2015](https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2015.00312/full)): people look before they go.

### 2.3 Errors that look human

- **Errors need a visible cause** [V]. The Halo pause looked like a bug. Ocio Barriales' combat-accuracy chapter keeps difficulty predictable by letting only token-holders hit, and makes the deliberate misses visible near misses: tracers past the face, the top of the cover ([Game AI Pro 3, ch. 33](http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter33_Using_Your_Combat_AI_Accuracy_to_Balance_Difficulty.pdf)).
- **Human hockey errors have causes Jon can read** [E]: a misread because the player did not scan; biting on a fake (Brault's 42% novice rate); arriving late because he reacted late; over-committing to the puck carrier and leaving his man; a bobble on a hard pass. Each can come from the perception and belief layers rather than from a dice roll.
- **Don't repeat the same mistake in the same way.** Repeated identical mistakes were a quick bot tell in UT2004 [S] ([Świechowski & Ślęzak 2025](https://arxiv.org/pdf/2505.20011)).

### 2.4 Commitment, hysteresis, momentum

- **People change their minds rarely, and mostly to fix errors.** In a dot-motion task, changes of mind were mostly corrections of an initial error and happened within the 300-400 ms of processing still under way after the move began [M, 3 subjects] ([Resulaj et al. 2009](https://pmc.ncbi.nlm.nih.gov/articles/PMC2875179)).
- **Game-AI tools for commitment** [V]: an "inertia bonus" on the running behaviour's score, "which prevents flip flopping", or a minimum time before a new choice ([IAUS wiki](https://github.com/ProjectBorealis/IAUS/wiki)); dual-utility reasoning, where a rank picks the category ("the puck is loose: race for it") and a weighted random pick among the good options avoids both robotic predictability and silly choices ([Dill, Game AI Pro 2](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter03_Dual-Utility_Reasoning.pdf)).
- **Commitment reads as human.** UT^2's single-minded pursuit (1.1) and the judged "back and forth" bots point the same way. A skater who takes a wrong line and sticks with it looks more human than one who corrects perfectly every 20 ms [E].

## 3. Individuality

- **Few parameters suffice.** Five MiniDungeons 2 personas "vary solely in the weights of decision-making utilities" yet "exhibit a number of distinct decision making and play styles" [M] ([Holmgård et al. 2015](https://doi.org/10.1609/aiide.v11i5.12849)).
- **Consistency over a game.** Halo gave each race a fixed personality established over minutes, Grunts always cowardly, Elites always aggressive, which made AI easier to design and for players to learn and predict [V] (talk notes, [page 5](https://halo.bungie.org/misc/gdc.2002.haloai/talk.html?page=5) and [page 6](https://www.halo.bungie.org/misc/gdc.2002.haloai/talk.html?page=6)). EA NHL ties tendencies to named stars (Ovechkin's power-play spot, Draisaitl's sharp-angle shots) [V].
- **Looks first.** "Clones of appearance are far easier to detect than motion clones"; colour variation, orientation and motion can mask copied models [M] ([McDonnell et al. 2008](https://doi.org/10.1145/1360612.1360625)). Five identical line figures that differ only by team colour and handedness will read as copies whatever their tendencies [E]. Cheap distinctions: helmet colour or number, height ±5 cm, stance width, stick length, a skating-style parameter from the skating note.
- **A Kucherov in numbers.** Not the fastest, strongest, or hardest shot [V] ([Daily Faceoff 2025](https://www.dailyfaceoff.com/news/tampa-bay-lightning-nikita-kucherov-most-underrated-hart-trophy-art-ross-trophy)); a teammate describes one-touching a rimmed puck twice and finding a pass through a crowd [V]. In 2023-24 NHL tracking he had 41.5 possessions per 20 minutes at 5v5, 7th among forwards (tied with McDavid at 41.5; forward average 31.3); average NHL possessions last 1.29 s, 1.05 s in the offensive zone, and the longest-holding forwards average only 1.7-2.0 s [M] ([LINHAC 2025, Tables 3-5](https://ecp.ep.liu.se/index.php/linhac/article/view/1208)). So the playmaker profile is "many quick touches", not "long carries" [E]. The hockey-IQ note in this round should supply his decision parameters.

**A profile per AI skater [E]**, fixed for the game, about six numbers:

| Parameter | What it changes | Range |
|---|---|---|
| reaction base | the 0.18 s base delay | ±0.04 s |
| scan rate | head checks per second off the puck | 0.2-0.6 /s |
| anticipation | chance his read pre-empts a pass he covered | 0.1-0.5 |
| shoot vs pass | `SHOOT_XG` threshold | 0.10-0.22 |
| patience | how long he carries before a forced choice; pass/shoot under pressure | 0.5-2.0 s |
| aggression | pressure distance, commit to the carrier, poke timing | low/high |
| chatter | how often he calls | 0-1 |

A "Kucherov" would be fast to read, high anticipation, pass-first but dangerous to shoot, patient, a frequent caller. A "grinder" is slower to read, aggressive, short patience, loud [E].

## 4. Difficulty and fairness

- **Rubber-banding.** The developers of the racing game Pure dropped speed-based rubber-banding because "it's obvious when AI riders are going superhumanly fast or brain dead slow"; they varied per-rider skills within limits instead [V] ([Game Developer](https://www.gamedeveloper.com/design/the-pure-advantage-advanced-racing-game-ai)). Soren Johnson's rule: "perception becomes reality", so avoid anything a player might suspect is a cheat; hidden catch-up frustrates, open rules feel fair [V] ([Game Developer](https://www.gamedeveloper.com/game-platforms/analysis-game-ai-our-cheatin-hearts)).
- **Hidden adaptation can work if nobody notices.** A game timer silently stretched or shrunk by a factor of 1.4 with performance raised immersion (42 players, F(1,40) = 7.41, p = 0.010), and no player noticed [M] ([Denisova & Cairns 2015](https://www-users.york.ac.uk/~pc530/pubs/Denisova_CHIPLAY15.pdf)). One 90-second game; the authors warn players may feel "short changed" over repeated play.
- **Keep elite but beatable** [E]. Lower the level through slower perception (longer delay, fewer scans, less anticipation), not through slower legs or random misses; keep the skating limits honest at every level; no hidden help on any puck, for the AI as for Jon. A weaker AI then makes errors Jon can exploit (it didn't see his teammate sneak behind), which is how a game against weaker players feels.
- **"Too good" looks like a bot.** Pixel-perfect precision is "strongly associated with bots" [S]. A fast pass that always lands exactly on the tape at exactly 10 m/s, or a shot from the same model every time, risks the same reading; the puck-skills note covers pass and shot variety.

## 5. Presence: what makes a virtual player feel like a person in VR

### 5.1 Contingency: he responds to me

- **Plausibility.** Slater separates the sense of being there from the plausibility illusion, the sense that the events are really happening. Plausibility depends on how far the system "can produce events that directly relate to the participant" [E, theory] ([Slater 2009](https://diposit.ub.edu/items/7edd2c08-1af3-478b-9ed0-b3d34a9a5944/full)).
- **People find people by mutual response.** In the perceptual-crossing experiment, blindfolded pairs searched for each other on a shared 1-D line among a fixed object and a moving copy of the partner that could not respond. 65.9% of clicks went to the partner, 23.0% to the copy, 11.0% to the fixed object. Clicks per encounter were similar for partner and copy: the partner was found because both kept seeking each other [S] ([Auvray & Rohde 2012, reviewing Auvray et al. 2009](https://pmc.ncbi.nlm.nih.gov/articles/PMC3377933)).
- **For the sim [E]:** a teammate feels like a person when he responds to Jon specifically: he looks at Jon when Jon has the puck, gets into a lane Jon can pass through, calls for it, and reacts when Jon ignores him. The AI already weights Jon 1.3× as a pass target (`_decide`), but nothing visible shows that it knows Jon is there.

### 5.2 Gaze

- **It can help or hurt.** Pairs talking in shared VR saw avatars whose gaze was random or "inferred from voice". Across 48 questionnaires, inferred gaze beat random gaze for a semi-photorealistic avatar, but made responses worse for a basic "match-stick" avatar: appearance and behaviour interact [M] ([Garau et al. 2003](https://doi.org/10.1145/642611.642703)). Game gaze at a puck is not conversation gaze, but Jon's figures are match-stick figures, so test it [E].
- **Mutual gaze and space.** Everyone kept more space around a virtual human than around a human-sized object; women kept more distance from agents that made eye contact [M] ([Bailenson et al. 2001](https://doi.org/10.1162/105474601753272844)).
- **Body motion may be enough to coordinate.** In a VR crossing task (17 participants, moving with a joystick) a virtual walker's gaze did not change how people avoided it; "body motion cues were sufficient" [M] ([Lynch et al. 2018](https://api.openalex.org/works/doi:10.1109/VR.2018.8446180)). So gaze is worth testing as a social cue, not relied on for collision avoidance.

### 5.3 Readable intent

- **Legible motion is not the same as predictable motion.** A collaborator's motion should be "intent-expressive", and the most legible motion can differ from the most efficient one [M, HRI experiments] ([Dragan et al. 2013](https://doi.org/10.1109/HRI.2013.6483603)).
- **Hockey's own signals** [V]: a receiver gives "a good target ... stick on the ice" and communicates ([Minnesota Hockey](https://www.minnesotahockey.org/news_article/show/1245725)). Defender posture and stick-in-lane belong to the hockey-IQ and skating notes.
- **For the sim [E]:** a teammate who wants the puck turns his body and blade toward Jon and holds the blade flat for 0.5-1 s before and as he gets open. Jon learns to pass when he sees the target, which is what he does in a real game.

### 5.4 Voice

- **What players say.** In 46 U18/U21 Swiss academy players working in pairs, 77% of talk was orienting (what to do, how, when, where). Talk, mainly the orienting kind, fell with practice while shared knowledge grew; the direct link between the two was weak (r = 0.22, p = 0.15) [M] ([Blaser & Seiler 2019](https://www.frontiersin.org/articles/10.3389/fpsyg.2019.00077/full)). The authors cite earlier work that in-game messages are usually one or two words and repetitive [S].
- **Developers' rules** [V]: speak to make coordination visible (F.E.A.R.); call threats the player has not seen, whispered or shouted by urgency, and comment on what just happened (Ellie). Rate-limit gifts and lines so they stay special (Ellie's long timers).
- **Hockey calls** [V]: "time", "man on", "wheel", "over", "reverse", "leave it" are standard. I found no list from Hockey Canada or USA Hockey; the coaching sites differ by team.
- **The sim's voice [D].** `record.Voice` renders each line through a PowerShell call to Windows' speech engine: "Man on!", "Time!" and "Wheel!" took 0.75, 0.36 and 0.34 s to render, and the clips last 1.08-1.30 s with speech only from about 0.10 s to 0.37-0.55 s. `VoiceQueue` speaks one line at a time and sleeps for the whole clip. A live "man on" would arrive too late.

### 5.5 Personal space, contact, comfort

- **Approach raises arousal.** 12 men were approached 12 times by one or four virtual characters (women or human-sized cylinders): skin-conductance responses rose the closer they came, somewhat more with four, and fell with repetition [M] ([Llobera et al. 2010](https://doi.org/10.1145/1857893.1857896)). Characters and cylinders gave similar physiological responses.
- **Vection and sickness.** Of 30 players in a VR game, 15 of 17 who got sick reported unexpected, uncontrolled self-motion, against 4 of 13 who stayed well (χ² = 10.48, p = 0.001); vection strength itself did not differ [M] ([Teixeira, Miellet & Palmisano 2022](https://www.frontiersin.org/journals/virtual-reality/articles/10.3389/frvir.2022.860919/full)). I found no study of vection caused by moving characters around a stationary viewer. Round 2's comfort note lists "the many moving AI bodies" as one candidate cause of an earlier sickening 3v3; it is untested.
- **For the sim [E]:** no AI arrives inside about 1 m of Jon at speed from outside his view; any bump is telegraphed (visible and slowing for about 0.5 s); no figure crosses within about 1 m of his face at a sprint; a teammate in his way steps aside late with a word, as Ellie did, rather than sliding away instantly; Jon is never pushed (as now).

## 6. Architecture and testing

### 6.1 Which kind of AI for a 50 Hz Python sports AI

- **State machines and behaviour trees** suit the lowest level and fixed priorities (F.E.A.R. had three states; UT^2 a priority list "similar to a behavior tree") [V]. Cost: trivial.
- **Utility, or dual utility with inertia,** suits choosing among a handful of intents (chase, support, pressure, cover, receive, carry, pass, shoot), and tendencies become weights [E]. Cost: tens of µs per skater.
- **Planners (GOAP, HTN)** are overkill for a 3v3 with a handful of actions; even F.E.A.R. ran its squads with an ad-hoc layer above individual planners [V].
- **Learned policies** are out of reach: 10^8-10^11 training steps (1.4). Inference would be cheap; training is not.

Recommended layering [E]:

1. **Perception** (per skater, every AI tick): which objects are in his central, peripheral or rear zone; a perceived event enters a queue with its delay.
2. **Belief**: the puck, the carrier and each player as he last perceived them, extrapolated linearly; the truth only arrives through perception, a scan, a call, or contact with the puck.
3. **Intent** (every 0.1-0.25 s, staggered per skater): dual-utility choice among a few intents, with an inertia bonus and a minimum hold; team roles (chaser, F1/F2, D-side) assigned with hysteresis.
4. **Motion and expression** (every tick): steering on the shared skating model (sibling note); head target from the attention scheduler; stick pose (target, lane); voice calls.

The real puck stays physical throughout: a skater's belief may be wrong, but if the puck reaches his blade, the physics decides [E]. Each layer can be logged and tested on its own: perception by unit tests of what he can see; belief by its lag; intent by its switch rate; motion by the skating note's numbers.

### 6.2 Testing with one tester

- **Pairwise, not ratings.** Ratings show order (recency) and inconsistency effects that ranks avoid [M, via the review's evidence] (*Corrected in fact-check:* [S]: the review cites Yannakakis & Hallam 2011 for this, and says ranks reduce these effects) ([Yannakakis & Martínez 2015](https://www.um.edu.mt/library/oar/bitstream/123456789/22952/1/Ratings_are_Overrated.pdf)).
- **Protocol [E]:**
  - A then B then A, 3 minutes each, same seed and level;
  - after each pair, one forced choice: "which felt more like playing with people?" and one: "which was fairer?";
  - one sentence on why;
  - Jon does not know which is new; blinding fails often (in the 2021 study 11 of 16 players worked out the real purpose; the paper prints "61%", but 11/16 is 69% [M, D]), so swap the order between days.
- **Watch as well as play.** Togelius and colleagues argue that judging while playing is "prone to distortion effects" and that an outside observer may judge better [E, their argument; the 2021 study notes nobody has tested it] ([Togelius et al., *Assessing Believability*](https://www.um.edu.mt/library/oar/bitstream/123456789/22848/1/Assessing_Believability.pdf)). After a session, show Jon 30 s of replay from above or a far corner and ask the same question [E].
- **Name the players.** After a game with profiles, ask who the playmaker was. If Jon can't tell, the profiles are too weak or the looks too similar [E].
- **Log AI positions.** The game recordings do not log AI positions every tick. A compact `ai.csv` at 50 Hz (5 AI skaters and 2 goalies × 6 numbers, about 13 kB/s as text) would let self-play metrics run on Jon's real games [D, 50 × 7 × 6 × about 6 bytes = 12.6 kB/s].

**Self-play metrics, with today's values [D]** (seeds 1/2):

| Tell | Today | Direction |
|---|---|---|
| Target changes within one tick of a possession change | 96-97% | toward 0; median onset 0.2-0.3 s |
| Skaters pushing a new way within 40 ms (of those already pushing whose push turned >45° within 1 s) | 76-77% (fact-check re-run: 76-79% within two ticks) | toward 0 |
| Off-puck time with the puck behind (>90°) | 15-17% | keep; but reacting to it only after a look |
| Chaser changes per team per loose-puck minute | 4.9-5.3 | under 1 |
| ...of which back within 1 s | 39-42% | near 0 |
| Mark switches per defender-minute (defending a carrier) | 8.8-9.5 | about 1-2 |
| Target jumps >2 m per skater-minute, possession unchanged | 10.8-11.6 | near 0 |
| Nearest opponent to an AI carrier, median | 1.15-1.22 m (57-59% under 1.5 m) | varies by read and aggression |
| AI possession length, mean | 0.97-1.20 s (median 0.56-0.67 s; 40-46% under 0.5 s) | NHL 1.29 s: means close; see the caveat in section 7 |
| AI tick cost, mean / p99 | 0.83 / 1.6 ms | stay under about 1.5 ms mean |

## 7. `threes.py` against all this

What will read as robotic to a hockey player. The skating note covers the body (top speed, acceleration, shoves, backward skating, gait); these are the rest.

1. **Same-tick reactions** (`Game.update` → `_targets` every 20 ms from the true puck). The nearest players should react first, the far side later, some not at all. Today it feels like "they knew before it happened" [E].
2. **Omniscience** (`_decide`, `_lane`, `_defend`, `_chase` read every true position). A defender with his back to a back-door cut covers it anyway; a carrier hits a teammate behind him blind.
3. **Flicker** [D, code]. `_chase` re-picks the quickest skater every tick. `_defend` re-pairs marks every 0.6 s. `_support` re-sorts spots by distance every tick and mirrors them when the carrier crosses x = 0 (`side = 1 if c[0] >= 0`). `_carry_to` flips its slot point within 2 m of it and mirrors on the same rule. In real hockey a switch is a call ("switch!", "I got him") and happens a few times a shift [E].
4. **Dice instead of reads.** Pokes are rolls (`POKE_RATE` × level × closeness), not strikes when the puck is exposed. Under pressure the carrier passes on a coin flip (`rng.random() < 0.5`). Hard pucks are picked up 45% of the time at random. *Corrected in fact-check:* the 45% roll applies to a puck 7-16 m/s faster than the stick (`_loose`); slower ones are always taken, faster ones never.
5. **Identical pressure.** The marking defender skates to `stick + 0.6 m` goal side of the carrier; an opponent is within 1.5 m of an AI carrier 57-59% of the time [D]. Real defenders gap, angle and choose when to close (hockey-IQ note).
6. **No attention, no voice, no individuals.** Facing is the travel direction above 1 m/s (`_skate`); no teammate ever speaks; all five share the same constants and look.
7. **The puck is off the drawn blade.** The puck rides 0.75 m straight ahead (`STICK_R`); `figures._local` draws the blade from (1.05 m ahead, 0.42 m aside) to (1.12, 0.12). The nearest point of the blade is about 0.39 m from the puck [D: √(0.37² + 0.12²)]. It reads as a puck floating ahead of the stick.
8. **Already fine.** Possessions last a mean 1.0-1.2 s against the NHL's 1.29 s [D, M]. *Corrected in fact-check:* only the means match. The AI's median possession is 0.56-0.67 s and 40-46% last under 0.5 s [D], and the NHL figure comes from the league's own tracking-based possession model, which is not the sim's `holder` rule. LINHAC gives no median to compare, so treat "already fine" as "not obviously wrong". The AI goes round Jon rather than pushing him. Shots use a goalie-based chance model with aim errors.

## What this means for the sim

One change at a time, each testable. They assume the sibling note's steady targets, soft avoidance and skating model land first or alongside; these items sit on top.

1. **Decision commitment** (`_decide`, `_chase`, `_defend`, `_support`).
   - Extends the skating note's "steady targets" from points to intents.
   - Replace `_decide`'s threshold chain with a small dual-utility choice (shoot, pass to X, carry on a plan: drive the wall, cut to the slot, delay and protect). Give the current plan an inertia bonus (×1.2 [E]) and a minimum hold of 0.5-1 s unless a clearly better option appears (xG jump of 0.05 or a lane opening).
   - Chaser and marks: switches happen through an explicit "switch" event with hysteresis, logged and, later, spoken.
   - Cost: a few µs per skater per decision.
   - Measure: chaser changes per loose-puck minute under 1; mark switches about 1-2 per defender-minute; intent switches logged per minute.
   - Headset A/B: commitment on/off.
2. **Perception delay and belief** (new per-`Player` fields `seen_puck`, `seen_t`, `pending`; `_targets` and `_decide` read the belief, not `self._puck()`).
   - On each puck event (possession change, pass, shot, a puck entering a new zone) compute each skater's delay: base 0.18 s + exponential tail (mean 0.1 s) in central view (±50°); +0.1 s in peripheral view (±110°); rear: on his next scan, a call, or the puck within 1.5 m (heard or felt) [E, from 2.1].
   - Expected events (the pass he was covering) at about 0.1 s.
   - Use `level` and the player profile to scale the base.
   - Physical contacts with the puck stay instant and honest.
   - Cost: a few dot products per skater per tick, about 20-50 µs in Python [E].
   - Measure: decision-onset median 0.2-0.3 s with spread (p10-p90 about 0.15-0.5 s); goals and turnovers per minute (expect more of both: watch the balance).
   - Headset A/B: delay on/off. Ask which felt more like people.
3. **Attention-driven head** (`Player.head`, drawn per the skating note's item 6).
   - The scheduler picks where the head points: the puck by default; a check toward the area that matters (back door, his man, the open lane) at the profile's scan rate; the passer before a reception; Jon when Jon has the puck and this teammate wants it, or before an AI passes to Jon.
   - Perception (item 2) uses the head direction, so a check really refreshes his picture: what he looks at, he knows.
   - Head turns lead decisions by about 0.2-0.5 s where possible [E, from Authié's gaze lead].
   - Cost: trivial in the AI; drawing as in the skating note.
   - Headset A/B: attention head against a turn-only head. Watch Garau's warning: if Jon finds the line-figure heads odd, keep them subtle.
4. **Calls** (outbox `say` items with a new `call` kind; `audio.Mixer.speak`).
   - Pre-render about 12 short calls in two or three voices at load, trim silence, play with priority.
   - Calls:
     - "Man on!": Jon has the puck and an opponent he has not looked at is within about 3 m or 1 s;
     - "Time!": nobody within about 4 m;
     - "Here!" / "Yep!": a teammate open, with his stick target showing;
     - "Shoot!": Jon in the slot with a lane;
     - "Wheel!" / "Over!" in Jon's own end;
     - "Switch!" / "I got him": when marks change;
     - opponents' calls ("Ball!", "Got him") quieter.
   - Use Jon's head yaw to judge what he has not seen (as Ellie did).
   - Rate-limit to about one call per 2-3 s per team. No call when Jon already looked.
   - Cost: about 3.5 MB of clips (36 clips × 0.5 s × 48,000 samples/s × 4 bytes) [D]; render time at load 0.3-0.75 s per clip, off the main thread [D].
   - Headset A/B: calls on/off. Measure Jon's turnovers in the 2 s after a "man on".
   - Comfort: none; it is sound. Spatial panning toward the caller is a later step.
5. **Stick target and readable intent** (`figures._local` gets a "target" pose; `Player.wants_puck`).
   - A teammate who has chosen to be the receiver turns his blade flat toward the passer for 0.5-1 s and holds it.
   - Also fix the 0.39 m gap between the carried puck and the drawn blade (puck-skills note decides which constant moves).
   - Cost: one more cached pose per player.
   - Headset A/B: target on/off; do Jon's passes go to the open man sooner?
6. **Profiles and looks** (`Player.profile`, set in `Game.__init__`).
   - The table in section 3; one named archetype per AI (playmaker, shooter, grinder, two-way D, puck-moving D).
   - A distinct look per player (helmet colour band or number, height, stance).
   - Cost: trivial.
   - Test: Jon names the playmaker after a game; pairwise "which team felt like individuals".
7. **Difficulty through perception** (`level`).
   - Map `level` mostly onto reaction base, scan rate and anticipation (item 2), then aggression; keep `WILD` and `vmax` scaling small.
   - Never speed up or slow down AI by score (no rubber band).
   - Test: Jon's win rate and "fairness" choice across two levels.
8. **Errors with causes** (`_possession`, `_loose`).
   - Replace random poke rolls with a poke chance that depends on the carrier exposing the puck (puck away from his body, his head down, his speed) and on whether the poker was beaten by a fake (bit early). Keep the outcome in physics.
   - Pickups of hard passes fail by relative speed and whether the receiver was looking (item 3), not by a flat 45%.
   - Cost: small.
   - Measure: turnovers per minute stay in range; Jon's "fairness" choice.
9. **Comfort guard** (`_skate` targets).
   - Keep AI targets out of a 1 m bubble around Jon unless the skater is visible to him and slowing.
   - Telegraph any contact (0.5 s visible approach, decelerating).
   - Log the closest AI approach per minute and the AI's angular speed across Jon's view, so a sickening session can be checked against it.
10. **Logging** (`game.py` Log): an `ai.csv` per game at 50 Hz with positions, velocities, facing, head, intent, so every metric above runs on Jon's real games.

Suggested A/B order: 1, then 2, then 3, then 4. Items 5-8 can follow in any order. Item 9 should ride along with 2 and 3. Item 10 can come any time.

## Open questions

- **Reaction times in hockey play.** I found no measurement of how long skaters take to respond to passes, turnovers or shots in games. Tracking data (NHL EDGE at 12 Hz for players [M], [LINHAC 2025](https://ecp.ep.liu.se/index.php/linhac/article/view/1208)) could answer it, but it is not public.
- **Do heads on line figures help?** Garau's match-stick result says gaze can hurt a crude figure. Only an A/B in the headset can tell.
- **What delay suits Jon's game?** He plays adult rec; "Kucherovs" read faster than his opponents do. The best delay may be the one that feels fair, not the one measured in elite players.
- **Was the earlier 3v3 sickness about AI motion?** Untested. Log AI motion across his view (item 9) and compare sessions.
- **Voice placement.** Whether calls need to come from the caller's direction to help, or a central voice is enough, is untested.
- **Kucherov's decision parameters** (anticipation, patience, pass/shot thresholds) need the hockey-IQ note's numbers; this note gives only the structure.
- **Sports-game AI postmortems with data** (EA NHL, FIFA/EA FC, NBA 2K, Rocket League) were not found; only marketing pages.

## Sources

Game-bot human-likeness and evaluation
- Schrum, Karpov & Miikkulainen, BotPrize 2012 poster: https://people.southwestern.edu/~schrum2/AAAI-BotPrizePoster.pdf
- UT Austin news, BotPrize 2012: https://www.cs.utexas.edu/news/2012/artificially-intelligent-game-bots-pass-turing-test-turing%E2%80%99s-centenary
- Polceanu 2013, MirrorBot (abstract): https://doi.org/10.1109/CIG.2013.6633618
- Even, Bosser & Buche 2021, believability protocol, Frontiers in Computer Science: https://www.frontiersin.org/articles/10.3389/fcomp.2021.774763/full
- Świechowski & Ślęzak 2025, human-like agents survey (AAMAS): https://arxiv.org/pdf/2505.20011
- Togelius, Yannakakis, Karakovskiy & Shaker, Assessing Believability: https://www.um.edu.mt/library/oar/bitstream/123456789/22848/1/Assessing_Believability.pdf
- Yannakakis & Martínez 2015, Ratings are overrated: https://www.um.edu.mt/library/oar/bitstream/123456789/22952/1/Ratings_are_Overrated.pdf
- Maia chess, Microsoft Research: https://www.microsoft.com/en-us/research/?p=708031 ; paper: https://arxiv.org/abs/2006.01855v3
- Holmgård et al. 2015, persona-based player modelling: https://doi.org/10.1609/aiide.v11i5.12849

Developer talks and books [V]
- Butcher & Griesemer, Halo AI, GDC 2002: https://halo.bungie.org/misc/gdc.2002.haloai/talk.html?page=16 (also pages 5, 6, 19)
- Orkin, Three States and a Plan: The A.I. of F.E.A.R., GDC 2006: https://pages.cs.wisc.edu/~dyer/cs540/handouts/gdc2006_orkin_jeff_fear.pdf
- Dyckhoff, Ellie: Buddy AI in The Last of Us: http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter35_Ellie_Buddy_AI_in_The_Last_of_Us.pdf
- Rabin, Agent Reaction Time: http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter05_Agent_Reaction_Time_How_Fast_Should_An_AI_React.pdf
- Rabin, Vision Zones and Object Identification Certainty: http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter04_Vision_Zones_and_Object_Identification_Certainty.pdf
- Rabin, The Illusion of Intelligence: http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter01_The_Illusion_of_Intelligence.pdf
- Dill, Dual-Utility Reasoning: http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter03_Dual-Utility_Reasoning.pdf
- Ocio Barriales, Using Your Combat AI Accuracy to Balance Difficulty: http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter33_Using_Your_Combat_AI_Accuracy_to_Balance_Difficulty.pdf
- IAUS wiki (inertia bonus): https://github.com/ProjectBorealis/IAUS/wiki
- Pure racing AI: https://www.gamedeveloper.com/design/the-pure-advantage-advanced-racing-game-ai
- Soren Johnson, Game AI & Our Cheatin' Hearts: https://www.gamedeveloper.com/game-platforms/analysis-game-ai-our-cheatin-hearts
- EA NHL 27 gameplay blog: https://www.ea.com/games/nhl/nhl-27/news/nhl-27-gameplay-presentation
- EA NHL 26 tendencies, via RMNB: https://russianmachineneverbreaks.com/2025/08/26/nhl-26-alex-ovechkin-office-power-play-tendency/
- HELIOS2008 team description (Delaunay positioning): https://wrighteagle2d.github.io/robocup/2008/2D_TDP_helios.pdf

Learned football
- Kurach et al. 2020, Google Research Football: https://arxiv.org/pdf/1907.11180
- Liu et al. 2022, simulated humanoid football: https://ar5iv.labs.arxiv.org/html/2105.12196

Perception, reaction, decisions
- Lipps, Galecki & Ashton-Miller 2011, sprinters' reaction times: https://pmc.ncbi.nlm.nih.gov/articles/PMC3198384
- Rink-control model (reaction 0.189 s): https://ar5iv.labs.arxiv.org/html/2205.13678
- Brault et al. 2012, VR rugby side-step: https://pmc.ncbi.nlm.nih.gov/articles/PMC3372470/
- Gooch, Snowling & Hulme 2012, ex-Gaussian RT: https://pmc.ncbi.nlm.nih.gov/articles/PMC3413905
- Authié et al. 2015, gaze and head anticipation in walking: https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2015.00312/full
- Resulaj et al. 2009, changes of mind: https://pmc.ncbi.nlm.nih.gov/articles/PMC2875179
- Jordet et al. 2020, scanning: https://pmc.ncbi.nlm.nih.gov/articles/PMC7573254
- Bespomoshchnov et al. 2026, hockey scanning: https://doi.org/10.1080/02640414.2026.2744018

Presence and virtual humans
- Slater 2009, place illusion and plausibility: https://diposit.ub.edu/items/7edd2c08-1af3-478b-9ed0-b3d34a9a5944/full
- Auvray & Rohde 2012, perceptual crossing review (reports Auvray et al. 2009): https://pmc.ncbi.nlm.nih.gov/articles/PMC3377933
- Garau et al. 2003, avatar realism and gaze: https://doi.org/10.1145/642611.642703
- Bailenson et al. 2001, mutual gaze and personal space: https://doi.org/10.1162/105474601753272844
- Lynch et al. 2018, virtual walker gaze: https://api.openalex.org/works/doi:10.1109/VR.2018.8446180
- Llobera et al. 2010, proxemics with dynamic characters: https://doi.org/10.1145/1857893.1857896
- McDonnell et al. 2008, Clone attack: https://doi.org/10.1145/1360612.1360625
- Dragan, Lee & Srinivasa 2013, legibility: https://doi.org/10.1109/HRI.2013.6483603
- Teixeira, Miellet & Palmisano 2022, unexpected vection: https://www.frontiersin.org/journals/virtual-reality/articles/10.3389/frvir.2022.860919/full

Difficulty
- Denisova & Cairns 2015, hidden timer adaptation: https://www-users.york.ac.uk/~pc530/pubs/Denisova_CHIPLAY15.pdf

Hockey and team communication
- Blaser & Seiler 2019, verbal communication in football: https://www.frontiersin.org/articles/10.3389/fpsyg.2019.00077/full
- Minnesota Hockey, giving a target: https://www.minnesotahockey.org/news_article/show/1245725
- LINHAC 2025, individual puck possessions: https://ecp.ep.liu.se/index.php/linhac/article/view/1208
- Daily Faceoff 2025, Kucherov: https://www.dailyfaceoff.com/news/tampa-bay-lightning-nikita-kucherov-most-underrated-hart-trophy-art-ross-trophy

## Fact-check

Fact-checked 2026-11-13. I checked about 87 load-bearing claims: about 59 claims against their cited sources, 15 statements about the code, and 13 self-play numbers, timings and sums. 75 held up. 12 needed a correction or a caveat, each marked inline "*Corrected in fact-check:*". None had to be dropped. No code or other file was changed. My scripts and outputs are in `C:\Users\jhill\AppData\Local\Temp\claude\d5760a1e5391f178\c9432537-7115-4ab8-897a-637cb1235a5b\scratchpad\ai-round\factcheck-human\` (`fc_selfplay.py`, `fc_voice.py`, `abstracts.py`, `fc_seed1.txt`, `fc_seed2.txt`).

**Self-play, re-run.** I wrote my own logger and analysis. It does not reuse the researcher's analysis code, and it reads the chaser from `_chase`'s own output instead of re-deriving it. The same seeds replay the same games (scores 2-3 and 3-4), and every number in the section 6.2 table came out the same:
- target changes on the first tick: 96.7% and 96.4%;
- puck behind the skater: 17.1% and 15.1%;
- chaser changes: 4.90 and 5.25 per loose-puck minute, 39% and 42% back within 1 s;
- mark switches: 8.82 and 9.52 per defender-minute;
- target jumps: 10.8 and 11.6 per skater-minute;
- possessions: mean 1.20 and 0.97 s;
- nearest opponent: median 1.22 and 1.15 m, 57% and 59% of the time under 1.5 m.

Some things to know about these numbers:
- The games are 6 AI skaters with no Jon.
- "Loose puck" time includes passes on their way, which is 63-67% of live time.
- Each mark-switch rate rests on only 8-10 defender-minutes.

The push-onset figure is right, but it is a share of the skaters who were already pushing and then turned (corrected inline).

**Timings and sums.**
- Re-running `cost.py` gave a mean AI tick of 0.79 ms and a p99 of 1.57 ms (the note says 0.83 and 1.6).
- `record.Voice` took 0.35-0.43 s to render "Man on!", "Time!" and "Wheel!" once warm. The clips were 1.08-1.30 s long, with speech from 0.10 s to 0.37-0.55 s. The note's figures match.
- The 0.389 m gap between the carried puck and the drawn blade is right. The nearest point is the toe end, at (1.12, 0.12) in `figures._local`.
- The clip memory (3.46 MB), the `ai.csv` rate (12.6 kB/s) and the vection shares (15/17 = 88%, 4/13 = 31%) are right.

**Code.** Each of these matches `threes.py`, `figures.py`, `record.py`, `sandbox.py`, `audio.py` and `game.py`:
- `_chase` re-picks every tick; `_defend` re-pairs every 0.6 s; `_support` and `_carry_to` mirror at x = 0.
- Pokes are rolls; the carrier under pressure passes on a coin flip; the marker goes to the stick plus 0.6 m.
- Jon gets a 1.3× pass weight; facing follows velocity above 1 m/s.
- The AI top speed is 2.85 m/s at skate 3; Jon is never pushed; no AI teammate speaks.
- `VoiceQueue` speaks one line at a time, and `Voice.say` sleeps for the whole clip.

One claim needed a fix: the "45% for hard pucks" applies only to pucks 7-16 m/s faster than the stick.

**Sources confirmed against the text.**
- **Game bots:** BotPrize (52.2/51.9/36.0%, 27 vs 23 judgments, humans 40%, UT^2's design quotes); Even et al. (0.38 against -0.19 to -0.33, p < 0.001, "61%" for 11 of 16); Świechowski & Ślęzak (54 papers, the tells); Maia (46-52%, 35-40%, 12 million games, >25% of blunders).
- **Developer talks:** Halo (36/8% and 0/43%, 25-35 non-hardcore players, the pause "Feature was a Bug", "less than a third"); F.E.A.R.'s quotes.
- **Commercial and learned AI:** EA NHL 26 and 27; HELIOS; Google Research Football (500M steps, the A/B transfer); Liu et al. (8 × 10^10 steps, six weeks, 1 h 45 min of mocap).
- **Reaction and perception:** Rabin's 0.19/0.22/0.38 s and his 0.2-0.4 s rule; Lipps (166/189 ms, Beijing 2008); the rink-control model (0.189 s from Lipps, +0.1 s for defence); Brault (268 vs 193 ms, 12 vs 12, VR); Jordet (0.44 scans/s); Authié (557/264 ms against the pelvis, n = 10); vision zones (1-2 s in The Last of Us).
- **Design tools:** Ocio Barriales (tokens, tracers past the face); Resulaj (3 subjects, 300-400 ms); the IAUS inertia bonus; Dill's dual utility; Holmgård's personas.
- **Kucherov and difficulty:** McDonnell; LINHAC (41.5 vs 31.3, 1.29 and 1.05 s, 12 Hz players); Daily Faceoff; Pure; Soren Johnson; Denisova & Cairns (42 players, F(1,40) = 7.41, factor 1.4).
- **Presence and communication:** Slater; Auvray (65.9/23.0/11.0%); Garau ("match-stick", 48 questionnaires); Bailenson; Lynch (17, joystick); Llobera (12 men, 12 approaches); Teixeira (15/17 vs 4/13, χ² = 10.48); Dragan; Minnesota Hockey; Blaser & Seiler (46 players, 77%, r = 0.22, p = 0.15); Togelius ("prone to distortion effects").
- **Not re-fetched:** Bespomoshchnov's 135 ms. It matches the round-1 and skating notes, and it is tagged [S].

**Corrected.**
- **Tags:** the BotPrize "3 minutes" was a qualifying-round observation, not a judged result; the Google Research Football difficulty knob is a design description; "one or two words" is [S]; the ratings-vs-ranks claim is [S], and ranks "reduce" these effects rather than avoid them.
- **Wording that went past the source:** F.E.A.R. does not report coordination being invisible without dialogue; the Ellie chapter has no rule that the player must see her help; Rabin does not call the head look "most powerful".
- **Missing qualifiers:** Brault's 42%/14% are for deceptive trials; Gooch's ex-Gaussian data are children's; the push-onset share; the 45% pickup; possession length, where only the means match (the AI's median is 0.56-0.67 s) and the NHL figure comes from a different possession model.

**What the synthesis can lean on.**
- The measured tells of the current AI: same-tick reactions, omniscience, chaser and mark flicker, and identical pressure. They reproduce exactly and they follow from the code.
- The lab reaction-time ranges, Brault's expert-waits result, the Halo playtest numbers, the BotPrize and Maia numbers, LINHAC's Kucherov profile, and the voice latency.

**What to treat with care.**
- Most of the "how to make it feel human" advice is developer experience [V] or our estimate [E]. Nobody has run a controlled human-likeness study of sports-game AI.
- The BotPrize results rest on 23-27 judgments per bot.
- The suggested delay of 0.2-0.45 s comes from lab tasks and sprint starts, not hockey play.
- Garau's gaze result is about conversation, and Auvray's result is secondary [S].
- The vection study is about the player's own motion, not about AI bodies moving around him.
- The self-play numbers come from 6-AI games with no Jon, so his presence in the headset may change them.
