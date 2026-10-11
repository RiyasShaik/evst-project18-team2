"""Step 2: before/after analysis of First Pandemic (541-750 CE) land-use signal + figures + tables."""
import sys, os, json
import numpy as np, pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

S = pd.read_csv(sys.argv[1])
CLIM = pd.read_csv(sys.argv[2])
OUT = sys.argv[3]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(42)

IND = {'cereal': 'Cereal pollen (%)', 'arbor': 'Cultivated trees: Olea+Juglans+Castanea+Vitis (%)',
       'pastoral': 'Pastoral indicators: Plantago lanceolata+Rumex (%)', 'anthro': 'All anthropogenic indicators (%)',
       'ap_natural': 'Natural tree/shrub pollen (%)', 'richness': 'Rarefied richness E(S100)'}
REG = ['E. Mediterranean & Anatolia', 'W. Mediterranean', 'W. & Central Europe', 'British Isles', 'E. Europe']
PRE, POST, PLACEBO, REC = (400, 540), (541, 750), (250, 399), (751, 900)

S = S[S.chron != 'other-cal'] if (S.chron != 'other-cal').sum() > 0.8 * len(S) else S

# ---------- site-level window means ----------
def wmean(d, w):
    x = d[(d.age_ce >= w[0]) & (d.age_ce <= w[1])]
    return x[list(IND)].mean(), len(x)

recs = []
for (ds, site), d in S.groupby(['datasetid', 'site']):
    pre, npre = wmean(d, PRE); post, npost = wmean(d, POST)
    plc, nplc = wmean(d, PLACEBO); rec, nrec = wmean(d, REC)
    r = dict(datasetid=ds, site=site, lon=d.lon.iloc[0], lat=d.lat.iloc[0], region=d.region.iloc[0],
             n_pre=npre, n_post=npost, n_placebo=nplc, n_rec=nrec,
             median_unc=d[(d.age_ce >= 400) & (d.age_ce <= 750)].age_unc.median())
    for k in IND:
        r[f'{k}_pre'], r[f'{k}_post'], r[f'{k}_plc'], r[f'{k}_rec'] = pre[k], post[k], plc[k], rec[k]
    recs.append(r)
W = pd.DataFrame(recs)
core = W[(W.n_pre >= 2) & (W.n_post >= 2)].copy()
core.to_csv(f'{OUT}/site_window_means.csv', index=False)

# ---------- statistics ----------
def test(df, k, a='pre', b='post'):
    d = (df[f'{k}_{b}'] - df[f'{k}_{a}']).dropna()
    if len(d) < 5:
        return dict(n=len(d))
    w = stats.wilcoxon(d) if (d != 0).any() else None
    nd, nu = (d < 0).sum(), (d > 0).sum()
    boot = [np.median(rng.choice(d.values, len(d))) for _ in range(2000)]
    return dict(n=len(d), median_change=np.median(d), ci_lo=np.percentile(boot, 2.5), ci_hi=np.percentile(boot, 97.5),
                pct_sites_decline=100 * nd / len(d), wilcoxon_p=w.pvalue if w else np.nan)

rows = []
for scope, df in [('All sites', core)] + [(r, core[core.region == r]) for r in REG]:
    for k in IND:
        t = test(df, k); t.update(scope=scope, indicator=k); rows.append(t)
T = pd.DataFrame(rows)
T.to_csv(f'{OUT}/table_pre_vs_post.csv', index=False)

# placebo: is the 541-750 change larger than the change between two earlier windows of similar length?
pl = core[core.n_placebo >= 2]
prow = []
for scope, df in [('All sites', pl)] + [(r, pl[pl.region == r]) for r in REG]:
    for k in ['cereal', 'arbor', 'pastoral', 'anthro', 'ap_natural']:
        real = (df[f'{k}_post'] - df[f'{k}_pre']).dropna()
        plac = (df[f'{k}_pre'] - df[f'{k}_plc']).dropna()
        idx = real.index.intersection(plac.index)
        if len(idx) < 5:
            continue
        p = stats.wilcoxon(real[idx], plac[idx]).pvalue
        prow.append(dict(scope=scope, indicator=k, n=len(idx), median_change_pandemic=real[idx].median(),
                         median_change_placebo=plac[idx].median(), p_pandemic_vs_placebo=p))
P = pd.DataFrame(prow); P.to_csv(f'{OUT}/table_placebo.csv', index=False)

