# Environmental change before and after the First Pandemic

EVST course project 18 · Team 2 · IIIT Hyderabad · Monsoon 2026

**Question.** Did vegetation, agriculture and land use change after the First (Justinianic) Pandemic (541–750 CE), and can that change be separated from the Late Antique Little Ice Age (LALIA, 536–660 CE)?

**Answer in one line.** No: across 281 fossil-pollen sites, farming indicators rose and woodland fell after 541, with a modest pause in 550–650 CE that reconstructed temperature does not explain; the Eastern Mediterranean shows no significant post-541 decline, and the HYDE 3.2 land-use model's cropland moves opposite to the pollen.

| Deliverable | File |
|---|---|
| Final report | [`report/final_report.pdf`](report/final_report.pdf) (HTML: [`report/final_report.html`](report/final_report.html)) |
| Final presentation | [`presentation/Team2_Project18_Final_Presentation.pptx`](presentation/Team2_Project18_Final_Presentation.pptx) (PDF copy alongside; speaker notes and timing in the slides and in [`presentation/SPEAKER_GUIDE.md`](presentation/SPEAKER_GUIDE.md)) |
| Mid-term versions of the tables | [`tables/mideval/`](tables/mideval/) |

## Data

- **Fossil pollen**: [Neotoma Paleoecology Database](https://www.neotomadb.org/), 1,099 pollen datasets between 10°W–50°E and 30–56°N whose ages span 400–750 CE. After filtering (0–1200 CE, ≥100 grains, default calendar-scale chronology), removing 14 duplicate records and pooling cores from the same lake: 12,508 samples, 1,064 records, 984 sites; **281 core sites** with ≥2 samples both in 400–540 and 541–750 CE.
- **Climate** (NOAA Paleoclimatology): Alpine tree-ring summer temperature (Büntgen et al. 2011); PAGES 2k Euro-Med European summer temperature (Luterbacher et al. 2016); Kocain Cave, SW Turkey (Jacobson et al. 2021) and Soreq Cave, Israel (Orland et al. 2009) speleothem isotopes.
- **Land-use model**: HYDE 3.2.1 cropland, grazing land and population density (Klein Goldewijk et al. 2017, [doi:10.17026/dans-25g-gez3](https://doi.org/10.17026/dans-25g-gez3)) within 25/50/100 km of each site.

## Methods

Site-level before/after comparison (400–540 vs 541–750 CE) of cereal, pastoral, cultivated-tree (olive, walnut, chestnut, vine), natural-tree pollen and rarefied richness; paired Wilcoxon tests with bootstrap CIs; a placebo test on rates of change (250–399 → 400–540 CE); six window-sensitivity tests; z-score composites and climate correlations; site fixed-effects regressions of land use on temperature, plague period and trend (SEs clustered by site and 25-yr bin); HYDE vs pollen in space and in the direction of change; an expanded Eastern Mediterranean sample; a Monte Carlo that perturbs every age within its age-model error (1,000 realisations).

## Reproduce

Python 3 with the versions in [`requirements.txt`](requirements.txt) (`pip install -r requirements.txt`).

```bash
./run.sh          # every table, figure, the report HTML and the slide charts, from data/ (about 2 minutes, offline)
./run.sh --full   # first rebuild data/: Neotoma (~500 MB), HYDE grids, NOAA climate series
```

The report PDF is printed from the HTML with headless Chrome (`google-chrome --headless --no-pdf-header-footer --print-to-pdf=report/final_report.pdf report/final_report.html`). The slide deck is built with Node: `npm install pptxgenjs react-icons react react-dom sharp && node presentation/build_deck.js`.

| Path | Contents |
|---|---|
| `code/query.py` | Lists the Neotoma pollen datasets in the study area (`data/neotoma_dataset_list.json`) |
| `code/dl.py` | Downloads each Neotoma record through API v2 |
| `code/process.py` | Picks calendar-scale ages, filters samples, classifies taxa, computes indicators and rarefied richness |
| `code/clean.py` | Keeps default chronologies, removes duplicate records (`data/duplicate_records.csv`), pools cores of one site |
| `code/hyde.py` | Reads the HYDE 3.2.1 grids (200–1000 CE) from the DANS archive; land use and population around each site |
| `code/climate.py` | Fetches the PAGES 2k Euro-Med and Eastern Mediterranean speleothem series from NOAA |
| `code/common.py` | Windows, indicators, regions and plot conventions shared by all scripts |
| `code/analyse.py` | Before/after tests, placebo, sensitivity, composites; Figs 1–5 and 9 |
| `code/final.py` | Climate, regression, Eastern Mediterranean sample, HYDE, Monte Carlo; Figs 6–8, 10, 11; `tables/text_numbers.json` |
| `code/report.py` | Writes `report/final_report.html` from the tables (checks every qualitative statement) and `presentation/deck_numbers.json` |
| `code/slide_figs.py` | Charts for the presentation (`presentation/charts/`) |
| `data/` | Cleaned samples, climate series, HYDE site values and 0.25° grids, list of Neotoma dataset IDs, removed duplicates |
| `figures/`, `tables/` | Report figures (Fig. 1–11) and result tables |

## Team

Jetty Jithendra Sai Ram (2024101102) · N Pavaneswar (2024102063) · Shaik Babu (2024101032) · Dr Shashang (2024101069)
