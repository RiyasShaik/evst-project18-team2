# Final presentation · speaker guide

**Slot:** 30 minutes = 25 min presentation (hard stop) + 5 min questions. The deck has 19 slides planned for about **22 minutes**, leaving 3 minutes of buffer. Each slide's speaker notes contain the script and its time.

## Suggested split (change it if you prefer, but keep blocks contiguous)

| Slides | Topic | Speaker | Time |
|---|---|---|---|
| 1–4 | Title, question, pollen indicators, data | N Pavaneswar | 4.25 min |
| 5–8 | Methods, Europe-wide result, robustness, regions | Shaik Babu | 5.5 min |
| 9–13 | Climate, regression, Eastern Mediterranean, HYDE | Jetty Jithendra Sai Ram | 7.0 min |
| 14–19 | Dating uncertainty, answers, since mid-term, limitations, conclusion, sources | Dr Shashang | 5.0 min |

Rehearse once with a timer. If you are running late at slide 13, shorten slides 16 and 17 to one sentence each.

## Numbers everyone should know

- 1,099 Neotoma datasets → 12,508 samples, 1,064 records, 984 sites → **281 core sites** (≥2 samples before and after 541); 23 in the Eastern Mediterranean.
- After 541: all farming indicators **+0.28 percentage points (p < 0.001)**, natural trees **−0.70 (p = 0.004)**; cereal rose at 56% of sites, fell at 30%.
- Placebo (rates per century): +0.14 across 541 vs 0.00 before (p = 0.007).
- Regression: temperature −0.005 SD (p = 0.78); first plague century 550–650 −0.12 SD (p = 0.024), only in W. & Central Europe; gone with a quadratic trend.
- HYDE cropland falls at 85% of sites, cereal pollen at 30%.
- Monte Carlo: cereal and all farming stay significant in 98–100% of 1,000 runs; regional results outside W. & Central Europe do not.

## Likely questions

1. **Why does farming rise if the plague killed so many people?** Pollen records land use, not deaths. Mortality may have been concentrated in cities and along trade routes, where few pollen sites lie, or survivors took over vacant land quickly. Mordechai et al. (2019) reach the same conclusion from other evidence.
2. **Are your 281 sites independent?** Each lake or bog counts once: we removed 14 duplicate Neotoma records and pooled cores from the same lake (promised at mid-term). Some sites lie a few km apart; we list this as a limitation.
3. **Why not test each plague wave (541, 558, 573 …)?** The median age error is ±176 years, longer than the gaps between waves.
4. **Why does the first-60-years test (541–600) show nothing?** Only 79 sites have enough samples in that short window; it shows neither a rise nor a fall, which is consistent with "no abandonment".
5. **How do you know temperature does not matter?** In every regression over 300–900 CE the temperature term is near zero; the 4th century was as cold as the LALIA in the European mean but shows no shortfall. Caveat: the reconstruction is uncertain (±0.9 °C), which could hide a small effect.
6. **What happened to your mid-term Eastern Mediterranean result?** With 23 sites instead of 13 the arboriculture decline is −0.07 points, not significant, started around 425 CE and does not survive the dating test. We withdrew the mid-term "regional mark" conclusion.
7. **Why is Iran in the "Eastern Mediterranean"?** The region is defined by coordinates (south of 43°N, east of 19°E), as at mid-term; one core site (Lake Almalou) is in NW Iran. The region is heterogeneous and we say so.
8. **Why not archaeological data?** No open, harmonised settlement or plague-occurrence dataset covers the whole study area at the needed resolution.
9. **What is the placebo test?** The same comparison one step earlier (250–399 → 400–540). We compare rates per century because the window midpoints are 145.5 and 175.5 years apart.
10. **Why is HYDE wrong?** HYDE allocates cropland from historical population estimates, which have a Late Antique dip to 600 CE; the pollen shows no such dip. HYDE grazing land, which rises after 600, does agree with pastoral pollen.
11. **Can you show it is reproducible?** `./run.sh` regenerates every number, table and figure in about 2 minutes; the report is written from the tables by `code/report.py`.
