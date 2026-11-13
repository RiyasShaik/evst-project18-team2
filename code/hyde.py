"""Step 1b: HYDE 3.2.1 (Klein Goldewijk et al. 2017) land use and population around every pollen site, 200-1000 CE.
Reads only the needed grids (and only the rows north of 28 N) out of the 5.3 GB DANS archive with HTTP range requests.
The archive is Deflate64-compressed, which needs `pip install inflate64`."""
import io, os, sys, zipfile, zlib, requests
import numpy as np, pandas as pd
from inflate64 import Inflater

S = pd.read_csv(sys.argv[1])
OUT = sys.argv[2]
GRID = sys.argv[3]
CACHE = sys.argv[4] if len(sys.argv) > 4 else 'raw/hyde_window.npz'
URL = 'https://archaeology.datastations.nl/api/access/datafile/'
BASE, GEN = 5490328, 5490327          # HYDE3_2_1-baseline.zip, HYDE3_2_1-general_supplementary.zip (doi:10.17026/dans-25g-gez3)
YEARS = range(200, 1001, 100)
R0, R1, C0, C1 = 384, 744, 2016, 2784  # rows 58-28 N, cols 12 W-52 E of the 5' global grid
RADII = (25, 50, 100)


class Remote(io.RawIOBase):
    """Seekable file over HTTP range requests, so zipfile only fetches the members it opens."""
    def __init__(self, fid):
        self.fid, self.pos = fid, 0
        self.refresh()
        self.size = int(requests.get(self.url, headers={'Range': 'bytes=0-0'}, timeout=60).headers['Content-Range'].split('/')[-1])

    def refresh(self):
        self.url = requests.get(URL + str(self.fid), allow_redirects=False, timeout=60).headers['Location']

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos

    def seek(self, off, whence=0):
        self.pos = [off, self.pos + off, self.size + off][whence]
        return self.pos

    def readinto(self, b):
        end = min(self.pos + len(b), self.size) - 1
        if self.pos > end:
            return 0
        for t in range(6):
            try:
                r = requests.get(self.url, headers={'Range': f'bytes={self.pos}-{end}'}, timeout=300)
                if r.status_code == 206:
                    break
                self.refresh()
            except requests.RequestException:
                pass
        else:
            raise IOError('range request failed')
        b[:len(r.content)] = r.content; self.pos += len(r.content)
        return len(r.content)


def window(z, name):
    """Rows R0:R1, cols C0:C1 of one ascii grid; stops inflating (and downloading) after row R1."""
    i, f = z.getinfo(name), z.fp
    f.seek(i.header_offset); h = f.read(30)
    pos = i.header_offset + 30 + int.from_bytes(h[26:28], 'little') + int.from_bytes(h[28:30], 'little')
    end = pos + i.compress_size
    inflate = Inflater().inflate if i.compress_type == 9 else zlib.decompressobj(-15).decompress
    out, buf, r = [], b'', -6
    while r < R1 and pos < end:
        f.seek(pos); c = f.read(min(1 << 20, end - pos)); pos += len(c)
        *lines, buf = (buf + inflate(c)).split(b'\n')
        for line in lines:
            if R0 <= r < R1:
                out.append(np.array(line.split()[C0:C1], float))
            r += 1
    a = np.array(out[:R1 - R0])
    a[a < 0] = np.nan
    return a


if os.path.exists(CACHE):
    G = dict(np.load(CACHE))
else:
    zb = zipfile.ZipFile(io.BufferedReader(Remote(BASE), 1 << 20))
    zg = zipfile.ZipFile(io.BufferedReader(Remote(GEN), 1 << 20))
    G = dict(land=window(zg, 'general_files/maxln_cr.asc'))
    for y in YEARS:
        G[f'crop{y}'] = window(zb, f'baseline/asc/{y}AD_lu/cropland{y}AD.asc')
        G[f'graz{y}'] = window(zb, f'baseline/asc/{y}AD_lu/grazing{y}AD.asc')
        G[f'popd{y}'] = window(zb, f'baseline/asc/{y}AD_pop/popd_{y}AD.asc')
        print(y, 'done', file=sys.stderr)
    os.makedirs(os.path.dirname(CACHE) or '.', exist_ok=True)
    np.savez_compressed(CACHE, **{k: v.astype('float32') for k, v in G.items()})
land = G.pop('land')

lat = 90 - (np.arange(R0, R1) + .5) / 12
lon = -180 + (np.arange(C0, C1) + .5) / 12
LON, LAT = np.meshgrid(lon, lat)
rows = []
for (ds, x, y0), _ in S.groupby(['datasetid', 'lon', 'lat']):
    ix = np.ix_(np.abs(lat - y0) <= 1, np.abs(lon - x) <= 1 / np.cos(np.radians(y0)) + .1)   # box enclosing the 100 km circle
    LO, LA, ld = LON[ix], LAT[ix], land[ix]
    d = 6371 * 2 * np.arcsin(np.sqrt(np.sin(np.radians(LA - y0) / 2) ** 2 +
                                     np.cos(np.radians(y0)) * np.cos(np.radians(LA)) * np.sin(np.radians(LO - x) / 2) ** 2))
    for y in YEARS:
        r = dict(datasetid=ds, year=y)
        for k in RADII:
            m = (d <= k) & (ld > 0)
            L = np.nansum(ld[m])
            r[f'crop_{k}'] = np.nansum(G[f'crop{y}'][ix][m]) / L if L else np.nan
            r[f'graz_{k}'] = np.nansum(G[f'graz{y}'][ix][m]) / L if L else np.nan
        m = (d <= 50) & (ld > 0)
        r['popd_50'] = np.nansum(G[f'popd{y}'][ix][m] * ld[m]) / np.nansum(ld[m]) if m.any() else np.nan
        rows.append(r)
pd.DataFrame(rows).to_csv(OUT, index=False, float_format='%.5g')

# 0.25-degree land-use fraction grids for the maps
agg = lambda a: a.reshape(a.shape[0] // 3, 3, a.shape[1] // 3, 3)
L4 = np.nansum(agg(land), axis=(1, 3))
q = {k: np.where(L4 > 0, np.nansum(agg(v), axis=(1, 3)) / np.where(L4 > 0, L4, 1), np.nan).astype('float32')
     for k, v in G.items() if not k.startswith('popd')}
np.savez_compressed(GRID, lat=lat.reshape(-1, 3).mean(1), lon=lon.reshape(-1, 3).mean(1), **q)
print(len(rows), 'site-years written')
