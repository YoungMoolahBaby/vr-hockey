# Shot outcomes: what real shots do

Research round "Shot release", 2026-11-10. Topic: real shot speeds by skill and shot type, their spread, what skating adds, how high and how steeply pucks leave the blade, and how players lift the puck. The aim is acceptance bounds for the sim's called shot speeds and launches.

This note builds on `Hockey physics feel/stick and puck contact.md` (speed table, contact times) and `VR hockey stick and puck feel/hockey_hands_science.md` (Villaseñor, Woo, Zane). It does not repeat them. Most new numbers come from McGill and WSU theses whose full text I read, and from the NHL's own puck-tracking data.

Tags: **[M]** measured in the cited study. **[D]** derived by me (arithmetic shown). **[E]** estimate or physics with stated assumptions. **[V]** vendor claim, coaching blog or anecdote. **[S]** secondary: read in a citing source, not the primary. 1 m/s = 2.237 mph.

## Bottom line

1. **The sim's median is right, and its tail is not.** In NHL tracking, a player's 90th-percentile shot is 1.18-1.46x his average shot speed, and his 99th percentile is 1.31-1.70x. His hardest shot of the whole season is 1.38-1.80x (11 players, 288-598 attempts each) **[D from M]**. The sim's p90 / median is 77 / 42 = 1.8 and its max / median is 105 / 42 = 2.5. Both lie outside every player sampled. The sim's 105 mph equals the NHL's hardest game shot of a whole season: 102.6, 106.0 and 103.5 mph in the last three seasons **[M]**.
2. **For an adult rec player with a 42 mph median: p90 about 50-57 mph, p99 about 58-65 mph, ceiling about 70 mph standing and 75 mph skating** **[D]**. (Retagged in fact-check: the p90 range and the ceilings are arithmetic, but the p99 range is **[E]**. The NHL ratios give 1.31-1.70 × 42 = 55-71 mph, median 1.49 × 42 = 63 mph, and 58-65 is a judgement inside that.) Measured adult male recreational shots: wrist 16.0 ± 2.5 m/s (36 mph) and slap 23.3 ± 3.9 m/s (52 mph) by radar in a lab **[M]**. Mean + 2 SD gives a strong rec player's hardest standing slap at about 31 m/s (70 mph) **[D]**.
3. **Skating adds about the skater's own extra speed, typically 2-3 m/s (4-7 mph).** On real ice, skating wrist shots were 1.9-2.1 m/s faster than standing ones, for 1.7-1.8 m/s more body speed at release (ratio 1.05-1.28) **[M, D]**. Players were moving at about 3 m/s at release, after a run-up of about 9 m with at least two strides **[M]**. (Corrected in fact-check: the first draft said players "slow to" 3 m/s. Nobody measured their approach speed, so whether they slowed down to shoot is unknown.) In the sim, a 4.5 m/s sprint should add at most about 4.5 m/s (10 mph), and only along the skating direction **[E]**.
4. **Group-mean blade speeds top out at about 29 m/s** (corrected in fact-check; the first draft said "no measured blade moves faster than about 30 m/s"). Peak blade speed is 20-25 m/s in wrist shots and 18-29 m/s at slap-shot impact **[M]**. The elite slap-shot mean is about 29 m/s, with a trial SD of up to 4.3 m/s (Lomond 2005, 1000 Hz video). So some single elite trials probably pass 30 m/s **[D]**, though no paper reports one. In a lab study of 25 university shooters, the toe reached 28 m/s at most at release **[M]**. A wrist shot leaves at 1.26-1.32x the heel speed (Michaud-Paquette) or the blade-marker speed (Robbins, who does not say which of his three blade markers he used). It leaves at only 0.91-0.98x the toe speed **[D from M]**. So the puck does not outrun the fastest part of the blade. Lab systems show tracking spikes too, and they filter them out or exclude the shot **[M]**. Single 40+ m/s ticks in the sim are tracking artefacts, not shots.
5. **In a wrist shot the puck rides the blade for 80-290 ms (mean 150-180 ms) and about 1.2 m (0.84-1.79 m)** **[M]**. The sim's 75 ms "rides" are therefore not too long for a sweep or wrist shot. The real difference is direction: the blade carries the puck toward the target, the face sets the elevation, and the follow-through rises after release **[E]**.
6. **Shots on net leave with no more than about 4-6 m/s of vertical speed.** That is what reaching the top corner takes from the slot or point, at 8-17°. In-close roof shots need 30-50° (6-8 m/s) **[D]**. Lower shots need less. (Retagged in fact-check: these figures come from my own flight model aimed at the top corner. They are upper bounds, not measured "typical" values.) Just 1.5% of NHL shot attempts miss over the net **[M]**. Saucer passes peak at 0.05-0.3 m (1-2.4 m/s vertical) **[V, D]**. The highest famous saucer peaked at 3 m (7.7 m/s) **[S, D]**. Only a deliberate lob reaches 8-14 m/s vertical: launched at 30-60° and only 12-20 m/s in total, it peaks at 3-10 m **[E]**. Puck heights in game flips have never been measured.
7. **Lifting is done with the face and the wrists, not by carrying the puck upward** **[E]** (retagged in fact-check). Players open the face by rolling the wrists while the puck runs from heel to toe, and a high follow-through gives a high shot **[V]**. A cupped (closed) face keeps the puck down **[V]**. Measured (corrected in fact-check, because the first draft swapped top and bottom): the thesis's "roll" at release was about 22° for top-corner wrist shots and about 48° for bottom corners (25 shooters) **[M]**. That "roll" is the angle between the blade's heel-to-toe line and a global axis, not a wrist-roll or face-opening angle. Top-corner shots had more blade pitch at release (118-119° against 99-100°). They also changed pitch more during contact (57-58° against 35-39°) **[M]**. The thesis author calls this a "scoop": "moving the blade under the puck to permit application of a vertical force component". So real lifting does involve getting the blade under the puck during contact. What the measurements do not show is the puck riding a rising blade after release.
8. **In flight, a shot spins at 14-27 rev/s, flies tilted about 21° to its path, and loses 1.7-3.0 m/s over 7.5-15 m** **[M]**. That loss implies a drag rate of about 0.006-0.010 /m, which is 1.5-2.4x the sim's `air_k` of 0.0043 **[D]**. (Corrected in fact-check from "0.007-0.008, nearly twice". The thesis does not say over what distance the loss was taken: the targets were 7.5 m and 15 m away, but most shots were tracked only to 6 m and 10 m. About 0.25 m/s of the loss is the climb to the 0.76 m target, not drag. See section 5.)

## 1. Shot speeds by level and shot type

### How the measurement method moves the numbers

