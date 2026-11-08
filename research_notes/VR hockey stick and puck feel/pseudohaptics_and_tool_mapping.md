# Pseudo-haptics, visual-motor mapping and two-handed tool mapping for a controller-only VR hockey stick

Scope: perceptual techniques other than vibration hardware (pseudo-haptics, visual and audio cues, mapping two controllers onto one stick) for a Quest 3 / Touch Plus, PC VR, standing, no props, no hand tracking. Numbers in "Cited Findings" come from the primary papers where I could read them in full (Rietzler 2018 x2, Samad 2019, Burns 2007 thesis, Prachyabrued & Borst 2016). Other items come from abstracts or search-indexed summaries and are marked when the evidence is weak. Hockey-specific recommendations are my inferences and are listed under "Inferences".

## 1. Pseudo-haptic weight and inertia: C/D ratio, visual lag or offset, what users notice or tolerate, and the cost to precision and motor learning

### Takeaway
Two families exist. Subtle C/D-ratio changes (about 0.7 to 1.3) shift perceived weight only slightly (about ±5 g on a 185 g object) but keep hand ownership. Large visible lag or offset springs (8 to 42 cm) are read as weight and raise presence and enjoyment, but they are a metaphor rather than a true percept, and they move the displayed hand or tool away from where the arm is. For a light composite stick used for precise work, the evidence points to keeping any distortion under the detection thresholds (about 4.5°, gain 0.88 to 1.07) and using it only for the load from the puck, not as a constant heavy feel.

