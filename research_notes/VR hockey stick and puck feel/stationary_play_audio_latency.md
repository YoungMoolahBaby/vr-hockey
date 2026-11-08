# Stationary, tethered play; skating substitutes; sound and latency pipeline (VR hockey trainer)

Scope: the body and environment around the hands for a standing, tethered (Quest 3 + Link cable) player who always holds two Touch Plus controllers (no stick prop, no hand tracking), in a Python + pyopenxr app with a 1 kHz physics thread and a separate render thread. Research pass: November 2026. Older sources are marked with their year. Practical notes for the Python app are in the Inferences sub-sections; facts with sources are in Cited Findings.

## 1. How do VR sports and fitness games handle a moving sport in a small space? (stationary/standing modes, locomotion options, comfort findings, skating specifics)

### Takeaway
The comfort evidence ranks teleport/discrete moves as least sickening and continuous joystick steering as most sickening, with arm-based and lean-based methods in between; standing (vs sitting) raises presence without changing sickness. VR hockey titles split between free-skating (arm-swing or stick-driven skating, roomscale) and stationary drill or cognition trainers (Sense Arena). Arm-swing skating clashes with a two-handed stick grip, so for this trainer the strongest options are fixed-spot drills, scripted or discrete repositioning between reps, and small head/torso lean or short real steps for fine positioning.

