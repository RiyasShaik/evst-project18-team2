# Environmental Change before and after the First Pandemic

EVST course project 18 · Team2 · IIIT Hyderabad, Monsoon 2026

**Question:** Did vegetation, agriculture and land use change after the First (Justinianic) Pandemic (541–750 CE), and can that change be separated from the Late Antique Little Ice Age (536–660 CE)?

**Data:** fossil pollen from the [Neotoma Paleoecology Database](https://www.neotomadb.org/) (891 records queried, 164 core records from 159 sites, 7,517 samples) and the Central European tree-ring climate reconstruction of Büntgen et al. (2011, NOAA Paleoclimatology).

**Method:** site-level before/after comparison (400–540 vs 541–750 CE) of cereal, cultivated-tree, pastoral and natural-tree pollen and rarefied richness; paired Wilcoxon tests with bootstrap CIs; a placebo comparison (250–399 vs 400–540 CE); ±50-year boundary sensitivity tests; z-score regional composites compared with the climate record.

## Reproduce

Requires Python 3 with `pandas`, `numpy`, `scipy`, `matplotlib`.

```bash
./run.sh          # analysis from data/samples.csv (~1 min, offline) -> out/
./run.sh --full   # re-download the 891 Neotoma records (~470 MB) and rebuild samples.csv first
```

| Path | Contents |
|---|---|
| `code/dl.py` | Downloads each Neotoma record through API v2 |
| `code/process.py` | Picks calibrated ages, filters samples (0–1200 CE, ≥100 grains), classifies taxa, computes indicators and rarefied richness |
| `code/analyse.py` | Window means, Wilcoxon tests, bootstrap CIs, placebo and sensitivity tests, figures |
| `data/` | Processed samples, per-site window means, climate series, list of Neotoma dataset IDs |
| `figures/` | Fig. 1–6 (PNG, 200 dpi) |
| `tables/` | Result tables (pre vs post, placebo, sensitivity) and summary |

## Team

N Pavaneswar (2024102063) · Shaik Babu (2024101032) · Jetty Jitendra Sai Ram (2024101102) · Dr Sashangh (2024101069)
