# Loading the stick on the ice: where, how far, when it lets go, and what it adds

Research round "Shot release", 2026-11-10.

## Bottom line

1. **The ice comes only a few hundredths of a second before the puck.** In slap shots the blade meets the ice 27-41 cm (mean 33 cm) and 10-19 ms (mean 14 ms) behind the puck (6 shooters, on ice and synthetic ice). Elite players take 14 ms and recreational players 17 ms from toe contact to puck contact. A finite-element (FE) model put the best distance at about 24 cm. Snap shots load 5-8 cm behind the puck (coaching only). Wrist shots load with the puck already on the blade. A press held 0.6 s before a swing is not how skilled players load a stick. *Corrected in fact-check:* recreational players may do something like it. In Hannon 2010 (synthetic ice), low-calibre players' shaft strain began 349 ± 299 ms before puck contact, against 85 ± 136 ms for high-calibre players **[M]**. Hannon's start event is a strain threshold, not ice contact, so treat this as a hint.
2. **How far it bends.** Slap shots: 11-12.5° for recreational players, 15-19° for skilled ones (range across studies 11-22°). Wrist shots: 6-11°. At the blade that is about 9-13 cm (recreational slap), 12-16 cm (skilled slap, up to about 20 cm in the strongest shots) and 5-10 cm (wrist) **[D]**. At puck contact a slap shot carries only 4-7° (3-7 cm). Most of the bend builds *during* puck contact. Peak vertical blade forces are about 45 N (wrist) and 100-165 N (slap). The sim's 12 cm cap matches a typical skilled slap shot's peak. Jon's 19-31 cm presses would take about 130-470 N, more than any measured shot.
3. **When it lets go.** The bend peaks about 14 ms after puck contact, at about the moment the blade leaves the ice (elite players: 13 ms after puck contact). It recoils while the puck is still on the blade. In the best shots the puck leaves as the shaft comes back straight. Elite players bend through the first 29% of puck contact and recoil until 89%. Recreational players start bending only halfway through, and bend little. A hand-held stick's quarter period (its "release time") is 21-23 ms, the same scale as a slap shot's 15-53 ms of contact.
4. **The recoil adds a few percent, not half.** Bend energy, estimated from the measured bend, was 2.1 J (recreational) and 16.5 J (elite), against 67 J and 152 J of puck energy. Even if all of it reached the puck, that is at most about 2-5% (recreational) and 6% (elite) of puck speed **[D]**. *Corrected in fact-check:* Villaseñor's puck carried an accelerometer (0.260 kg in all). For a 0.17 kg puck at the same speeds the bound is about 2.5% (recreational) and 9% (elite). The angle-based bends in §2, on a held-stick spring, allow up to about 10-15% **[D]**. So read it as "a few percent, at most about 10%". Changing stick flex moves shot speed by 0-4%. Players differ by 32% and sticks by 14%. The often-quoted "40-50% of slap-shot speed from the bend" would need 64-75% of the puck's energy to come from the bend **[D]**. *Corrected in fact-check:* it traces to Roy et al. 1974 (4 junior B players, film), whose method is not described in the citing sources **[S]**.
5. **A static press fires nothing.** Pressing straight down bends the shaft in its own vertical plane (the lie plane), not toward the target. Lifting hands the stored energy back to the hands. The blade leaves the ice at about zero speed and catches up with the hands over roughly 10-15 ms **[E]**. *Corrected in fact-check:* that holds if the hands do the damping. With a damper between stick and blade, as in the sim's flex, it takes 30-40 ms (§7). Only a bend loaded along the sweep (by ice friction or the puck) can whip the blade forward. Even that bend is wasted if the blade leaves the ice before it reaches the puck (measured).
6. **A minimal model needs one bending mode with the right stiffness, a one-sided ice, and a force limit.** A held stick's blade behaves like 0.13-0.20 kg on a 0.7-1.8 kN/m spring, depending on grip (10-17 Hz; measured about 11 Hz). The sim's 2.6 kN/m spring (21 Hz, 12 ms quarter period) is about twice too stiff **[D]**. *Corrected in fact-check:* the formula behind these numbers reads 4-20% high against Cross's clamp test. Against Kays's roller test it reads 26-44% low. So the honest band is about 0.6-2.6 kN/m, and the sim is about 1.2-4x too stiff, 2x in the middle **[D]**. The ice should hold the bend and let it go through the spring, never as a step. VR hands are infinitely strong position sources, so the press needs a force cap or slide, as the sim has now.
7. **For the sim:** the energy-free bow is honest to within the 2-6% the recoil can add (*fact-check:* 2.5-10%). The velocity kink at lift-off is not physical: a real blade ramps up. A 75 ms contact is normal for a wrist shot (elite wrist shots keep the puck on the blade 103-107 ms), so contact length is not what marks a bad scoop. A blade rising and accelerating with the puck is. *Corrected in fact-check:* Léger's 103-107 ms runs from the blade's forward acceleration to an end event the paper never defines. Read it as "about 0.1 s of push", not a measured puck-on-blade time.

Tags: **[M]** measured in the cited study. **[D]** derived by me, arithmetic shown. **[E]** estimate, physics with stated assumptions, or the output of a published model (a model is not a measurement). **[V]** vendor claim, coaching tip or player anecdote. **[S]** secondary: read in a citing source, not the primary.

Sim values used below ([puck.py](../../prototype/puck.py)): blade mass 0.15 kg. Tip stiffness from flex (a 3-point test taken over a 1.17 m span, then a 0.80 m cantilever) is 2,568 N/m at flex 75 and 2,910 N/m at flex 85. Damping ratio 0.6 or 1.5. The ice bow (`ICE_BEND`) goes up to 0.12 m, across the shaft toward up, and stores no energy. `MAX_BEND` is 0.15 m.

This note builds on [hockey_hands_science.md](../VR%20hockey%20stick%20and%20puck%20feel/hockey_hands_science.md) §5 and [stick and puck contact.md](../Hockey%20physics%20feel/stick%20and%20puck%20contact.md). It does not repeat their shot-speed and contact-time tables.

## 1. Where and when the blade meets the ice

