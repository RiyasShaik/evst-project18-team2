"""Step 0: list Neotoma pollen datasets in the study area whose calendar-scale age range spans 400-750 CE.
Final version: also keeps records stored as polygons (centroid) and with Calendar/Varve-year chronologies
(the mid-evaluation list required calibrated-radiocarbon ages spanning 100-950 CE)."""
import json, sys, requests

OUT = sys.argv[1] if len(sys.argv) > 1 else 'neotoma_dataset_list.json'
BOX = {"type": "Polygon", "coordinates": [[[-10, 30], [50, 30], [50, 56], [-10, 56], [-10, 30]]]}
CAL = ('Calibrated radiocarbon years BP', 'Calendar years BP', 'Varve years BP', 'Calendar years AD/BC')


def bp(a, u):
    return 1950 - a if u == 'Calendar years AD/BC' else a


def centroid(g):
    """Point coordinates, or the vertex mean of the outer ring for sites stored as polygons."""
    c = g['coordinates']
    if g['type'] == 'Point':
        return c
    while isinstance(c[0][0], list):
        c = c[0]
    return [sum(p[0] for p in c) / len(c), sum(p[1] for p in c) / len(c)]


keep, off = {}, 0
while True:
    d = requests.get('https://api.neotomadb.org/v2.0/data/datasets', timeout=300,
                     params=dict(datasettype='pollen', loc=json.dumps(BOX), limit=500, offset=off)).json()['data']
    if not d:
        break
    for x in d:
        s = x['site']
        lon, lat = centroid(json.loads(s['geography']))
        for ds in s['datasets']:
            ar = [a for a in ds.get('agerange') or [] if a['units'] in CAL and None not in (a['ageold'], a['ageyoung'])]
            if ds['datasettype'] != 'pollen' or not ar:
                continue
            old = max(max(bp(a['ageold'], a['units']), bp(a['ageyoung'], a['units'])) for a in ar)
            young = min(min(bp(a['ageold'], a['units']), bp(a['ageyoung'], a['units'])) for a in ar)
            if old >= 1550 and young <= 1200 and -10 <= lon <= 50 and 30 <= lat <= 56:
                keep[ds['datasetid']] = [ds['datasetid'], s['sitename'], round(lon, 5), round(lat, 5), old, young]
    off += 500
json.dump(sorted(keep.values()), open(OUT, 'w', encoding='utf-8'))
print(len(keep), 'datasets')
