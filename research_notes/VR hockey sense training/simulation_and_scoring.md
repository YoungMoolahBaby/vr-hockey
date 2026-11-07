# Simulating opponents and teammates, and scoring decisions, in a VR hockey-sense trainer

Scope: how virtual skaters should move and behave (kinematics, timing, cues), how to author and adapt scenarios, how to score decisions, and how existing VR sports trainers build content. Unit conversions and derived numbers are marked as inferences. "Snippet-level" means the figure came from a search-result excerpt and the page itself was not opened. Those figures should be checked before they go into code.

---

## 1. Realistic hockey kinematics for simulated skaters, passes and shots (NHL vs. adult recreational)

### Takeaway
NHL tracking gives solid figures for elite peak speeds. The median forward tops out just over 22 mph (about 9.8 m/s), the median defenseman just under, and record speeds reach about 24.6 mph (11 m/s). Biomechanics studies give elite acceleration of about 4.4 m/s² over the first 6 m. Measured pass speeds, average in-game speeds and any adult-recreational skating kinematics are poorly documented, so recreational values must be scaled down from elite data and tuned by hand.

### Cited Findings
**Skating speed (NHL EDGE tracking)**
- Median forward top speed is slightly above 22 mph. The 10th-90th percentile range for forwards is about 21-23 mph. The median defenseman is slightly below 22 mph, with a 10th-90th percentile range of about 20.2-22.8 mph. The fastest recorded skaters are Denis Gurianov (forward, 2021-22) at 24.6 mph and Martin Fehervary (defenseman, 2022-23) at 24.21 mph. — [Puck Over The Glass, NHL EDGE skating speed part 1](https://puckovertheglass.substack.com/p/nhl-edge-skating-speed-part-1)
- EDGE counts a "speed burst" from an 18 mph threshold up, and also reports 20+ and 22+ mph tiers. Forwards burst at about twice the rate of defensemen. The 10th-percentile forward bursts more often than the 90th-percentile defenseman. — [Puck Over The Glass part 1](https://puckovertheglass.substack.com/p/nhl-edge-skating-speed-part-1)
- Average even-strength speed has a similar range for both positions, with defensemen a bit more than 1 mph slower than forwards. EDGE does not publish an exact league average. Average speed is counted at even strength only, because special teams play at a slower pace. — [Puck Over The Glass part 1](https://puckovertheglass.substack.com/p/nhl-edge-skating-speed-part-1)
- Average top speed in 2024-25 was 22.03 mph for forwards and 21.54 mph for defensemen. Forwards averaged about 1.3 bursts of 20+ mph per game and defensemen about 0.54 (snippet-level). — [Dobber Hockey](https://dobberhockey.com/?p=83264). Another 2025-26 summary gives an average max of about 21.65 mph for forwards and about 21.72 mph for defensemen (snippet-level, so the sources disagree slightly). — [The Hockey Fanatic](https://www.thehockeyfanatic.com/?p=3772)
- In the 2026 Stanley Cup Final, the top skating speed was 23.53 mph (Eric Robinson). Jack Eichel led with 34 bursts of 20+ mph across the Final, including 10 in one game, and 105 across the playoffs. He had only five 22+ mph bursts in the whole postseason. — [NHL.com EDGE leaders](https://www.nhl.com/news/nhl-edge-stats-leaders-for-2025-2026-season)
- In 2025-26 McDavid led the league with 94 bursts of 22+ mph and 419 bursts of 20+ mph (snippet-level, mid-season). — [NHL.com EDGE leaders](https://www.nhl.com/news/nhl-edge-stats-leaders-for-2025-2026-season)

**Acceleration and sprinting**
- Greer & Dillman studied 69 elite players at the 1983 National Sports Festival. Velocity at 20 ft (6.1 m) was 7.07 m/s, and average acceleration over that distance was 4.37 m/s². — [ISBS proceedings, Acceleration of elite ice hockey players](https://ojs.ub.uni-konstanz.de/cpa/article/view/1412/1170)
- Buckeridge et al. tested 9 elite and 9 recreational players on 30 m maximal forward sprints. The elite players were faster in the acceleration phase. Elite players mainly activated the hip abductors and knee extensors together, while recreational players relied more on the ankle plantar flexors. Strides could be classified by skill level with 83% success. — [BISp record, Buckeridge et al. 2015](https://www.bisp-surf.de/Record/PU201709007467)
- Elite U14 players (US camp) ran a 30 m forward sprint in 4.34 ± 0.14 s. — [Sport-iat record](https://lida.sport-iat.de/ta/Record/4070638)
- A Swiss study of 57 U17, U20 and pro players timed 0-10, 10-20 and 20-30 m splits. The 10-20 m split best separated developing players from elite ones. — [VALD summary](https://valdperformance.com/news/sprint-performance-in-elite-ice-hockey)

**Reaction time and reach (parameters used in a published hockey rink-control model)**
- A player-motion model for hockey used these values (Big Data Cup-style analysis of the 2022 Olympic women's tournament):
  - reaction time t_r = 0.189 s (from Lipps et al. 2011)
  - max speed v_max = 35.5 ft/s (10.8 m/s; Kendall Coyne Schofield, 2019 NHL All-Star skills event)
  - resistance γ = 1.3 s⁻¹ (Fujimura & Sugihara 2005)
  - pick-up reach of 6.5 ft
  - defenders' intercept reaction time = t_r + 0.1 s
  - goalies restricted to within 8 ft of the net

  — [Pass Evaluation in Women's Olympic Hockey (arXiv 2205.13678)](https://ar5iv.labs.arxiv.org/html/2205.13678)
- Elite handball goalkeepers in VR took 348-372 ms from ball release to peak forearm acceleration. Level of graphical detail did not change this time significantly. — [Vignais et al. 2009, JSSM](https://jssm.org/08-4-501.p_d_f)

**Pass and puck physics**
- The same paper modelled passes as soft, medium and hard at 45, 65 and 85 ft/s, chosen from summary statistics of attempted passes. Puck-ice friction was μ = 0.1, with Stokes drag k/m (Allain 2020). Trajectories were evaluated every 0.05 s and every 0.05 rad. — [arXiv 2205.13678](https://ar5iv.labs.arxiv.org/html/2205.13678)
- A LINHAC paper studied how pass speed affects reception success for all 5v5 NHL passes in 2017-18. I could not see the results. — [LINHAC paper](https://www.ecp.ep.liu.se/index.php/linhac/article/download/739/644)
- A low-authority trivia source puts typical NHL passes at 30-60 mph and hard passes at 80-90 mph. Treat these as unverified. — [QuizzClub](https://quizzclub.com/trivia/what-is-the-average-speed-of-a-hockey-puck/answer/5762)

**Shot speed**
- Slap shots measured by Woo et al.: elite 29.14 ± 1.39 m/s, recreational 26.46 ± 0.66 m/s. — [ISBS, The ice hockey slap shot, elite versus recreational](https://ojs.ub.uni-konstanz.de/cpa/article/view/1368)
- Wu et al. 2003 compared 20 skilled and 20 unskilled players. Slap shots were much faster than wrist shots, and puck speed depended on skill and strength. I could not get the figures. — [BISp record](https://www.bisp-surf.de/Record/PU201103001949)
- In 20 pro and semi-pro players, strength and power correlated with puck speed at r = .29-.72 for wrist shots and .16-.62 for slap shots. — [Bežák & Přidal 2017, Acta Gymnica](https://doaj.org/article/8eda0e09c0ae4356ab9aed27e8a9bdd8)
- 2026 Stanley Cup Final: hardest shot attempt 95.12 mph (Nikishin), hardest shot on goal 91.44 mph (Marner). — [NHL.com](https://www.nhl.com/news/nhl-edge-stats-leaders-for-2025-2026-season)

**Workload and shift structure**
- In 113 recreational men over 35 (Hockey Heart Study), heart rate averaged a maximum of 184 bpm in games. In 75.6% of recordings it went above the age-predicted maximum, and it stayed above 85% of the predicted maximum for about 30 minutes. — [Atwal et al. 2002, CMAJ](https://www.cmaj.ca/content/cmaj/166/9/1131.4.full-text.pdf)
- Professional players skate about 4-5 km per game, almost half of it at high intensity. Shifts last 30-80 s with 4-5 min of recovery (snippet-level). — [Sports Medicine Open 2015](https://link.springer.com/content/pdf/10.1186/s40798-015-0026-8.pdf). This conflicts with NHL EDGE, which recorded Shea Theodore skating 5.86 miles (about 9.4 km) in one Final game. — [NHL.com](https://www.nhl.com/news/nhl-edge-stats-leaders-for-2025-2026-season)

**Tracking data rates (for replaying real data)**
- In the NHL puck-and-player tracking system, the puck was located 60 times per second and each player 15 times per second (1 Hz while on the bench), using infrared emitters triangulated by 14-16 roof cameras. The league later moved toward optical or other tracking, so the current hardware may differ. — [SportTechie/SMT](https://smt.com/watching-hockey-through-a-four-inch-window-how-real-time-data-is-poised-to-transform-the-nhl); [SVG](https://www.sportsvideo.org/2020/01/27/live-from-nhl-all-star-active-player-puck-tracking-is-set-to-transform-nhl-stanley-cup-playoffs/)
- Stathletes' broadcast-derived tracking of the 2022 Olympic women's games runs at 30 fps. — [arXiv 2205.13678](https://ar5iv.labs.arxiv.org/html/2205.13678)

### Inferences
- Conversions:
  - 18 mph = 8.0 m/s; 20 mph = 8.9 m/s; 22 mph = 9.8 m/s; 24.6 mph = 11.0 m/s
  - passes of 45/65/85 ft/s = 13.7/19.8/25.9 m/s (31/44/58 mph)
  - Woo slap shots: elite 65 mph, recreational 59 mph
  - The U14 30 m time of 4.34 s means an average of 6.9 m/s.
- Elite starting parameter set for an NHL-like opponent:
  - v_max 10-11 m/s for rush attackers
  - typical "high-speed" skating 8-9 m/s, used sparingly: even McDavid's rate implies a few 22+ mph bursts per game
  - first-step acceleration about 4-4.5 m/s² from a standstill
  - first-order velocity response with γ ≈ 1.3 s⁻¹
  - perception-to-action delay about 0.19 s, plus about 0.1 s for defenders reacting to a puck release
- Recreational adults: no measured skating kinematics exist (see Gaps). A defensible starting point is about 70-85% of elite speed and noticeably lower acceleration (the Buckeridge finding of weaker hip/knee drive), tuned by playtesting. Slap shot speed is only about 10% lower in Woo's lab data, but the Woo "recreational" group was probably fairly skilled.
- Puck flight time sets the decision window. At 26 m/s a 15 m pass takes about 0.6 s, ignoring friction. A 90 mph (40 m/s) shot from 30 ft (9.1 m) arrives in about 0.23 s. The engine should model time-to-intercept per player, not just distance.
- To replay real data, upsample 15 Hz player tracking and 30 Hz broadcast tracking to 72-120 Hz headset rates with smoothing (for example a spline or a Kalman filter). Then retarget onto mocap skating cycles, because tracking gives only a centroid.
- Opponents that skate at a constant top speed will look wrong. Elite skating mixes glide, short bursts and pivots, and fatigue lowers average speed late in games (see Gaps).

### Gaps
- No peer-reviewed measurement of skating speed or acceleration in adult recreational ("beer league") games. The Hockey Heart Study measured heart rate only.
- No reliable source for NHL pass speed distributions. The arXiv bins are the best citable values.
- No data on turning radius, crossover or tight-turn kinematics, or backward-skating speed at any level. EDGE does not publish these, and no biomechanics paper surfaced.
- No wrist or snap shot speeds by skill level in m/s (Wu et al. 2003 likely has them but was not readable).
- No hockey-specific choice reaction times. 0.189 s is a generic simple reaction time.

---

## 2. Behaviour models for virtual players: scripted vs. rule-based vs. learned, and the visual fidelity needed

### Takeaway
Research shows experts read an opponent's movement (kinematics), not surface appearance. Expert advantages survive reduction to point-light or untextured avatars, so the money should go into accurate, mocap-driven body and centre-of-mass motion rather than photorealism. Learned "ghosting" models from tracking data exist for soccer and American football but not for hockey, and simple baselines are hard to beat. A practical engine combines real-data playbacks or scripted plays with a rule-based reactive layer.

### Cited Findings
**Visual fidelity and kinematic cues**
- Vignais et al. 2009 (10 top-league French handball goalkeepers, CAVE display) tested five levels of detail:
  - L0 textured, L1 untextured, L2 wireframe, L3 point-light, and L4 point-light with a 5 cm ball instead of 15 cm
  - Time to respond (348-372 ms), stop success (L0 26.2%, L1 24.5%, L2 27.3%, L3 21.3%, L4 16.4%) and limb-to-ball distance did not differ significantly across levels.
  - Limb trajectories did differ between L1 and the point-light levels, so goalkeepers changed motor strategy.
  - Throws were mocapped at 200 Hz (12 cameras, 36 markers) and played back through the MKM animation engine. Ball speed was 20 m/s, and the ball was occluded at 6 m.
  - Ten extra throws to other targets were mixed in to keep goalkeepers uncertain.

  — [Vignais et al. 2009, JSSM](https://jssm.org/08-4-501.p_d_f)
- A related study by the same group (2010, a judgment task rather than a motor task) reportedly found judgments in the L4 point-light-ball condition significantly less accurate than in all other conditions (snippet-level, not verified). — [Franck Multon publications 2010](https://people.irisa.fr/Franck.Multon/2010.htm)
- In badminton, 12 world-class and 12 non-expert players predicted stroke depth from video or point-light displays. Experts kept the same pattern of information pick-up under point-light display and drew on kinematic features novices could not use. — [Abernethy, Zawi & Jackson 2008, via HKU repository](https://repository.hku.hk/handle/10722/115071)
- An fMRI study found task-sensitive brain areas were very similar for normal and point-light badminton clips, which points to kinematics as the key information. — [Wright et al. 2011, via Neurosynth](https://neurosynth.org/studies/21741450)
- With deceptive running actions, point-light results closely matched filmed ones. Experienced players beat novices but were still impaired by deception. — [Mori & Shimada 2013, Attention, Perception & Psychophysics](https://link.springer.com/content/pdf/10.3758/s13414-013-0435-z.pdf)
- Rugby side-step in VR (Brault et al. 2012):
  - Experts used the honest cue, centre-of-mass dynamics (tau-based).
  - Novices were fooled by deceptive upper-trunk yaw and out-foot placement (p < .001).
  - Experts waited longer before moving, which gave them more information and fewer errors (p < .05).
  - Deceptive attackers organise head, trunk and upper limbs to deceive while keeping centre-of-mass displacement small.

  — [Brault et al. 2012, PLoS ONE](https://pmc.ncbi.nlm.nih.gov/articles/PMC3372470/); [follow-up 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6743770/)
- A VR handball study used morphed genuine and disguised throws on human-like avatars to test how kinematic cues are weighed against situational probability. — [VU Amsterdam, PSE](https://research.vu.nl/ws/files/121792032/Integrating_situational_probability_and_kinematic_information_when_anticipating_disguised_movements.pdf)
- Point-light training improved cricket batters' prediction of ball type. The on-field benefit appeared only for body positioning, not bat-ball interception. — [Murdoch conference paper](https://researchportal.murdoch.edu.au/esploro/outputs/conferencePaper/Training-of-anticipatory-skill-in-a/991005540244307891)
- Harris et al. 2020 (validation framework) argue that psychological, affective and ergonomic fidelity decide transfer, and that judging a simulator by surface visual realism is a common mistake. They propose testing construct validity (does the simulator separate experts from novices?) and physical and psychological fidelity. — [Harris et al. 2020, Frontiers in Psychology](https://www.frontiersin.org/articles/10.3389/fpsyg.2020.00605/pdf); applied to golf putting in [Harris et al. 2021](https://eprints.whiterose.ac.uk/166505/13/Harris2021_Article_ExploringSensorimotorPerforman.pdf)

**Learned behaviour models (tracking data)**
- Data-driven ghosting (Le, Carr, Yue, Lucey; MIT Sloan 2017):
  - Deep imitation learning trained on a season of pro soccer tracking data gives a "league-average" defensive model. Fine-tuning on one team's data gives a team-specific style.
  - Example: ghost defenders gave 71.8% expected goals vs. 69.1% for Swansea's actual defending.
  - Disney holds a granted patent on this (US 12,165,395, Dec 2024).

  — [Disney Research](https://studios.disneyresearch.com/2017/03/03/data-driven-ghosting-using-deep-imitation-learning/); [patent listing](https://trea.com/information/data-driven-ghosting-using-deep-imitation-learning/patentgrant/20de9a0f-d1e7-4f0d-a066-181e2daafbb4)
- Ghosting has been applied to NFL defenders using a full regular season of tracking data. — [Frontiers in Sports and Active Living 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8353517)
- Trajectory prediction with graph networks and attention: the authors note it is surprisingly hard to train a deep model that beats linear extrapolation. — [Victor et al., arXiv 2106.00173](https://ar5iv.labs.arxiv.org/html/2106.00173)
- Hockey-specific learned work is sparse:
  - A Sloan 2018 model learned team-activity representations from hockey trajectories alone and beat a video network (C3D). It is for analysis, not generating movement. — [Mehrasa et al.](https://www2.cs.sfu.ca/~mori/research/papers/mehrasa-sloan18.pdf)
  - A 2025 paper builds a multi-agent reinforcement learning environment for hockey from the McGill Hockey Player Tracking Dataset. — [IAFOR ECE2025](https://papers.iafor.org/wp-content/uploads/papers/ece2025/ECE2025_93889.pdf)

**Data-replay (scripted from real tracking)**
- Beyond Sports recreates matches in 3D from x, y, z tracking data, with "plug and play" ready-made scenarios or custom ones built from a club's own data. A 2014 report said conversion took more than an hour and was about 95% accurate (old figure). — [Neowin](https://www.neowin.net/news/sports-begin-using-virtual-reality-for-training-learning-entertainment); [Training Ground Guru](https://trainingground.guru/articles/stoke-city-to-use-vr-to-train-keepers)

### Inferences
- **Fidelity budget:** spend on correct whole-body kinematics (mocapped skating strides, stick and blade orientation before a pass or shot, head and shoulder orientation, centre-of-mass path). Textured, photoreal avatars are optional. Small, low-contrast objects can hurt, as the reduced ball did in Vignais' L4 condition. Keep the puck visually salient, for example with a slight size boost or a contrast outline, if testing shows it gets lost.
- **Deception needs separate channels:** the animation system must let "honest" cues (centre-of-mass path, skate edges, blade angle at release) diverge from "dishonest" cues (head look, shoulder fake, stick fake). Otherwise players cannot learn to read the honest cues.
- **Recommended architecture (hybrid):**
  - (a) Author or import plays as timed waypoint and event scripts, from NHL-style tracking or coach-drawn plays.
  - (b) A rule-based reactive layer per agent: a defender gaps up based on time-to-intercept, pressures the puck carrier, collapses on the slot. Rules are parameterised by the kinematic limits in section 1.
  - (c) A learned policy (imitation or ghosting) only later, once hockey tracking data is available. Linear-extrapolation and rule baselines are strong, so evaluate against them.
- **Validation step:** before trusting a scenario set, run a construct-validity check (Harris framework). Experienced players should beat novices on accuracy or response time. Low-scoring scenarios that do not separate them should be fixed.

### Gaps
- No published study of avatar fidelity or point-light displays in ice hockey specifically. The evidence comes from handball, badminton, rugby, cricket and running.
- No public hockey imitation-learning or ghosting model or dataset of NHL quality was found. NHL EDGE raw tracking is not public.
- No study found on how skating-animation fidelity (stride timing, edges) affects anticipation.

---

## 3. Scenario design for decision training

### Takeaway
Effective designs:
- are first-person and life-size, with action-like responses
- use randomised, structured variability (contextual interference)
- include genuine and deceptive actions and several valid options
- use temporal occlusion or a response deadline to force anticipation
- adapt difficulty so success sits around 70-80%

Training of more than 4 weeks, 2-4 sessions a week and 10-25 minutes per session is the meta-analytic suggestion. Transfer to the ice is roughly half the size of lab gains.

### Cited Findings
**Effect sizes and dose**
- Zhu et al. 2024, meta-analysis of 22 team-sport studies (Hedges' g):
  - lab accuracy g = 1.51 [0.98, 2.05]; on-court transfer accuracy g = 0.65 [0.15, 1.16]
  - lab response time g = −0.91; transfer response time g = −0.44
- Moderators (none statistically significant):
  - 3D/VR stimuli g = 0.96 vs. life-size video 0.46 vs. computer video 0.19
  - sport-specific action responses 0.87 vs. verbal or keyboard 0.41
  - programs over 4 weeks 1.25 vs. 4 weeks or less 0.38
  - sessions under 20 min 0.56 vs. over 20 min 0.72

  The authors suggest more than 4 weeks, 2-4 sessions a week and 10-25 minutes per session, using first-person VR with sport-specific responses. Explicit and implicit instruction showed no significant difference. — [Zhu et al. 2024, Behavioral Sciences](https://pmc.ncbi.nlm.nih.gov/articles/PMC11505547/)
- Jia et al. 2024, scoping review of 20 studies on VR and 360° video for team-sport decisions:
  - 360° video was used in 11 studies, animated head-mounted-display VR in 6, CAVEs in 5.
  - 360° video is slow to shoot and cannot be modified. Animated VR is interactive but needs engineering and may misrepresent object physics.
  - Response modes: verbal (10 studies), motor or action (6), keypress with four options such as shoot, dribble, pass left, pass right.
  - Recommendations: computer-generated content to scale production, action responses, motion capture, eye tracking, and feedback on alternative solutions for high-level athletes.
  - Weaknesses: some post-tests reused training scenarios, and tasks were often low in complexity.
  - Transfer results were mixed. Pagé et al. 2019 found transfer, Panchuk et al. 2018 none in real matches, Kittel et al. 2020 none, and Fortes et al. 2021 found VR beat video.

  — [Jia et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11284098/)
- Ma et al. 2023 (systematic review) conclude VR can improve athletes' perception and cognition "under certain conditions". — [Frontiers in Psychology](https://frontiersin.org/articles/10.3389/fpsyg.2023.1164117)

**Variability, contextual interference and structure**
- Broadbent et al. 2015 (tennis anticipation via simulation):
  - Random practice beat blocked practice on 7-day retention accuracy and on decision time in a field transfer test.
  - In Broadbent's thesis, "smart-random" sequences (tactically structured, like real rallies) beat purely random ones on retention accuracy and field decision time.
  - Random practice demands more cognitive effort (JEP:HPP 2017).

  — [Broadbent PhD thesis, LJMU](https://researchonline.ljmu.ac.uk/id/eprint/4590/); [Broadbent et al., LJMU](https://researchonline.ljmu.ac.uk/id/eprint/2060/)

**Uncertainty, occlusion and deception**
- Vignais' handball VR occluded the ball partway through flight and mixed unanalysed "filler" throws into the target set to keep uncertainty. — [Vignais et al. 2009](https://jssm.org/08-4-501.p_d_f)
- WIN Reality (baseball VR) uses "Disappearing Pitch" and "Recognition Window" drills, which are temporal occlusion in product form. — [WIN Reality blog](https://winreality.com/?p=185404)
- Deceptive and genuine actions: see Brault (rugby) and the VU handball avatar morphing study in section 2.

**Adaptive difficulty**
- Math Garden (Klinkenberg, Straatemeier & van der Maas 2011) uses an Elo-inspired system that updates learner ability and item difficulty in real time. Items are sampled at a mean success probability of .75, not the .50 that is most informative for testing, so practice stays challenging but motivating. Scoring includes response time. — [UvA DARE record](https://dare.uva.nl/id/67ab8977-5e36-4f9f-962d-be294f2b8c09); [Klinkenberg profile](https://www.uva.nl/en/profile/k/l/s.klinkenberg/s.klinkenberg.html)
- NeuroTracker (3D multiple-object tracking) sets speed thresholds with an adaptive up-down staircase. A vendor reports a 39% mean threshold gain in elite athletes over 5 weeks. — [NeuroTracker patent](https://patents.google.com/patent/US10096258); [NeuroTracker blog (vendor)](https://neurotrackerx.com/post/the-effects-of-perceptual-cognitive-training-on-subjective-performance-in-elite-athletes)
- Adding motor demands early in a hard perceptual-cognitive program can hurt acquisition. A table-tennis study found cognitive task difficulty followed the Challenge Point Framework. — [NeuroTracker patent / CPF summary](https://patents.google.com/patent/US10706730)

**Feedback**
- In a video-based handball anticipation task, four knowledge-of-results frequency schedules made no difference to novices' learning or retention. Gains persisted over a 7-month retention interval. — [Schorer, Cañal-Bruland & Cobley 2010, IJSP](https://www.ijsp-online.com/abstract/view/41/107)
- Feedback on alternative solutions is recommended for high-level athletes. Many VR studies limited feedback to the options shown. — [Jia et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11284098/)
- STRIVR's coaching workflow re-watches the rep, with the athlete turning their head to find the open receiver they missed, and discusses alternatives with a coach. — [ABC7](https://abc7news.com/post/virtual-reality-technology-helping-football-players-master-the-game/1182990/)

### Inferences
- **Scenario template for hockey (data model):**
  - an initial state: positions and velocities of 10 skaters plus the puck, and game state (strength, zone, score, clock)
  - a timeline of scripted intents for each agent, plus reactive rules
  - decision points with a deadline or occlusion time
  - a set of candidate options, each with a precomputed value (see section 4)
  - deception flags: honest vs. faked cue channels
  - variability knobs: jitter ±x m on positions, ±y% on speeds, and choice of which option is "open"
- **Sequencing:** present scenarios "smart-random". Interleave scenario types (2-on-1, D-to-D under forecheck, net-front coverage) instead of blocking them, but keep game-plausible sequences, for example breakout followed by neutral-zone regroup.
- **Difficulty knobs for a staircase or Elo item:**
  - time to decision (occlusion earlier, attackers faster)
  - number of options and how close their values are
  - deception rate
  - visual load (more moving players)
  - scanning demand (key information placed behind the player)

  Target about 75% success for practice and about 50% for assessment blocks.
- **Elo implementation (standard form; the Math Garden equations were not verified):**
  - P(correct) = 1 / (1 + exp(−(θ_player − β_scenario)))
  - after each trial: θ += K·(score − P) and β −= K·(score − P)
  - score can blend correctness with speed, as Math Garden does
  - use a larger K early or with few trials, and choose the next scenario so P is about 0.75
- **Feedback:** knowledge-of-results frequency matters little in the one direct test. Prioritise instant replay from the player's own head pose with the best option highlighted, plus a summary every block, over constant interrupting cues.
- **Avoid scenario leakage:** hold out unseen scenarios for assessment (Jia's critique), and use real on-ice outcomes, not lab scores, as the real proof of transfer.

### Gaps
- No hockey-specific study of temporal occlusion or VR decision training with transfer data was found. Kim et al. 2026 (Korean journal) used video pass choice plus eye tracking with multiple-object-tracking training. Fixation accuracy rose in both groups, with no significant group × time interaction. — [Kim, Kwon & Yook 2026](https://kjss.sports.re.kr/assets/pdf/1069/journal-37-2-177.pdf)
- No study found that uses Elo for sport-decision scenarios. The Elo evidence is from education (Math Garden).
- Effects of feedback timing (immediate vs. delayed, bandwidth) in VR team-sport decision training were not found. Only frequency was tested, in one video study.

---

## 4. Decision scoring: metrics, validity, pitfalls, and hockey analytics models as scorers

### Takeaway
The most defensible scoring combines four things:
- (a) choice quality against a model-computed value of each option (an analytics-style expected-value model), cross-checked by an expert panel
- (b) response time measured from the moment information first becomes available
- (c) pre-decision scanning from headset yaw
- (d) consistency across repeated variants

Accuracy against expert or model values is far better than accuracy against the outcome. Lab scores often fail to predict game performance, and the scanning-performance link is small, so scores should be reported as training metrics, not talent verdicts.

### Cited Findings
**Response measures used in VR research and products**
- Measures used across VR studies: decision accuracy (most common), response time, gaze, judgment accuracy, confidence, rate of "unexplained" decisions, and presence or realism ratings. Eye movements alone classified soccer goalkeepers into three expertise levels with 78.2% accuracy (Hosp et al.). — [Jia et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11284098/)
- Validity problems:
  - High-level players were faster but no more accurate (Wirth et al. 2018).
  - Neither video test separated elite referees (Kittel et al. 2021).
  - Perceptual-cognitive test scores did not predict on-field performance (Van Maarseveen et al. 2018).

  — [Jia et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11284098/)
- Rezzil's VR reaction module was found valid and reliable for measuring reaction speed. — [MTI 9(9):91 via Crossref](https://api.crossref.org/works/10.3390%2FMTI9090091)
- Sense Arena reports reaction time and accuracy after each round, team benchmarks and leaderboards. — [The Hockey Writers](https://thehockeywriters.com/sense-arena-developing-future-virtual-reality-sports-training/); [Quest store listing](https://queststoredb.com/game/nhl-sense-arena-25-hockey/3454538864674405)

**Scanning and head turns**
- Jordet et al. 2020 (EPL, 21 matches, 9,574 possessions): more scans before receiving went with higher pass completion. A Bayesian hierarchical model controlled for player and pass difficulty. The effect was small but positive, and match demands constrain scanning. — [Jordet et al. 2020, Frontiers in Psychology](https://pmc.ncbi.nlm.nih.gov/articles/PMC7573254)
- Scan frequency varies by position (central midfielders and centre-backs highest, forwards lowest) and drops under tight marking. The youth study found similar results. — [Aksum dissertation, NIH Norway](https://nih.brage.unit.no/nih-xmlui/handle/11250/2828246)
- McGuckian et al. linked more head turns to faster and more forward passes and to turning with the ball, but not to pass success. — [McGuckian et al., NIH Brage](https://nih.brage.unit.no/nih-xmlui/handle/11250/2595844?show=full)
- A registered trial (VR-SCANPASS, SensiballVR; 22 U16-U17 players, 3 sessions a week for 7 weeks) measures scanning frequency and passing accuracy. No results yet. — [ClinicalTrials.gov NCT07144371](https://clinicaltrials.gov/study/NCT07144371)

**Hockey analytics as option-value functions**
- Pass evaluation from tracking (2022 Olympic women's data):
  - Rink control uses a pitch-control model with β = 2.5 (Spearman 2016).
  - P(pass success) = sum of offensive control along the simulated puck path.
  - Location value LV = scoring probability × rink control. Scoring probability uses distance decay ℓx = 2000 and ℓy = 500, an angle factor, and a penalty behind the goal line.
  - Expected pass value = Σ LV × P(offence controls) along the pass.
  - Best outcome = maximum expected pass value over all angles and speeds, including not passing.
  - Relative outcome = best outcome ÷ value of the actual pass. This compares the chosen option directly with the optimum.
  - Sample: 289 offensive-zone passes, too small for strong conclusions.

  — [arXiv 2205.13678](https://ar5iv.labs.arxiv.org/html/2205.13678)
- Possession value: a real-time framework for hockey values a pass as the expectation over all possible receivers (Liiga event data). — [LINHAC 2023](https://ecp.ep.liu.se/index.php/linhac/article/download/737/642/754)
- PxG: a neural network predicts the xG of the shot following a pass from pass origin, reception point, duration and estimated speed. It uses event data only, and the authors say tracking data would improve it. — [LINHAC 2025 student paper](https://www.ida.liu.se/research/sportsanalytics/LINHAC/LINHAC25/papers/linhac25student-paper57.pdf)
- Passing and pressure metrics from NHL puck and player tracking (Waterloo). — [LINHAC 2022](https://cs.uwaterloo.ca/~brecht/papers/passing-linhac-2022.pdf)
- Expected goals:
  - MoneyPuck's xG uses gradient boosting and deliberately has no explicit rebound or rush variables. Its "flurry-adjusted" xG discounts the 2nd, 3rd and later shots in a flurry and is more repeatable and predictive. — [MoneyPuck about](https://moneypuck.com/about.htm)
  - Public xG models typically use distance, angle, shot type, rebound and rush. — [CMU class presentation](https://www.stat.cmu.edu/cmsac/summer2021/XGoal-10-min.html)
  - Pre-shot movement (passes before the shot) adds value. — [Hockey Graphs](https://hockey-graphs.com/2019/08/12/expected-goals-model-with-pre-shot-movement-part-1-the-model/)
- Zone entries:
  - Controlled entries (carry-ins) produce more than twice the shots of uncontrolled (dump-in) entries (Tulsky, 330 tracked NHL games). — [NBC Sports](https://www.nbcsports.com/fantasy/hockey/news/article-hockey-analytics-zone-entries)
  - League average 0.66 unblocked shot attempts per controlled entry vs. about 0.29 per uncontrolled. Swiss data (more than 56k entries): 47% of controlled entries vs. 18% of dump-ins led to a shot (snippet-level attributions). — [Hockey Graphs](https://hockey-graphs.com/2017/08/10/measuring-the-importance-of-individual-player-zone-entry-creation/); [Thibaud Chatel](https://thibaudchatel.substack.com/p/assessing-the-risk-management-of)
  - The gap is smaller on the power play. — [NHL Special Teams](https://nhlspecialteams.com/blog/2016/2/13/is-dumping-the-puck-damaging-on-the-power-play)
  - Exit type barely affects entry quality. — [Hockey Graphs](https://hockey-graphs.com/2019/08/01/exit-types-dont-affect-entry-quality-much/)
- Ghosting-style scoring: compare the defence's actual positioning with a learned "league-average" defence by xG (the Swansea example in section 2). — [Disney Research](https://studios.disneyresearch.com/2017/03/03/data-driven-ghosting-using-deep-imitation-learning/)

**Hockey expertise and decision style**
- A cognitive task analysis of elite and intermediate hockey players found experts decide in a recognition-primed way (pattern recognition rather than comparing options one by one). — [Mulligan, SFU thesis](https://summit.sfu.ca/_flysystem/fedora/sfu_migrate/9369/etd4364.pdf)

### Inferences
- **Per-trial scoring formula (proposal):**
  - quality Q = V(chosen) / V(best), in the spirit of "relative outcome", or regret = V(best) − V(chosen). V comes from the engine's own model: P(pass completes) × value of the target location, with control and value as in arXiv 2205.13678.
  - Because the engine knows every agent's state and kinematic limits exactly, it can compute pass success probabilities from simulated time-to-intercept rather than estimating them from broadcast data. This is an advantage over real-game analytics.
- **Multiple valid options:** treat any option within about 10% of V(best) as "correct". Expert-panel ratings (for example 3-5 coaches rating each option 1-5) can calibrate or override V where the model is weak: net-front battles, puck protection, line changes, game state. Check rater agreement (for example Fleiss' kappa) before using panel labels.
- **Response time:** measure from the first frame the decisive cue is visible (the defender commits, the lane opens), not from scenario start. Report it together with accuracy (a speed-accuracy view, as Math Garden does), not separately.
- **Scanning from the headset (no eye tracking needed):**
  - Count yaw excursions over about 30-45° away from the puck in the 5-10 s before reception. Report scans per second and whether the scan covered the area where the best option appeared. This is "information-directed scanning" and is more meaningful than raw frequency.
  - Expect a weak link to correct passing (Jordet), so scanning should guide coaching, not count as a pass/fail grade.
  - Eye tracking (for example on Quest Pro-class headsets) can add fixations on honest cues, such as the attacker's hips or centre of mass versus head or stick.
- **Do not score on outcome alone:** a good choice can fail through stochastic execution. Score the choice against its expected value and show the outcome separately.
- **Coarse proxies for entry decisions:** "carry when there is speed and space, dump when not" can be valued with the shots-per-entry figures above (0.66 vs. 0.29), adjusted for strength state.

### Gaps
- No validated hockey video or VR decision test (expert-novice discrimination, test-retest reliability) was found. Larkin-style validated instruments exist for Australian football and soccer, not hockey.
- No published head-turn or scanning norms for ice hockey (shoulder checks by position, scans before receiving).
- No public hockey pass-value model built on full-season NHL tracking. The Olympic model has 289 passes. NHL EDGE data are aggregated by season and not available frame by frame.
- No evidence on whether Sense Arena's or Rezzil's decision scores predict on-ice performance. The Sense Arena "25% improvement" claim is vendor-reported.

---

## 5. How existing VR sports trainers build scenarios, and lessons learned

### Takeaway
Products split into two routes:
- **360° video capture** (STRIVR): authentic but costly, cannot be edited, and the viewer stays in one place.
- **CG simulation driven by tracking data, mocap or authored plays** (Beyond Sports, Rezzil, Sense Arena, WIN Reality): editable, adaptive and scalable.

For hockey, where skating moves the viewpoint, the CG route with mocapped skaters is the fitting one.

### Cited Findings
- **STRIVR:**
  - Films 360° video of practice from the quarterback's spot on a tripod or pedestal, not a helmet. Footage must be stitched into one 180° or 360° view, and bad stitching makes it unusable.
  - The pedestal makes in-game capture hard. Training is mostly stationary because VR locomotion is unsolved.
  - Coaches use it interactively: re-watching reps and discussing how to adapt.
  - The business model supplies cameras, processing software and headsets.

  — [Phys.org 2016](https://phys.org/news/2016-03-athletes-edge-virtual-reality.pdf); [ABC7](https://abc7news.com/post/virtual-reality-technology-helping-football-players-master-the-game/1182990/); [Voices of VR #429](https://voicesofvr.com/?p=3455); [MIT Technology Review](https://cdn.technologyreview.com/s/609473/finally-a-useful-application-for-vr-training-employees)
- **Beyond Sports:**
  - The engine rebuilds matches in 3D from positional data from standard stadium tracking.
  - Offers ready-made "plug and play" training scenarios plus tailor-made ones from a club's data.
  - Focus areas: spatial awareness, decision-making, high pressure, and many scenarios packed into short sessions.
  - Clubs: AZ Alkmaar, PSV, the Dutch national team, Stoke City (goalkeepers).

  — [Training Ground Guru](https://trainingground.guru/articles/stoke-city-to-use-vr-to-train-keepers); [Digital Sport](https://digitalsport.co/dutch-football-club-to-use-vr-and-game-data-to-recreate-previous-matches); [Neowin](https://www.neowin.net/news/sports-begin-using-virtual-reality-for-training-learning-entertainment)
- **Sense Arena (hockey):**
  - Quest 2/3; 100+ drills for skaters and goalies (an older article says 50+).
  - Built around decision-making, scanning and awareness, including odd-man situations such as a 5-on-3.
  - Metrics: reaction time and accuracy after each round, individual accounts in team plans, benchmarks, leaderboards.
  - Pricing about $34-65 a month. The "25% performance improvement" claim is vendor-reported and was not independently verified.

  — [The Hockey Writers](https://thehockeywriters.com/sense-arena-developing-future-virtual-reality-sports-training/); [Quest store listing](https://queststoredb.com/game/nhl-sense-arena-25-hockey/3454538864674405); [The Hockey News](https://thehockeynews.com/news/virtual-reality-has-come-to-nhl-training)
- **Rezzil Player 22:**
  - Sport-based cognitive games (reaction, concentration, coordination) and quarterback drills for distance perception and situational awareness.
  - About 60 heading drills, which researchers have used.
  - Its reaction module has been validated.

  — [Road to VR](https://www.roadtovr.com/player-22-rezzil-investment-2-m/); [Jia et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11284098/); [MTI](https://api.crossref.org/works/10.3390%2FMTI9090091)
- **WIN Reality (baseball):**
  - Virtual pitchers are built from real pitch data and real windups, covering a range of speeds and arm angles.
  - Occlusion-style drills: Disappearing Pitch, Recognition Window.
  - An independent comparison found VR and regular-practice groups both improved on a video pitch-recognition test. The gains are not unique to VR.

  — [WIN Reality blog](https://winreality.com/?p=185404); [The Alliance Fastpitch](https://thealliancefastpitch.com/?p=28142)
- **Research systems:**
  - Motion capture: VICON at 100-200 Hz into the MKM animation engine for synthetic humanoids.
  - CAVE vs. HMD: the review recommends HMDs for cost and portability.
  - 360° capture: a camera about 1.5 m high, about 15 m from play.

  — [Vignais et al. 2009](https://jssm.org/08-4-501.p_d_f); [Jia et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11284098/)

### Inferences
- **Lessons to adopt:**
  - (1) Build scenarios as data (tracking-style timelines plus rules), not baked video, so they can be varied and staircased. This is the Beyond Sports and WIN Reality model. STRIVR's limits (cannot be edited, stationary viewpoint, stitching cost) are exactly what hockey cannot accept.
  - (2) Ship a curated "plug and play" library plus a coach authoring path (draw a play on a rink diagram, or import tracking), as Beyond Sports does.
  - (3) Give the coach review tools: replay from the player's viewpoint plus a top-down view with the best option overlaid.
  - (4) Run construct-validity checks before making claims, because vendor improvement claims are not independently backed.
- **For hockey specifically:** the player is moving, so either drive the camera along a scripted skating path (risk of motion sickness) or use seated or standing "decision-point" freezes with short glides. The research base favours action-like responses such as stick and head movement over button presses (section 3).

### Gaps
- No public technical post-mortem or developer talk from Sense Arena, Rezzil or Beyond Sports on authoring pipelines, data formats or AI behaviour was found. The details above come from press and vendor material.
- How Sense Arena builds its virtual opponents (mocap vs. procedural, scripted vs. adaptive) and how it defines "accuracy" for decision drills is undocumented in the sources found.
- WIN Reality's difficulty levels and adaptation logic are undocumented.