### Cited Findings
**Locomotion and cybersickness research**
- A 2018 comparison of four methods (joystick, arm-cycling, point-tugging, teleport) found teleport and arm-cycling caused less simulator sickness than joystick and point-tugging; arm-cycling beat teleport on enjoyment and task completion time. Arm-cycling is a different technique from arm-swinging (older, 2018). — [Coomer et al. 2018, ResearchGate](https://www.researchgate.net/publication/326760529_Evaluating_the_effects_of_four_VR_locomotion_methods_joystick_arm-cycling_point-tugging_and_teleporting)
- A 2019 study (as summarized secondhand) found arm-swinging produced significantly more nausea than teleportation; the arm-swing evidence base is thin and mixed. — [Teleportation in VR: a mini-review (NSF PAR)](https://par.nsf.gov/servlets/purl/10374128)
- In a 25-person study, steering was on average more sickening than teleporting, but 9 participants were sicker with teleport; sickness rose with time for both. Standing vs sitting did not change sickness but standing increased presence during virtual locomotion (2019). — [Clifton & Palmisano, Virtual Reality (Springer)](https://link.springer.com/article/10.1007/s10055-019-00407-8)
- Joystick steering keeps strong visual acceleration with no matching vestibular input, which provokes sickness; teleport removes continuous optic flow and minimizes sickness but hurts spatial orientation; the 2025 maze study judged joystick the best overall balance of efficiency, usability and comfort. — [Scientific Reports 2025](https://www.nature.com/articles/s41598-025-12143-y)
- Over repeated sessions, overall cybersickness fell slightly, but nausea and disorientation rose notably with joystick navigation. — [ACM, Changes in Navigation over Time](https://dl.acm.org/doi/full/10.1145/3613902)
- A 2025/2026 two-game study found teleportation was generally the most usable method and linked to lower cybersickness on most measures, compared with slide-walk and walk-in-place. — [Applied Sciences (MDPI), teleport vs slide vs walk-in-place](https://doi.org/10.3390/app16178472)
- "Locomotion in place" compared joystick, teleport and leaning as stationary methods (2019). — [Buttussi & Chittaro, ResearchGate](https://www.researchgate.net/publication/334489684_Locomotion_in_Place_in_Virtual_Reality_A_Comparative_Evaluation_of_Joystick_Teleport_and_Leaning) (I did not read the full results.)
- Arm-swinging is listed among alternatives to thumbstick/teleport that reduce hardware needs but "can interfere with simultaneous interaction or provide limited directional precision." — [arXiv 2601.02167](https://arxiv.org/html/2601.02167v2)
- Body-centric methods (walking-in-place, leaning) increase embodiment, but many need repeated stepping, torso motion or state changes. — [arXiv 2604.10237, Glide-in-Place](https://arxiv.org/pdf/2604.10237)
- In-place gestures for locomotion are typically detected with HMD or IMU sensors, not controllers. — [arXiv 2209.01059](https://arxiv.org/pdf/2209.01059)
- Community wiki (lower authority): walking-in-place is high-immersion but moderate fatigue; controller-set direction adds an artificial step new users forget. — [VR & AR Wiki, Locomotion](https://vrarwiki.com/wiki/Locomotion)

**Meta design guidance (official)**
- Default to comfort options (teleport, snap turn) and let users opt into slide and smooth turn; snap turn is "the comfort option" but may disorient some users. — [Meta, Locomotion user preferences](https://developers.meta.com/vr/design/locomotion-user-preferences/); [Meta IWSDK, Locomotion Turn](https://developers.meta.com/horizon/documentation/web/iwsdk-concept-locomotion-turn/)
- Match avatar speeds to real walking/running, keep acceleration events brief and infrequent, use stepped translations, restrict movement axes, vignettes, occluding/peripheral geometry and simpler textures; simulating physical activity (e.g., walking in place) reinforces comfort. No numeric speed values are given. — [Meta, Locomotion best practices](https://developers.meta.com/horizon/design/locomotion-best-practices/)
- Vignette default strength 0.4 to 0.6, enabled only while moving, with a short fade-out on stop; advanced vignettes block only the regions with the most motion cues. — [Meta IWSDK, Slide locomotion](https://developers.meta.com/horizon/documentation/iwsdk/concepts/locomotion/slide/); [Meta, Comfort](https://developers.meta.com/vr/design/comfort/)
- Flat terrain, forward movement and distant walls are more comfortable; keep a steady frame rate to avoid judder. — [Meta, Locomotion comfort and usability](https://developers.meta.com/horizon/design/locomotion-comfort-usability/)
- Orientation-aware design: a seated user turns with the controller; a standing user can grab items remotely instead of bending; a roomscale user can reach all meaningful interactions inside the boundary. The most restrictive comfort mode allows only forward/back movement so the user turns physically. — [Meta, Content guidelines](https://developers.meta.com/horizon/resources/publish-content-consider/); [Meta, Locomotion comfort and usability](https://developers.meta.com/horizon/design/locomotion-comfort-usability/)

**VR hockey titles (what exists)**
- "Hockey VR" is described as moving by swinging your arms to mimic skating (listicle claim of "about 80% accuracy" vs real skating; treat as marketing). — [5thscape, Best VR hockey games 2026](https://5thscape.com/blog/best-vr-hockey-games/)
- Hockey Player VR (PC VR) advertises free skating over the whole rink with "no teleporting, no rails, no fixed positions"; a user review complained skating felt slow with little momentum. — [Hockey Player VR site](https://hockeyplayervr.com/); [Meta store listing](https://www.meta.com/experiences/pcvr/hockey-player-vr/1831386233574800/)
- Pick-up League Hockey (Quest) lists Sitting, Standing and Roomscale modes. — [Meta store](https://www.meta.com/experiences/pick-up-league-hockey/4092691917425965/)
- HockeyVR (Quest) is a physics-based sim with an optional "RealStick" mount that clips a controller to a real stick (a prop; context only, excluded by Jon's constraint). — [HockeyVR](https://melcher.ca/hockeyvr/)
- Hockey+ exists in Early Access on Quest (no locomotion details found). — [Meta store](https://www.meta.com/experiences/hockey-early-access/7828614980570171/)
- NHL Sense Arena is a stationary VR trainer; players can train while staying in place (sponsored article). — [Hockey Journal (sponsored)](https://www.hockeyjournal.com/elevate-your-brain-training-with-sense-arena/); [Sense Arena players page](https://hockey.sensearena.com/players)
- Slapshot: Rebound is a flat-screen PC game (WASD skating + mouse stick), not VR. — [Steam](https://store.steampowered.com/app/1173370/Slapshot_Rebound/); [GameGrin](https://www.gamegrin.com/articles/so-i-tried-slapshot-rebound/)

### Inferences
- Both controllers are "the stick," so any locomotion that uses the arms (arm-swing, arm-cycling, grab-and-pull) fights the stick; the arXiv note on arm-swing interfering with simultaneous interaction applies directly. Reserve arm motion for the stick.
- Ranked options for this trainer (lowest sickness first):
  1. Fixed-spot drills (current design): zero artificial vection; keep it as the default.
  2. Discrete repositioning between reps: a short fade or blink to the next spot (teleport-class comfort), e.g., "point -> walk the line 3 m left" between shots.
  3. Short scripted glides with a vignette (0.4 to 0.6) and gentle acceleration, for situations where the skate path matters (e.g., gap control, backward skating while a puck carrier approaches). Keep them brief and infrequent per Meta guidance; ice is flat with distant walls, which Meta rates as comfortable geometry.
  4. Lean or small-step steering for fine positioning: measure HMD horizontal offset from a calibrated center (HMD-based detection is the norm per arXiv 2209.01059); a deadzone of a few cm, then a capped glide speed. Real steps of 20 to 40 cm map 1:1 and cost no comfort.
  5. Thumbstick slide as an opt-in: the bottom-hand controller's thumbstick is reachable while gripping, but it is the most sickening continuous method in the literature.
- "Skate-in-place" from knee bend or weight shift could be read from HMD height and lateral sway (crouch = skating stance), but no study of hockey-specific skate-in-place detection was found; treat as an experiment and keep it optional.
- Stand for training (presence gain, no sickness penalty per Clifton & Palmisano).
- Defenseman-specific: much D-zone and point play is small lateral shuffles, pivots and stick positioning, so a near-stationary player with discrete repositioning covers a large share of real D situations; full-ice rushes are the poor fit.

### Gaps
- No peer-reviewed study of skating-specific VR locomotion (hockey, speed skating, ski sims) on comfort or skill was found; hockey titles' locomotion is described only by store pages and listicles.
- Snap-turn angle recommendations: Meta's pages fetched give no numbers.
- No study found on arm-swing skating while also holding a virtual stick.

## 2. Keeping the player oriented without twisting the tether (world rotation, snap turn, reorientation, small-space Guardian, Link cable management)

### Takeaway
Rotate the world, not the player: present each drill facing the cable-free direction and use snap or scripted world rotation to face new situations; track cumulative real yaw and nudge the player back. Physically, a ceiling pulley, slack, and untwisting by reversing turns are the standard cable fixes; a stationary boundary suits a cluttered room.

### Cited Findings
- Snap turn is Meta's default comfort turn; smooth turn should be opt-in with tuned speed and acceleration. Snap, quick, blink, position-warp and teleport turns all help reorient. — [Meta, Locomotion best practices](https://developers.meta.com/horizon/design/locomotion-best-practices/); [Meta IWSDK Turn](https://developers.meta.com/horizon/documentation/web/iwsdk-concept-locomotion-turn/)
- A seated user can turn with the controller rather than physically turning (Meta content guideline example). — [Meta, Content guidelines](https://developers.meta.com/horizon/resources/publish-content-consider/)
- Discrete virtual rotation has been studied with pointing vs leaning-directed steering (uni- vs bimanual). — [arXiv 2406.14212](https://arxiv.org/pdf/2406.14212) (not read in full)
- Cable advice (retail blog, low authority): a ceiling pulley keeps the Link cable off the floor and reduces drag when turning; leave slack; route along walls; turning the same way repeatedly twists the cable, so reverse a few turns to untwist before a session. — [CordTheory, Quest Link cable management](https://cordtheory.com/quest-link-cable-management/); [Deep-Matrix, Link cable setup](https://deep-matrix.com/blog/quest-link-cable-setup-guide/)
- Quest 3 offers a room-scan or drawn custom boundary and a stationary boundary (third-party guide, not Meta). — [Tech-Insider, Quest 3 setup 2026](https://tech-insider.org/virtual-desktop-quest-3-setup-2026/)

### Inferences
- Make "drill forward" = the direction the cable hangs away from; the app can store that yaw at calibration and spawn each drill facing it.
- Track cumulative HMD yaw (unwrapped, not modulo 360) during a session; when it passes about +/-270 degrees, show a gentle "turn back" cue between reps, or fold the next drill's world rotation to bring him back to center.
- Hockey motions that turn the body (shoulder checks, retrieving a rim behind the net) can be staged so the puck path comes to him rather than requiring a full spin: e.g., spawn the rim retrieval already facing the boards rather than starting at the net and turning.
- Use a stationary boundary sized to the reach of a stick swing (the virtual stick extends past the controllers, so the boundary should protect the real hands, not the virtual blade). Keep the virtual blade well inside reach geometry so he does not swing real hands into furniture chasing a far puck.

### Gaps
- No official Meta guidance specific to tethered Link cable twist or cable-aware reorientation was found.
- No research on reorientation tricks (redirected rotation, world rotation gains) specifically for tethered stationary sports.

## 3. Does stationary practice transfer? (off-ice stickhandling/shooting, VR hockey training, how much skating matters for puck skills)

### Takeaway
Evidence that off-ice training transfers is real but modest and depends on how closely the off-ice movement matches the on-ice one; there is no controlled trial showing off-ice stickhandling (or VR stick work) transfers to on-ice puck control. VR hockey trainers mainly claim cognitive and decision-making transfer, backed by vendor data and one small youth study.

### Cited Findings
- Adolescent players: off-ice agility training transferred to on-ice skating and agility, but on-ice agility training was more beneficial; authors recommend mixing both. — [JSSM 2019](https://www.jssm.org/jssm-18-680.xml-Fulltext)
- A 2025 kinematic/EMG comparison of on-ice vs off-ice side-cutting found transfer "hinges on the consistency of an athlete's movement patterns between off-ice and on-ice environments," and off-ice patterns do not replicate on-ice stability demands. — [Frontiers in Bioengineering 2025](https://www.frontiersin.org/journals/bioengineering-and-biotechnology/articles/10.3389/fbioe.2025.1692676/full); [PMC12634552](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12634552/)
- Scoping review: off-ice and on-ice test results transfer modestly to selection and performance indicators. — [PMC8473052](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8473052/)
- In elite juniors, off-ice indicators were not strongly associated with point shares. — [PMC9465767](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9465767/)
- A registered trial (Leksand) is studying grip strength as critical to stickhandling, shooting, passing and puck control; no results yet. — [ClinicalTrials.gov NCT07115160](https://clinicaltrials.gov/study/NCT07115160)
- Practitioner sources argue off-ice stickhandling with high repetition and instant feedback corrects flaws (not controlled studies). — [Stickhandling Master PDF](https://cdn3.sportngin.com/attachments/document/0127/7285/L._Stick_Handling_Master.pdf); [Potent Hockey](https://potenthockey.com/blogs/news/train-smarter-at-home-your-guide-to-off-ice-hockey-practice)
- Sense Arena FAQ claims studies and testimonials show VR training translates cognitive skills on-ice, and cites average improvement after 20 sessions without study design details (vendor). — [Sense Arena FAQ](https://hockey.sensearena.com/resources/faqs)
- A Charles University (Prague) study with 10 to 11 year olds developed a VR program focused on cognitive processes and hockey-specific activities (Peric 2019, cited secondhand; the original was not found). — [Skelton literature review 2020](https://nicholasdskelton.com/2020/11/08/5314-final-submission/)

### Inferences
- The likely transferable value of a controllers-only, stationary trainer is perceptual-cognitive (reads, timing, where to put the stick, pass selection, shot selection at the point) more than fine motor puck control, because the motor pattern differs (no stick weight, no blade-ice contact, controllers instead of a shaft).
- To maximize motor-pattern similarity anyway (the 2025 side-cutting finding): keep his real stance (knees bent, lower body as on ice), keep the hand spacing and top/bottom hand roles matching a left shot, and keep stick lie/length matched to his real stick so the blade sits where his eyes expect it.
- Skating matters for puck skills mainly through body position relative to the puck; the drills he chose (behind-net retrieval, point play) are the situations where a D-man skates least, which suits a stationary trainer.

### Gaps
- No randomized or controlled study found on off-ice stickhandling transfer to on-ice puck control.
- No independent (non-vendor) study found on VR hockey training transfer, and none on controller-only (no stick) hockey training.
- No study found quantifying how much skating movement contributes to puck skill acquisition.

## 4. Game audio for physical feel (real hockey sounds, recorded vs synthesized, variation, spatial audio, impact sound and perceived weight/hardness, VR sports games)

### Takeaway
Impact sound measurably changes perceived hardness, stiffness and weight: higher frequency and faster decay read as harder/stiffer, louder and lower-pitched read as heavier. Standard game practice is a pool of recorded variants per contact type, small random pitch/gain offsets, and collision speed driving gain (and sometimes pitch); recorded arena libraries exist for puck-on-blade, boards, glass and ice.

### Cited Findings
**Perception research**
- Klatzky, Pai & Krotkov (2000): both decay and frequency of synthetic contact sounds affected judgments of material; they gave a regression metric for perceived material similarity from impact sounds (older, 2000). — [Perception of material from contact sounds (UBC PDF)](https://www.cs.ubc.ca/labs/lci/papers/docs2000/pai-KlaPai00.pdf)
- Hardness is the key perceptual dimension in contact sounds; sounding-object hardness relies on the most accurate acoustic information, while impact properties more strongly drive perceived hammer (striker) hardness; listeners rate hardness from synthetic impacts too. — [Giordano et al., Material categorization and hardness scaling](https://www.researchgate.net/publication/267977938_Material_categorization_and_hardness_scaling_in_real_and_synthetic_impact_sounds); [Giordano & Avanzini, Perception and Synthesis of Sound-Generating Materials (2014)](https://avanzini.di.unimi.it/downloads/publications/giordano_springer14.pdf)
- PHANToM experiments: when people tapped virtual surfaces while hearing impact sounds, their stiffness rankings rose with the sound's auditory stiffness, for recorded and synthesized sounds (DiFranco et al., 1990s). — [The Effect of Sound on Haptic Perception](https://www.researchgate.net/publication/221012240_The_Effect_of_Sound_on_Haptic_Perception)
- Low-level acoustic features (frequency, damping) affected multisensory stiffness more than the sound's material category; auditory influence differs between unisensory and multisensory tasks. — [PLOS ONE 2016, "Metal Sounds Stiffer than Drums"](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0167023)
- Louder sounds make physical and virtual objects feel heavier; low-pitched sounds are perceived as heavier. — [MDPI Applied Sciences 2024, review of audio-based pseudo-haptics](https://www.mdpi.com/2076-3417/14/14/6020); [Audio-influenced pseudo-haptics review 2025](https://www.researchgate.net/publication/393882712_AUDIO-INFLUENCED_PSEUDO-HAPTICS_A_REVIEW_OF_EFFECTS_APPLICATIONS_AND_RESEARCH_DIRECTIONS)
- Pseudo-haptics (cross-modal visual/audio cues) is an established approach for conveying haptic properties without force feedback. — [Pseudo-haptics survey, arXiv 2406.01102](https://arxiv.org/pdf/2406.01102)

**Real hockey sound sources**
- A 292-effect ice hockey library recorded in an indoor arena with natural reverb includes puck-on-boards, slap shots, goalie pads, and a puck with a recorder taped to it sliding on ice. — [A Sound Effect, Ice Hockey](https://www.asoundeffect.com/sound-library/ice-hockey/); [Hockey sound effects collection](https://www.asoundeffect.com/sound-library/hockey-sound-effects/)
- Stick libraries cover shot types, passes, drops, scrapes, stick-on-stick, boards and ice; Sound Ideas has puck-into-boards, slap shot on boards, stick on glass. — [Pond5 hockey stick and puck](https://www.pond5.com/sound-effects/1/hockey-stick-and-puck.html); [Sound Ideas album](https://music.apple.com/ca/album/hockey-sound-effects/948981149)

**Variation and physics-driven playback**
- Small random pitch shifts per play reduce repetition and improve feel; pitch can encode collision strength or speed. — [Game Developer, The Power of Pitch Shifting](https://www.gamedeveloper.com/audio/the-power-of-pitch-shifting)
- Typical starting values (guide, low authority): 5 to 10 variants, pitch +/-10%, volume +/-3 dB. — [Generalist Programmer, Game audio guide 2026](https://generalistprogrammer.com/game-audio-development)
- NVIDIA Boom: impact events from physics pick a random sound from the pool for the matching threshold group; volume is computed from event data and per-material thresholds. — [NVIDIA Omniverse Boom docs](https://docs.omniverse.nvidia.com/kit/docs/omni.audio.boom/latest/index.html)
- Impact sounds built from 3 layers with independent variation; impact sound changes with ball speed. — [GameDev.net, Sounds in Roundrick](https://gamedev.net/tutorials/audio/music-and-sound-fx/sounds-in-roundrick-r4714)
- Physically based synthesis directly from physics-engine collision data (VFoley, Phya) is an alternative to samples (older). — [Southampton eprint](https://eprints.soton.ac.uk/371717/1/10.1.1.149.9848.pdf)

### Inferences
- Since controllers carry no stick weight, sound is one of the few channels that can sell puck mass and blade stiffness. Use the research directly: a puck-on-blade "catch" should have a clear low-mid body (weight) plus a short, bright transient (hard rubber on composite), with fast decay; a soft pass reception = quieter, duller (lower cutoff), longer; a slapper = loud, bright, with a crack layer.
- Map 1 kHz physics data to sound parameters at the moment of contact: relative normal speed -> gain (and a little brightness via low-pass cutoff or pitch), contact type (blade heel/toe, ice, boards, glass, post, stick-on-stick) -> sample pool. Continuous contacts (puck cradled on blade while stickhandling, blade scraping ice) need a looping scrape layer whose gain follows tangential speed, not one-shot triggers.
- Hybrid approach fits his pipeline: short recorded one-shots for the transient character (licensed library or his own phone recordings at a rink), synthesized modal decays to vary pitch and decay per hit cheaply (Klatzky's decay/frequency parameters are the knobs).
- Spatial: real sound from distant events arrives late (sound travels about 343 m/s, so a puck hitting end boards 50 m away is heard about 145 ms after it happens). Simple distance gain + delay + left/right panning by head-relative azimuth gets most of the cue; the stick-blade sounds are close to the head and need little spatialization but must be the fastest path.
- An arena ambience bed (low rink hum, distant skates, occasional crowd) masks silence between contacts and makes the space feel large; keep it quiet so contact sounds stay dominant.

### Gaps
- No acoustic or spectral analysis of puck-on-blade, puck-on-ice or puck-on-post contact was found.
- No public talk or article found on how a leading VR sports game (e.g., Eleven Table Tennis, hockey titles) builds its contact audio; no NHL broadcast audio workflow found.
- No VR-specific study of impact sound changing perceived stick or puck weight when the user holds a controller (all perception findings are lab or desktop haptic setups).

## 5. Audio and haptic latency on Windows PC VR (winsound vs low-latency engines, Python options, mixing, Link audio routing, simultaneity thresholds)

### Takeaway
winsound cannot play from memory asynchronously and is not a mixer, so it is the wrong tool; a single continuously running output stream with a mixing callback (python-sounddevice/PortAudio on WASAPI, or miniaudio) is the standard fix. Shared-mode WASAPI floors around 10 ms periods and 20 to 45 ms measured end-to-end; exclusive or IAudioClient3 low-latency modes go lower. Detection thresholds for impact-sound asynchrony are roughly 25 ms (sound early) and 40 to 50 ms (sound late), so the whole hand-to-ear path should aim under about 40 ms.

### Cited Findings
**winsound**
- winsound: SND_ASYNC returns immediately; SND_MEMORY plays a WAV memory image, but "This module does not support playing from a memory image asynchronously, so a combination of this flag and SND_ASYNC will raise RuntimeError"; SND_NOSTOP does not interrupt playing sounds; SND_PURGE is "not supported on modern Windows platforms"; PlaySound(None, 0) stops any playing waveform sound. — [Python docs, winsound](https://docs.python.org/3/library/winsound.html)

**Windows audio paths and measured latencies**
- Windows 10+ low-latency audio: apps can query driver-supported buffer sizes and choose one through WASAPI (IAudioClient3) or AudioGraph. — [Microsoft Learn, Low Latency Audio](https://learn.microsoft.com/en-us/windows-hardware/drivers/audio/low-latency-audio)
- python-sounddevice: latency='low' or 'high' (default 'high') selects the device's default low/high latency, or a value in seconds; the open stream's actual latency is readable via its latency attribute; WasapiSettings(exclusive=True) enables exclusive mode (docs updated 2026-10-26). — [python-sounddevice docs PDF (0.5.6)](https://app.readthedocs.org/projects/python-sounddevice/downloads/pdf/latest/); [python-sounddevice 0.3.11 PDF](https://python-sounddevice.readthedocs.io/_/downloads/en/0.3.11/pdf/)
- A WASAPI inspection tool reports driver buffer figures such as 3 ms low / 10 ms high on one machine, explicitly not total latency. — [negg0s/wasapi-latency](https://github.com/negg0s/wasapi-latency)
- Shared-mode periods: one Windows 11 report found 480 frames (10 ms) as default, minimum and maximum on several devices; miniaudio reported 480-frame internal buffers even when 128 was requested. miniaudio passes the requested period to the backend and inserts an intermediate buffer if the backend cannot match. — [miniaudio discussion #1084](https://github.com/mackron/miniaudio/discussions/1084); [miniaudio issue #949](https://github.com/mackron/miniaudio/issues/949)
- Estimated shared-mode minimum = 10 ms engine + 10 ms driver = 20 ms; exclusive about 10 ms (2018, older). — [Nirbheek, Low-latency audio on Windows with GStreamer](https://blog.nirbheek.in/2018/03/low-latency-audio-on-windows-with.html?showComment=1525112690757)
- Measured: OpenAL Soft lowest shared period tended to 30 ms and up, exclusive about 20 ms; a miniaudio user measured 45 ms shared and (oddly) 125 ms exclusive at a 128-frame request; "low-latency shared mode is just very device/driver specific." — [OpenAL Soft issue #682](https://github.com/kcat/openal-soft/issues/682); [miniaudio issue #937](https://github.com/mackron/miniaudio/issues/937)
- A user reports WASAPI exclusive below about 11 ms crackles on their hardware. — [Steam forum](https://steamcommunity.com/app/607260/discussions/0/2289464808490899892)
- About 1 to 1.5 ms output latency with sounddevice on WDM-KS, oscilloscope-measured (2015, Windows 7, anecdotal). — [PsychoPy forum](https://discourse.psychopy.org/t/low-sound-latency-with-sounddevice-module-wdm-ks-driver/912)
- pygame.mixer: pre_init must be called before pygame.init(); historical default buffer was large (3072 then 4096 samples); a 2012 Windows report saw no latency change when shrinking the buffer to 128 (older). — [pygame users list 2012](https://archives.seul.org/pygame/users/Dec-2012/msg00023.html); [Blender Artists, pygame docs quote](https://blenderartists.org/t/pygame-for-blender-2-49b-windows/459539)

**Link / headset audio**
- Users report 100 to 200 ms (and 100 to 250 ms in a guide) of headset audio delay when audio is routed through SteamVR's Quest audio device, which disappeared when output went to PC headphones; the guide says native Oculus/Meta apps do not show it (forum and guide claims, unverified). — [Steam forum, SteamVR](https://steamcommunity.com/app/250820/discussions/0/3193621324043154078); [MediaModHub](https://mediamodhub.com/how-to-fix-audio-desync-in-vr-headsets/)
- Guides recommend a 48 kHz format on both sides to avoid resampling desync (unverified). — [MediaModHub](https://mediamodhub.com/how-to-fix-audio-desync-in-vr-headsets/)
- A single report of about 1 s audio delay over Air Link in Half-Life: Alyx (anecdotal). — [Steam forum, Half-Life: Alyx](https://steamcommunity.com/app/546560/discussions/0/3122659822742963100)

**Simultaneity thresholds**
- Tap-to-sound simultaneity threshold: about -25 ms (sound first) and +42 ms (hit first) on average (cited in the driving paper). — [arXiv 2307.05451](https://arxiv.org/html/2307.05451)
- Audio-haptic (force-feedback wheel): mean detection thresholds 123 ms (haptic first) and 88 ms (audio first); 20% of drivers noticed 50 ms audio-first or 65 ms haptic-first offsets. — [arXiv 2307.05451](https://arxiv.org/abs/2307.05451)
- Virtual button: audio-tactile thresholds 179 ms (audio first) and 451 ms (haptic first), showing thresholds depend heavily on task. — [IEEE ToH 2023](https://doi.org/10.1109/toh.2023.3268842)
- Visual-haptic: asynchronies of about 45 ms often cited; 20 to 50 ms often unnoticed. Audio-visual: delays detected at 15 to 50 ms when audio leads, 40 to 140 ms when video leads. — [Detection of temporal delays in visual-haptic interfaces](https://www.researchgate.net/publication/8555436_Detection_of_Temporal_Delays_in_Visual-Haptic_Interfaces); [PMC5193434](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5193434/)

### Inferences
- Replace winsound with one persistent output stream: open a sounddevice.OutputStream (WASAPI host API, 48 kHz, float32, blocksize 128 to 256 frames = 2.7 to 5.3 ms) at startup; preload all samples as numpy arrays; the physics thread pushes small events (sample id, gain, pitch/rate, pan, scheduled sample offset) into a queue; the callback pops events and sums active voices into the output block. This gives unlimited overlapping sounds, no file I/O per hit, and a fixed, measurable latency (read stream.latency).
- The callback is Python, so it needs the GIL; a busy 1 kHz Python physics loop can delay it and cause underruns. Keep the callback to a few numpy adds, keep a voice cap (e.g., 16), and if underruns appear, raise blocksize one step before trying exclusive mode. Exclusive mode on the Quest's virtual audio endpoint may not be supported; test.
- Timestamp-accurate onsets: when the physics thread detects a contact at time t, convert it to a sample offset within the next block so hits are not quantized to block boundaries (matters at 1 kHz physics, where contacts happen between audio blocks).
- Output device choice: the Link headset endpoint is the natural target. Pick it explicitly by name in sounddevice rather than relying on the Windows default; avoid any SteamVR audio redirection, since the large reported delays are tied to that path. Measure end-to-end once (e.g., record the headset speaker and a controller tap with a phone at high frame rate) rather than trusting reported numbers.
- Target budget from the thresholds: sound may lag the visual/haptic contact by up to about 40 ms before people notice (hit-first threshold about 42 ms), but sound that leads is noticed at about 25 ms. So never play the sound early (no prediction-driven early triggers unless confident); aim for total contact-to-ear latency of 20 to 40 ms.
- Haptics: Touch Plus haptics would be triggered through OpenXR (xrApplyHapticFeedback). Since audio leading haptics is noticed at smaller offsets than the reverse, trigger the haptic pulse on the same physics event as the sound, and do not hold the haptic back to sync with slower audio.

### Gaps
- No measured latency for winsound.PlaySound was found (Jon's "tens of milliseconds" observation stands as the only data point), and the docs do not state whether PlaySound overlaps sounds.
- No official Meta figure for Link (wired) headset audio latency, and no data on whether WASAPI exclusive works on the Quest audio endpoint.
- No measurements found for XAudio2, FMOD or Wwise on Windows in comparable setups, nor for the pyminiaudio Python binding's period control.
- No measurement of OpenXR haptic (xrApplyHapticFeedback) latency over Link was found.

## 6. End-to-end motion-to-photon and controller latency over Link, prediction, and Python app practices (render rate, timing, threading, GIL)

### Takeaway
Over wired Link with the Meta OpenXR runtime, a hobbyist measured about 32 ms headset motion-to-photon at high bitrate (about 80 ms at 150 Mbps); controller latency is largely hidden by runtime prediction (2 to 13 ms effective on older PC headsets in a peer-reviewed test), but only if the app locates controllers at the frame's predictedDisplayTime, as late as possible before rendering. In Python, the render loop must hit frame rate reliably (ASW masks misses but adds artifacts), and sleeping or GIL contention in the physics thread must not starve it.

### Cited Findings
- Hobbyist measurement (Quest 2): wired Link with the Oculus OpenXR runtime gave about 32 ms headset delay at 500 Mbps; around 150 Mbps gave about 80 ms; the cable itself likely adds little. — [Greendayle, VR motion-to-photon latency (GitHub)](https://github.com/Greendayle/VR-Motion-to-photon-latency-)
- Peer-reviewed controller motion-to-photon measurement (HTC Vive, Rift, Rift S, Valve Index; not Quest Link): with motion prediction, latency was functionally 2 to 13 ms (2022). — [Behavior Research Methods 2022, s13428-022-01983-5](https://link.springer.com/10.3758/s13428-022-01983-5) (full text not accessible; figure from abstract summary)
- OpenXR: predictedDisplayTime from xrWaitFrame is the anticipated display time of the next frame, and "the better the predicted display time, the less latency experienced by the user"; in 1.1 it refers to the midpoint of the display interval. Controllers are located by passing that time to xrLocateSpace on a pose action space after xrSyncActions; past times are allowed only back to about 50 ms before the latest pose, otherwise position may be invalid. — [OpenXR 1.0 spec](https://registry.khronos.org/OpenXR/specs/1.0/html/xrspec.html); [OpenXR 1.1 spec](https://registry.khronos.org/OpenXR/specs/1.1/html/xrspec.html)
- Prediction becomes increasingly accurate when called closer to the target time. — [OpenXR DisplayTiming docs (Haskell binding)](http://expipiplus1.github.io/vulkan/openxr-0.1-docs/OpenXR-Core10-DisplayTiming.html)
- Meta: calling xrWaitFrame early on the main thread gives the freshest predicted time for head and controller queries; doing it on the render thread forces estimated timing, so poses can lag one frame by display time (Unity setting). — [Meta, Unity OpenXR settings](https://developers.meta.com/horizon/documentation/unity/unity-openxr-settings/); [Meta, Synchronizing and submitting frames](https://developers.meta.com/horizon/documentation/native/android/mobile-openxr-frames/)
- Oculus Debug Tool: PC ASW can be Disabled / forced 45 fps with or without ASW / Auto; Meta recommends turning ASW off to judge app performance; Encode Bitrate accepts 1 to 2000 Mbps, with high values risking instability; dynamic bitrate is available. — [Meta, Oculus Debug Tool](https://developers.meta.com/vr/documentation/native/pc/dg-debug-tool/?locale=en_US)
- Python 3.11+ on Windows: time.sleep uses a high-resolution waitable timer (docs state 100 ns resolution on Windows 10+); before 3.11 the timer resolution was about 15.6 ms without the high-resolution flag or 1 ms with timeBeginPeriod; time.time() and time.monotonic() can stay coarse because they follow interrupt time. — [Python docs, time](https://docs.python.org/3/library/time.html); [bpo-45429](https://bugs.python.org/issue45429); [CPython commit 55868f1](https://github.com/python/cpython/commit/55868f1a335cd3853938082a5b25cfba66563135); [discuss.python.org](https://discuss.python.org/t/higher-resolution-timers-on-windows/16153)

### Inferences
- Render loop order per frame: xrWaitFrame -> xrBeginFrame -> xrSyncActions -> xrLocateSpace(controller, predictedDisplayTime) -> draw -> xrEndFrame. Locate the stick pose immediately before drawing, not at the top of a long frame. Draw the stick from that predicted pose even if physics used an older sample, so the blade the eye sees matches the hand.
- Physics thread at 1 kHz: sample controller pose with xrLocateSpace at "now + a few ms" (or at the latest predicted time) each tick, or interpolate between poses the render thread publishes. Check pyopenxr/runtime thread-safety for calling xrLocateSpace off the render thread before relying on it (not verified here).
- Use time.perf_counter() (not time.time()) for all physics and audio-event timestamps; on Python 3.11+, time.sleep(0.001) is precise enough for a 1 kHz loop, but a busy-wait tail of about 0.2 ms tightens jitter at a CPU cost.
- GIL: the 1 kHz pure-Python physics, the render thread, and the audio callback all contend for one interpreter lock. Vectorize physics with numpy or move the inner loop to compiled code (numba, Cython) so it releases the GIL; consider lowering sys.setswitchinterval (the default switch interval is 5 ms per Python docs, not fetched here) so the render and audio threads get the lock sooner.
- Run at the Quest 3 Link refresh you can always hold (72, 90 or 120 Hz); a line renderer should hold 90 or 120 Hz easily. Test with ASW disabled in the Debug Tool to see real misses, then decide whether to leave it on Auto.
- Budget sketch for "blade touches puck" (estimates, not measurements): pose sample at most 1 ms (1 kHz physics) + contact detection within the same tick + visual on next displayed frame (prediction hides most tracking delay; plus up to one frame of 8 to 11 ms) + audio 10 to 40 ms depending on the stream setup and Link audio path. Audio is likely the slowest leg, which is why the persistent low-latency stream matters most.

### Gaps
- No measured controller motion-to-photon or haptic latency for Quest 3 over wired Link was found; the 32 ms figure is a Quest 2 hobbyist headset measurement.
- No source found on pyopenxr-specific threading rules or GIL behavior in pyopenxr calls.
- The 2022 Behavior Research Methods article could not be opened (login redirect); its per-headset raw latencies are not recorded here.
