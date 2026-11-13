"""Step 2: before/after analysis of the First Pandemic (541-750 CE): site window means, Wilcoxon tests with bootstrap
intervals, placebo and sensitivity tests, z-score composites. Figures 1-5 and 9 of the report.

Usage: analyse.py data/samples.csv data/buentgen.csv data/hyde_grid.npz tables/ figures/
The unit of analysis is the site (`siteid`, written by clean.py): cores from the same lake are pooled."""
import sys, os, json
import numpy as np, pandas as pd
from scipy import stats
from common import IND, REG, EM, COL, PRE, POST, PLACEBO, REC, inwin, mid, binc, shade, style, land, plt

S = pd.read_csv(sys.argv[1])
CLIM = pd.read_csv(sys.argv[2])
G = np.load(sys.argv[3])
OT, OF = sys.argv[4], sys.argv[5]
for d in (OT, OF):
    os.makedirs(d, exist_ok=True)
rng = np.random.default_rng(42)
style()
K = list(IND)
lab = lambda w: f'{w[0]}–{w[1]}'

# ---------- site window means ----------
W = S.groupby('siteid').agg(site=('site', 'first'), lon=('lon', 'first'), lat=('lat', 'first'), region=('region', 'first'),
                            n_records=('datasetid', 'nunique'))
for tag, w in dict(pre=PRE, post=POST, plc=PLACEBO, rec=REC).items():
    x = S[inwin(S.age_ce, w)].groupby('siteid')
    W = W.join(x[K].mean().add_suffix('_' + tag)).join(x.size().rename('n_' + tag))
W = W.fillna({f'n_{t}': 0 for t in ('pre', 'post', 'plc', 'rec')})
W['median_unc'] = S[inwin(S.age_ce, (400, 750))].groupby('siteid').age_unc.median()
core = W[(W.n_pre >= 2) & (W.n_post >= 2)].copy()
core.reset_index().to_csv(f'{OT}/site_window_means.csv', index=False)


def wilcox(d):
    return stats.wilcoxon(d).pvalue if (d != 0).any() else np.nan


def test(d):
    d = d.dropna()
    boot = np.median(rng.choice(d.values, (2000, len(d))), axis=1)
    return dict(n=len(d), median_change=np.median(d), ci_lo=np.percentile(boot, 2.5), ci_hi=np.percentile(boot, 97.5),
                pct_sites_increase=100 * (d > 0).mean(), pct_sites_decline=100 * (d < 0).mean(),
                pct_sites_no_change=100 * (d == 0).mean(), wilcoxon_p=wilcox(d))


scopes = lambda df: [('All sites', df)] + [(r, df[df.region == r]) for r in REG]
T = pd.DataFrame([dict(scope=s, indicator=k, **test(df[f'{k}_post'] - df[f'{k}_pre'])) for s, df in scopes(core) for k in K])
T.to_csv(f'{OT}/table_pre_vs_post.csv', index=False)

# ---------- placebo: is the change across 541 faster than the change between 250-399 and 400-540? ----------
# Changes are divided by the distance between window midpoints (175.5 yr vs 145.5 yr), so that a steady trend gives
# the same rate in both comparisons; the raw changes are kept for reference.
G_REAL, G_PLC = mid(POST) - mid(PRE), mid(PRE) - mid(PLACEBO)
pl = core[core.n_plc >= 2]
prow = []
for s, df in scopes(pl):
    for k in ['cereal', 'arbor', 'pastoral', 'anthro', 'ap_natural']:
        real, plac = (df[f'{k}_post'] - df[f'{k}_pre']), (df[f'{k}_pre'] - df[f'{k}_plc'])
        ok = real.notna() & plac.notna()
        real, plac = real[ok], plac[ok]
        if len(real) < 5:
            continue
        rr, rp = 100 * real / G_REAL, 100 * plac / G_PLC
        prow.append(dict(scope=s, indicator=k, n=len(real), median_change_pandemic=real.median(), median_change_placebo=plac.median(),
                         median_rate_pandemic_per_century=rr.median(), median_rate_placebo_per_century=rp.median(),
                         p_rate=wilcox(rr - rp), p_raw_change=wilcox(real - plac)))
P = pd.DataFrame(prow)
P.to_csv(f'{OT}/table_placebo.csv', index=False)

# ---------- sensitivity to the windows ----------
SENS = [('Main', PRE, POST), ('Narrow', (450, 540), (541, 640)), ('Early plague only', (450, 540), (541, 600)),
        ('Boundary 50 yr earlier', (350, 490), (491, 700)), ('Boundary 50 yr later', (450, 590), (591, 800)),
        ('Following period', POST, REC)]