- **Radar reads wrist shots low.** At WSU, on ice, for 2 shooters (29 wrist and 56 slap shots), puck speed from high-speed video averaged 6.9 mph above radar for wrist shots (SD 6.7 mph, up to 21 mph). For slap shots it averaged 3.8 mph above (SD 6.1, up to 25 mph) **[M]**. The author saw that "for wrist shots especially, the radar gun seemed to pick up the speed of the blade rather than the puck" (Kays 2013, MS thesis, [WSU](https://hdl.handle.net/2376/102559)).
- **Motion capture reports a peak.** Robbins et al. took "peak values ... anywhere during the shooting task" from marker derivatives, after a 25 Hz low-pass filter **[M]** ([accepted manuscript, McGill](https://mcgill.scholaris.ca/items/0bd89c2e-f31a-4711-be9d-e8976e62d629)).
- **Lab protocols cap speed.** Wu (2002) had players shoot at a 0.6 × 0.6 m target 3 m away from a 3 m square of polyethylene. Michaud-Paquette (2008) used corner targets 4 m away **[M]**. Both trade speed for accuracy.
- **Best-of-N is not a game median.** Lab studies report maximum-effort trials. NHL game data cover every attempt, tips and quick releases included. So the NHL forwards' game average (53 mph) is lower than the pro lab wrist shot (66 mph) **[M]**.

### Adult recreational and university players (new this round)

| Study | Who | Setting, method | Wrist | Slap |
|---|---|---|---|---|
| Wu 2002, MA thesis ([McGill](https://mcgill.scholaris.ca/items/57e71f85-0e3c-4547-8c93-27c7453af77e)) | 10 men with "recreational experience in ice hockey" (the "unskilled" group; quote corrected in fact-check), age 25 ± 7 | lab polyethylene, radar, 3 shots × 3 sticks | **16.0 ± 2.5 m/s (36 mph)** [M] | **23.3 ± 3.9 m/s (52 mph)** [M] |
| same | 10 men, university or college players, age 23 ± 2 | same | 19.7 ± 2.8 m/s (44 mph) [M] | 30.0 ± 2.6 m/s (67 mph) [M] |
| same | 10 women, recreational / 10 women, university | same | 9.0 ± 1.0 / 13.6 ± 1.5 m/s [M] | 13.3 ± 2.0 / 18.8 ± 2.6 m/s [M] |
| Robbins et al. 2021 ([J Sports Sci 39:1001](https://doi.org/10.1080/02640414.2020.1853336); [manuscript](https://mcgill.scholaris.ca/items/0bd89c2e-f31a-4711-be9d-e8976e62d629)) | 10 men "recreational" (any level below major junior or Canadian university), age 26 ± 5 | **real ice**, 9 m to the net, Vicon 240 Hz | standing **26.4 ± 3.0 m/s (59 mph)**; skating 28.3 ± 2.9 (63 mph) [M] | — |
| same | 10 men elite (major junior or Canadian university) | same | standing 29.2 ± 1.4 (65 mph); skating 31.4 ± 0.8 (70 mph) [M] | — |
| Kays 2013 ([WSU thesis](https://hdl.handle.net/2376/102559)) | 6 shooters (WSU; level not stated in what I read) | real and synthetic ice, radar | per-shooter averages 42.1-54.4 mph (18.8-24.3 m/s) [M] | per-shooter averages 45.4-62.5 mph (20.3-27.9 m/s) [M] |
| Michaud-Paquette 2008 ([McGill MSc](https://mcgill.scholaris.ca/items/d0f8ff7a-b20d-4f9e-bd4d-63f0e46934b8)) | 25 university men, varsity to recreational | lab, standing, corner targets 4 m away, Vicon | mean 65.6-67.3 km/h (18.2-18.7 m/s, 41-42 mph); range 40-93 km/h (11-26 m/s) [M] | — |
| Manning 2020 ([McGill MSc](https://mcgill.scholaris.ca/items/b1aeee2a-3d9a-4144-b9b1-2d91b8fee7c2)) | 9 experienced men (high school to varsity), age 27 ± 3 | real ice, 2-3 strides, 18-camera Vicon | 29.0 ± 3.4 m/s (65 mph) [M] | 31.4 ± 3.4 m/s (70 mph) [M] |
| Lomas 2004 ([McGill MSc](https://mcgill.scholaris.ca/items/29e2e0e1-e17d-4a91-84b5-360d5e1b98e6)) | women, 16 varsity / 13 intramural, age 18-25 | real ice, 6.1 m, radar, mean of best 3 of 5 | standing 19.1 / 15.1 m/s; skating 21.9 / 16.7 m/s [M] | standing 22.9 / 17.5 m/s; skating 26.2 / 18.1 m/s [M] |

What I read from this:

- "Recreational" covers two very different groups **[E]**. One is the novice or adult-onset player (Wu's rec group, "unskilled" next to university players: 36 mph wrist, 52 mph slap). The other is anyone who has played below major junior or Canadian university level and still plays (Robbins: 59 mph wrist). (Corrected in fact-check: the first draft called Robbins's group "former competitive players". The paper only says they "played in any level lower than" major junior or university, and that they played in the current and previous season.) Jon's earlier sim median of 41-44 mph sits between them, on the novice side.
- Wu's lab wrist shots and Robbins's on-ice wrist shots differ by 10 m/s for "recreational" players. Three things add up to that gap: radar reading low on wrist shots (about 3 m/s per Kays), a 3 m accuracy target against a 9 m one, and the definition of the groups **[E]**.
- Spread within a group: Wu's coefficient of variation for the men was 9-17% **[M]** (corrected in fact-check from 14-17%). It was 15.4% for rec wrist, 16.9% for rec slap, 13.9% for university wrist and 8.6% for university slap shots. That spread mixes players with trials, so a single player's own spread is smaller.

### Snap shots, backhands, youth

- **Snap.** Elite U14 players (age 13.6) hit 16.7 m/s with a wrist shot, 19.7 with a long snap and 18.4 with a short snap **[M]** ([Novak et al. 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9465741)). That makes the snap 1.10-1.18x the wrist shot **[D]**: 70.8 / 60.0 = 1.18 and 66.4 / 60.0 = 1.11. Two pros in 1975 recorded wrist 24.6, snap 27.3 and slap 37.1 m/s **[S]**: Naud 1975, as tabled in Wu 2002, Appendix A.
- **Backhand.** I found one number only. Junior B players skating recorded 17.8 m/s on the backhand against 22.5 m/s for wrist shots, so the backhand was about 79% of the wrist shot **[S]** (Roy 1974, as tabled in Wu 2002). A retailer says backhands run 50-70 mph **[V]** ([HockeyMonkey](https://www.hockeymonkey.com/learn/types-of-hockey-shots)).
- **Youth.** 11 boys aged 9-11 recorded 38.2 ± 4.0 mph (17.1 m/s; range 30-44), best of 2, any shot type, with a Bushnell radar at 9.1 m **[M]** ([Frontiers 2024](https://www.frontiersin.org/articles/10.3389/fspor.2024.1418713/full)). Slap shots by age: 19.2 m/s at 11-12, 26.1 m/s at 15-16 and 26.7 m/s at 17+ **[S]** (Roy 1973, via Wu 2002). The 9-11 figure is as high as the elite U14 wrist shot, so treat it with caution.

### Pros and the NHL

- **In the lab:** pros and semi-pros recorded wrist 29.3 ± 2.8 and slap 34.8 ± 3.5 m/s, best of 5 by radar ([Bezák & Přidal 2017](https://gymnica.upol.cz/doi/10.5507/ag.2017.007.html)). Two DEL pros recorded slap 36.4 and one-timer 38.0 m/s ([Swarén et al. 2019](https://www.scitepress.org/publishedPapers/2019/83516/pdf/index.html)) **[M]**. Both studies are in the earlier note.
- **NHL EDGE puck tracking, 2025-26 regular season [M]:**
  - League averages are given by position. Forwards average 53.2 mph (23.8 m/s) per shot attempt, and their top shot averages 83.6 mph. Defensemen average 67.8 mph (30.3 m/s), with a top shot of 88.9 mph (39.7 m/s). Read from the leagueAvg fields of the [EDGE skater shot-speed API](https://api-web.nhle.com/v1/edge/skater-shot-speed-detail/8478402/20252026/2) (forward) and the [same API for a defenseman](https://api-web.nhle.com/v1/edge/skater-shot-speed-detail/8480069/20252026/2).
  - The hardest game shot of the season was 102.6 mph (2023-24), 106.0 mph (2024-25) and 103.5 mph (2025-26) ([EDGE top-10 API](https://api-web.nhle.com/v1/edge/skater-shot-speed-top-10/all/max/20252026/2)).
  - The average forward records 0.005 attempts over 100 mph per season, and the average defenseman 0.074.

## 2. Spread: the 90th and 99th percentiles

There are no published percentile tables of shot speed for any level. I derived them from NHL EDGE.

**Method [D].** For 11 skaters (9 forwards, 2 defensemen) in 2025-26, EDGE gives each player's average and top shot speed and his attempts in 70-80, 80-90, 90-100 and 100+ mph bins. The NHL stats API gives his total shot attempts ([realtime report](https://api.nhle.com/stats/rest/en/skater/realtime?limit=-1&cayenneExp=seasonId=20252026%20and%20gameTypeId=2)). From those I made exceedance counts at 70, 80 and 90 mph, plus 1 at the top shot. The 90th and 99th percentiles come from log-linear interpolation of those counts (script `calc/edge_players.py` in the session scratchpad).

| Player | Attempts | Avg (mph) | p90 | p99 | Season top | p90/avg | p99/avg | top/avg |
|---|---|---|---|---|---|---|---|---|
| F1 | 507 | 48.4 | 70.7 | 79.9 | 82.0 | 1.46 | 1.65 | 1.70 |
| F2 | 402 | 53.3 | 76.2 | 84.6 | 88.3 | 1.43 | 1.59 | 1.66 |
| F3 | 370 | 55.5 | 74.2 | 83.0 | 86.3 | 1.34 | 1.49 | 1.55 |
| F4 | 533 | 62.5 | 80.7 | 88.1 | 92.1 | 1.29 | 1.41 | 1.47 |
| F5 | 562 | 58.8 | 81.4 | 90.8 | 93.1 | 1.38 | 1.54 | 1.58 |
| F6 | 542 | 61.8 | 86.4 | 93.8 | 97.3 | 1.40 | 1.52 | 1.57 |
| F7 | 288 | 49.8 | 72.0 | 84.7 | 89.6 | 1.45 | 1.70 | 1.80 |
| F8 | 598 | 58.6 | 80.1 | 85.7 | 91.0 | 1.37 | 1.46 | 1.55 |
| F9 | 372 | 55.1 | 72.2 | 80.3 | 86.3 | 1.31 | 1.46 | 1.57 |
| D1 | 476 | 68.0 | 81.2 | 90.7 | 95.0 | 1.19 | 1.33 | 1.40 |
| D2 | 546 | 70.9 | 83.5 | 93.2 | 98.2 | 1.18 | 1.31 | 1.38 |
| **Median** | | | | | | **1.37** | **1.49** | **1.57** |

- **[D]** The league averages give the same top/avg ratio: forwards 83.6 / 53.2 = 1.57, defensemen 88.9 / 67.8 = 1.31.
- **[D]** The tail falls fast. Defensemen average per player 48.1 attempts at 70-80 mph, 21.6 at 80-90, 4.3 at 90-100 and 0.07 over 100. Each 10 mph step cuts the count by 2.2x, then 5x, then 58x. That is a hard ceiling, not a long tail.
- **Caveats.** "Avg" is a mean over all attempts, tips and deflections included, not a median. The bins and averages are EDGE's own, and the speed method is not published **[E]**.

**Applied to an adult rec player [D].**
- Ratio method: with a median of 42 mph (the sim's), the NHL median ratios give p90 = 1.37 × 42 ≈ 57 mph, p99 = 1.49 × 42 ≈ 63 mph, and a season's hardest shot = 1.57 × 42 ≈ 66 mph.
- Capability method: Wu's recreational slap, 23.3 ± 3.9 m/s, gives a strong rec player's hardest standing slap at 23.3 + 2 × 3.9 = 31.1 m/s (70 mph).
- With skating (section 3), add about 2-3 m/s, so about 75 mph.
- Taken together: **p90 50-57 mph, p99 58-65 mph, about 70 mph standing and 75 mph skating as a hard ceiling**. (Fact-check: p90 50-57 is 1.18-1.37 × 42. The p99 range is a judgement **[E]** inside the 55-71 mph that the ratios allow.)
- **[E] Denominator caveat (added in fact-check).** The percentiles assume that EDGE's speed bins count the same attempts as the stats API's total, which includes 26.7% blocked attempts. If EDGE leaves blocked shots out, the true p90 is about 1 mph higher (F1: 71.9 instead of 70.7 mph). The ratios barely move.
- The sim's tail (p90 77, max 105 mph, the max with a 4.5 m/s sprint) sits at elite-slap and NHL-record level.

## 3. What skating adds

| Source | Stationary → skating | Body speed |
|---|---|---|
| Robbins et al. 2021, wrist, real ice [M] | rec 26.4 → 28.3 m/s (+1.9); elite 29.2 → 31.4 (+2.1). Blade +2.0 in both groups | at release: 2.78 ± 0.36 (elite) and 3.07 ± 0.60 m/s (rec) skating; 1.12 and 1.23 m/s "stationary" (the pelvis still moves) |
| Lomas 2004, women, regular puck [M] | varsity wrist +2.8, slap +3.3 m/s; rec wrist +1.6, slap +0.6 m/s (the text gives +9.5 and +12.5 km/h for varsity, averaged over both pucks) | not measured; players chose the approach speed for a "maximum velocity" shot |
| Doré & Roy 1975, slap, 9 players [M] | 26.9 → 29.0 m/s (+2.1) | not stated |
| Cotton 1966, adults [S] | slap +2.8, wrist +2.5 m/s | — |
| Alexander 1963, 30 players [S] | slap +4.5, wrist +6.0 m/s (old method: an "impact" device) | — |

(The last two rows are tabled in Wu 2002, Appendix A.)

- **[D]** Robbins's ratio of puck gain to extra body speed is 2.13 / (2.78 − 1.12) = 1.28 (elite) and 1.93 / (3.07 − 1.23) = 1.05 (rec). Skating adds about its own speed, and a bit more for skilled players, who also rotate the trunk more when skating.
- **[M]** Robbins's players had "approximately 9 m to skate and release the shot, allowing them at least two full skating strides". They were moving at about 3 m/s at release. (Corrected in fact-check: the first draft read this as "skaters slow down to shoot". The approach speed was not measured, and a two-stride run-up may simply not reach more than 3 m/s.)
- **[M]** For scale, the league-average top skating speed shown on a defenseman's EDGE page for 2025-26 is 21.6 mph (9.7 m/s). EDGE's averages appear to be by position ([EDGE skater detail API](https://api-web.nhle.com/v1/edge/skater-detail/8480069/20252026/2)).
- **[E] Physics.** The puck's ice-frame speed is the body's speed plus the shot's speed relative to the body. So skating can add at most the component of skating velocity along the shot. A sideways sprint adds nothing to a shot aimed ahead. Real players do not add their full top speed, because the shot needs a planted skate (Robbins logged which skate stayed on the ice).

## 4. Blade speed, puck-to-blade ratio, contact time

### Blade speeds [M]

| Shot | Blade speed | Source |
|---|---|---|
| Slap, standing, lab | 29.14 m/s elite and 26.46 m/s rec at impact. Of that, 16.0 / 17.4 m/s came from stick rotation and 13.1 / 9.1 m/s from translation (the hands and body) | [Woo et al. 2004, ISBS](https://ojs.ub.uni-konstanz.de/cpa/article/view/1368) (5 + 5 players, polyethylene, electromagnetic tracking at only 60 Hz, which may clip peaks) |
| Slap, mid-blade marker (added in fact-check) | forward component 17.7 (elite) / 18.3 (rec) m/s at puck contact. At stick-off, 27.5 ± 4.3 / 15.1 ± 6.3 m/s, about 29 m/s resultant for elite **[D]** | [Lomond 2005, McGill MSc](https://mcgill.scholaris.ca/items/04d8dd90-f525-493d-9689-f4848abcb01f), Table 11 (8 elite, 7 rec, stationary, polyethylene, 1000 Hz video) |
| Slap, blade at the impact point | 23.9 m/s at ice contact, 22.5 just before the puck, 11.4 just after puck contact (the puck takes the momentum), 19.4 at the end | Kays 2013 (6 shooters). Blade speed before impact did not predict puck speed; speed after impact did |
| Wrist, peak blade marker (on ice) | rec 20.2 standing / 22.2 skating; elite 22.9 / 24.9 m/s | Robbins et al. 2021 |
| Wrist, toe and heel at release (lab) | toe 67.6-72.6 km/h (18.8-20.2 m/s), max 100.9 km/h (28.0 m/s); heel 50.1-52.5 km/h (13.9-14.6 m/s) | Michaud-Paquette 2008, Table 4.3 |
| Wrist, blade at impact point at the end | 46.7 ± 2.0 mph (20.9 m/s) | Kays 2013 |

- **[D] Puck against blade, wrist shots.** Robbins: puck / blade = 26.38 / 20.17 = 1.31, 28.31 / 22.20 = 1.28, 29.22 / 22.89 = 1.28 and 31.35 / 24.87 = 1.26. Michaud-Paquette, by target: puck / heel = 1.27-1.32 and puck / toe = 66.6 / 72.6 = 0.92, 0.91, 0.97 and 0.98. **The puck leaves at about the toe's speed, never well above it.** The extra over the heel comes from the blade rotating (the toe moves faster than the heel) and the puck rolling toward the toe. (Fact-check: Robbins tracked three blade markers and does not say which one gives "blade speed". His ratio also compares peaks that may come at different times, so "mid-blade" is my reading **[E]**.)
- **[M] Tracking spikes happen in labs too.** Manning dropped 5 of 360 shots because |v| changed by more than 4.5 m/s during the "initial flight phase" ("measurement errors"). That phase is a 54 ms window (13 frames at 240 Hz) starting 20 ms after peak puck speed. He set 4.5 m/s as the mean long-shot speed loss plus 3 SD. He dropped 23 more for wobble over 30° and 49 for missing markers. Robbins low-passed markers at 25 Hz. Kays's radar and video disagreed by up to 21-25 mph on single shots.
- **[E]** No study reports a group mean above about 29 m/s or a single trial above 28 m/s. Lomond's elite slap shots had a trial SD of 4.3 m/s, though, so some elite trials very likely passed 30 m/s. Nobody has measured the blade on an NHL 100 mph slap shot. (Corrected in fact-check from "no study reports a blade faster than 30 m/s".) A 40+ m/s blade speed for one physics tick is still far outside the range of a recreational player. A shot speed called from such a tick says nothing about the shot.

### Contact time and distance [M]

- Wrist shot, lab, 25 shooters, by target: mean contact 180 / 180 / 170 / 150 ms, range 80-290 ms. The puck travelled 1.16-1.25 m with the blade (range 0.84-1.79 m) (Michaud-Paquette 2008). The author contrasts this "~180 ms" with a golf club's "~10 ms" and notes that blade orientation changes throughout contact.
- Slap shot: 27 ± 5 (rec) and 38 ± 9 ms (elite) (Villaseñor 2006); 20 ± 2 ms slap and 15 ± 2 ms one-timer in pros (Swarén 2019). Both are in the earlier notes.
- High-calibre players spent 20% more of the time from first puck contact to release keeping contact **[S]** (Hannon et al. 2011, as summarised in Kays 2013).
- **[E] For the sim.** A 75 ms ride is a short wrist shot, not an anomaly. The anomaly is a puck that rides a blade accelerating upward. In real wrist shots the blade path is mostly horizontal toward the target, and the face angle sets a modest elevation (section 5).

## 5. Elevation and height

### Shots [D]

These are point-mass flights with quadratic drag k = 0.006 /m and no lift, from a puck centre 1.3 cm above the ice (script `calc/trajectories.py`). The puck's real lift (it flies tilted about 21°) would lower these angles slightly.

| Case | Speed | Launch angle | Vertical speed at launch |
|---|---|---|---|
| Lab top corner, 4 m, 1.0 m high (Michaud-Paquette set-up) | 18.5 m/s | 17° | 5.5 m/s |
| Target 0.76 m high at 7.5 m and at 15 m (Manning set-up) | 29 m/s | 8° | 4.2 m/s |
| Slot (9 m) to top corner (1.05 m) | 18 / 26 m/s | 15° / 10° | 4.6 / 4.7 m/s |
| Point (18 m) to top corner | 25 / 34 m/s | 12° / 8° | 5.3 / 4.8 m/s |
| Roof from 2 m, to 1.1 m | 12 m/s | 33° | 6.5 m/s |
| Roof from 1 m, to 1.1 m | 10 m/s | 50° | 7.7 m/s |
| Top of 3.66 m end glass from 12 m / 20 m | 25 m/s | 23° / 21° | 9.7 / 8.8 m/s |

- **[M]** In the NHL in 2025-26, 2,354 of 152,892 skater shot attempts (1.54%) missed over the net, and 691 (0.45%) hit the crossbar. By comparison, 20.9% went wide and 26.7% were blocked (NHL stats API, realtime report, summed over all skaters).
- **[M]** In 11 skaters' own seasons, over-the-net misses were 0.3-1.9% of attempts. Pros control elevation tightly.
- **[M]** Pucks do leave the rink high. One NHL venue's on-site medical service saw 51 spectators struck by pucks over six seasons (2013-2018). Strikes that nobody reported for care are not counted (fact-check). They happened mostly along the sides where the glass is lower and there is no netting ([Milsten & Ness 2022](https://pubmed.ncbi.nlm.nih.gov/35435157/)). That is about one every five home games **[D]**: 51 / (6 × 41).
- **[S]** A puck-flight simulation built on take-off conditions measured from top-level players looked at glass height. Raising the barrier from a 117 cm board with no glass to 380 cm cut "potentially dangerous" shots by 80%. Their fastest speed fell from 28.4 to 25.2 m/s, and only a 10.8 m wall stopped all of them ([Böhm, Schwiewagner & Senner 2007](https://doi.org/10.1007/BF02844205), abstract via [BISp](https://www.bisp-surf.de/Record/PU201103001702) and Michaud-Paquette 2008). Three players shot 108 lab shots, and the angles simulated were a modelling choice. I could not get the measured angle distribution, as the paper is paywalled.

### Passes and flips

- **Saucer pass.** Near the net it "usually rises a maximum of 30 centimeters", and long passes "can easily rise over 3 meters" **[V]** ([Wikipedia](https://en.wikipedia.org/wiki/Saucer_pass), tagged as needing citations). 0.3 m needs 2.4 m/s vertical **[D]**: √(2 × 9.81 × 0.3).
  - A widely shown NHL saucer pass travelled 116.3 ft (35.4 m) with a 10 ft (3.05 m) peak, per the broadcast **[S]**. Physicist Alain Haché put its launch at about 20°, against 0-5° for a typical pass **[E by Haché]** ([The Hockey News](https://thehockeynews.com/news/article/the-science-behind-erik-karlssons-jaw-dropping-game-3-saucer-pass)). That peak needs 7.7 m/s vertical **[D]**. My drag model gets 30 m of range with a 2.9 m peak from 22.6 m/s at 20°, close to the broadcast numbers **[D]**.
- **Flip or clearing lob.** I found no measured height **[gap]**. Flights from my model **[E]**:

| Launch | Vertical speed | Peak | Range |
|---|---|---|---|
| 12 m/s at 45° | 8.5 m/s | 3.6 m | 14 m |
| 15 m/s at 45° | 10.6 m/s | 5.4 m | 21 m |
| 18 m/s at 45° / 60° | 12.7 / 15.6 m/s | 7.7 / 11.4 m | 29 / 25 m |
| 20 m/s at 45° | 14.1 m/s | 9.3 m | 34 m |

So the sim's launches (8-14 m/s vertical, rising 3-10 m) match a deliberate high flip clearing the zone. That is a real play, but it is slow overall and launched at 30-60°, with a visible scooping motion **[E]**.

- **[E] Other sources of high vertical speed in real play.** A hard shot or pass deflecting off an angled stick or body keeps the incoming energy and can go almost straight up. Deliberate juggling pops are slow (well under 3 m/s). Neither is the shooter's own blade carrying the puck upward on the follow-through. No measurements exist for either.

### Puck flight [M]

Manning 2020: 182 wrist and 101 slap shots on ice.

- **Spin:** wrist 21.6 ± 4.1 rev/s, slap 26.8 ± 4.6 rev/s.
- **Tilt:** the angle of attack (the puck's tilt to its path) was 21.5 ± 7.7° for wrist shots and 20.2 ± 6.0° for slap shots; 95% fell between 6 and 35°.
- **Speed loss:** 1.74 ± 0.42 m/s from release to a target 7.5 m away and 2.96 ± 0.50 m/s to one 15 m away. These figures pool wrist and slap shots (mean release speed 29.9 m/s). The thesis does not say how the speed at the target was obtained. Its measured positions were taken at 6 m and 10 m, "the maximum distances at which most shots had visible data" (fact-check).
- **Wobble:** 23 of 360 shots wobbled by more than 30°.
- Michaud-Paquette's lab wrist shots spun 13.6-17.0 rev/s (4,885-6,131 °/s). Top-corner shots spun more (about 17 rev/s) than bottom-corner ones (about 14 rev/s). (Corrected in fact-check: the first draft swapped them. Table 4.3 gives 6,131 and 6,121 °/s for the top corners against 5,140 and 4,885 °/s for the bottom.)
- **[D] Drag** (corrected in fact-check). With v = v0·e^(−kx) and the pooled release speed of 29.9 m/s: ln(29.9 / 28.16) / 7.5 = 0.0080 /m and ln(29.9 / 26.94) / 15 = 0.0069 /m. If the losses were measured over the 6 m and 10 m where the puck was tracked, k = 0.0100 and 0.0104 /m. Climbing to the 0.76 m target costs about 9.81 × 0.75 / 29.9 = 0.25 m/s. Without it, k = 0.0068 and 0.0063 /m. **So k is about 0.006-0.010 /m, 1.5-2.4x the sim's `air_k` of 0.0043.** The direction holds (more drag than the sim), but the size is not pinned down. The pucks also carried marker pins, which Böhm found change the drag coefficients by less than 10%.

## 6. How players lift the puck, and the follow-through

**Measured.**

- **[M]** In wrist shots at four corners 4 m away, roll at release averaged about 22° for the **top** corners and about 48° for the **bottom** corners. The values are 22.07 and 21.81° (TC, TI) against 47.95 and 47.45° (BC, BI). (Corrected in fact-check: the first draft swapped top and bottom. The thesis confirms TC/TI are the top corners, e.g. "puck velocity at release was from 47 to 86 km/h for the top corners", which matches the TC column.) The thesis defines roll as "the angle between the global Y-axis and j", where j runs from the heel marker to the toe marker. So it is the direction of the blade's long axis, not rotation about it. It does not measure face opening directly (Michaud-Paquette 2008, sections 3.6.1 and Table 4.3).
- **[M]** Pitch at release was 117.9 and 119.0° for the top corners against 99.5 and 99.9° for the bottom. Pitch changed during contact by 58.2 and 57.0° (top) against 38.6 and 35.2° (bottom). The author reads this as a "scoop" for top targets: "moving the blade under the puck to permit application of a vertical force component to the puck", followed by a "flick" at the end of contact (added in fact-check).
- **[M]** Release roll, together with changes in blade angle, puck speed, heel speed and shaft bend, predicted top-corner accuracy (R² 0.76). Bottom-corner models explained only 0.36-0.40. Shooters hit the top corners less often (45% against 67%).
- **[M]** The thesis's "puck to blade position" at release was 22-23 cm for top corners against 18.5-18.7 cm for bottom corners. Contact lasted 180 ms for top corners against 150-170 ms for bottom corners. (Both corrected in fact-check, because the first draft swapped top and bottom.)
- **[M]** The stick's angle to the ice ("attacking angle") was 53° in wrist shots and 55° in slap shots (Wu 2002).
- **[M]** Wrist shots bent the shaft 10.8° (32 mm) in Wu's lab and 3-4° in Michaud-Paquette's. The two studies measured bend differently.
- **[M]** The hands were 0.34 m apart in wrist shots against 0.60 m in slap shots (Wu 2002).

**Coaching [V]:**

- **Lifting a wrist shot.** "Roll your wrists to open the blade, this will allow the puck to lift off the ice." "Push down with your top hand, and pull up with your bottom hand to add some power" ([How To Hockey](https://howtohockey.com/how-to-raise-the-puck-and-improve-your-accuracy/)). Start "cupping the puck" with the top hand rolled down, roll the wrist up to lift, then re-cup on the follow-through to keep the puck under the crossbar. For close-range lifts, "flip that top hand upward with a really quick snap of the wrist" ([HockeyShot](https://hockeyshot.com/blogs/training-academy/how-to-lift-the-puck)).
- **Follow-through.** Point the toe at the target. A low follow-through with the blade toward the ice gives a low shot, and a high follow-through a high shot (several coaching pages, seen in search summaries; e.g. [How To Hockey, wrist shot](https://howtohockey.com/?p=67)).
- **Saucer pass.** Open the face, start the puck near the heel and sweep it to the toe while rolling the wrist. The spin keeps it flat ("the more spin the flatter the pass"), and a flick at release lifts it. Use a sweep, not a slap ([Sniper's Edge](https://www.snipersedgehockey.com/blogs/the-inside-post/how-to-saucer-pass-in-ice-hockey); [OMHA](https://www.omha.net/news_article/show/1142056); seen in search summaries).
- **Toe drag shot.** It moves the puck 2-4 in sideways or toward the body before a snap, to change the angle past a stick. It uses minimal backswing ("drag + snap") and continuous stick contact ([CoachThem](https://coachthem.com/blog/5-shooting-techniques-for-high-pressure-situations); [HockeyShare](https://www.hockeyshare.com/drill/11147); search summaries).

**[E] Physics of lift.** A puck pushed by a vertical face gets no upward impulse. Opening the face by an angle φ tilts the contact normal up by φ, and the puck can then ride up the face against friction. So the launch angle comes mostly from the face angle at release plus the blade's own upward velocity. Bottom corners need about 6° of launch at 4 m and top corners about 17°. (Corrected in fact-check: the first draft cited "26° extra roll" for top corners as support. Top corners in fact had 26° *less* of the thesis's roll, and that roll is not a face angle. The measured support is the larger pitch and pitch change for top corners, the "scoop" above. No study gives the face angle against the launch angle directly.)

**[M] Slap-shot loft (added in fact-check).** Lomond 2005 (Table 14) measured blade "loft": the angle between a segment across the blade's width and the ice plane, which grows as the blade opens. At puck contact it was 76 ± 6° (elite) and 83 ± 10° (rec). By stick-off it had opened to 108 ± 10° and 110 ± 11°. Elite shooters used a wider loft range (13° against 6°). The author links this to the wrist snap. My reading is that 90° is a vertical face, so the face is a little closed at contact and opens as the puck rolls to the toe **[E]**. A cupped face tilts the normal down and presses the puck into the ice. That fits the earlier note's point that closing the face traps bouncing pucks.

## What this means for the sim

| Check | Real-world bound | Sim now (measured in Jon's replays) |
|---|---|---|
| Median called shot speed, adult rec | 36-59 mph depending on background; novice-side rec 36-52 mph | 41-44 mph: **plausible** |
| p90 / median | ≤ 1.45 (NHL players 1.18-1.46) | 77 / 42 = 1.8: **too fat** |
| p99 / median | ≤ 1.7 (NHL 1.31-1.70) | — |
| Max / median over a session or season | ≤ 1.8 (NHL 1.38-1.80) | 105 / 42 = 2.5: **too fat** |
| Absolute, adult rec | p90 ≈ 50-57 mph, p99 ≈ 58-65 mph, about 70 mph standing / 75 mph skating ceiling | p90 77, max 105 mph: **fail** |
| Skating gain | ≈ body speed component along the shot, typically +2-3 m/s; ≤ +4.5 m/s at the sim's sprint | max 105 mph in the sprint session: check that the skating gain stays within that |
| Blade speed (any point) | wrist peak 20-25 m/s, toe ≤ 28 m/s at release, slap impact 18-29 m/s. Group means ≤ 29 m/s; single elite slap trials probably reach a little over 30 m/s (corrected in fact-check) | single ticks 40+ m/s: **artefact** |
| Hand (stick translation) speed | about 9-13 m/s in slap shots. This is Woo's translational part of the blade speed, not a measured hand speed (retagged in fact-check) **[D]** | — |
| Puck exit / blade speed | ≈ 0.9-1.0 × toe speed; ≈ 1.3 × mid-blade or heel (wrist); about 1.0 × blade before impact (slap) | 0.98 on slow taps: **matches** |
| Wrist-shot contact | 80-290 ms, puck travels 0.8-1.8 m with the blade | 75 ms rides: **within range**, so contact time alone cannot flag a scoop |
| Vertical speed, shots | ≤ 4-6 m/s to reach the top corner (an upper bound from my model, not a measured typical value; retagged in fact-check); ≤ 8 m/s in-close roofs; 9-10 m/s only for wild shots over the glass (NHL: 1.5% over the net) | 8-14 m/s scoops: **too frequent if not deliberate** |
| Vertical speed, saucer | 1-2.4 m/s short; ≤ 8 m/s for a 3 m-high long saucer | — |
| Vertical speed, deliberate lob | 6-14 m/s at 30-60° and 12-20 m/s total (no measurement) | the only real play the scoops resemble |
| Launch angle | shots 5-20°, roofs ≤ 50°, lobs 30-60°; near-vertical only for slow juggles (< 3 m/s) or deflections | — |
| Peak height | shots ≤ 2 m on net, about 2-4 m when over the glass; saucer 0.05-3 m; lob 2-10 m | 3-10 m: **lob-height** |
| In-flight drag | k ≈ 0.006-0.010 /m for a tilted, spinning shot (corrected in fact-check from 0.007-0.008; the distance basis is not stated in the source) | `air_k` 0.0043 /m: 0.4-0.7 of that (higher drag would shave pop-up heights) |

Concrete suggestions **[E]**:

1. **Call shot speed the way labs and radar do:** from the puck's flight over the first 0.1-0.3 m or 10-20 ms after release, not from one tick. Discard a call when the puck's speed varies by more than about 4.5 m/s within the first ~50 ms of free flight. (Corrected in fact-check: Manning's rule applies to |v| over his 54 ms initial-flight window, starting 20 ms after peak speed, not to neighbouring samples. A per-sample jump test would need a much smaller threshold.)
2. **Use the shape tests as regression checks for any replay batch.** Require p90 / median ≤ 1.45 and max / median ≤ 1.8. These hold for every NHL player sampled whatever his skill, so they test the physics and tracking rather than Jon's strength.
3. **Treat any blade-point speed above about 30-35 m/s as a tracking fault.** For a recreational player, also flag any puck exit above about 1.1 × the toe's speed over the contact window.
4. **A launch with more than 8 m/s of vertical speed should need a visible flip.** That means an open face and the hands rising while the blade is under the puck. It should never come from the follow-through after the puck has gone forward. In a session of rec shooting such launches should be rare, a few per hour at most if Jon is not deliberately flipping **[E]**.

## Gaps

- **No shot-speed distribution has been measured for adult recreational players**, in games or in practice. There are only lab means and SDs (Wu, n = 10), per-shooter averages (Kays, n = 6) and anecdotes. My p90/p99 come from NHL distribution shapes.
- **Wrist-shot speed of "recreational" players is uncertain by about 10 m/s** across methods: radar against motion capture, a 3 m target against 9 m, and novice against former competitive players. The only same-shot comparison I found is Kays's, of radar against high-speed video, for two shooters (corrected in fact-check: it was video, not motion capture).
- **No measured distribution of launch elevation exists** for game shots, passes or flips. NHL puck tracking has heights, but nothing published gives them. The Böhm et al. (2007) take-off data are paywalled.
- **No measured heights for clearing flips or lobs.** My 2-10 m peaks are physics.
- **Backhand speed:** one 1974 junior figure (via a thesis table). **Snap shot:** elite U14 players and two pros from 1975.
- **Follow-through kinematics** (blade height and speed after release, and its link to shot height) are described only by coaching.
- **Blade loft in slap shots** was measured by Lomond (2005, [McGill](https://mcgill.scholaris.ca/items/04d8dd90-f525-493d-9689-f4848abcb01f)). The full text does contain the results (corrected in fact-check; see section 6). Loft against launch angle is still unmeasured, and so is loft in wrist shots.
- **Blade speed in NHL-level slap shots** (puck 45+ m/s) was not found. Elite university slap shots average about 29 m/s at the blade with SDs up to 4 m/s, so single trials above 30 m/s are likely but unreported.
- **Deflection pop-ups** (shots or passes glancing up off sticks) have no measurement, though they are the real-world source of steep, fast pucks.

## Sources read in full this round

McGill repository full texts: Robbins et al. 2021 (accepted manuscript), Wu 2002, Michaud-Paquette 2008, Manning 2020, Lomas 2004, and Lomond 2005 (results added in fact-check). Also the WSU Kays 2013 thesis PDF, Woo et al. 2004 (ISBS PDF), and the NHL EDGE and NHL stats APIs (2023-24 to 2025-26). The rest are abstracts, coaching pages or secondary tables, tagged as such above. The scratch scripts are in this session's scratchpad: `calc/edge_players.py` (percentiles) and `calc/trajectories.py` (flight arithmetic).

## Fact-check (2026-11-10)

I checked the 20 claims below, chosen because the sim could be tuned to them. For each one I opened the source: the thesis or paper text (rendering the table page from the PDF where the text was garbled), the NHL APIs directly, or the abstract. I also re-ran both scratch scripts and got the same output. The inline fixes above are marked "corrected in fact-check" or "retagged in fact-check".

| # | Claim in the draft | Verdict | What the source actually says |
|---|---|---|---|
| 1 | Wu 2002: rec men wrist 16.0 ± 2.5 m/s, slap 23.3 ± 3.9 m/s (radar, lab) | confirmed (group wording fixed) | Table 6: unskilled men wrist 16.0 ± 2.5, slap 23.3 ± 3.9; skilled 19.7 ± 2.8 / 30.0 ± 2.6 m/s. Peak radar speed, 3 m square of polyethylene, 0.60 × 0.60 m target about 3 m away, 3 shots × 3 sticks. The rec group is ten men "with recreational experience in ice hockey", age 25.4 ± 7.3. The quoted phrase "recreational to no experience" is not in the thesis. |
| 2 | Wu: coefficient of variation 14-17% for the men | corrected | Table 6 CVs: rec wrist 15.4%, rec slap 16.9%, university wrist 13.9%, university slap 8.6%. So 9-17%. |
| 3 | Robbins 2021: rec wrist 26.4 ± 3.0 standing, 28.3 ± 2.9 skating; elite 29.2 / 31.4; blade 20.2-24.9 m/s | confirmed | Table 2: puck 26.38 ± 3.04, 28.31 ± 2.92, 29.22 ± 1.39, 31.35 ± 0.84; blade 20.17, 22.20, 22.89, 24.87 m/s. Real ice, release about 9 m from the net, 14-camera Vicon at 240 Hz, 25 Hz low-pass, 10 + 10 men age 26 ± 5. The blade marker used (one of three) is not named. |
| 4 | Robbins's rec players are "former competitive players who now play rec" | unsupported | "Recreational participants played in any level lower than" major junior or Canadian university, and all "actively played hockey during the current and previous season". The paper gives no playing history. |
| 5 | "Players slow to about 3 m/s at release" | corrected | Pelvis speed at release was 2.78 ± 0.36 (elite) and 3.07 ± 0.60 m/s (rec), and 1.12 / 1.23 m/s "stationary". The run-up was "approximately 9 m ... at least two full skating strides". Approach speed was not measured, so "slow to" has no support. |
| 6 | Skating adds +1.9 / +2.1 m/s (ratio 1.05-1.28); Doré & Roy +2.1 m/s | confirmed | The arithmetic from Robbins's Table 2 checks out. Doré & Roy 1975, Table 2: slap 26.9 ± 1.5 → 29.0 ± 1.4 m/s, "nine skillful adult amateur" players in an arena. Their speed is timed from blade impact to target, so it is a flight average. |
| 7 | NHL EDGE: hardest game shot 102.6 / 106.0 / 103.5 mph (2023-24 to 2025-26); league averages 53.2 / 83.6 mph (F), 67.8 / 88.9 mph (D); 0.005 / 0.074 attempts over 100 mph | confirmed | Re-fetched: 102.59, 106.00 and 103.51 mph (regular season). leagueAvg fields 53.19, 83.62, 67.85 and 88.92 mph, and 0.0049 and 0.0741. |
| 8 | Per-player p90/avg 1.18-1.46, p99/avg 1.31-1.70, top/avg 1.38-1.80 | confirmed | `edge_players.py` reproduces the table. I re-fetched the inputs for F1 and D2 from EDGE and the stats API, and they match. Added caveat: if EDGE's bins leave out blocked attempts, p90 rises by about 1 mph. |
| 9 | Rec bounds: p90 50-57, p99 58-65, ceiling about 70 mph standing / 75 mph skating | corrected (p99 retagged [E]) | 1.18-1.37 × 42 = 50-57 mph. 23.3 + 2 × 3.9 = 31.1 m/s = 70 mph, plus 2-3 m/s = 74-76 mph. The NHL ratios give p99 = 55-71 mph. No arithmetic gives 58-65. |
| 10 | 1.5% of NHL shot attempts go over the net | confirmed | Stats API realtime report 2025-26, summed over 940 skaters: 2,354 / 152,892 = 1.54%. Crossbar 691 (0.45%), wide 20.88%, blocked 26.72%. |
| 11 | Wrist-shot contact 80-290 ms (means 150-180) over 0.84-1.79 m; toe 18.8-20.2 m/s (max 28.0), heel 13.9-14.6 m/s; puck/toe 0.91-0.98, puck/heel 1.27-1.32 | confirmed (values are at release) | Michaud-Paquette 2008, Table 4.3 (25 men, varsity to rec, standing, silicone-sprayed polyethylene, 4 m, Vicon 240 Hz): contact 180/180/170/150 ms, range 80-290; distance 123.1/116.9/124.7/115.9 cm, range 83.8-179.4. Toe 72.6/72.05/69.55/67.57 km/h, max 100.9; heel 52.5/51.04/51.53/50.09; puck 66.6/65.6/67.28/65.93 km/h. Speeds are frame differences at release. |
| 12 | Roll at release about 48° for top corners and 22° for bottom; puck-to-blade 18.5-18.7 cm top / 22-23 bottom; contact 150-170 ms top / 180 bottom; spin about 14 rev/s top / 17 bottom | corrected (all four had top and bottom swapped) | Table 4.3 columns are TC, TI (top) then BC, BI (bottom). Roll 22.07, 21.81 / 47.95, 47.45°. Puck-to-blade 22.0, 23.0 / 18.5, 18.7 cm. Contact 180, 180 / 170, 150 ms. Spin 6,131, 6,121 / 5,140, 4,885 °/s. The text confirms T = top: "47 to 86 km/h for the top corners" matches the TC range. Roll is "the angle between the global Y-axis and j" (the heel-to-toe line), not face opening. I re-rendered page 71 from the PDF myself. |
| 13 | "Lifting is done with the face and the wrists, not by carrying the puck upward" (stated as if measured) | unsupported (retagged [E]) | The same thesis says top targets require the shooter to "scoop" under the puck, "moving the blade under the puck to permit application of a vertical force component", with a larger pitch change during contact (57-58° against 35-39°). Nothing in it measures the follow-through after release. |
| 14 | "No measured blade moves faster than about 30 m/s" | corrected | Woo 2004: blade at impact 29.14 ± 1.39 (elite) and 26.46 ± 0.66 m/s (rec), 5 + 5 players, polyethylene, electromagnetic tracker at 60 Hz. Lomond 2005, Table 11 (1000 Hz video, 8 elite + 7 rec): mid-blade forward velocity at stick-off 27.51 ± 4.31 m/s for elite, 9.7 m/s sideways, about 29.2 m/s resultant. Means stay at or below 29 m/s, but with a 4.3 m/s SD some elite trials very likely passed 30. The highest single value reported anywhere I read is 28.0 m/s (toe, wrist). |
| 15 | Kays 2013: video read 6.9 mph above radar for wrist shots (SD 6.7, up to 21) and 3.8 mph for slap (SD 6.1, up to 25); slap blade 23.9 / 22.5 / 11.4 / 19.4 m/s; wrist 46.7 mph | confirmed | Same numbers in the thesis. The comparison covers 2 shooters only (29 wrist, 56 slap shots). The slap blade speeds are 53.5, 50.4, 25.5 and 43.3 mph. The wrist "final stick speed", 46.7 ± 2.0 mph, carries a camera-trigger timing caveat. |
| 16 | Manning 2020: wrist 29.0 ± 3.4, slap 31.4 ± 3.4 m/s; spin 21.6 / 26.8 rev/s; angle of attack 21.5 / 20.2° (95% within 6-35°); speed loss 1.74 / 2.96 m/s; 5 of 360 shots excluded as errors | confirmed | Table 2 and sections 4.4.4 and 5.1. Nine men age 26.6 ± 3.2, highest level high school to varsity, real ice, 18-camera Vicon at 240 Hz, 50 Hz Butterworth filter. The speed losses pool all 283 wrist and slap shots (mean 29.9 m/s). |
| 17 | Drag k ≈ 0.007-0.008 /m, "nearly twice" `air_k` | corrected to 0.006-0.010 /m (1.5-2.4x) | The thesis does not say over what distance the loss was taken. The targets were 7.5 and 15 m away, but positions were measured at ≥ 6 m and ≥ 10 m, "the maximum distances at which most shots had visible data". About 0.25 m/s of each loss is the climb to the 0.76 m target. Section 5 shows the arithmetic. |
| 18 | Suggestion: drop a call when speed "jumps by more than about 4.5 m/s between neighbouring samples (Manning's exclusion rule)" | corrected | Manning excluded shots whose speed magnitude "varied by more than 4.5 m/s during the initial flight phase". That phase is 54 ms (13 frames at 240 Hz) starting 20 ms after peak puck speed. The threshold is the long-shot mean loss + 3 SD. It is not a per-sample rule. |
| 19 | Saucer heights (≤ 30 cm close, > 3 m long); the famous saucer at 116.3 ft with a 10 ft peak, launched at about 20°; 51 spectators struck at one NHL venue | confirmed (as tagged [V] / [S]) | The Wikipedia sentences are verbatim, on a page with a "needs more citations" banner (June 2013). The Hockey News gives 116.3 ft and 10 ft "according to the Sportsnet broadcast", and quotes Haché: a typical pass is 0-5°, this one "around 20 degrees". The PubMed abstract gives 51 strikes among patients seen by on-site EMS, 2013-2018, at one US venue, mostly on the sides "where the glass level is lower and there is no protective netting". |
| 20 | Gap: Lomond's blade-loft results were cut off in the repository text | corrected | The full text has them. Table 14 gives loft at puck contact of 76 ± 6° (elite) and 83 ± 10° (rec), opening to 108 ± 10° and 110 ± 11° by stick-off. Elite loft range was 13° against 6°. Added to section 6. |

**Other spot checks, all confirmed.** Novak 2022, Table 2: long snap 70.8 ± 7.0, short snap 66.4 ± 6.3, wrist 60.0 ± 9.5 km/h (16 boys aged 13.6, radar, best of 3 from 7-10 m). Frontiers 2024: 38.2 ± 4.0 mph, range 30-44 (11 players aged 9-11, Bushnell radar at 9.1 m, best of 2, shot of their choice). Wu Appendix A rows for Naud 1975, Roy 1973 and 1974, Cotton 1966 and Alexander 1963. Böhm 2007 abstract (Springer): 117 → 380 cm cut dangerous shots by 80%, top speed 28.4 → 25.2 m/s, 10.8 m stops all shots. Wu's attacking angles of 53.0 / 54.9°, hand spacing of 0.337 / 0.602 m and wrist bend of 10.8° (0.032 m). EDGE league top skating speed of 21.59 mph. `air_k` = 0.0043 in `prototype/puck.py`.

**Retags I made without changing a number.** "Shots on net leave with only 4-6 m/s vertical" is now an upper bound for the top corner from my own model, not a typical value. Woo's 9-13 m/s "hand speed" is the stick's translational part of the blade speed. The "mid-blade" in the puck/blade ratio is my reading, because Robbins does not name his marker.

**What changes for the sim.**
- The acceptance bounds on shot speed and its spread stand. So does the 0.98 puck/blade match on slow taps.
- The drag target widens to 0.006-0.010 /m.
- A tracking-fault limit of 30-35 m/s for a rec player's blade is still reasonable. Just don't present it as "no human exceeds 30".
- Any filter modelled on Manning should test speed change over a ~50 ms free-flight window, not between neighbouring samples.
- The lift mechanism in the sources is a blade that gets under the puck and pitches during contact (a "scoop"), then a flick. So a sim launch with real lift during contact is not wrong in itself. The fault to target is a puck carried upward on the follow-through after release.