# sensitivity: narrower windows (450-540 vs 541-640) and boundary shifted to 500 / 600
sens = []
for lab, a, b in [('Main 400-540 vs 541-750', PRE, POST), ('Narrow 450-540 vs 541-640', (450, 540), (541, 640)),
                  ('Shift -50: 350-490 vs 491-700', (350, 490), (491, 700)), ('Shift +50: 450-590 vs 591-800', (450, 590), (591, 800)),
                  ('Recovery 541-750 vs 751-900', POST, REC)]:
    for k in ['cereal', 'anthro', 'ap_natural']:
        dd = []
        for _, d in S.groupby('datasetid'):
            x, nx = wmean(d, a); y, ny = wmean(d, b)
            if nx >= 2 and ny >= 2:
                dd.append(y[k] - x[k])
        dd = pd.Series(dd).dropna()
        sens.append(dict(test=lab, indicator=k, n=len(dd), median_change=dd.median(), pct_decline=100 * (dd < 0).mean(),
                         wilcoxon_p=stats.wilcoxon(dd).pvalue))
pd.DataFrame(sens).to_csv(f'{OUT}/table_sensitivity.csv', index=False)

# ---------- composite curves (site z-scores, 25-yr bins) ----------
Z = S[S.datasetid.isin(core.datasetid)].copy()
for k in IND:
    g = Z.groupby('datasetid')[k]
    Z[k + '_z'] = (Z[k] - g.transform('mean')) / g.transform('std').replace(0, np.nan)
Z['bin'] = (Z.age_ce // 25) * 25 + 12.5
SB = Z.groupby(['datasetid', 'region', 'bin'])[[k + '_z' for k in IND]].mean().reset_index()

def composite(df, col):
    out = []
    for b, d in df.groupby('bin'):
        v = d[col].dropna().values
        if len(v) < 5:
            continue
        bs = [rng.choice(v, len(v)).mean() for _ in range(500)]
        out.append((b, v.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5), len(v)))
    return pd.DataFrame(out, columns=['bin', 'mean', 'lo', 'hi', 'n'])

def shade(ax):
    ax.axvspan(536, 660, color='#9ecae1', alpha=.35, lw=0, label='LALIA cooling 536–660')
    ax.axvline(541, color='#b2182b', lw=1.5, ls='--', label='Plague arrives 541')
    ax.axvspan(541, 750, color='#fcbba1', alpha=.18, lw=0)

plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})

# Fig 1 map
fig, ax = plt.subplots(figsize=(8, 5.2))
cols = dict(zip(REG, ['#d95f02', '#e7298a', '#1b9e77', '#7570b3', '#66a61e']))
for r in REG:
    d = core[core.region == r]; ax.scatter(d.lon, d.lat, s=18, c=cols[r], label=f'{r} (n={len(d)})', edgecolor='k', lw=.3)
ax.set_xlim(-11, 50); ax.set_ylim(30, 57); ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
ax.set_title(f'Fig. 1  Neotoma pollen records used (n={len(core)}), ≥2 samples before and after 541 CE')
ax.legend(fontsize=8, loc='lower left'); ax.grid(alpha=.3)
try:
    import cartopy  # noqa
except Exception:
    pass
fig.tight_layout(); fig.savefig(f'{OUT}/fig1_site_map.png', dpi=200); plt.close()

# Fig 2 composites, all sites, 4 indicators + climate
fig, axs = plt.subplots(5, 1, figsize=(8, 11), sharex=True)
for ax, k in zip(axs[:4], ['cereal', 'anthro', 'ap_natural', 'richness']):
    c = composite(SB, k + '_z'); c = c[(c.bin >= 200) & (c.bin <= 1000)]
    ax.fill_between(c.bin, c.lo, c.hi, color='grey', alpha=.3); ax.plot(c.bin, c['mean'], 'k-o', ms=3)
    shade(ax); ax.axhline(0, color='grey', lw=.5); ax.set_ylabel('z-score'); ax.set_title(IND[k], fontsize=10, loc='left')
axs[0].legend(fontsize=8, loc='upper right')
cl = CLIM[(CLIM.year >= 200) & (CLIM.year <= 1000)].copy()
cl['t31'] = cl.tempJJA.rolling(31, center=True).mean()
axs[4].plot(cl.year, cl.tempJJA, color='#bbb', lw=.5); axs[4].plot(cl.year, cl.t31, color='#2166ac', lw=2)
shade(axs[4]); axs[4].set_ylabel('°C anomaly'); axs[4].set_title('Central European JJA temperature (Büntgen et al. 2011), 31-yr mean', fontsize=10, loc='left')
axs[4].set_xlabel('Year CE'); fig.suptitle('Fig. 2  Pan-European composite of land-use indicators vs climate (mean ± 95% bootstrap CI)', fontsize=11)
fig.tight_layout(); fig.savefig(f'{OUT}/fig2_composite_all.png', dpi=200); plt.close()