srow = []
for name, a, b in SENS:
    xa, xb = S[inwin(S.age_ce, a)].groupby('siteid'), S[inwin(S.age_ce, b)].groupby('siteid')
    ma, mb, na, nb = xa[K].mean(), xb[K].mean(), xa.size(), xb.size()
    ok = na[na >= 2].index.intersection(nb[nb >= 2].index)
    for k in ['cereal', 'pastoral', 'anthro', 'ap_natural']:
        t = test(mb.loc[ok, k] - ma.loc[ok, k])
        srow.append(dict(test=name, before=lab(a), after=lab(b), indicator=k, **t))
pd.DataFrame(srow).to_csv(f'{OT}/table_sensitivity.csv', index=False)

# ---------- composites: site z-scores in 25-yr bins ----------
Z = S[S.siteid.isin(core.index)].copy()
for k in K:
    g = Z.groupby('siteid')[k]
    Z[k] = (Z[k] - g.transform('mean')) / g.transform('std').replace(0, np.nan)
Z['bin'] = binc(Z.age_ce)
SB = Z.groupby(['siteid', 'region', 'bin'])[K].mean().reset_index()


def composite(df, col, nmin=5):
    out = []
    for b, d in df.groupby('bin'):
        v = d[col].dropna().values
        if len(v) < nmin or not 200 <= b <= 1000:
            continue
        bs = rng.choice(v, (500, len(v))).mean(1)
        out.append((b, v.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5), len(v)))
    return pd.DataFrame(out, columns=['bin', 'mean', 'lo', 'hi', 'n'])


# Fig 1: sites
fig, ax = plt.subplots(figsize=(8.6, 6.2))
land(ax, G)
for r in REG:
    d = core[core.region == r]
    ax.scatter(d.lon, d.lat, s=20, c=COL[r], label=f'{r} ({len(d)})', edgecolor='k', lw=.3, zorder=3)
ax.set_xlim(-11, 50); ax.set_ylim(30, 57); ax.set_aspect(1 / np.cos(np.radians(43)))
ax.set_xlabel('Longitude (°E)'); ax.set_ylabel('Latitude (°N)'); ax.grid(alpha=.3)
ax.legend(fontsize=8.5, loc='upper center', bbox_to_anchor=(.5, -.11), ncol=3, frameon=False)
fig.tight_layout(); fig.savefig(f'{OF}/fig01_site_map.png'); plt.close()

# Fig 2: Europe-wide composites and Alpine temperature
fig, axs = plt.subplots(5, 1, figsize=(8, 11.5), sharex=True)
for i, (ax, k) in enumerate(zip(axs[:4], ['cereal', 'anthro', 'ap_natural', 'richness'])):
    c = composite(SB, k)
    ax.fill_between(c.bin, c.lo, c.hi, color='grey', alpha=.3, lw=0); ax.plot(c.bin, c['mean'], 'k-o', ms=3)
    h = shade(ax, legend=True); ax.axhline(0, color='grey', lw=.5); ax.set_ylabel('z-score')
    ax.set_title(f"{'abcd'[i]}  {IND[k]}", fontsize=10, loc='left')
axs[0].legend(handles=h, fontsize=8, loc='upper left', frameon=False)
cl = CLIM[(CLIM.year >= 190) & (CLIM.year <= 1010)].set_index('year').tempJJA
axs[4].plot(cl.index, cl, color='#bbb', lw=.5); axs[4].plot(cl.index, cl.rolling(31, center=True).mean(), color='#2166ac', lw=2)
shade(axs[4]); axs[4].set_ylabel('°C anomaly')
axs[4].set_title('e  Central European June–August temperature (Büntgen et al. 2011): annual and 31-yr mean', fontsize=10, loc='left')
axs[4].set_xlabel('Year CE'); axs[4].set_xlim(190, 1010)
fig.tight_layout(); fig.savefig(f'{OF}/fig02_composites.png'); plt.close()

# Fig 3: site-level change map
fig, ax = plt.subplots(figsize=(8.8, 5.8))
land(ax, G)
ch = core.anthro_post - core.anthro_pre
v = np.nanpercentile(np.abs(ch), 90)
sc = ax.scatter(core.lon, core.lat, c=ch, cmap='RdBu', vmin=-v, vmax=v, s=28, edgecolor='k', lw=.3, zorder=3)
cb = plt.colorbar(sc, ax=ax, shrink=.85, extend='both')
cb.set_label('Change in all anthropogenic indicators,\npercentage points (541–750 minus 400–540 CE)')
ax.set_xlim(-11, 50); ax.set_ylim(30, 57); ax.set_aspect(1 / np.cos(np.radians(43))); ax.grid(alpha=.3)
ax.set_xlabel('Longitude (°E)'); ax.set_ylabel('Latitude (°N)')
fig.tight_layout(); fig.savefig(f'{OF}/fig03_change_map.png'); plt.close()