| Study | Players | Shot | Ice before puck (time) | Ice behind puck (distance) |
|---|---|---|---|---|
| Kays 2013, WSU MSc ([thesis](https://rex.libraries.wsu.edu/esploro/outputs/graduate/Ice-hockey-wrist-and-slap-shots/99900525127201842)) | 6, age 18-44, mixed skill; 2 on real ice, 4 on synthetic ice; 1000 fps video | slap | 10-19 ms by shooter, mean 14 ± 3.5 ms **[M]** | 10.8-16.0 in (27-41 cm), mean 12.9 ± 2.2 in (33 ± 6 cm) **[M]** |
| Lomond 2005, McGill MSc ([thesis](https://mcgill.scholaris.ca/items/04d8dd90-f525-493d-9689-f4848abcb01f); [paper, Sports Eng 10:87](https://link.springer.com/article/10.1007/BF02844206)) | 8 elite, 7 recreational; force plates + in-puck accelerometer | slap | toe contact to puck contact: 14 ms elite, 17 ms recreational **[M]** | not measured |
| Polano 2003, via Lomond 2005 | 3 varsity, 60 Hz video | slap | — | about 38 cm **[S]** |
| Kays & Smith 2017, FE model ([Sports Eng 20:245](https://lida.sport-iat.de/twm/Record/4047169)) | one shooter's measured hand motion (his average 62.5 mph) | slap | — | best at 24 cm **[E]** |
| Coaching ([HockeyShot](https://hockeyshot.com/blogs/training-academy/snap-shot-tips)); NHL player ([NHL.com](https://www.nhl.com/news/nhl-hardest-shot-past-champions-break-down-science-of-all-star-skills-competition)) | — | snap; slap | — | "2 to 3 inches" (5-8 cm) for a snap shot; "7-8 inches" for one NHL player's slap shot **[V]** |

- **The blade lands toe first, then rocks to the heel.** This "rocker" phase took 6 ms for elite players (13% of the shot) and 9 ms for recreational players (21%) **[M]** ([Lomond 2005](https://mcgill.scholaris.ca/items/04d8dd90-f525-493d-9689-f4848abcb01f)).
- **Distance mattered in the model but not in the field.** In Kays's FE model one shooter's measured hand motion was replayed with the puck moved in 1-inch steps. Puck speed went from 74.3 mph at 2.5 in (6 cm), to 80.3 mph at 9.5 in (24 cm), to 73.5 mph at 14.5 in (37 cm) **[E]**. In the field data, neither ice-impact time nor distance correlated with puck speed across the six shooters **[M]** ([Kays 2013](https://rex.libraries.wsu.edu/esploro/outputs/graduate/Ice-hockey-wrist-and-slap-shots/99900525127201842), Fig. 3.42 and Fig. 4.22). The model replays one shooter with fixed hand motion, so it isolates an optimum that real players wash out by adapting their swing.
- **How hard the blade hits the ice is uncertain.** The FE model's peak blade-ice force was 152 lb (676 N), 3 ms after ice contact **[E]**. Force plates under the blade give much less: peak vertical forces of 122-135 N **[S]** ([Pearsall et al. 1999, via Kays](https://rex.libraries.wsu.edu/esploro/outputs/graduate/Ice-hockey-wrist-and-slap-shots/99900525127201842)) and 165 ± 50 N skilled against 105 ± 48 N unskilled **[M]** ([Pearsall et al. 2001, ISBS](https://ojs.ub.uni-konstanz.de/cpa/article/view/3779)).
- **On real ice the blade digs in.** Kays filmed the blade digging in at first contact and, in some shots, scraping through the ice up to puck contact. On synthetic ice, players "were not able to dig the blade into the surface due to its hardness" **[M]**, qualitative (Kays 2013, §4.4.3).
- **Wrist shots have no separate ice strike.** The puck starts near the heel. The player sweeps it forward while pressing down to bend the shaft, and it rolls toward the toe **[S]** (Kays 2013, §2.3.1). No study measured when the blade first loads in a wrist shot.

## 2. How far the shaft bends

### Angles

| Source | Players, setting | Shot | Bend |
|---|---|---|---|
| [Pearsall et al. 2001](https://ojs.ub.uni-konstanz.de/cpa/article/view/3779) | 10 varsity, 10 recreational; lab force plate, 480 fps; shafts of 13.7, 16.6 and 17.9 kN/m (3-point) | slap | "bending angle" 19.1 ± 5.0° skilled against 12.5 ± 3.5° unskilled; "deflection angle" 5.7 ± 1.5° against 3.7 ± 1.0° **[M]**. The paper does not define the two angles. |
| Pearsall et al. 1999, via Kays 2013 | 6 elite; 4 shafts, 13-19 kN/m | slap | 18-22° (averaged across sticks), reached 23-27 ms after first contact **[S]** |
| [Simard et al. 2004, ISBS](https://ojs.ub.uni-konstanz.de/cpa/article/view/1369) | 1 semi-pro; polyethylene sprayed with WD-40 | slap | 11.0-16.0° by stick (composite mean 12.9°, wood 16.0°) **[M]** |
| Hoerner 1989, via Kays 2013 | game-like setting | slap; wrist | 13° stiff stick, 15° flexible; wrist 6° and 7° **[S]** |
| Wu et al. 2003, via Kays 2013 | 20 men, 20 women, skilled and unskilled | slap; wrist | mean 12.7° (slap), 10.8° (wrist) **[S]** |
| Woo et al. 2004, via [Zane 2012](https://mcgill.scholaris.ca/items/aab2df80-5fd0-437c-a6d8-cd44c577354d) | skilled against unskilled | slap | 15° against 11° **[S]** |
| [Kays 2013](https://rex.libraries.wsu.edu/esploro/outputs/graduate/Ice-hockey-wrist-and-slap-shots/99900525127201842) | 6 shooters | slap | mean maximum 15.0° and 14.3° on the two 85-flex sticks; 7.0° and 6.9° at puck contact on the same sticks **[M]** |
| Russell & Hunt 2009, citing Haché ([PDF](https://www.acs.psu.edu/drussell/publications/russell-hunt-tpt-formatted.pdf)) | — | slap and wrist | "up to 30 degrees" **[S]** |

- **Bend predicts speed within a study.** Peak bend against puck velocity: r² = 0.82 (Villaseñor, n = 9) **[M]**. Wu et al. reported r = 0.80 **[S]** (*unsupported in fact-check:* Kays's review of Wu says only "a high correlation"; no r = 0.80 found in Kays, Villaseñor or Lomond), and Kays found shooters with more peak bend shot faster in both shot types **[M]**. But part of this is skill: skilled players bend more *and* swing better.
- **Stiffer sticks bend less.** The 77-flex stick strained 7-27% more than the 102 flex, depending on gauge and calibre; the difference was significant at the two gauges nearest the blade **[M]** ([Hannon 2010](https://mcgill.scholaris.ca/items/212dd3a6-79f6-4e61-8e47-a6abc33141b2)). The most flexible stick bent 28.3% more in wrist shots **[M]** ([Grover et al., Calgary](https://journalhosting.ucalgary.ca/index.php/jura/article/view/30152)).

### Measured "deflection distances"

- Wu et al. 2003: shaft deflection 0.045 m (elite) against 0.031 m (recreational) **[S]** (via Kays 2013). The definition was not given in the citing text.
- Villaseñor 2004: d = 0.040 ± 0.022 m (elite) against 0.012 ± 0.008 m (recreational) **[M]** ([thesis](https://mcgill.scholaris.ca/items/20d44d6b-f579-48c0-a068-4d118cc607cc), Table 4.2.9). Here d = 0.30 m × tan θ, where θ is the summed joint angle of the three shaft segments below the bottom hand. So it measures the lower shaft only, not the blade tip. It implies about 7.6° and 2.3° of bend in that region **[D]**: atan(0.040/0.30) and atan(0.012/0.30).

### From angle to centimetres at the blade **[D]**

Treat the shaft as a uniform beam held at two points (the hands) with the load at the blade. With a = bottom hand to blade and b = hand spacing, the blade moves δ = 2a(a+b)/(2b+3a) × θ, where θ is the blade's tangent angle relative to the line between the hands.

- **Slap grip.** Kays measured the bottom hand 26.9 in (0.68 m) from the blade and the hands 25.8 in (0.66 m) apart **[M]**. δ ≈ 0.54 m per radian. A clamped cantilever of 0.68 m gives 0.45 m per radian. Kays's lower markers sit mid-way down the lower shaft, so they read about 90% of the tip's angle, which pushes the factor up to about 0.6 m. I use **0.45-0.6 m per radian**.
  - 4° → 3-4 cm
  - 7° → 5.5-7 cm
  - 11-12.5° → 9-13 cm
  - 15° → 12-16 cm
  - 19° → 15-20 cm
  - 22° → 17-23 cm
- **Wrist grip.** The bottom hand sits about 10 in higher on the shaft (Kays, 21.5 in from the butt), so a ≈ 0.93 m and b ≈ 0.43 m **[M]**. δ ≈ 0.69 m per radian, so 6-11° → about 7-13 cm.
- **A cross-check with force puts the numbers lower.** A skilled slap shot's 165 N on a 1.3-1.5 kN/m held stick is 11-13 cm, the low end of the angle-based range. Measured vertical blade force in wrist shots is only about 44 N. On a 0.7-0.8 kN/m held stick that is 5.5-6.3 cm (44/800 and 44/700). The rest of the wrist-shot angle must come from sideways load (puck and ice friction), or the marker-based angles overstate the tip motion. My working figures:
  - wrist shot: **5-10 cm**
  - recreational slap shot: **9-13 cm**
  - skilled slap shot: **12-16 cm**, up to about 20 cm for the strongest shots
- The shaft tapers, so the real lower shaft bends more than a uniform beam would. That puts more of the angle near the blade and slightly less tip motion per degree **[E]**.

### What a held stick is: stiffness and mass at the blade

| Measurement | Setup | Stiffness at the blade |
|---|---|---|
| Cross & Lindsey 2016, Tennis Warehouse University ([flex](https://twu.tennis-warehouse.com/learning_center/hockeyflex.php); not peer-reviewed) | handle clamped at two points 50 cm apart, 5.35 kg hung on the blade end, mostly 85-flex sticks | 59-68 mm deflection: **770-890 N/m** **[M]** |
| Same | same clamps, blade pulled down 9 cm and let go | vibrates "about 11 times per second"; quarter period ("release time") **20.7-23.3 ms** **[M]** |
| [Kays 2013](https://rex.libraries.wsu.edu/esploro/outputs/graduate/Ice-hockey-wrist-and-slap-shots/99900525127201842), Table 3.2 | rollers at the bottom-hand point and 30 in above it, a 10 lb weight hung along the blade | near the heel: 5.7-8.1 lb/in (**1,000-1,425 N/m**) for flex 85-102; at the toe: 1.8-3.0 lb/in (315-525 N/m), because the blade twists **[M]** |
| Cross 2016 ([physics](https://twu.tennis-warehouse.com/learning_center/hockeyphysics.php)) | — | "typically about 1000 N/m for a hockey stick held or clamped near the handle end" **[E]** |

- **The flex rating converts cleanly.** Flex is pounds per inch in a 3-point test over a 1.0 m span **[S]** (Cross & Lindsey: "The standard test distance is L = 1.0 m"). So EI = flex × 4.448 / 0.0254 / 48 ≈ **3.65 × flex N·m²**: 274 N·m² at flex 75 and 310 at flex 85 **[D]**. Cross & Lindsey give "about … 310" for their 85-flex sticks, which matches.
- **Stiffness at the blade for a stick held by two hands** is k = 3EI / (a²(a+b)) **[D]**. It checks against Cross's measured value: a = 0.86, b = 0.50 and flex 85 give 925 N/m, against the measured 770-890 (4-20% high).
- *Added in fact-check:* **it reads low against Kays's bench test** **[D]**. Kays's rollers sat 36 in (0.91 m) above the blade and 30 in (0.76 m) above that (his Fig. 3.2 and §3.2.2). The formula then gives 664 N/m at flex 85 and 782 N/m at flex 100. Kays measured 1,000-1,045 N/m and 1,060-1,180 N/m near the heel (Table 3.2). That is 1.35-1.6x the formula, and 1.8x for his 102 flex. The two bench tests disagree by about 1.4-2x, so the held-stick stiffness below is good to about ±40%.

| Flex | Slap grip (a 0.68, b 0.66) | Wrist grip (a 0.93, b 0.43) | Sim (`tip_stiffness`) |
|---|---|---|---|
| 75 | 1,325 N/m | 698 N/m | 2,568 N/m |
| 85 | 1,501 N/m | 791 N/m | 2,910 N/m |
| 100 | 1,766 N/m | 930 N/m | 3,424 N/m |

- **The sim is about 2x too stiff** **[D]**, for two reasons:
  - It converts flex over a 1.17 m span, not 1.0 m, which makes EI 1.17³ = 1.60x too large.
  - It clamps the shaft at the bottom hand (3EI/L³ with L = 0.8 m). Two hands that each push but cannot hold a moment are softer. At flex 75 that factor is 2,568 / (1.60 × 1,325) = 1.2x with a slap grip, or 2.3x with a wrist grip.
  - *Corrected in fact-check* **[D]**: scaled to Kays's bench test (formula × 1.35-1.6), flex 75 gives 1.8-2.1 kN/m with a slap grip and 0.94-1.1 kN/m with a wrist grip. The sim is then 1.2-1.4x too stiff for a slap grip and 2.3-2.7x for a wrist grip. Scaled to Cross (formula ÷ 1.04-1.2), it is 2.0-2.3x and 3.8-4.4x. "About 2x" is the middle of 1.2-4.4x.
- **Effective mass at the blade.** Cross's 770-890 N/m at 10.7-12.1 Hz gives m = k/(2πf)² = 0.13-0.20 kg **[D]**. The sim's 0.15 kg is right. The earlier estimate from WSU's pivoted-stick inertias was 0.20-0.27 kg.
- **First held mode.** With k = 0.7-1.8 kN/m and m = 0.15-0.20 kg, it comes to about 9-17 Hz and a quarter period of 15-27 ms **[D]**. Cross measured about 11 Hz and 21-23 ms. The sim gives 20.8 Hz and 12.0 ms. This corrects the earlier report's reading of the sim's "first mode near 21 Hz" as the quick, not wobbly, whip the evidence favoured: a held stick is about half as fast.
- **Force at the blade for a given bow** **[D]**:
  - 12 cm of bow takes 0.12 × 700-1,500 ≈ 85-180 N. That is a skilled slap shot's peak vertical force (165 ± 50 N).
  - Jon's median press of 19 cm takes 130-285 N. His 90th percentile, 31 cm, takes 215-465 N. Both are beyond any measured shot.

### Bending is three-dimensional

- **The shaft bends both ways, with timing offsets.** Strain about the shaft's minor axis peaked at about half the major-axis value, and 10-20 ms earlier. The author reads this as "complex 3D bending and possibly torsion" **[M]**. Stiffness changed the bending but not hand forces or shot speed **[M]** ([Flemming 2015, McGill MSc](https://mcgill.scholaris.ca/items/cefd38e6-93bf-4a49-b8e0-e7d58f7bedd9); 18 players, flex 77/87/102; abstract only).
- **The strain peaks just below the bottom hand.** Strain was greatest at the gauge nearest the bottom hand: 4,900 ± 1,170 µε (high calibre) against 3,690 ± 1,430 µε (low calibre) in slap shots. It was 54-64% lower 600 mm further down, near the blade **[M]** ([Hannon 2010](https://mcgill.scholaris.ca/items/212dd3a6-79f6-4e61-8e47-a6abc33141b2); 17 men, synthetic ice, strain at 10 kHz).
- **The blade twists, so the toe is softer.** The toe is 2-3x softer than the heel **[M]** (Kays's table above).

## 3. When the bend is released

### One well-measured slap shot

This is Kays's shooter 5, with a wood stick and the fastest shot on it (66 mph). Bend and puck speed come from 1000 fps two-camera video **[M]** ([Kays 2013](https://rex.libraries.wsu.edu/esploro/outputs/graduate/Ice-hockey-wrist-and-slap-shots/99900525127201842), Fig. 3.52):

| Time from puck contact | Event |
|---|---|
| before −11 ms | a slight bend from swinging the stick |
| −11 ms | blade hits the ice; the bend first dips |
| 0 ms | puck contact; bend about 4° |
| +14 ms | peak bend, 15°; recoil begins |
| later | the puck keeps speeding up, but more slowly; it leaves as the bend returns to zero, then the shaft swings past straight |

- **The blade slows into the puck and speeds up through it.** Averaged over all shooters, the blade at the impact point moved at 53.5 mph at ice contact and 50.4 mph just before the puck. It dropped to 25.5 mph just after puck contact and ended at 43.3 mph **[M]**. Speed lost loading the ice and the puck comes back during contact.
- **Holding speed through contact is what makes a fast shot.** Puck speed rose with blade speed *after* puck contact, not with blade speed before it **[M]**. One shooter had the fastest incoming blade (60.4 mph) but the slowest shots. He was also the only one whose blade sped up after hitting the ice, which suggests "little stick loading".

### Skill and the bend-recoil sequence

Villaseñor 2004 tested 4 elite and 5 recreational players, standing slap shots, with an accelerometer in the puck and 1000 Hz video ([thesis](https://mcgill.scholaris.ca/items/20d44d6b-f579-48c0-a068-4d118cc607cc); [J Appl Biomech 22(3)](https://journals.humankinetics.com/view/journals/jab/22/3/article-p202.xml)):

- **Elite players bend early and recoil through the contact.** They bent the shaft from first puck contact to 28.8% of the contact window, then recoiled until 88.6% of it **[M]**.
- **Recreational players bend late and barely recoil.** Their bend began only at 44.4% of the window and lasted 18.2% of it. A recoil phase was "relatively non existent", and was "presumed" to take 35.4% **[M]**.
- **Elite players often bend before the puck.** In elite players the bend typically started before puck contact, at a time the study did not determine **[M]**.
- **The puck leaves and returns.** The puck was on the blade 38 ± 9 ms (elite) against 27 ± 5 ms (recreational), with one to three separations **[M]**. Other measurements:
  - 3-4 separate touches per slap shot, with the puck sliding 17-23 cm toward the toe **[M]** ([Simard et al. 2004](https://ojs.ub.uni-konstanz.de/cpa/article/view/1369))
  - in Kays's FE model, 42 ms from first touch to release, but only 27 ms in contact, over 4 touches **[E]**
- **Strong players load fast.** High-calibre players reached peak strain 3-4x faster than low-calibre players **[M]** ([Hannon 2010](https://mcgill.scholaris.ca/items/212dd3a6-79f6-4e61-8e47-a6abc33141b2)). *Corrected in fact-check:* "3 to 4 times" is the abstract's wording. The results table gives 53-56 ms against 348-350 ms to peak strain (about 6x). The whole slap shot took 143 against 429 ms (3x). Hannon's event times are noisy: his "start" is the first rise in strain near the blade, not ice contact, and the start-to-puck interval was 85 ± 136 ms. So I don't use his times for sequencing.

### The bend lets go when the blade leaves the ice

- **The blade lifts off about 13 ms after puck contact in elite shots.** Lomond measured toe contact to puck contact at 14 ms and toe contact to the stick leaving the ice at 27 ms in elite slap shots. For recreational players the figures are 17 ms and 24 ms **[M]**. The thesis text reads "0.0017 s" for the recreational 17 ms. That must be 0.017 s, since it is given as 39% of a shot of about 45 ms. So the blade leaves the ice about 13 ms after puck contact for elite players and about 7 ms after for recreational players **[D]**.
- **That is when the bend peaks.** Peak bend in Kays's shot came 14 ms after puck contact **[M]**. The two studies are different players, but they agree. The ice holds the bend, and the recoil starts when the blade unweights **[E]**.
- **Players describe the same thing.** It is a "whipping action of the blade … as soon as ice friction is decreased, just before puck release" **[S]** (Robichaud 2002, via [Simard et al. 2004](https://ojs.ub.uni-konstanz.de/cpa/article/view/1369)).
- **Timing studies roughly agree.** Pearsall 1999 put time to peak bend at 23-27 ms after first contact and time to peak force at 24-26 ms **[S]**. Roy et al. 1974 (4 junior B players; *attribution corrected in fact-check*, the note had "Roy & Doré") measured bend durations of 63 ms (standing) and 82 ms (skating) slap shots. They also found that the shaft's peak angular velocity of deflection correlated with the puck leaving the blade **[S]** (via [Lomond 2005](https://mcgill.scholaris.ca/items/04d8dd90-f525-493d-9689-f4848abcb01f)).

### Wrist shot

- **The bend unloads while the puck is still speeding up.** In Kays's wrist shot the shaft already carried about 4° when the video started. It began to unload at about 47.5 ms, yet the puck kept speeding up until it left the blade at the end of the record **[M]** (Fig. 3.53). The text says the puck left at "0.01 seconds", which can only mean about 0.1 s on a plot that runs to 0.12 s.
- **Elite wrist shots keep the puck on the blade about 100 ms.** Contact time was 103-107 ms, against 50-53 ms for slap shots **[M]** ([Léger et al. 2022, Sensors 22:3419](https://pmc.ncbi.nlm.nih.gov/articles/PMC9105185)). That was 10 Junior A, university and pro players with Vicon at 240 Hz. Wrist contact was timed from blade acceleration above 150 m/s², slap contact from puck speed above 5 m/s. *Added in fact-check:* the paper defines no puck-release event; its only end event is the puck reaching the net. So the end of "contact time" is undefined, and the slap figure (50-53 ms) is longer than Villaseñor's 27-38 ms.
- **Flex and kick point did not change speed.** Flex 70 against 95, and low against high kick point, left speeds unchanged (wrist 27.4-27.9 m/s, slap 31.7-32.0 m/s) **[M]**.

### A bend released before the puck is wasted

- **One measured shot shows the loss.** Kays's slowest shooter built "nearly 4 degrees" on the ice. The bend fell to nearly zero before he reached the puck: the blade bounced off the ice and struck the puck higher up. His shot was 18 mph slower than the best shooter's **[M]** ([Kays 2013](https://rex.libraries.wsu.edu/esploro/outputs/graduate/Ice-hockey-wrist-and-slap-shots/99900525127201842), Figs. 3.39-3.40).
- **The field study found it generally.** "Swings where the blade bounced on the ice released energy stored in the stick, resulting in lower puck speeds" **[M]** ([Kays & Smith 2014, Procedia Eng 72:563](https://lida.sport-iat.de/ta/Record/4032115?lng=en); 6 players). *Corrected in fact-check:* this is the same six-player data set as Kays 2013. The thesis shows it for one shooter (shooter 6), so it is not independent support.
- **Shot timing matters as much in golf.** In 16 of 40 golfers the shaft was already recoiling when the club met the ball, so the flex *cost* clubhead speed **[M]** (Worobets 2008, below).

## 4. How much of the puck's speed the recoil adds

### Energy accounting

| Villaseñor 2004 (puck + accelerometer 0.260 kg) | Elite (n = 4) | Recreational (n = 5) |
|---|---|---|
| Puck speed | 33.5 ± 5 m/s | 22.3 ± 3.2 m/s |
| Peak stick kinetic energy in the swing | 179 ± 77 J | 123 ± 43 J |
| Stick bend energy, E_d | 16.5 ± 13.3 J | 2.1 ± 2.1 J |
| Puck kinetic energy | 152 ± 49 J | 67 ± 17 J |

All **[M]**, with one caveat. E_d is an *estimate inside the study*: ½Kd², where K = 15,000 N/m is a 3-point stiffness taken from Wu et al., and d is the lower-shaft distance from §2. It is an order of magnitude, not a calibrated energy. Puck speed correlated with E_d at r² = 0.81.

- **Upper bound on the recoil's share of speed** **[D]**. Suppose all of E_d reached the puck. The puck's speed without it would be v√(1 − E_d/E_puck).
  - Elite: 16.5 / 152 = 10.8% of the energy, which is 1 − √0.892 = **5.6% of the speed**.
  - Recreational: 2.1 / 67 = 3.1% of the energy, which is **1.6% of the speed**.
  - *Corrected in fact-check* **[D]**: E_puck was computed with the 0.260 kg puck-plus-accelerometer (thesis §3.1). A 0.17 kg puck at the same speeds carries 95 J (elite) and 42 J (recreational). Then 16.5 / 95 = 17% of the energy is **9% of the speed**, and 2.1 / 42 = 5% is **2.5%**.
  - *Added in fact-check* **[D]**: the §2 angle-to-centimetre figures on a 1.3-1.5 kN/m held stick give more. Skilled 12-16 cm stores 9-19 J (10-20% of 94 J, 5-11% of speed). Recreational 9-13 cm stores 5-13 J (13-30% of 42 J, 7-16% of speed). These sit above the force-based numbers below, the same mismatch §2 notes.
- **The same bound from forces and stiffness** **[D]**. Energy is U = F²/2k. A skilled slap shot's 165 N on a 1.3-1.5 kN/m held stick stores 9-10.5 J. The puck carries 94 J at 33.3 m/s and 0.17 kg, so U is ≤ 11% of it, or ≤ 6% of the speed. Unskilled, 105 N stores 3.7-4.2 J, against 42-46 J for a 22-23 m/s puck: ≤ 10%, ≤ 5%. A wrist shot's 44 N on a 0.7-0.8 kN/m stick stores 1.2-1.4 J, against 27-34 J for an 18-20 m/s puck: ≤ 5%, ≤ 2.5%.
- **Cross's worked example lands in the same place** **[E]**. A 1000 N/m stick bent 0.2 m holds 20 J, against 76 J for a puck at 30 m/s. "It is clear from this result that the puck did not get its energy from the bending of the stick." In his models, flex mainly changes how long the push lasts and how the force is spread over it ([Cross 2016](https://twu.tennis-warehouse.com/learning_center/hockeyphysics.php)).
- **The swing is the energy source.** The stick's swing kinetic energy (123-179 J) is 11-60x the bend energy (179/16.5 and 123/2.1). The bend is a way to keep the blade pushing longer, not a separate power source **[D]**.

### Stiffness studies: how much does the spring matter?

| Study | Players | Result |
|---|---|---|
| Pearsall et al. 1999 ([abstract](https://sponet.de/sponet/Record/4004514)) | 6 elite; 13-19 kN/m | most flexible (13 kN/m) fastest; variability across players > across sticks **[M]**. 108.2 against 105.9 km/h (2%) **[S]**: *retagged in fact-check*. The abstract gives no speeds; Kays 2013 and Lomond 2005 give them. 105.9 km/h is the extra-stiff shaft (17 kN/m), not the stiffest (19 kN/m), and was the only significant pairwise difference. |
| [Pearsall et al. 2001](https://ojs.ub.uni-konstanz.de/cpa/article/view/3779) | 20 | no effect of stick on slap speed **[M]** |
| Roy & Doré 1976, via Villaseñor | 11-year-olds; 17.1 against 24.1 lb/in | flexible stick 56.8 against 54.4 km/h (+4.4%) **[S]** |
| Worobets et al. 2006 ([Sports Eng 9:191](https://doi.org/10.1007/BF02866057)) | 5 elite, 8 of 30 sticks | wrist: stiffness mattered through the energy stored; slap: "energy considerations were unable to explain" speed changes **[M]**, abstract only |
| [Grover, Wannop & Stefanyshyn, c. 2013](https://journalhosting.ucalgary.ca/index.php/jura/article/view/30152) | 14 analysed; Easton 85/100/110 flex (6,400 / 7,400 / 8,000 N/m) | wrist: most flexible +2.7%; slap: stiffest +3.2%; each player's best stiffness differed **[M]** |
| [Kays & Smith 2014](https://lida.sport-iat.de/ta/Record/4032115?lng=en) | 6 | player-to-player 32%, stick-to-stick 14% **[M]** |
| [Kays & Smith 2017](https://lida.sport-iat.de/twm/Record/4047169) | 6 + FE | slap: speed *fell* with stiffness ("constant force" player); wrist: speed *rose* with stiffness ("constant displacement" player) **[M]** |
| Kays 2013 FE | model | doubling shaft stiffness: +3.9 mph; ±16% stiffness: 1.5 mph **[E]** |
| [Léger et al. 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9105185) | 10 | flex 70 against 95: no change **[M]** |

**Reading [D].** Across studies the stick's spring moves shot speed by 0-4%, in either direction depending on shot and player. That fits the ≤ 2-6% energy bound above.

### The "40-50%" claim

- **The source gives no derivation.** "[Pearsall, Turcotte & Murphy 2000] attribute 40% to 50% of final slap shot velocity to the amount of deflection" **[S]** ([Laliberte 2009, The Sport Journal](https://thesportjournal.org/article/biomechanics-of-ice-hockey-slap-shots-which-stick-is-best/)). ~~The review notes the figure's derivation is not shown.~~ *Corrected in fact-check:* the review makes no comment on the derivation. It cites the 2000 chapter (p. 690), which I could not open.
- *Added in fact-check:* **The figure is older.** Lomond 2005 (§2.1.1.1, p. 15) traces it to Roy et al. 1974. That study filmed 4 junior B players at 200-500 Hz; their maximum slap shot was 89 km/h. "The authors attributed 40 to 50% of puck velocity to shaft deflection in the slap shot trials; whereas only 25 to 34% and 8 to 10% … in the wrist and backhand shots." They thought the deflection came mainly from blade-ice friction, not the puck. Lomond adds that "the precise contribution of blade flexion was not investigated" **[S]**.
- *Added in fact-check:* **A model claim of the same kind.** Baroud et al. 1999 (FE model of a wood stick, via Lomond 2005) found 11 J of deformation energy "translated into an 11.3 m/s increase in puck velocity" **[S]**. That is just √(2 × 11 / 0.17) = 11.4 m/s for a puck starting from rest. Added to a puck already at 30 m/s, 11 J gives √(900 + 129) − 30 = 2.1 m/s, or 7% **[D]**.
- **The energy measurements rule it out** **[D]**. 40-50% of speed would need 1 − 0.6² = 64% to 1 − 0.5² = 75% of the puck's energy to come from the bend. Villaseñor measured at most 11%. The claim probably counts the stick's whole "catapult" motion, not elastic return.

### Preload and friction in scaled and FE models

- **In a scaled lab model, preload helped a lot** **[M]**. Cross & Lindsey used a 30 cm aluminium-beam pendulum ([TWU 2016](https://twu.tennis-warehouse.com/learning_center/hockeyvelocity.php/1000)). Bending it against a "table-top ice" before it hit the puck raised puck speed 15-34%, more with the hand placed nearer the top. Collisions became "superelastic" (COR 1.16). They warn: "Performed or timed incorrectly, puck speed may actually decrease." This is a scaled model with a stiff, light beam, so the 15-34% is not a hockey number.
- **In the FE slap shot, ice friction loaded the shaft** **[E]**. With hand motion prescribed, blade-ice friction from 0 to 0.35 raised puck speed from 75 to 85.2 mph (+14%), the peak of the sweep. Higher friction made the shaft flex more, and twist more. This is the same mechanism the sim tried (+5-11% on a synthetic slap shot). The size matches, but it rests on a fixed-hands model and a friction coefficient nobody has measured.
- **The FE model's hands were too stiff.** The model shot 76 mph against the video's 66 mph. Kays blames "this inability for the stick to rotate freely in the hands" **[E]**. A stick welded to the hands overstates speed by about 15%.

### Golf, for comparison

- **Kick velocity is small and can be negative.** In 40 golfers (Worobets 2008, Calgary PhD, [record](https://ucalgary.scholaris.ca/items/4f37ab6b-f902-44b9-a9d2-84f0a9a7167d)), the shaft's peak "kick velocity" was 2.4 m/s, at about 95% of the downswing. At impact it was +0.9 m/s in 60% of golfers and −0.7 m/s in 40%, against a clubhead speed of 43.4 m/s. That is +2% or −1.6% **[M]**. Whether flex helps depended on "how the player loads the club".
- **A golf swing model agrees.** A golf forward-dynamics model found that shaft stiffness changed clubhead speed by ≤ 0.1 m/s **[S]** (MacKenzie & Sprigings 2009, Sports Eng 12:13, from a search summary of the thesis record only).

### Puck speed against blade speed

- **The best measured shot left 1.27x the blade's speed.** In Kays's shot the blade hit the ice at 51.9 mph and the puck left at 66.0 mph **[M]**. Across the field study, the average blade speed just before puck contact was 50.4 mph and the average puck speed about 54 mph, a ratio of about 1.07 **[D]**. *Corrected in fact-check:* Kays's field puck speeds are radar. For the 56 tracked slap shots, video tracking read 3.8 mph (SD 6.1) above radar (§3.4.3, p. 92). With that, the average ratio is about 57.8 / 50.4 = 1.15 **[D]**.
- **Measured blade speeds at impact are 22-29 m/s.** That is 26.5 m/s recreational and 29.1 m/s elite in slap shots (60 Hz electromagnetic tracking, [Woo et al. 2004](https://ojs.ub.uni-konstanz.de/cpa/article/view/1368)), and 22.5 m/s in Kays's mixed group **[M]**.

## 5. Energy stored against energy returned

- **The one direct test isn't retrievable.** Worobets et al. 2006 reproduced each shot's measured bend on a bench, with supports placed where the hands were. Stored and returned energy were the areas under the loading and unloading curves, and the loss was their difference **[S]** (method via Kays 2013). Their numbers sit behind the paywall. I could not get them.
- **The shaft itself loses little.** Free-free modal tests of seven sticks put the first bending mode at 46-53 Hz and the second at 117-141 Hz (cheap and expensive group averages) **[M]**. For a wood stick the first mode was 45.5 Hz, with a "damping" of 1.2 Hz **[M]** (Kays 2013, Table 3.3). Read as a half-power bandwidth that is ζ ≈ 1.3%; read as ζ·f it is 2.6% **[D]**. Either way a bent shaft keeps most of its energy over a half cycle. Wood damps 2-4x more than composite (earlier note).
- **The losses are in the hands and the timing.** The hands damp the stick and bend it back. Energy released while the puck isn't on the blade goes into the stick's vibration and the hands (§3). The sim's 0.6 / 1.5 damping ratios stand for the hands. No one has measured a held stick's damping **[E]**.
- **The puck's own bounce barely matters.** The FE model's puck speed hardly changed with puck restitution 0.23-0.60 (≤ 0.8 mph) or puck stiffness (≤ 0.5 mph) **[E]**. A shot is a push, not a bounce, as the earlier note found.

## 6. What a minimal real-time stick model needs

The sports-engineering models range from Cross's one-spring rotation model to Kays's FE model:

- **Cross 2016** **[E]** ([physics](https://twu.tennis-warehouse.com/learning_center/hockeyphysics.php)) has three steps. A constant-force push, a collision, and then a rotating stick (I₀ ≈ 0.45 kg·m²) with one spring for flex. Flex sets the release time and how the force is spread. It does not change the final speed for the same energy.
- **Kays 2013 / Kays & Smith 2015 FE** **[E]** ([Procedia Eng 112:22](https://lida.sport-iat.de/mint/Record/4035912)) has a linear elastic stick, a viscoelastic puck, and gloved hands driven by measured motion. It reproduced the ice lead (15 ms against 13 ms in video; 11.5 against 11.3 in), the contact pattern (27 ms over 4 touches) and the strain profile shape. Speed came out 15% high because the hands were too rigid.
- **Kays & Smith 2017** **[M/E]**: whether a player acts like a constant force (big loads, slap shot) or a constant displacement (small loads, wrist shot) flips the sign of the stiffness effect.

What that implies for a real-time model:

1. **One bending mode at the blade is enough for speed** **[E]**. The held stick's lowest mode (about 11 Hz, quarter period about 22 ms) overlaps the 15-100 ms contact. The next modes (46-60 Hz free-free and up) have quarter periods of ≤ 5 ms. They respond almost statically during a push, so they matter for feel (vibration, the earlier note) and not for puck speed. The sim's single mass-spring is the right structure.
2. **The stiffness must be the held-stick value** **[D]**. That is k = 3EI / (a²(a+b)) with EI = 3.65 × flex N·m², which gives 0.7-1.8 kN/m depending on grip, with m ≈ 0.15-0.20 kg. (*Corrected in fact-check:* about 0.6-2.6 kN/m once both bench tests are allowed for.) A wrist grip (bottom hand high) is about half as stiff as a slap grip.
3. **The ice must be a one-sided support that holds the bend** **[E]**. The normal force holds the blade up. When the blade sweeps, friction holds it back. Only a bend the ice is holding should store energy. It is released through the spring when the support goes, which happens when the blade unweights or the friction drops. It is never released as a step.
4. **The hands need a force limit** **[D/E]**. Measured blade forces in shots are 45-165 N (the skilled mean plus one SD is about 215 N). VR hands are kinematic: a "constant displacement" player with no limit. A 19 cm press would ask a held stick for 130-285 N. The sim's cap (12 cm of bow, then the stick slides up through the hands) does this job. At a real held stiffness, 12 cm is 85-180 N, a skilled slap shot's peak.
5. **Release only along the direction of loading** **[E]**. A vertical press bends the shaft in its lie plane. A sweep against friction or the puck bends it along the face normal. Only the second can push a puck toward the target.
6. **The stick must give at the hands** **[E]**. Kays's rigid-hands model overshot speed by 15%. The sim's bottom-hand slide and damping play this role.
7. **No energy from the press by default** **[D]**. The bend energy a press could honestly store is ≤ 1-2 J (wrist) to about 10-16 J (strong slap shot). The recoil's honest share of speed is ≤ 2-6% (*corrected in fact-check:* ≤ 2.5-9% for a regulation puck, up to about 10-15% by the angle-based bends). The sim's energy-free bow gives 0%, which is inside the honest range. A friction-loaded bow worth +5-11% sits at or above the top of it.

## 7. Pressing into the ice without sweeping, then lifting

No study tested this. The physics below is **[E]**. It assumes a uniform shaft, a blade face square to the shot, and the lie plane (the vertical plane through the shaft) perpendicular to the face.

1. **Press.** The hands go down; the ice pushes up on the blade. The shaft bows within the lie plane, with the blade end relatively up and along the shaft's line, not toward the target. The stored energy is U = F²/2k.
   - On a 0.7-1.5 kN/m held stick, 50 N stores 0.8-1.8 J, 100 N stores 3.3-7.1 J, and 165 N stores 9-19 J **[D]**.
   - The spring force is square to the shaft. With the shaft at about 45° to the ice, its horizontal and vertical parts are about equal. Unless the blade's edge grips the ice, the blade slides a little along its own length (heel to toe). That motion is along the blade, not toward a puck in front of the face.
   - With no sweep there is no friction load along the face normal, so nothing is cocked toward the target.
2. **Lift, at any speed.** While the bend lasts, the ice keeps the blade pinned. The spring pulls it *down* onto the ice, so it cannot move. As the hands rise the bend shrinks. Its energy goes back into the hands, which "receive" the push.
3. **Lift-off.** The blade leaves the ice when the bend reaches zero. At that moment its speed is about zero. The spring then pulls it after the hands.
   - At that instant the spring force is zero and only the damper pulls, so its first acceleration is 2ζω·v_hands. With ω = 73-93 rad/s (k 0.8-1.3 kN/m, m 0.15 kg) that is about 90-110 s⁻¹ × v_hands at ζ = 0.6, and 220-280 s⁻¹ × v_hands at ζ = 1.5 **[D]**. For 1 m/s of hand lift at ζ = 0.6, that is about 100 m/s².
   - It reaches the hands' speed after about 1.16/ω = 12-16 ms at ζ = 0.6, or 0.86/ω = 9-12 ms at ζ = 1.5. Its speed then overshoots the hands' by about 25% at ζ = 0.6, or 8% at ζ = 1.5 **[D]**. These come from solving the damped spring with the blade starting at rest and the hands moving at a steady speed, checked by numerical integration.
   - *Corrected in fact-check* **[E/D]**: the two bullets above assume the blade stays down until the bend is gone. With the damper between stick and blade, as in the sim's `Flex`, the damper pulls up with c·v_hands while the bend still pushes down. The blade lifts once kd < c·v_hands, with d = 2ζ·v_hands/ω of bend left. At 1 m/s that is 1.3-1.6 cm (ζ 0.6) or 3.2-4.1 cm (ζ 1.5). It leaves at zero speed *and* zero acceleration. A 1 µs integration (m 0.15 kg, k 0.8-1.3 kN/m) gives these results:
     - ζ 0.6: the blade reaches hand speed 30-38 ms after lift-off, then overshoots by about 10%.
     - ζ 1.5: it reaches 90% of hand speed only after 70-90 ms, with no overshoot.
     The 12-16 ms and 25% above hold only if the hands do all the damping. Either way the blade ramps up with no step.
   - Nothing is thrown: the energy went back to the hands in step 2.
4. **What a puck in front of the face feels.** Only the blade face rising past it, with face friction (puck on tape μ ≈ 0.43-0.50, earlier note). An open face would lift it a little, and a cupped face would press it down. It gets no forward push.
5. **The real exception is a press with a sweep.** Then the ice friction holds the blade back and loads a bend along the face normal. When the blade unweights, that bend whips the blade forward. If the puck is on the blade, the puck gets it, as in §3. If not, it is lost to vibration, which is the "bouncing blade" loss Kays & Smith measured.

**Compared with the sim [D].**

- **What matches.** The sim's bow goes "across the shaft, toward up", which is the lie plane. It stores no energy, which matches step 2: the energy goes back to the hands.
- **What doesn't.** At the end of the bow the blade jumps to the hands' full rising speed in one tick, because the bow is kinematic. A real blade starts from rest and catches up over about 10-16 ms (step 3). *Corrected in fact-check:* that becomes 10-40 ms, depending on where the damping sits.
- **Why it matters.** The jump adds an unphysical vertical step to the blade's contact velocity just as a pressed blade lifts near the puck. That is the moment the launch glitches cluster around.

## What this means for the sim

| Quantity | Real value | Source | Sim now | What to match |
|---|---|---|---|---|
| Blade stiffness when held | 0.7-1.8 kN/m by grip (flex 75: 1.3 slap grip, 0.7 wrist grip); measured 0.77-0.89 (two clamps) and 1.0-1.4 kN/m (heel). *Corrected in fact-check:* about 0.6-2.6 kN/m, because the formula reads 4-20% high against Cross and 26-44% low against Kays | Cross & Lindsey; Kays 2013; §2 **[M/D]** | 2.57 kN/m (flex 75) | about half the current value (1.2-4x softer by grip and bench test): flex over a 1.0 m span and two-hand supports |
| Effective blade mass | 0.13-0.20 kg | from Cross **[D]** | 0.15 kg | keep |
| First held mode, quarter period | about 11 Hz, 21-23 ms | Cross **[M]** | 20.8 Hz, 12 ms | 9-17 Hz, 15-27 ms by grip |
| Ice before puck (slap) | 10-19 ms, 27-41 cm; elite 14 ms. *Added in fact-check:* low-calibre strain onset 349 ± 299 ms before puck contact (Hannon) | Kays; Lomond; Hannon **[M]** | Jon's presses come up to 0.6 s before swings | a press held long before a swing should carry nothing into the shot |
| Bend at puck contact (slap) | 4-7° ≈ 3-7 cm | Kays **[M/D]** | — | — |
| Peak bend | recreational slap 11-12.5° (9-13 cm); skilled 15-19° (12-16 cm, up to about 20 cm); wrist 6-11° (5-10 cm) | §2 **[M/D]** | bow cap 12 cm, flex cap 15 cm | 12 cm ≈ a typical skilled slap shot and enough for a recreational player; only the strongest shots reach 15-20 cm |
| Peak blade force | wrist about 45 N; slap 100-165 N | Wu; Pearsall **[M/S]** | unlimited (kinematic hands) | cap at about 150-200 N; slide beyond (as now) |
| Time of peak bend | about 14 ms after puck contact, as the blade leaves the ice (elite lift-off 13 ms after contact) | Kays; Lomond **[M/D]** | — | release when the blade unweights, through the spring |
| Elastic energy at peak | recreational about 2-6 J; elite about 10-16 J; wrist about 1-2 J | Villaseñor; §4 **[M/D]** | bow 0 J (by design); at 2.57 kN/m a 12 cm bow would hold 18.5 J | if a bow ever stores energy: ≤ 10 J recreational, ≤ 16 J elite |
| Recoil's share of puck speed | ≤ 2-5% (recreational) to ≤ 6% (elite); stick-to-stick 0-4%. *Corrected in fact-check:* ≤ 2.5-9% with a regulation-mass puck, up to about 10-15% from angle-based bends | §4 **[D/M]** | 0% from the bow | stay ≤ about 5%, never above about 10% |
| Lift-off after a press | vertical speed 0, reaching hand speed in about 10-16 ms, then up to 1.25x hand speed (ζ 0.6) or 1.08x (ζ 1.5). *Corrected in fact-check:* with the sim's stick-to-blade damper, it takes 30-38 ms with a 1.1x overshoot (ζ 0.6), or 70-90 ms to reach 90% (ζ 1.5) | §7 **[E/D]** | jumps to hand speed in one tick | no step: initial acceleration between 0 and 2ζω × v_hands, depending on where the damping acts |
| Recoil direction | along the loading direction; vertical press → lie plane only | §7 **[E]** | bow direction correct | never release a press bow along the face normal |
| Puck on blade | slap 15-53 ms (1-4 touches); wrist about 100 ms (elite 103-107 ms; *fact-check:* Léger never defines the end event) | Villaseñor; Swarén; Léger **[M]** | scoops about 75 ms | 75 ms is normal for a sweep; judge scoops by a rising, accelerating blade instead |
| Blade speed at puck contact | slap 22-29 m/s (Kays's mixed group 22.5, recreational 26.5, elite 29.1) | Woo; Kays **[M]** | single ticks over 40 m/s | over about 30 m/s is beyond anything measured in these labs, even for elite players |
| Puck / blade speed | 1.07 average (*fact-check:* about 1.15 after Kays's radar-vs-video offset), 1.27 best shot (vs blade at ice contact) | Kays **[D]** | 0.98 slow tap; 1.1-1.26 earlier tests | keep ≤ about 1.3 |

Two cautions:

- **Softening the spring changes other things** **[D]**. Halving k:
  - doubles how far the blade lags under steady hand acceleration (x = ma/k)
  - makes the blade give about 1.4x more under a pass (x ≈ v/ω, and ω ∝ √k), so the earlier note's 3.4 cm for a 10 m/s pass would become about 5 cm
  - for the same force, doubles both the bend and its energy (U = F²/2k); for the same bend, halves the energy

  Check reception give and the "hands" damping before changing it.
- **Friction loading is real, but its size rests on two weak legs** **[E]**. These are a fixed-hands FE model (+14% at μ = 0.35) and an unmeasured blade-ice friction coefficient. If it comes back, it should store energy only while the blade sweeps on the ice, release it along the sweep direction, and drop it (as vibration) if the blade lifts before reaching the puck.

## Gaps

- **Blade-ice friction during shots.** No one has measured the coefficient, static or sliding, on real ice, or how far a blade digs in. Kays's model assumed 0 to 0.6.
- **Energy returned to the puck in play.** Worobets's bench test of stored against returned energy exists, but I couldn't retrieve its numbers. No in-play measurement separates elastic return from the hands' push.
- **Held-stick damping and effective mass with real hands.** Cross clamped the handle; no one measured a stick held in gloved hands.
- **A static press, or a press and lift without a swing.** Untested. §7 is physics only.
- **Ice-contact timing for wrist and snap shots.** Only slap shots are timed. Snap-shot distances are coaching tips.
- **Peak bend against blade lift-off in the same shots.** They agree across two studies (Kays; Lomond) but were never measured together.
- **Adult recreational data are thin.** The recreational groups are 5-10 players per study, mostly in labs on force plates or synthetic ice, where the blade cannot dig in.
- **Conflicting contact times.** Hannon found *longer* puck contact for low-calibre players (80 against 58 ms). Villaseñor found shorter (27 against 38 ms). The event definitions differ, and neither is on real ice.
- **Bend direction.** Major- against minor-axis bending and torsion are only partly described (Flemming, abstract). Nobody gives a stick's stiffness for each bending direction at the blade.
- **The "40-50%" figure** (Pearsall, Turcotte & Murphy 2000) could not be traced to a calculation. *Updated in fact-check:* Lomond 2005 traces it to Roy et al. 1974 (4 junior B players, film). Their method is still not described in any source I could open.
- *Added in fact-check:* **Held-stick stiffness.** Two bench tests (Cross & Lindsey; Kays) disagree with the two-support beam formula in opposite directions. Measured stiffness sits 4-17% below it (Cross) and 35-80% above it (Kays). A held-stick stiffness test with real grips would settle the sim's spring.

## Fact-check (2026-11-10)

I opened each primary source below and checked the numbers against its own text, tables and conditions. Sources read in full: Kays 2013 thesis (PDF), Lomond 2005 thesis (PDF), Villaseñor 2004 thesis (PDF), Hannon 2010 thesis (PDF), Pearsall et al. 2001, Simard et al. 2004 and Woo et al. 2004 (ISBS PDFs), Cross & Lindsey's three TWU pages, and Léger et al. 2022 (PMC). Abstracts only: Kays & Smith 2014 and 2017, Pearsall et al. 1999, Worobets et al. 2006 (catalog record), Grover 2013, Flemming 2015. Laliberte 2009 was read in full. I re-ran the sim's `tip_stiffness` and the §7 lift-off with a 1 µs integration.

| # | Claim in the note | Verdict | What the source actually says |
|---|---|---|---|
| 1 | Slap-shot ice lead 10-19 ms (mean 14 ± 3.5), 27-41 cm (33 ± 6); 6 shooters, 2 on real ice, 4 synthetic, 1000 fps | confirmed | Kays 2013 Table 3.7: 0.010-0.019 s, mean 0.014 ± 0.0035 s; 10.8-16.0 in, mean 12.9 ± 2.24 in. §3.4: six players aged 18-44; two WSU varsity players on real ice, the rest on synthetic ice; slap shots at 1000 fps. No correlation with puck speed (Fig. 3.42). For shooter 5's modelled shot Kays gives 11 ms (§3.4.4) and 13 ms (§4.4.2). |
| 2 | Lomond: toe contact to puck contact 14 ms elite, 17 ms recreational; toe contact to stick off the ice 27 / 24 ms; rocker 6 ms (13%) / 9 ms (21%) | confirmed | Lomond 2005 §4.1.2 and §5.3, 8 elite and 7 recreational players. The "0.0017 s" is a typo; §5.3 says 0.017 s. **Condition:** lab shots on polyethylene sheets with silicone spray, on force plates, not ice. |
| 3 | Elite lift-off about 13 ms after puck contact, recreational about 7 ms | confirmed [D] | 27 − 14 = 13 ms and 24 − 17 = 7 ms, from the same Lomond means. These are differences of group means, not per-shot timings. |
| 4 | Pearsall 2001: bend 19.1 ± 5.0° skilled vs 12.5 ± 3.5° unskilled; deflection 5.7 vs 3.7°; force 165 ± 50 vs 105 ± 48 N; shafts 13.7/16.6/17.9 kN/m; 480 fps | confirmed | Table 2: P_THETA 19.1 ± 5.0 vs 12.5 ± 3.5; DEFLEC 5.7 ± 1.5 vs 3.7 ± 1.0; FMAX_Z 164.7 ± 49.9 vs 104.7 ± 48.2 N. 10 varsity vs 10 recreational. **Conditions:** shots from an AMTI force platform in a lab; video in the sagittal plane only. Neither angle is defined. |
| 5 | Kays: maximum bend 15.0° and 14.3° on the two 85-flex sticks, 7.0° and 6.9° at puck contact | confirmed | Kays §3.4.4 (Fig. 3.51 text): sticks H2 and L2, both 85 flex. These are the most compliant sticks, so they are the top of the range, not typical values. Bend is the angle between the top and bottom marker pairs (Fig. 3.24). |
| 6 | One slap shot: ice at −11 ms, about 4° at puck contact, 15° peak at +14 ms, puck leaves as the bend returns to zero (66 mph) | confirmed | Kays Fig. 3.52 text and §3.4.3: "maximum deflection of 15 degrees at 0.014 seconds". Shooter 5 "was able to take advantage of the entire recoil phase with the puck leaving the blade as the deflection was zero degrees". **n = 1 shot.** The generalisation is consistent with Villaseñor's elite group: bend for 28.8% of 38 ms ≈ 11 ms **[D]**. |
| 7 | Villaseñor: elite bend 0-28.8% of contact, recoil to 88.6%; recreational bend from 44.4% lasting 18.2%, recoil "presumed" 35.4%; elite bend often starts before contact | confirmed | Villaseñor 2004 thesis §5.3-5.4, word for word. Elite pre-contact bending "was not determined". |
| 8 | Villaseñor sample: 4 elite, 5 recreational; contact 38 ± 9 vs 27 ± 5 ms | confirmed | Thesis §3.2: four elite, five recreational (threshold 100 km/h). Kays 2013's review gets this backwards ("five elite and four recreational"). §5.3: 0.038 ± 0.009 s and 0.027 ± 0.005 s. **Condition:** polyethylene "artificial ice" in a lab. |
| 9 | Villaseñor energy table (E_d 16.5 ± 13.3 / 2.1 ± 2.1 J; E_puck 152 ± 49 / 67 ± 17 J; stick KE 179 ± 77 / 123 ± 43 J; puck 33.5 ± 5 / 22.3 ± 3.2 m/s; K = 15,000 N/m; d = 0.30 m × tan θ; r² 0.82 and 0.81) | confirmed | Tables 4.1.2, 4.2.9, 4.3.2 and 4.3.3; Eq. 3.5.8-3.5.11; §4.14 (max angle and d, r² = 0.82) and §4.16 (E_d, r² = 0.81). K is assumed from Wu's 3-point tests. Lomond 2005 misquotes these as r, not r². |
| 10 | Recoil adds at most 2-5% (rec) to 6% (elite) of puck speed | corrected | Villaseñor's E_puck uses a 0.260 kg puck-plus-accelerometer (thesis §3.1). For a 0.17 kg puck the same E_d bounds speed at 2.5% (rec) and 9% (elite) **[D]**. The note's own §2 bends on a held-stick spring give up to 10-15% **[D]**. "A few percent, at most about 10%" is what the evidence supports. |
| 11 | "40-50%" has no derivation; "the review notes the derivation is not shown" | corrected | Laliberte 2009 quotes the figure and cites Pearsall, Turcotte & Murphy 2000, p. 690. It says nothing about a derivation. Lomond 2005 §2.1.1.1 traces the figure to Roy et al. 1974 (4 junior B players, film at 200-500 Hz). They also gave 25-34% for wrist and 8-10% for backhand shots, and blamed blade-ice friction for the bend. "The precise contribution of blade flexion was not investigated." The 64-75% energy arithmetic stands. |
| 12 | Cross & Lindsey: two clamps 50 cm apart, blade 86 cm beyond; 5.35 kg gives 59-68 mm (770-890 N/m); about 11 Hz; release time 20.7-23.3 ms | confirmed | TWU "hockeyflex" page (15 Nov 2016): clamped "at the handle end and also at a point 50 cm from the handle end", L2 = 86 cm, 13 sticks of measured flex 79-90. Release time is timed "from the lowest point to the straight (horizontal) position", a quarter period. **Not peer-reviewed.** |
| 13 | Flex is lb/in over a 1.0 m span, so EI ≈ 3.65 × flex N·m² (310 at flex 85) | confirmed | Cross & Lindsey: "The standard test distance is L = 1.0 m"; "EI for all the sticks is about k/48 = 310". This is one physicist's web page, not a published standard. Manufacturers' test spans were not checked. Arithmetic re-run: 4.448 / 0.0254 / 48 = 3.648. |
| 14 | k = 3EI/(a²(a+b)) gives 0.7-1.8 kN/m held, so the sim (2,568 N/m at flex 75, 20.8 Hz, 12.0 ms) is about 2x too stiff | corrected | The formula and the sim's numbers re-compute exactly. Against Cross it reads 4-20% high. Against Kays's roller test (supports 36 in and 66 in up the shaft, 10 lb on the blade; Table 3.2: 5.7-8.1 lb/in = 1.0-1.4 kN/m) it reads 26-44% low. So the band is about 0.6-2.6 kN/m and the sim is 1.2-4.4x too stiff. 2x is the middle. |
| 15 | Effective blade mass 0.13-0.20 kg | confirmed [D] | m = k/(2πf)² with Cross's 770-890 N/m and f = 1/(4 × 20.7-23.3 ms): 0.134-0.196 kg. It rests on Cross's clamp test alone. |
| 16 | Léger 2022: wrist puck-on-blade 103-107 ms, slap 50-53 ms; flex 70 vs 95 no change | corrected (overstated) | Table 5: wrist 103-107 ms, slap 50-53 ms ✓. n = 10 (2 Junior A, 5 university, 3 pro), synthetic ice, Vicon 240 Hz ✓. But the paper never defines contact time. There is no release event, and the only END event is the puck reaching the net. Wrist START is the blade's forward acceleration, not puck contact. Slap speed did not differ between sticks; for wrist speed no test is reported. |
| 17 | Woo 2004: blade speed at impact 29.1 elite vs 26.5 m/s recreational, 60 Hz electromagnetic | confirmed | ISBS 2004: 29.14 ± 1.39 vs 26.46 ± 0.66 m/s, 5 + 5 players, 60 Hz. At 60 Hz a 27 m/s blade moves 45 cm per sample, so treat the values as rough. |
| 18 | Kays blade speeds 53.5 / 50.4 / 25.5 / 43.3 mph; puck/blade ratio 1.07 average, 1.27 best | partly corrected | Speeds confirmed (§3.4.3). Best shot confirmed: Table 4.10 gives blade 51.9 mph at ice contact and puck 66.0 mph. The 1.07 uses radar puck speeds. For slap shots, video tracking read 3.8 mph (SD 6.1) above radar, which makes it about 1.15 **[D]**. |
| 19 | A bend released before the puck is wasted (Kays's shooter 6; Kays & Smith 2014 "generally") | confirmed, retagged | Kays Figs. 3.39-3.40: shooter 6 built "nearly 4 degrees", it decayed, and the blade "bounced off of the ice surface". His shot was 48 mph against shooter 5's 66 mph. Kays & Smith 2014 abstract: "Swings where the blade bounced on the ice, released energy stored in the stick, resulting in lower puck speeds." This is the same six-player data set, not independent evidence. |
| 20 | FE model: best ice distance 24 cm (74.3 → 80.3 → 73.5 mph); friction 0 → 0.35 raises speed 75 → 85.2 mph; model 76 vs 66 mph from rigid hands | confirmed | Kays §4.4.2-4.4.3 and Fig. 4.22/4.25 text. Kays & Smith 2017 abstract: "optimal loading distance … 24 cm". Kays blames "this inability for the stick to rotate freely in the hands". |
| 21 | Pearsall 1999: 108.2 vs 105.9 km/h, tagged [M] from the abstract | corrected (retag) | The abstract gives no speeds, only that the 13 kN/m stick was fastest and bent most. The numbers come from Kays 2013 and Lomond 2005 **[S]**. 105.9 km/h was the extra-stiff (17 kN/m) shaft. |
| 22 | Stiffness studies: Grover +2.7% wrist / +3.2% slap, 6,400-8,000 N/m, 14 analysed, 28.3% more bend; Kays & Smith 32% vs 14%; Kays & Smith 2017 sign flip; Worobets 2006 | confirmed | Grover 2013 (JURA extended abstract, an undergraduate project): 22 recruited, 14 analysed. Kays & Smith 2014 and 2017 abstracts as quoted. Worobets 2006 catalog abstract: stiffness mattered for wrist but not slap shots, and "how the athlete loads the stick has as much influence … as stick construction". |
| 23 | Hannon 2010: peak strain 4,900 ± 1,170 vs 3,690 ± 1,430 µε; 54-64% lower 600 mm down; 77 flex 7-27% more; high calibre reached peak 3-4x faster; start-to-puck 85 ± 136 ms | corrected | Strain values, percentages and 85 ± 136 ms (high calibre) confirmed: 17 men, synthetic ice, 10 kHz. "3 to 4 times" is the abstract's wording. Table 8 gives 53-56 vs 348-350 ms to peak (about 6x). The note left out the low-calibre start-to-puck time: 349 ± 299 ms. That bears on "a long press is not how real players load". |
| 24 | Wu et al. 2003 reported r = 0.80 between bend and speed | unsupported | Kays's review says only "a high correlation between stick bending and peak velocity". No r = 0.80 appears in Kays, Villaseñor or Lomond. Wu's own paper was not opened. |
| 25 | Simard 2004: 11.0-16.0° (composite mean 12.9°), 3-4 touches, puck slides 17-23 cm | confirmed | Table 2: 13.5, 15.6, 11.0, 11.5° (composites) and 16.0° (wood); 3.5-4.1 rebounds; 173-230 mm. 1 semi-pro, polyethylene with WD-40. |
| 26 | §7: after a press, the blade starts with acceleration 2ζω·v and reaches hand speed in 12-16 ms (ζ 0.6) with 25% overshoot | corrected [E] | The arithmetic is right if the blade leaves exactly when the bend reaches zero. It is not self-consistent with a stick-to-blade damper, which lifts the blade earlier. With the sim's `Flex` form: lift-off with 1.3-4.1 cm of bend left, at zero acceleration; hand speed after 30-38 ms (ζ 0.6, about 10% overshoot); 90% only after 70-90 ms (ζ 1.5). The conclusion "no step; ramp over tens of ms" holds. |

**Additional source found:** Baroud et al. 1999, an FE wood stick via Lomond 2005: 11 J of bend "translated into an 11.3 m/s increase in puck velocity" **[S]**. That figure assumes the puck starts from rest; on a 30 m/s puck the same 11 J adds about 7% **[D]** (§4).

**Not re-checked:** Hoerner 1989, Wu et al. 2003, Polano 2003, Roy et al. 1974 and Roy & Doré 1976 (all secondary in the note and correctly tagged [S]); Worobets 2008 (golf, record has no abstract); MacKenzie & Sprigings 2009; coaching and NHL quotes ([V]).
