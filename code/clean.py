"""Step 1b: clean the sample table written by process.py, in place.

1. Keep only ages from each record's default chronology (records whose default chronology is not calendar-scale
   would otherwise fall back to another chronology; the paper states that default chronologies are used).
2. Drop duplicate records. Neotoma holds some cores twice (e.g. an EPD copy and a re-upload). A record is a duplicate
   when at least half of its samples (same age to the year and same pollen sum) also occur in another record of the
   same site; the record with more samples (then the lower dataset id) is kept.
3. Pool the remaining records of one site. Records with the same site name within 2 km of each other are different
   cores from the same lake or bog; they get one `siteid` (the lowest dataset id), so every site counts once.

Writes the cleaned samples.csv and duplicate_records.csv (the records dropped in step 2)."""
import sys
import numpy as np, pandas as pd

F = sys.argv[1] if len(sys.argv) > 1 else 'data/samples.csv'
LOG = sys.argv[2] if len(sys.argv) > 2 else 'data/duplicate_records.csv'

S = pd.read_csv(F)
if 'siteid' in S:
    sys.exit(f'{F} is already cleaned')
n0, r0 = len(S), S.datasetid.nunique()
S = S[S.chron == 'default'].copy()
n_chron = n0 - len(S)

key = {ds: set(zip(g.age_ce.round(0), g.pollensum.round(0))) for ds, g in S.groupby('datasetid')}
first = S.groupby('datasetid')[['site', 'lon', 'lat']].first()
drop = []
for name, g in first.groupby('site'):
    ids = sorted(g.index, key=lambda i: (-len(key[i]), i))
    for i, a in enumerate(ids):
        for b in ids[:i]:
            if b in drop:
                continue
            share = len(key[a] & key[b]) / len(key[a])
            if share >= .5:
                drop.append(a)
                break
log = first.loc[drop].assign(duplicate_of=[next(b for b in sorted(first[first.site == first.loc[a, 'site']].index,
                                                                  key=lambda i: (-len(key[i]), i))
                                                if b not in drop and len(key[a] & key[b]) / len(key[a]) >= .5) for a in drop])
log.reset_index().to_csv(LOG, index=False)
S = S[~S.datasetid.isin(drop)]

first = S.groupby('datasetid')[['site', 'lon', 'lat']].first()
site = {}
for name, g in first.groupby('site'):
    for ds in sorted(g.index):
        x = g.loc[ds]
        near = [o for o in sorted(g.index) if o < ds and o in site and
                np.hypot((g.loc[o, 'lon'] - x.lon) * np.cos(np.radians(x.lat)), g.loc[o, 'lat'] - x.lat) * 111 <= 2]
        site[ds] = site[near[0]] if near else ds
S.insert(1, 'siteid', S.datasetid.map(site))
S = S.sort_values(['siteid', 'datasetid', 'age_ce'], kind='stable')
for c in ('lon', 'lat', 'alt', 'region'):
    S[c] = S.groupby('siteid')[c].transform('first')
S.to_csv(F, index=False)
print(f'{n0} samples / {r0} records in; dropped {n_chron} samples without a default calendar chronology and '
      f'{len(drop)} duplicate records; {len(S)} samples, {S.datasetid.nunique()} records, {S.siteid.nunique()} sites out')