# Fig 4: placebo, rates of change per century
fig, ax = plt.subplots(figsize=(9.5, 4.6))
pos, ticks = 0, []
for s, df in scopes(pl):
    a = 100 * (df.anthro_pre - df.anthro_plc) / G_PLC; b = 100 * (df.anthro_post - df.anthro_pre) / G_REAL
    ok = a.notna() & b.notna()
    if ok.sum() < 5:
        continue
    bp = ax.boxplot([a[ok], b[ok]], positions=[pos, pos + .8], widths=.6, patch_artist=True, showfliers=False,
                    medianprops=dict(color='k'))
    bp['boxes'][0].set_facecolor('#d9d9d9'); bp['boxes'][1].set_facecolor('#fc9272')
    ticks.append((pos + .4, f'{s}\n(n = {ok.sum()})')); pos += 2.2
ax.axhline(0, color='k', lw=.6); ax.set_xticks([t[0] for t in ticks]); ax.set_xticklabels([t[1] for t in ticks], fontsize=8)
ax.set_ylabel('Change in all anthropogenic\nindicators, pp per century')
ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, fc='#d9d9d9', ec='k', label='Before the plague: 250–399 → 400–540 CE'),
                   plt.Rectangle((0, 0), 1, 1, fc='#fc9272', ec='k', label='Across 541: 400–540 → 541–750 CE')],
          fontsize=8, loc='lower left', frameon=False, ncol=1)
fig.tight_layout(); fig.savefig(f'{OF}/fig04_placebo.png'); plt.close()

# Fig 5: regional composites
fig, axs = plt.subplots(len(REG), 2, figsize=(10, 12.5), sharex=True)
for i, r in enumerate(REG):
    for j, k in enumerate(['anthro', 'ap_natural']):
        ax = axs[i, j]; c = composite(SB[SB.region == r], k, 3)
        ax.fill_between(c.bin, c.lo, c.hi, color=COL[r], alpha=.25, lw=0); ax.plot(c.bin, c['mean'], '-o', color=COL[r], ms=3)
        h = shade(ax, legend=True); ax.axhline(0, color='grey', lw=.5)
        ax.set_title(f"{'abcdefghij'[2 * i + j]}  {r} ({core.region.eq(r).sum()} sites): {IND[k].lower()}", fontsize=9, loc='left')
        if j == 0:
            ax.set_ylabel('z-score')
axs[0, 0].legend(handles=h, fontsize=7.5, loc='upper left', frameon=False)
for ax in axs[-1]:
    ax.set_xlabel('Year CE'); ax.set_xlim(190, 1010)
fig.tight_layout(); fig.savefig(f'{OF}/fig05_regional.png'); plt.close()

# Fig 9: Eastern Mediterranean cultivated trees by site
e = core[core.region == EM].copy(); e['d'] = e.arbor_post - e.arbor_pre; e = e.sort_values('d')
fig, ax = plt.subplots(figsize=(8, 1.5 + .28 * len(e)))
ax.barh(range(len(e)), e.d, color=['#b2182b' if v < 0 else '#2166ac' for v in e.d])
ax.set_yticks(range(len(e))); ax.set_yticklabels(e.site + '  (' + e.arbor_pre.round(1).astype(str) + '%)')
ax.axvline(0, color='k', lw=.6); ax.set_ylim(-.7, len(e) - .3)
ax.set_xlabel('Change in cultivated-tree pollen (olive, walnut, chestnut, vine), percentage points,\n'
              '541–750 minus 400–540 CE; in brackets: level in 400–540 CE')
fig.tight_layout(); fig.savefig(f'{OF}/fig09_emed_arbor.png'); plt.close()

summ = dict(n_samples=int(len(S)), n_records=int(S.datasetid.nunique()), n_sites=int(S.siteid.nunique()),
            n_core_sites=int(len(core)), n_core_records=int(core.n_records.sum()), core_sites_with_2plus_records=int((core.n_records > 1).sum()),
            regions=core.region.value_counts().to_dict(), median_samples_pre=float(core.n_pre.median()), median_samples_post=float(core.n_post.median()),
            core_sites_with_age_range=int(core.median_unc.notna().sum()), median_age_half_range=float(core.median_unc.median()),
            n_placebo_sites=int(len(pl)), gap_real_yr=G_REAL, gap_placebo_yr=G_PLC)
json.dump(summ, open(f'{OT}/summary.json', 'w'), indent=1)
pd.set_option('display.width', 220); pd.set_option('display.max_columns', 20)
print(json.dumps(summ, indent=1)); print(T.round(3).to_string()); print(P.round(3).to_string())
print(pd.read_csv(f'{OT}/table_sensitivity.csv').round(3).to_string())