### Cited Findings
- **Rietzler et al., "Breaking the Tracking" (CHI 2018): the offset model.** The authors treat the offset between the tracked and displayed position as a force, F(o) = c·o, which balances the object's gravity, F(g) = m·g. The display updates as P = P(t-1) + v(t-1) + t·(F(g) + F(o)). If c = g, the steady offset equals the mass. A third force opposes velocity and scales with weight, so "lighter objects follow the tracked movements very closely, while heavier objects accelerate and also slow down at a lower rate". The offset ramps in while the hand moves after grabbing, so the object does not drop at once. In effect this is a spring-damper follow controller tuned by mass. — [Rietzler et al. 2018, Breaking the Tracking (PDF)](https://www.uni-ulm.de/fileadmin/website_uni_ulm/iui.inst.100/institut/mitarbeiterbereiche/rietzler/Breaking_the_Tracking.pdf)
- **Rietzler 2018, tolerance study (N=10, Rift CV1 + Touch, offsets 10 to 64 cm).** In the first pass, every participant rated offsets up to 20 cm as a "good" weight metaphor and accepted about 35 cm. By the last pass these rose to 24 cm (good) and 42 cm (accepted), so users got used to the offsets. — [Rietzler et al. 2018](https://www.uni-ulm.de/fileadmin/website_uni_ulm/iui.inst.100/institut/mitarbeiterbereiche/rietzler/Breaking_the_Tracking.pdf)
- **Rietzler 2018, bowling study (N=18): offsets versus no weight cue.**
  - Presence rose significantly with offsets (Witmer-Singer, p < .01, Z = -3.66, r = .61), but the medians barely moved: 5.58 versus 5.22.
  - Immersion and enjoyment also rose (r = .54 and r = .52; enjoyment medians 5.8 versus 5.3).
  - "I could feel the weight" had a median of 4.0 with offsets and 1.5 without (p < .01).
  - 12 of 18 participants preferred offsets, 2 preferred none, and 4 were undecided. 10 of 18 rated the offset condition more realistic; 1 rated the no-offset condition more realistic.
  - Source: [Rietzler et al. 2018](https://www.uni-ulm.de/fileadmin/website_uni_ulm/iui.inst.100/institut/mitarbeiterbereiche/rietzler/Breaking_the_Tracking.pdf)
- **Rietzler 2018, discrimination and absolute weight.** Users told two offsets apart 75% of the time at a 2.5 cm difference from an 8 cm base, and at 3.6 cm from a 20 cm base. Absolute weight guesses varied widely: a 4 cm offset was judged about 0.5 kg (SD about 0.8 kg) and a 28 cm offset about 3.5 kg (SD about 3 kg). The authors therefore advise "relative not absolute weights", for example sword versus stick. — [Rietzler et al. 2018](https://www.uni-ulm.de/fileadmin/website_uni_ulm/iui.inst.100/institut/mitarbeiterbereiche/rietzler/Breaking_the_Tracking.pdf)
- **Rietzler 2018, guidelines and limits.**
  - Guidelines: "Embrace the offset"; keep offsets under 24 cm for long interactions and use 42 cm only briefly.
  - Pseudo-haptic effects need the user to be looking and fade when attention shifts.
  - The authors call the result "a metaphorical perception". They expect lower ratings if users had first lifted a real weight.
  - The extracted text reports no precision or accuracy comparison.
  - Source: [Rietzler et al. 2018](https://www.uni-ulm.de/fileadmin/website_uni_ulm/iui.inst.100/institut/mitarbeiterbereiche/rietzler/Breaking_the_Tracking.pdf)
- **Samad et al., "Pseudo-Haptic Weight" (CHI 2019, Facebook Reality Labs).**
  - Experiment 1 (N=8) compared cubes at C/D 1.25 and 0.75. 4 of 8 participants reported a weight difference on their own before being asked, and 7 of 8 reported it overall.
  - Experiment 2 (N=14) tested C/D levels {0.7, 0.8, … 1.3}, with participants matching the weight on a PHANToM. A 185 g reference mass shifted by only about ±5 g, with hand-displacement differences of 5 to 10 cm.
  - The fitted cue weights were 0.82 for proprioception and 0.18 for vision. Limb ownership and object believability were preserved.
  - Caveat: the cube was a real, optically tracked object, chosen because 185 g is close to the mass of a Touch controller.
  - Source: [Samad et al. 2019 (PDF)](https://research.facebook.com/file/208988017925238/Pseudo-Haptic-Weight-Changing-the-Perceived-Weight-of-Virtual-Objects-By-Manipulating-Control-Display-Ratio.pdf), [DOI](https://doi.org/10.1145/3290605.3300550)
- **Samad 2019: the effect is a perceptual bias, not a metaphor.** The authors argue that within the tested range the illusion is a bias from integrating conflicting cues, and that implied masses are "highly discriminable" even when the absolute shift is small. — [Samad et al. 2019](https://research.facebook.com/file/208988017925238/Pseudo-Haptic-Weight-Changing-the-Perceived-Weight-of-Virtual-Objects-By-Manipulating-Control-Display-Ratio.pdf)
- **Moosavi et al. 2023 (Frontiers in VR).** Direct C/D-ratio manipulation gave more accurate weight perception than restricting the object's velocity. — [Moosavi et al. 2023](https://frontiersin.org/articles/10.3389/frvir.2023.973083/full)
- **Yu & Bowman 2020: rotation.**
  - Scaling an object's rotational motion according to its mass gave correct relative-mass judgments between two objects.
  - For mass distribution, adjusting rotation from real-time dynamics worked significantly better than moving the pivot point.
  - Caveat: the source is an aggregator abstract.
  - Source: [Yu & Bowman 2020 (abstract)](https://paper.nweon.com/6738)
- **DTU paper on moment of inertia.** It argues that VR interaction design rarely takes weight, let alone moment of inertia, into account, and that moment of inertia relates to an object's perceived weight and length (test scene: a light sword and a heavy hammer). — [DTU vrweight paper](https://people.compute.dtu.dk/jerf/papers/vrweight.pdf)
- **Zenner & Krüger (IEEE VR 2019): what goes unnoticed.** A hand offset of about 4.5° in either direction went unnoticed, a range of about 9°. Gain factors from 0.88 to 1.07 were undetectable: users could reach about 13.75% further or 6.18% less far than the virtual hand. The authors call these conservative lower bounds and describe the range as narrow. — [Zenner & Krüger 2019 preprint](https://umtl.cs.uni-saarland.de/paper_preprints/zenner-krueger-hand-redirection-thresholds-vr-19-pre-print.pdf)
- **Burns, MACBETH dissertation (UNC 2007): thresholds.**
  - The position-discrepancy threshold used was 0.20 m (19.09°) in all directions.
  - Velocity discrepancy followed a constant fraction of hand speed (Weber-like). Depending on direction, the hand avatar could move faster than the real hand by +38% to +63%, or slower by 6% to 46%, before half of users noticed. Examples: left +0.44/-0.08, up +0.51/-0.16, toward +0.63/-0.46.
  - Source: [Burns 2007, UNC TR07-002](https://techreports.cs.unc.edu/papers/07-002.pdf)
- **Burns 2007: drift costs performance.** On a "Simon" task, score per second was significantly lower on trials where the hand avatar drifted from the real hand (t39 = 3.18, p < .003). Even sub-threshold displacement can cost precision. — [Burns 2007](https://techreports.cs.unc.edu/papers/07-002.pdf)
- **Waltemate et al. (VRST 2016): latency.** Motor performance and the sense of simultaneity were affected above 75 ms of latency; agency and ownership declined only above 125 ms. Caserman et al. later found ownership affected from about 101 ms in an HMD. — [Waltemate et al. 2016 (PDF)](https://cg.cs.tu-dortmund.de/publications/2016-latency.pdf); [Caserman et al. 2019](https://www.kom.tu-darmstadt.de/papers/CMG19.pdf)

### Inferences
- **Do not make the stick feel heavy.** A senior composite stick is light; most of what a player feels is its inertia during fast swings and the load from the puck and the ice. A Rietzler-style weight offset on the stick (several cm) would sell "heavy", the opposite of what Jon asked for. It would also move the blade away from where his hands put it, and Burns shows drift costs precision. Keep the hand-to-knob mapping 1:1 and spend the small unnoticed budget (about 4.5°, gain about 0.9 to 1.07, velocity scaling within the Burns limits) only on the blade end and only during load events.
- **Sell the puck's weight as a relative load.** The heavy puck should come across as a short, local load: while the blade pushes, cradles or shoots the puck, the displayed blade lags its kinematic target slightly (a stiff Rietzler spring with puck-mass damping), and the lag appears as shaft bow rather than as hand offset. Rietzler's "relative not absolute" advice fits: the contrast between an empty stick and a stick carrying a puck is what users read.
- **Use rotation for inertia.** Hockey loads are mostly horizontal and rotational, not lifting against gravity. Yu & Bowman's result suggests a dynamics-based rotational cue (the blade's yaw response lags slightly under puck load) is the more relevant channel than vertical offset. It should stay sub-threshold because it changes the blade angle.
- **Effect size is small.** Samad's 0.18 visual weight implies that controller-only C/D tricks can nudge perceived weight but cannot override the true light controller. The strong effects in Rietzler come from large, obvious offsets that a precision trainer cannot afford. So pseudo-haptic weight here is seasoning, not the main course; sound and the puck's motion (question 6) likely carry more of the "heavy puck" feel.

### Gaps
- I found no study of pseudo-haptic weight or inertia for fast, ballistic swings (bat, sword, club, stick); all the measured work is about lifting or slow rotation. The DTU paper raises moment of inertia but I could not read its results.
- No study measured the precision cost of Rietzler-style offsets directly. The cost estimate rests on Burns' drift finding and on the latency thresholds.
- No study tested C/D or offset weight with a two-handed long tool.

## 2. Ground and surface contact without a physical surface: penetration versus constraint, "the floor pushes back", audio cues, and what users prefer and perform best with

### Takeaway
Users notice a hand or tool visibly passing through a surface far more readily than a mismatch between where they see and feel their hand, and they reject clipping. Constraining the visual (the hand or blade stops at the surface and an offset builds) raises immersion, enjoyment and the feeling of resistance. The catch, from the grasping literature, is that a purely constrained visual hides how far the user has really pushed, which hurts fine control. The best results came from constraint plus an explicit cue for depth or pressure (a ghost, colour, deformation or sound), with an escape strategy when the offset gets too large.

### Cited Findings
- **Burns et al., "The Hand Is More Easily Fooled than the Eye" (Presence 2006; VR 2005 "The Hand is Slower than the Eye").** Users are much less sensitive to visual-proprioceptive conflict than to visual interpenetration. — [dblp record, Presence 2006](https://dblp.uni-trier.de/rec/journals/presence/BurnsRPWMB06.html); [Burns 2007 thesis](https://techreports.cs.unc.edu/papers/07-002.pdf)
- **Burns thesis, Study 1 detail.** The discrepancy thresholds were significantly higher than the interpenetration thresholds in both the vertical condition (a hand moving down through a virtual tabletop; F1,17 = 61.74, p < .001) and the horizontal condition (F1,20 = 322.23, p < .001). Users also reported that interpenetration was easier to detect. — [Burns 2007](https://techreports.cs.unc.edu/papers/07-002.pdf)
- **Lindeman, Sibert & Templeman (VR 2001), as summarised by Burns.** Simulated surface constraints improve speed and accuracy on manual tasks, and users prefer them to having no constraint. Burns adds that the resulting position discrepancy is less likely to be noticed than the penetration it replaces. — [Burns 2007](https://techreports.cs.unc.edu/papers/07-002.pdf); citation: [dblp, Lindeman et al. VR 2001](https://dblp.org/pid/09/3385)
- **MACBETH.** The technique reconciles the hand avatar with the real hand after a collision by mixing position and velocity discrepancies at equally detectable levels. Users rated it more natural than the rubber-band and incremental-motion techniques and preferred it over both. Performance matched rubber-band and beat incremental-motion. — [Burns 2007](https://techreports.cs.unc.edu/papers/07-002.pdf)
- **Rietzler et al., "Conveying the Perception of Kinesthetic Feedback" (CHI 2018): the studies.**
  - Study 1 (N=12) pushed against unmovable walls with Rift and Touch, comparing clipping (the hand passes through) with a pseudo-haptic offset (the hand stops and the offset grows), each with and without vibration.
  - Offsets versus none raised immersion (p = .025, r = .56), enjoyment (p = .048, r = .44), the feeling of touch (r = .68) and the feeling of resistance (p = .001, r = .72).
  - Vibration alone raised touch and resistance but not immersion or enjoyment.
  - Offset plus vibration was strongest (restriction r = .84, realism r = .72).
  - Study 2 had N=20. Participants "did refuse the use of clipping".
  - Source: [Rietzler et al. 2018b (PDF)](https://www.uni-ulm.de/fileadmin/website_uni_ulm/iui.inst.100/institut/mitarbeiterbereiche/rietzler/ConveyingThePerception.pdf)
- **Rietzler 2018b: escape strategy and contact cues.**
  - One participant pressing against a static object with arms fully stretched struggled with the large offsets and suggested clipping as a fallback. The experts agreed on "an escape strategy, such as clipping, when offsets increase too high".
  - Participants asked for the hands to react on contact. Version 2 closed the virtual fingers on contact, and experts suggested deforming the fingers or changing their colour to show pressure.
  - In the condition with added sound effects, no participant rated the feedback insufficient.
  - Source: [Rietzler et al. 2018b](https://www.uni-ulm.de/fileadmin/website_uni_ulm/iui.inst.100/institut/mitarbeiterbereiche/rietzler/ConveyingThePerception.pdf)
- **Prachyabrued & Borst (IEEE TVCG 2016): grasping with a glove, but general visual-feedback lessons.**
  - The baseline hand that penetrates the object produces a "lighter touch" than a hand constrained outside it, but users dislike it.
  - A constrained hand "reduces performance and causes users to misunderstand grasp".
  - The best performers show the penetrating hand directly: inner hand, see-through, or a two-hand ghost. The two-hand ghost "gives good performance and reasonable subjective experience". Colour changes were the most liked.
  - The authors replace "avoid penetrating visuals" with "Interaction techniques should provide interpenetration cues to help users understand and control interaction (e.g., for light touch)".
  - Source: [Prachyabrued & Borst 2016 (PDF)](https://vrlab.cmix.louisiana.edu/wp-content/uploads/2025/04/Prachyabrued_Borst_GraspCues_TVCG.pdf)
- **Prachyabrued & Borst 2016: ghost tuning.** Four of five subjects preferred an inner ghost (the ghost marks the real hand). Four subjects ranked the rendering styles wireframe > coloured > skin. — [Prachyabrued & Borst 2016](https://vrlab.cmix.louisiana.edu/wp-content/uploads/2025/04/Prachyabrued_Borst_GraspCues_TVCG.pdf)
- **Canales et al. (ACM SAP 2019).** Across eight grasp visualisations, hands following the tracked position gave better performance, but the constrained outer hand was preferred. There were indications of higher ownership with the outer hand. — [Canales et al. 2019 (PDF)](https://research.facebook.com/file/1163009500853334/Virtual-Grasping-Feedback-and-the-Virtual-Hand-Ownership.pdf)
- **Canales & Jörg (MIG 2020).** "Audio feedback for grasping is preferred over visual feedback even though it seems to decrease grasping performance"; ownership showed little or no difference. — [Canales & Jörg 2020](https://par.nsf.gov/biblio/10314326)
- **Schell Games, I Expect You To Die (developer blog).** The hands have no colliders and pass through geometry, while held objects do collide. An early rule that dropped held objects when collision exceeded a threshold caused accidental drops and was changed. — [Schell Games engineering blog](https://legacymicrosites.schellgames.com/blog/engineering-a-super-spy-in-i-expect-you-to-die)

### Inferences
- **The complaint fits the evidence.** Jon's "the blade went through the ice" matches Burns: penetration is the most detectable artifact. His current design (the blade stops, the shaft bows, then the stick slides up through the hands) is the evidence-backed direction: constraint plus offset, with sliding as the escape strategy Rietzler's experts recommended.
- **Add a pressure cue.** Hockey depends on light touch, such as keeping the blade on the ice while stickhandling or controlling pressure on a sweep. Prachyabrued's result says a purely constrained visual hides how hard you are pressing. Candidate cues, in rough order of evidence:
  - a scrape or contact sound whose level scales with how far the controller target is below the ice (audio is preferred, per Canales & Jörg 2020);
  - visible shaft bow proportional to press depth (it is already there; make it legible);
  - optional debug or training aids: a faint wireframe ghost blade at the controller-implied depth, and a blade or ice tint by pressure.
  - Ice spray and shavings are plausible but untested (see question 6).
- **Where to put the offset as the controller goes below the ice.**
  - Option (a), the current behaviour, keeps the hands at the tracked pose and slides the stick through both gloves.
  - Option (b) keeps the gloves on the stick and lets the hands ride above their real position. Burns' unprimed position threshold is about 20 cm, so a few centimetres would go unnoticed, but the drift result shows a precision cost.
  - A hybrid fits the evidence: (b) for the first few centimetres, so the bow plus slight hand lift reads as "the ice pushes back", then (a) beyond that.
  - Sliding through the bottom hand is physically realistic, since players slide the bottom hand along the shaft. Sliding the knob through the top hand is not, so prefer to put the slide at the bottom hand where possible.
- **Reconcile after release with MACBETH-style rates.** When the blade lifts off the ice, the stick should return to the true grip without a pop. Close the gap during motion at no more than about 40% faster than hand speed (Burns: +38% to +63% depending on direction), and close it slowly when the hands are still.
- **Physics engine rule.** Following the Schell Games lesson, never drop the stick because of a collision overload.

### Gaps
- I could not read the exact interpenetration-threshold depths in centimetres (figure only) from Burns.
- All the contact studies use hands on walls, tabletops or grasped objects, not a held tool on a floor. I found no study of a hand-held tool contacting a virtual ground with controllers only, and no study comparing "tool clips into ground" with "tool constrained" for sports implements (for example, VR golf clubs and the turf). No data on which approach VR golf games use, or why.
- Lindeman 2001's numbers were not available; I have only Burns' summary.

## 3. Two-handed tool mapping: one rigid stick from two independently tracked controllers

### Takeaway
There is little controlled research. Engines and games converge on three mappings:
- the first hand alone;
- the first hand as anchor, pointed toward the second hand;
- an average of the two hands.

Physics-heavy games add constrained grips on splines with strength scaled by inertia. A hockey stick has a natural asymmetry: the top hand holds the knob and controls the stick's roll, while the bottom hand slides along the shaft. That makes "top hand anchors and rolls, bottom hand sets direction and slides" the faithful mapping. Averaging both hands would move the knob, which a real stick never does.

### Cited Findings
- **Unity XR Interaction Toolkit 2.5, `TwoHandedRotationMode`, three options.**
  - `FirstHandOnly`.
  - `FirstHandDirectedTowardsSecondHand`: "determines two handed rotation using the first hand and then directing the object towards the second one".
  - `TwoHandedAverage`: "directs the first hand towards the second hand, but uses the two handed average to determine the base rotation".
  - Source: [Unity XRI docs](https://docs.unity3d.com/Packages/com.unity.xr.interaction.toolkit@2.5/api/UnityEngine.XR.Interaction.Toolkit.Transformers.XRGeneralGrabTransformer.TwoHandedRotationMode.html)
- **Skydance Interactive, The Walking Dead: Saints & Sinners (Unreal Engine tech blog).**
  - The grip is a physical constraint between a physics hand and the held object; the visible hand is posed to match the grasp.
  - The hand's PID controller strength is scaled by each held object's moment of inertia, so long weapons get more strength without making empty hands over-responsive.
  - Grip points and "grip splines" define how objects can be held with one or two hands.
  - Caveat: the page returned 403 to me, so this is from search-indexed text.
  - Source: [Unreal Engine tech blog](https://www.unrealengine.com/tech-blog/skydance-interactive-shows-how-it-injected-vr-physicality-and-melee-combat-in-the-walking-dead-saints-sinners)
- **Boneworks (Stress Level Zero).**
  - Each weapon has its own weight. Using two hands makes it easier, but a sledgehammer still behaves differently from a light weapon. — [Road to VR, Boneworks mechanics overview](https://roadtovr.com/boneworks-physics-driven-mechanics-gameplay-overview/)
  - Two-handed weapons must be held with two hands to stay accurate. One reviewer found them "often less effective than the pistols and knives that can be accessed and utilized in half the time". — [UploadVR Boneworks review](https://uploadvr.com/boneworks-review/)
  - The player body has an actual simulated weight of 82 kg. — [Game Developer on Boneworks](https://gamedeveloper.com/design/how-classical-game-mechanics-and-physics-converge-in-vr-hit-i-boneworks-i-)
- **Blade & Sorcery (player forums, weak evidence).** Players describe the weapon "dragging behind" the hand when moved too fast for its weight as intentional weight simulation. Others complain weapons are too heavy, or that swings feel "lagging and floaty". I found no developer statement on how two-handed grips change strength. — [Steam community discussion (example thread)](https://steamcommunity.com/app/629730/discussions/0/1743355067135550800)
- **Half-Life: Alyx (Valve AMA).** "Our weapons all require only one hand, but they can be optionally grabbed and steadied by your offhand"; Valve wanted the player always to have a free hand. — [VentureBeat, Half-Life: Alyx AMA](https://venturebeat.com/business/half-life-alyx-ama-everything-we-learned)
- **Kayak VR: Mirage.** By default the double-ended paddle is linked to the positions of the two controllers. An optional mode straps the controllers to a real stick. — [TheSixthAxis review](https://www.thesixthaxis.com/2023/02/21/kayak-vr-mirage-psvr-2-review/)
- **Sense Arena / NHL Sense Arena (commercial hockey VR).** It solves the two-hand problem with a real stick: originally a Vive Tracker, now a 3D-printed mount for the Touch controller on the player's own stick. A 2025 Quest 3 mixed-reality module, DanglePro, targets stickhandling. This is the prop approach Jon has ruled out, shown here for contrast. — [VIVE blog on Sense Arena](https://blog.vive.com/us/look-sense-arena-vrs-first-pro-level-hockey-training-tool/); [GamesBeat, sensors on sticks](https://gamesbeat.com/sense-arena-unveils-vr-based-nhl-ice-hockey-training-with-sensors-on-sticks/)
- **Owlchemy Labs, "tomato presence".** Hiding the virtual hand while an object is held; hand presence carries over to the object, and players found it felt better. — [Owlchemy Labs](https://owlchemylabs.com/tomatopresence); [Road to VR](https://roadtovr.com/job-simulator-magic-hand-presence/)
- **Guiard (1987) kinematic chain model.** The two hands act as motors assembled in series. Commonly summarised as: the non-dominant hand sets a coarse frame of reference and the dominant hand works at a finer scale within it; I confirmed only the series-chain part against an abstract. — [Guiard 1987 (CogPrints)](https://web-archive.southampton.ac.uk/cogprints.org/625/)
- **Ghost or second rendering.** Showing both the constrained tool and a ghost of the true pose gave good performance and acceptable experience in grasping. — [Prachyabrued & Borst 2016](https://vrlab.cmix.louisiana.edu/wp-content/uploads/2025/04/Prachyabrued_Borst_GraspCues_TVCG.pdf)

### Inferences
- **Recommended mapping (fits Jon's current right-on-top, left-on-shaft setup).**
  - Knob position: the top-hand grip point, kinematic, 1:1.
  - Shaft direction: from the top-hand grip point toward the bottom-hand grip point, that is, XRI's `FirstHandDirectedTowardsSecondHand` with the top hand first.
  - Roll about the shaft axis (opening and closing the blade): from the top-hand controller's roll. In hockey the top hand rotates the stick, and two points cannot define roll anyway.
  - Bottom hand: projected onto the shaft and free to slide; it never moves the knob.
  - Avoid `TwoHandedAverage`-style mappings: they move the knob when the bottom hand moves, which a real stick never does.
- **One-handed fallback.** When the bottom hand releases (poke check, one-hand puck protection, reaching), direction must come from the top-hand controller orientation alone. That needs a per-user calibrated stick-in-hand angle, captured while both hands hold, and a short blend so the stick does not pop. If the top hand releases and only the bottom hand holds, a mapping centred on the bottom hand with a sliding grip is needed, which is rare in real play.
- **Lever-arm noise.** Deriving direction from two points about a hand-width to forearm-length apart, then extending to a blade much further from the knob, multiplies any relative tracking noise or latency between the two controllers by roughly (blade distance / hand separation). Blend the two-point direction with the top controller's own orientation (complementary filter) instead of heavy low-pass filtering, which would add lag (see question 4). This geometry argument is mine; I found no source that measures it.
- **Bottom-hand rendering.** Show the bottom glove snapped onto the shaft at the projected point. Burns' threshold of about 20 cm means small perpendicular gaps will not be noticed. If the bottom controller drifts far off the shaft (well beyond the thresholds), release the grip or show a ghost glove rather than stretching. The "tomato presence" option (hide the hands, show only the stick) is cheap to test, but gloves on the stick help hockey players read where their hands are.
- **What the physics games add.** Their two-handed lesson is that two hands should increase control and stability rather than speed. Boneworks and Blade & Sorcery use two hands to fight simulated weight, a model built for heavy weapons; hockey needs the opposite (light, precise), which supports kinematic mapping.

### Gaps
- I found no controlled study comparing two-handed long-tool mappings (anchor-directed versus averaged versus physics-constrained) on accuracy, preference or presence, and no GDC or postmortem source with numbers on two-handed weight from Boneworks, Bonelab, Blade & Sorcery or Alyx.
- No source on golf, pool cue or hockey VR games that derive the implement from two free controllers with a sliding hand; Kayak VR is the closest, and only at the level of a review.
- The Skydance details could not be verified first-hand (403).

## 4. Physics-driven (dynamic) versus kinematic held objects: latency, follow springs, fast precise swings versus heavy items

### Takeaway
Physics-driven grips (joints, PID or spring followers) give weight, collision response and believable heavy objects, but always add lag and some "floatiness". Games tune the follow strength by mass or inertia. For fast, precise sports implements, the evidence on latency and drift says to keep the chain from controller to implement kinematic and very low-latency, and to put dynamics only where they belong (blade flex, puck).

### Cited Findings
- **Latency thresholds.** Motor performance degrades above 75 ms of latency; agency and ownership decline above 125 ms (Waltemate 2016) and from about 101 ms in an HMD (Caserman 2019). — [Waltemate et al. 2016](https://cg.cs.tu-dortmund.de/publications/2016-latency.pdf); [Caserman et al. 2019](https://www.kom.tu-darmstadt.de/papers/CMG19.pdf)
- **Physics attachments lag in engines.** Objects attached through physics lag behind the controller in Unreal; disabling the low-latency update only makes the mesh lag too. A Reddit thread on physics-based swords suggests accepting about a frame of lag with well-tuned physics (forum evidence). — [Unreal forum thread](https://forums.unrealengine.com/t/vr-input-latency-on-attached-components-collision/437177)
- **Research system latency.** One research system for physics-based hand manipulation reported 42 ms end-to-end latency. — [Kumar & Todorov, Humanoids 2015](https://homes.cs.washington.edu/%7Etodorov/papers/KumarHumanoids15.pdf)
- **Strength scaled by inertia (Skydance).** Saints & Sinners scales PID strength by the held object's moment of inertia so long weapons stay controllable. — [Unreal Engine tech blog](https://www.unrealengine.com/tech-blog/skydance-interactive-shows-how-it-injected-vr-physicality-and-melee-combat-in-the-walking-dead-saints-sinners)
- **Deliberate lag reads as weight, and draws complaints.** Blade & Sorcery's lag on heavy weapons is read as weight by players, alongside complaints of "lagging and floaty" swings. — [Steam community discussion](https://steamcommunity.com/app/629730/discussions/0/1743355067135550800)
- **Rietzler's weight model is a mass-scaled spring-damper follower.** Heavy objects "accelerate and also slow down at a lower rate", which is visible lag by design. — [Rietzler et al. 2018](https://www.uni-ulm.de/fileadmin/website_uni_ulm/iui.inst.100/institut/mitarbeiterbereiche/rietzler/Breaking_the_Tracking.pdf)
- **Drift costs task performance.** Visual drift of the hand from its real position reduced task performance significantly (t39 = 3.18, p < .003). — [Burns 2007](https://techreports.cs.unc.edu/papers/07-002.pdf)
- **Restricting velocity is worse than C/D.** Velocity restriction gave less accurate weight perception than C/D-ratio manipulation (Moosavi 2023), so a velocity-capped follower is a weaker weight cue. — [Moosavi et al. 2023](https://frontiersin.org/articles/10.3389/frvir.2023.973083/full)

### Inferences
- **Keep the hand-to-stick chain kinematic.** Jon's "light flexible composite stick" means it should follow the hands kinematically with zero added lag, apart from the blade-end flex he already has. A heavy follower spring in the Blade & Sorcery style is the wrong model: it signals "heavy weapon" and costs precision.
- **If a follow spring is used at all** (for example, to smooth the stick returning after an ice-contact slide), keep its time constant well under one display frame during normal play, and let it engage only during contact events.
- **Collisions with the 1 kHz puck should see the true kinematic blade.** The puck should collide with the blade pose derived from the controllers (interpolated or predicted between 72 to 120 Hz poses), not with a lagged display copy. Otherwise display and physics disagree at high blade speed, and Jon will see the puck react to a blade he didn't see. Detailed interpolation is out of my scope but follows from this split.

### Gaps
- I found no controlled study comparing kinematic and physics-driven held objects on swing accuracy, timing or presence, and no published per-frame latency numbers from Boneworks, Bonelab or Blade & Sorcery.
- The claim that "physics feels better for heavy items, kinematic for sports" is supported only by developer and forum evidence plus the general latency and drift findings.

## 5. Flex and whip: conveying a flexible implement visually or with sound so the user feels load and release

### Takeaway
Direct evidence for tools like golf shafts, fishing rods or whips with controllers only is thin. But the pseudo-stiffness literature is consistent: visual deformation strongly biases perceived stiffness and compliance, and C/D changes during pressing go unnoticed over a wide range. Shaft bow under load is therefore a legitimate, well-grounded channel for "load". The "release" (spring-back) is unstudied but follows the same principle.

### Cited Findings
- **Srinivasan, Beauregard & Brock (1996), as described by later work.** When the visual deformation of a spring was altered, participants judged the spring with the higher visually rendered stiffness as stiffer: vision biased stiffness perception. — [Citing paper, PMC4129386](https://pmc.ncbi.nlm.nih.gov/articles/PMC4129386)
- **Weiss et al. (CHI 2023), pseudo-stiffness.** While pressing a fixed-stiffness object, C/D ratios from 0.7 to 3.5 went unnoticed. This is far wider than the range for free reaching. — [Weiss et al. 2023 (PDF)](https://www.medien.ifi.lmu.de/pubdb/publications/pub/weiss2023usingpseudostiffness/weiss2023usingpseudostiffness.pdf)
- **Bouzbib, Pacchierotti & Lécuyer (IEEE TVCG 2023, N=15).** Pseudo-stiffness depended on the user's input force and was helped by the object's scale. Pseudo-haptics could simulate stiffness up to about 24 N/cm. — [Bouzbib et al. 2023 record](https://katalog.dhi-paris.fr/vufind/Record/NLM35533013X/Details)
- **Fradin (work in progress).** Inconsistent visual deformation shifted perceived compliance toward the visual cue. — [Fradin WIP](https://jennafradin.github.io/files/wip2.pdf)
- **Rietzler 2018b.** Experts recommended visible deformation (hands or fingers, colour) to communicate pressure. — [Rietzler et al. 2018b](https://www.uni-ulm.de/fileadmin/website_uni_ulm/iui.inst.100/institut/mitarbeiterbereiche/rietzler/ConveyingThePerception.pdf)
- **Real VR Fishing (design example, not a study).** Line tension is shown with a colour-coded line and a circular meter ending in a red zone. — [6DOF Reviews](https://www.6dofreviews.com/reviews/real-vr-fishing-review)

### Inferences
- **Shaft bow is the best-supported controller-only cue for stick flex.** It should be:
  - proportional to the load (ice pressure or puck resistance);
  - visible in the first-person view (Rietzler: pseudo-haptics need sight). The lower shaft and blade are in view when looking down at the puck, so the bow sits where the eyes are.
  - honest: bend only between the bottom hand and the blade, never move the hands.
- **Load and release for shots.** On a slap or snap shot, the blade strikes the ice just before the puck. Show the shaft loading (bow building while the blade is pinned), then a fast spring-back with slight overshoot when the blade releases. Pair it with a launch sound and the puck's exit (question 6). The mass-spring flex Jon has can drive this directly if its natural frequency and damping are tuned so the release is quick (a whip) and not wobbly. Rietzler warns that low damping gives "wobbly movements".
- **Separate the visual flex from the physics.** Exaggerated visual flex (more bow than a real stick) would probably still read as "flexible" without harming transfer, as long as the physics blade the puck collides with stays at the kinematic plus physically plausible flex position. That separation is my design suggestion, not a tested result.

### Gaps
- I found no controlled study on visual flex of golf shafts, rods, whips or swords with controllers only, nor on whether showing flex improves timing (for example, release timing in shooting).
- No study on sound cues for flex (a "creak" or "load" sound).
- Hockey stick flex ratings and real bend magnitudes were not researched here (likely covered by the physics-focused notes).

## 6. Cross-modal effects: sound and visual cues that change perceived hardness, weight and contact

### Takeaway
Sound is the strongest non-haptic lever for "feel" in sport impacts: in golf, impact sound predicted perceived feel better than vibration. Sound with a hard tap, higher frequency and faster decay makes the same surface feel stiffer, and decay rate signals material. Collision sounds that imply a light object make a held object feel lighter. Visually, people judge relative mass from collision outcomes with simple rules: the object that rebounds or leaves faster is judged lighter. So the puck's exit speed and behaviour relative to the blade is a primary "weight" cue.

### Cited Findings
- **Roberts et al. (Loughborough; J. Sound & Vibration 2005; Proc. IMechE 2006): golf.** For elite golfers, sound pressure level, loudness and sharpness of the impact correlated positively with how pleasant and lively a shot felt. In the combined analysis, sound correlated more strongly with perceived feel than vibration did, and the authors concluded that sound is the most significant feedback from impact. — [Roberts et al. 2005](https://dspace.lboro.ac.uk/2134/11475); [Roberts et al. 2006, sound vs vibration](https://dspace.lboro.ac.uk/dspace-jspui/bitstream/2134/10860/2/The%20influence%20of%20sound%20and%20vibration%20from%20sports%20impacts.pdf)
- **DiFranco, Beauregard & Srinivasan (1997).** With identical physical stiffness, surfaces paired with harder-tapping sounds were ranked stiffer, and naive users were more swayed by sound. Liu & Ando (2016) found that higher-frequency and shorter-decay sounds were judged stiffer, and that low-level acoustic features mattered more than category labels. — [Liu & Ando 2016 (PMC), reviewing DiFranco 1997](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5130246/)
- **Klatzky, Pai & Krotkov (Presence 2000).** Decay rate affected material similarity judgments more than frequency did, and was the critical factor (not total energy or duration). Decay parameters correlated with physical damping. — [Klatzky et al. 2000 (PDF)](https://www.cs.ubc.ca/labs/lci/papers/docs2000/pai-KlaPai00.pdf)
- **Yamada et al. (VRST 2018).** A virtual collision sound implying a smaller, lighter object made a real held object feel lighter. A heavy-object sound left perceived weight unchanged in some conditions, so the effect is asymmetric. — [Yamada et al. 2018 (PDF)](https://www.rm2c.ise.ritsumei.ac.jp/papers/2018/vrst2018_yamada.pdf)
- **Gilden & Proffitt (1989): mass from collisions.**
  - Judgments of relative mass in collisions rest on two heuristics: an object that bounces back is judged lighter, and an object that leaves at higher speed is judged lighter.
  - Runeson argued instead that people use kinematic specification of dynamics, and the debate is unresolved.
  - Source: [Gilden & Proffitt 1989 (PDF)](https://labs.la.utexas.edu/gilden/files/2016/04/UnderstandingCollisionDynamics.pdf); [Gilden & Proffitt 1994 / Runeson debate](https://uva.theopenscholar.com/dennis-proffitt/publications/heuristic-judgment-mass-ratio-two-body-collisions)
- **Canales & Jörg 2020.** Audio feedback for grasp contact was preferred over visual feedback but slightly reduced performance. — [Canales & Jörg 2020](https://par.nsf.gov/biblio/10314326)
- **Rietzler 2018b.** With pseudo-haptics, vibration and added sound effects, no participant rated the haptic representation insufficient. — [Rietzler et al. 2018b](https://www.uni-ulm.de/fileadmin/website_uni_ulm/iui.inst.100/institut/mitarbeiterbereiche/rietzler/ConveyingThePerception.pdf)

### Inferences
- **Puck-on-blade sound.** Make it a short, strongly damped (fast-decay), low-to-mid-frequency "thock". Rubber on composite should not ring: a slow decay reads as metal or glass (Klatzky). Scale level and sharpness with impact speed so hard passes and shots sound "solid". The golf data suggest players judge the quality of contact largely by this sound.
- **Avoid sounds that imply a light puck.** Yamada's asymmetry warns that bright, light, clicky collision sounds can make the puck feel lighter, the opposite of the "heavy rubber puck" target.
- **Blade-on-ice sound.** A continuous scrape gated by contact, with level and brightness following blade speed and press depth, gives the missing "floor is there" cue and supports light-touch control (question 2). Evidence that audio contact cues are preferred is direct (Canales & Jörg). Evidence that they help precision is mixed: the same study found a small performance cost, so keep the visual cues too.
- **The puck's motion sells its mass.**
  - On stick contact, the puck's exit speed relative to blade speed, and its lack of rebound when cradled, should follow a realistic mass ratio and restitution.
  - A puck that pops off the blade faster than the blade, or bounces back off a soft cradle, will read as light by the Gilden & Proffitt heuristics.
  - When stickhandling, a puck that resists being dragged sideways and settles quickly on the blade reads as heavy.
- **Ice spray and snow.** Spray on hard stops or blade drags and a puck "thump" on landing are plausible "weight" signals, but I found no evidence on them (see Gaps).
- **Audio timing.** Audio latency and sync are covered in the sibling note `stationary_play_audio_latency.md`.

### Gaps
- I found no study on visual particle effects (ice spray, snow shavings) and perceived contact or force.
- No study on stick-and-puck sound in hockey specifically, or on audio-only weight cues for a held tool during swings. The ICAD 2024 AR sonification-of-weight paper appeared in results but I did not read it.
- Yamada 2018 effect sizes and N were not read in full.

## 7. Risks: breaking motor transfer, cybersickness and frustration; keeping the mapping honest for training

### Takeaway
Any visuomotor distortion that users adapt to (gain, rotation, offset) produces measurable after-effects. VR training without true haptics may shift how the movement is controlled. Both argue for an "honest" mapping in any mode meant for real-ice transfer, with pseudo-haptic and visual exaggerations confined to cosmetics, below detection thresholds, or behind a toggle. Positive transfer evidence (baseball) comes from training perception and decisions with adaptive difficulty, not from faking force. Cybersickness risk from hand or tool offsets appears low. Frustration risks come from too much lag or weight, and from large offsets with no escape strategy.

### Cited Findings
- **Harris, Buckingham, Wilson & Vine (Experimental Brain Research 2019).** Weaker depth cues and the near-total absence of realistic haptics in VR may push users toward a different visual control mode for action. Skills practised in VR may then not represent real-world skills, which could undermine transfer in sport training. — [Harris et al. 2019 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6794235)
- **Gray (Frontiers in Psychology 2017): baseball.** N=80 across adaptive VR hitting training, extra VR practice, extra real batting practice, and a control group, over 6 weeks. The adaptive VR group improved most on most measures, including on-field batting, had better league batting statistics the following season, and reached higher levels of competition over 5 years. Gray argues that designers should exploit what simulation can do, rather than only recreate the real situation. — [Gray 2017](https://www.frontiersin.org/articles/10.3389/fpsyg.2017.02183/text)
- **Kohli, Whitton & Brooks (3DUI 2013), as abstracted.** All virtual training was less effective than real-world training. After adapting, users trained as well in a warped virtual space as in an unwarped one, and the initial strange sensation faded after short repeated exposure. — [Kohli dissertation (UNC TR13-002)](https://techreports.cs.unc.edu/papers/13-002.pdf)
- **After-effects of distortion.**
  - Amplifying or reducing hand motion in VR shifted later open-loop pointing in the direction the gain predicted. — [ACAPS 2025 abstract](https://acaps2025.sciencesconf.org/649092/document)
  - Adapting to a 45° visuomotor rotation in immersive VR produced implicit after-effects. — [York CVR 2019](https://deniseh.lab.yorku.ca/files/2020/05/CVR2019_sm_0607.pdf?x64373)
  - In a wrist gain task, users rapidly returned to a gain of 1 under continuous feedback. — [HAL 01461217](https://hal-amu.archives-ouvertes.fr/hal-01461217)
- **Guidance hypothesis.** Frequent augmented visual feedback can create dependence. In Ronsse et al. (2011), visual feedback produced dependence where auditory pacing did not. Structured sonification may avoid the guidance effect. — [Ronsse et al. 2011 (Monash record)](https://research.monash.edu/en/publications/motor-learning-with-augmented-feedback-modality-dependent-behavio/); [Psychological Research 2016 sonification study](https://link.springer.com/10.1007/s00426-016-0775-0)
- **Cybersickness.** A 2025 randomized trial introduced proprioceptive mismatches during hand-object interaction while avoiding visual-vestibular conflict, and found no significant SSQ differences between groups. — [DOAJ record, 2025 trial](https://library.kab.ac.ug/Record/doaj-art-466ad8b10afb4ccda00fa9a9ece68a62/Description)
- **Frustration evidence.**
  - Blade & Sorcery players complain of overly heavy or floaty weapons. — [Steam community discussion](https://steamcommunity.com/app/629730/discussions/0/1743355067135550800)
  - A Boneworks reviewer found two-handed weapons less effective than one-handed ones. — [UploadVR review](https://uploadvr.com/boneworks-review/)
  - A Rietzler participant struggled with large offsets at full arm extension, which led to the escape-strategy advice. — [Rietzler 2018b](https://www.uni-ulm.de/fileadmin/website_uni_ulm/iui.inst.100/institut/mitarbeiterbereiche/rietzler/ConveyingThePerception.pdf)
  - Rietzler also notes weight offsets can serve as a natural limit inside experiences. — [Rietzler 2018](https://www.uni-ulm.de/fileadmin/website_uni_ulm/iui.inst.100/institut/mitarbeiterbereiche/rietzler/Breaking_the_Tracking.pdf)
- **Drift costs precision.** Hand drift reduced task performance (Burns), and latency above about 75 ms hurts motor performance (Waltemate). — [Burns 2007](https://techreports.cs.unc.edu/papers/07-002.pdf); [Waltemate et al. 2016](https://cg.cs.tu-dortmund.de/publications/2016-latency.pdf)

### Inferences
- **Honest-mapping policy for a training mode.**
  1. Knob and hands 1:1 with the controllers, with no gain, rotation or lag.
  2. The blade position used for physics and metrics is rigid stick geometry plus physically plausible flex only.
  3. Any pseudo-haptic weight or visual exaggeration (extra bow, load lag) stays below detection thresholds, or is cosmetic-only and does not change where the puck is struck.
  4. Log the gap between the true blade and the displayed blade, so Jon can see when the illusion is "lying".
  5. Gain or offset manipulations that users adapt to should be off by default, since they leave after-effects that could carry onto the ice.
- **Aim at what VR trains honestly.** The light stick feels different from a real stick in the hands no matter what is done. Real-ice "feel" (weight in the hands, puck vibration through the shaft) won't transfer from controllers alone, so the trainer is best aimed at what Gray's results show VR can train: reading the play, timing, positioning, stick angles and blade orientation, and decision-making with adaptive difficulty.
- **Keep the feel layers light-touch.** Present them as feedback that can be faded. Sound-based cues may resist feedback dependence better than visual overlays (Ronsse; sonification work).
- **Cybersickness.** Not a major risk from stick or hand mapping. Sickness drivers in a standing, stationary hockey trainer are head-camera related and outside this note.
- **Frustration guardrails.**
  - Never let the stick be yanked out of the hands by a collision (Schell Games' accidental-drop lesson).
  - Cap the offset when the controller is pushed deep below the ice: the stick slides rather than bowing without limit.
  - Avoid heavy-weapon lag.
  - Reconcile the stick to the hands smoothly after contact.

### Gaps
- I found no study on transfer of controller-only VR stick skills to real ice, or on whether pseudo-haptic cues help or hurt real-world transfer in any sport.
- After-effects of VR gain manipulation have been shown in lab pointing, but not as carry-over into real sport performance.
- The 2025 cybersickness trial is a single study, read only as an abstract.
- The guidance-hypothesis sources are general motor-learning work, not VR sport-specific.