# Fig 3 regional composites, cereal + anthro
fig, axs = plt.subplots(len(REG), 2, figsize=(10, 12), sharex=True)
for i, r in enumerate(REG):
    for j, k in enumerate(['anthro', 'ap_natural']):
        ax = axs[i, j]; c = composite(SB[SB.region == r], k + '_z'); c = c[(c.bin >= 200) & (c.bin <= 1000)]
        if len(c):
            ax.fill_between(c.bin, c.lo, c.hi, color=cols[r], alpha=.25); ax.plot(c.bin, c['mean'], '-o', color=cols[r], ms=3)
        shade(ax); ax.axhline(0, color='grey', lw=.5)
        ax.set_title(f'{r} (n={core.region.eq(r).sum()}) — ' + ('anthropogenic indicators' if k == 'anthro' else 'natural tree pollen'), fontsize=9, loc='left')
for ax in axs[-1]:
    ax.set_xlabel('Year CE')
fig.suptitle('Fig. 3  Regional composites (z-scores, 25-yr bins, 95% CI)', fontsize=11)
fig.tight_layout(); fig.savefig(f'{OUT}/fig3_regional.png', dpi=200); plt.close()

# Fig 4 site-level change map (anthro)
fig, ax = plt.subplots(figsize=(8, 5.2))
d = core.dropna(subset=['anthro_pre', 'anthro_post']); ch = d.anthro_post - d.anthro_pre
v = np.nanpercentile(np.abs(ch), 90)
sc = ax.scatter(d.lon, d.lat, c=ch, cmap='RdBu', vmin=-v, vmax=v, s=26, edgecolor='k', lw=.3)
plt.colorbar(sc, label='Δ anthropogenic indicators (pp)\n541–750 minus 400–540 CE')
ax.set_xlim(-11, 50); ax.set_ylim(30, 57); ax.grid(alpha=.3); ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
ax.set_title('Fig. 4  Site-level change in land-use indicators (red = decline, blue = increase)', fontsize=10)
fig.tight_layout(); fig.savefig(f'{OUT}/fig4_change_map.png', dpi=200); plt.close()

# Fig 5 pandemic vs placebo change distributions by region
fig, ax = plt.subplots(figsize=(9, 4.5))
pos = 0; ticks = []
for r in ['All sites'] + REG:
    df = pl if r == 'All sites' else pl[pl.region == r]
    a = (df.anthro_pre - df.anthro_plc).dropna(); b = (df.anthro_post - df.anthro_pre).dropna()
    if len(b) < 3:
        continue
    bp = ax.boxplot([a, b], positions=[pos, pos + .8], widths=.6, patch_artist=True, showfliers=False)
    bp['boxes'][0].set_facecolor('#d9d9d9'); bp['boxes'][1].set_facecolor('#fc9272')
    ticks.append((pos + .4, f'{r}\n(n={len(b)})')); pos += 2.2
ax.axhline(0, color='k', lw=.6); ax.set_xticks([t[0] for t in ticks]); ax.set_xticklabels([t[1] for t in ticks], fontsize=8)
ax.set_ylabel('Δ anthropogenic indicators (pp)')
ax.set_title('Fig. 5  Background change (grey: 250–399→400–540) vs pandemic-era change (red: 400–540→541–750)', fontsize=10)
fig.tight_layout(); fig.savefig(f'{OUT}/fig5_placebo.png', dpi=200); plt.close()

# Fig 6 eastern Mediterranean arboriculture by site
e = core[core.region == 'E. Mediterranean & Anatolia'].copy(); e['d'] = e.arbor_post - e.arbor_pre; e = e.sort_values('d')
fig, ax = plt.subplots(figsize=(8, 4.6))
ax.barh(e.site + '  (' + e.arbor_pre.round(1).astype(str) + '%)', e.d, color=['#b2182b' if v < 0 else '#2166ac' for v in e.d])
ax.axvline(0, color='k', lw=.6)
ax.set_xlabel('Δ cultivated-tree pollen (Olea+Juglans+Castanea+Vitis), percentage points\n541–750 CE minus 400–540 CE   (bracket = pre-pandemic level)')
ax.set_title('Fig. 6  Eastern Mediterranean & Anatolia: change in arboriculture by site', fontsize=10, loc='left')
fig.tight_layout(); fig.savefig(f'{OUT}/fig6_emed_arbor.png', dpi=200); plt.close()

# summary json
summ = dict(n_samples=int(len(S)), n_datasets_total=int(S.datasetid.nunique()), n_core_sites=int(len(core)),
            regions=core.region.value_counts().to_dict(), median_age_unc=float(core.median_unc.median()),
            chron=S.chron.value_counts().to_dict())
json.dump(summ, open(f'{OUT}/summary.json', 'w'), indent=1, default=str)
pd.set_option('display.width', 200); pd.set_option('display.max_columns', 20)
print(json.dumps(summ, indent=1, default=str)); print(T.round(3).to_string()); print(P.round(3).to_string())
print(pd.read_csv(f'{OUT}/table_sensitivity.csv').round(3).to_string())
