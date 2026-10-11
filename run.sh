#!/usr/bin/env bash
# Reproduce every number and figure of the mid-evaluation.
#   ./run.sh          -> analysis only, from data/samples.csv (about 1 min, offline)
#   ./run.sh --full   -> re-download 891 Neotoma records (~470 MB, 30-60 min) and rebuild samples.csv first
set -e
cd "$(dirname "$0")"
if [ "$1" == "--full" ]; then
  mkdir -p raw
  python3 code/dl.py data/neotoma_dataset_list.json raw
  python3 code/process.py raw data/samples.csv
fi
python3 code/analyse.py data/samples.csv data/buentgen.csv out
echo "Figures and tables written to ./out"
