"""Step 1: parse Neotoma downloads -> one row per pollen sample (0-1200 CE) with land-use indicators."""
import json, glob, re, math, sys
import pandas as pd
from collections import defaultdict

RAW = sys.argv[1] if len(sys.argv) > 1 else 'raw'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'samples.csv'

CEREAL = re.compile(r'cerealia|^secale|^triticum|^hordeum|^avena|^cf\. hordeum', re.I)
SECALE = re.compile(r'^secale', re.I)
ARBOR = re.compile(r'^(olea(?!ceae)|juglans|castanea|vitis)', re.I)   # cultivated trees (OJCV)
OLEA = re.compile(r'^olea(?!ceae)', re.I)
PAST = re.compile(r'^plantago lanceolata|^rumex (acetosa|acetosella)|^rumex(-type| undiff\.)?$|rumex subg\. acetosa', re.I)
TERR = {'TRSH', 'UPHE'}
CAL = ('Calibrated radiocarbon years BP', 'Calendar years BP', 'Varve years BP', 'Calendar years AD/BC')


def region(lon, lat):
    if lat < 43 and lon >= 19:
        return 'E. Mediterranean & Anatolia'
    if lat < 44 and lon < 19:
        return 'W. Mediterranean'
    if lon < 2 and lat >= 49.5:
        return 'British Isles'
    if lon < 16:
        return 'W. & Central Europe'
    return 'E. Europe'


def lrare(counts, n):
    """Rarefied richness E(S_n) (Hurlbert 1971)."""
    N = sum(counts)
    if N < n:
        return float('nan')
    lc = math.lgamma
    base = lc(N + 1) - lc(n + 1) - lc(N - n + 1)
    s = 0.0
    for c in counts:
        if N - c >= n:
            s += 1 - math.exp(lc(N - c + 1) - lc(n + 1) - lc(N - c - n + 1) - base)
        else:
            s += 1
    return s


def centroid(g):
    """Point coordinates, or the vertex mean of the outer ring for sites stored as polygons."""
    c = g['coordinates']
    if g['type'] == 'Point':
        return c
    while isinstance(c[0][0], list):
        c = c[0]
    return [sum(p[0] for p in c) / len(c), sum(p[1] for p in c) / len(c)]


def to_bp(a):
    """Calendar-scale age record with AD/BC ages converted to years BP."""
    if a['agetype'] != 'Calendar years AD/BC':
        return a
    return dict(a, age=1950 - a['age'],
                ageolder=None if a['ageolder'] is None else 1950 - a['ageolder'],
                ageyounger=None if a['ageyounger'] is None else 1950 - a['ageyounger'])


def pick_age(ages, default_id):
    cal = [to_bp(a) for a in ages if a['agetype'] in CAL and a['age'] is not None]
    if not cal:
        return None, None
    for a in cal:
        if a['chronologyid'] == default_id:
            return a, 'default'
    for a in cal:
        if 'MADCAP' in (a['chronologyname'] or ''):
            return a, 'MADCAP'
    return cal[0], 'other-cal'


rows = []
for f in glob.glob(f'{RAW}/*.json'):
    try:
        site = json.load(open(f, encoding='utf-8'))['data'][0]['site']
    except Exception:
        continue
    lon, lat = centroid(json.loads(site['geography']))
    cu = site['collectionunit']
    ds = cu['dataset']
    for s in ds['samples']:
        a, src = pick_age(s['ages'], cu.get('defaultchronology'))
        if a is None:
            continue
        ce = 1950 - a['age']
        if not (0 <= ce <= 1200):
            continue
        taxa = defaultdict(float)
        grp = {}
        for x in s['datum']:
            if x['units'] != 'NISP' or x['ecologicalgroup'] not in TERR or x['value'] is None:
                continue
            taxa[x['variablename']] += x['value']
            grp[x['variablename']] = x['ecologicalgroup']
        tot = sum(taxa.values())
        if tot < 100:
            continue
        pct = lambda rx: 100 * sum(v for k, v in taxa.items() if rx.search(k)) / tot
        trsh = sum(v for k, v in taxa.items() if grp[k] == 'TRSH')
        arbor = sum(v for k, v in taxa.items() if ARBOR.search(k))
        unc = None
        if a.get('ageolder') is not None and a.get('ageyounger') is not None:
            unc = abs(a['ageolder'] - a['ageyounger']) / 2
        rows.append(dict(
            datasetid=ds['datasetid'], site=site['sitename'], lon=lon, lat=lat, alt=site['altitude'],
            region=region(lon, lat), age_ce=ce, age_unc=unc, chron=src, agetype=a['agetype'], depth=s.get('depth'), pollensum=tot,
            cereal=pct(CEREAL), secale=pct(SECALE), arbor=pct(ARBOR), olea=pct(OLEA), pastoral=pct(PAST),
            ap_natural=100 * (trsh - arbor) / tot,
            richness=lrare([v for v in taxa.values() if v >= 1], 100),
        ))

df = pd.DataFrame(rows)
df['anthro'] = df.cereal + df.arbor + df.pastoral
df.to_csv(OUT, index=False)
print(len(df), 'samples from', df.datasetid.nunique(), 'datasets')
