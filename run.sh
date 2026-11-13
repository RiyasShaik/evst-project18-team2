#!/usr/bin/env bash
# Reproduce every number, table and figure of the final report, the report HTML and the presentation charts.
#   ./run.sh          analysis only, from the files in data/ (about 2 minutes, offline)
#   ./run.sh --full   rebuild data/ first: download the 1,099 Neotoma records listed in data/neotoma_dataset_list.json
#                     (~500 MB, 30-60 min), read the HYDE 3.2.1 grids from the DANS archive (~6 min) and fetch the
#                     NOAA climate series. code/query.py regenerates the dataset list (Neotoma keeps growing, so a new
#                     list can differ from ours).
# Requires the package versions in requirements.txt (small-sample Wilcoxon p-values differ between SciPy versions).
set -e
cd "$(dirname "$0")"
if [ "$1" == "--full" ]; then
  mkdir -p raw
  python3 code/dl.py data/neotoma_dataset_list.json raw
  python3 code/process.py raw data/samples.csv
  python3 code/clean.py data/samples.csv data/duplicate_records.csv
  python3 code/hyde.py data/samples.csv data/hyde_sites.csv data/hyde_grid.npz raw/hyde_window.npz
  python3 code/climate.py data
fi
python3 code/analyse.py data/samples.csv data/buentgen.csv data/hyde_grid.npz tables figures
python3 code/final.py data tables/mideval tables figures
python3 code/report.py tables report presentation
python3 code/slide_figs.py data tables presentation/charts
echo "Tables in ./tables, figures in ./figures, report HTML in ./report, presentation charts and numbers in ./presentation"
