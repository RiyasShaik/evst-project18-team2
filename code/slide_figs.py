"""Step 4: charts for the final presentation (presentation/charts), from the same data and definitions as the report.
Usage: slide_figs.py data/ tables/ presentation/charts/"""
import sys, os
import numpy as np, pandas as pd
from common import REG, EM, COL, PRE, POST, inwin, binc, LALIA_C, PLAGUE_C, land, plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

D, T, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
INK, PINE, RED, GOLD, MUTED = '#17261f', '#2b6a4e', '#a3342b', '#b07d1a', '#5b6b63'
plt.rcParams.update({'font.size': 15, 'font.family': 'DejaVu Sans', 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': MUTED, 'xtick.color': INK, 'ytick.color': INK, 'axes.labelcolor': INK, 'savefig.dpi': 170})
S = pd.read_csv(f'{D}/samples.csv')
G = np.load(f'{D}/hyde_grid.npz')
K = ['cereal', 'arbor', 'pastoral', 'anthro', 'ap_natural', 'richness']
W = S.groupby('siteid').agg(site=('site', 'first'), lon=('lon', 'first'), lat=('lat', 'first'), region=('region', 'first'))
for tag, w in dict(pre=PRE, post=POST).items():
    W['n_' + tag] = S[inwin(S.age_ce, w)].groupby('siteid').size()
W = W.fillna(0)
core = W[(W.n_pre >= 2) & (W.n_post >= 2)]
Z = S[S.siteid.isin(core.index)].copy()
for k in K:
    g = Z.groupby('siteid')[k]; Z[k] = (Z[k] - g.transform('mean')) / g.transform('std').replace(0, np.nan)
Z['bin'] = binc(Z.age_ce)
SB = Z.groupby(['siteid', 'region', 'bin'])[K].mean().reset_index()


def comp(sb, k, nmin=3):
    c = sb.groupby('bin')[k].agg(['mean', 'count', 'std']); c = c[(c['count'] >= nmin) & (c.index >= 200) & (c.index <= 1000)]
    return c.assign(se=c['std'] / np.sqrt(c['count']))


def shade(ax, legend=False):
    ax.axvspan(536, 660, color=LALIA_C, alpha=.45, lw=0, zorder=0)
    ax.axvspan(541, 750, ymin=.955, ymax=1, color=PLAGUE_C, alpha=.85, lw=0, zorder=5)
    ax.axvline(541, color=PLAGUE_C, lw=1.6, ls='--', zorder=1)
    ax.set_xlim(190, 1010)
    return [Patch(color=LALIA_C, alpha=.45, label='LALIA cooling 536–660'), Line2D([], [], color=PLAGUE_C, lw=6, label='Plague period 541–750')]


def band(ax, q, c, lab, lw=2.6):
    ax.fill_between(q.index, q['mean'] - 1.96 * q.se, q['mean'] + 1.96 * q.se, color=c, alpha=.15, lw=0)
    ax.plot(q.index, q['mean'], '-o', color=c, ms=4, lw=lw, label=lab)


def save(fig, name):
    fig.tight_layout(); fig.savefig(f'{OUT}/{name}.png', transparent=False, facecolor='white'); plt.close(fig)


# 1. site map
fig, ax = plt.subplots(figsize=(8.6, 6.2))
land(ax, G)
for r in REG:
    d = core[core.region == r]; ax.scatter(d.lon, d.lat, s=34, c=COL[r], edgecolor='k', lw=.4, zorder=3, label=f'{r} ({len(d)})')
ax.set_xlim(-11, 50); ax.set_ylim(30, 57); ax.set_aspect(1 / np.cos(np.radians(43))); ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values():
    s.set_visible(False)
ax.legend(loc='upper center', bbox_to_anchor=(.5, -.01), ncol=2, fontsize=13, frameon=False, handletextpad=.3, columnspacing=1)
save(fig, 'slide_map')

# 2. Europe-wide composites
fig, ax = plt.subplots(figsize=(11.5, 5.6))
h = shade(ax, True)
band(ax, comp(SB, 'anthro', 5), INK, 'Farming indicators (all anthropogenic)')
band(ax, comp(SB, 'ap_natural', 5), PINE, 'Natural tree & shrub pollen')
ax.axhline(0, color=MUTED, lw=.7); ax.set_ylabel('Site z-score (mean, 95% CI)'); ax.set_xlabel('Year CE')
h1, l1 = ax.get_legend_handles_labels()
ax.legend(h1 + h, l1 + [x.get_label() for x in h], loc='upper center', bbox_to_anchor=(.5, -.16), fontsize=12.5, frameon=False, ncol=2)
save(fig, 'slide_composite')

# 3. climate
B = pd.read_csv(f'{D}/buentgen.csv').set_index('year').tempJJA
P = pd.read_csv(f'{D}/pages2k_euromed.csv').set_index('year')
E = pd.read_csv(f'{D}/emed_climate.csv')
sm = lambda s: s.rolling(31, center=True).mean()
fig, axs = plt.subplots(1, 2, figsize=(13, 5.4))
ax = axs[0]; shade(ax)
ax.fill_between(P.index, sm(P.bhm_lo), sm(P.bhm_hi), color='grey', alpha=.18, lw=0, label='PAGES 2k 95% range')
ax.plot(B.index, sm(B), color='#2166ac', lw=2.4, label='Alpine tree rings')
ax.plot(P.index, sm(P.cps), color=INK, lw=2.4, label='PAGES 2k European mean')
ax.set_ylabel('Summer temperature anomaly, °C'); ax.set_xlabel('Year CE')
ax.legend(loc='upper center', bbox_to_anchor=(.5, -.17), fontsize=12, frameon=False, ncol=2)
ax.set_title('Europe: summer temperature (31-yr mean)', loc='left', fontsize=15)
ax = axs[1]; shade(ax)
for rec, col, lab in [('Kocain', '#8c510a', 'Kocain Cave, SW Turkey'), ('Soreq', '#01665e', 'Soreq Cave, Israel')]:
    v = E[(E.record == rec) & (E.age_ce >= 150) & (E.age_ce <= 1050)].set_index('age_ce').d18O
    z = -(v - v.mean()) / v.std()
    ax.plot(z.index, z, 'o', color=col, ms=3, alpha=.35)
    zb = z.groupby(binc(z.index)).mean().rolling(2, min_periods=1).mean()
    ax.plot(zb.index, zb, color=col, lw=2.6, label=lab)
ax.axhline(0, color=MUTED, lw=.7); ax.set_ylabel('δ¹⁸O z-score, inverted (up = wetter)'); ax.set_xlabel('Year CE')
ax.legend(loc='upper center', bbox_to_anchor=(.5, -.17), fontsize=12, frameon=False, ncol=2)
ax.set_title('E. Mediterranean: moisture (dots: measurements)', loc='left', fontsize=15)
save(fig, 'slide_climate')

# 4. regression
R = pd.read_csv(f'{T}/table_regression.csv')
inds = [('anthro', 'All farming'), ('cereal', 'Cereal'), ('pastoral', 'Pastoral'), ('ap_natural', 'Natural trees')]
fig, axs = plt.subplots(1, 2, figsize=(11.5, 5.4), gridspec_kw=dict(width_ratios=[1.25, 1]))
ax = axs[0]
for j, (t, lab, c) in enumerate([('T_eu_z', 'Temperature, +1 SD', '#2166ac'), ('plague_first', 'Plague, 550–650 (inside LALIA)', '#762a83'),
                                 ('plague_second', 'Plague, 650–750 (after LALIA)', '#e08214')]):
    r = R[(R.model == 'M2') & (R.scope == 'All sites') & (R.term == t)].set_index('indicator').loc[[k for k, _ in inds]]
    y = np.arange(len(inds))[::-1] + (1 - j) * .24
    ax.errorbar(r.coef, y, xerr=[r.coef - r.ci_lo, r.ci_hi - r.coef], fmt='o', color=c, ms=9, capsize=4, lw=2.2, label=lab)
ax.axvline(0, color=INK, lw=1); ax.set_yticks(np.arange(len(inds))[::-1]); ax.set_yticklabels([l for _, l in inds]); ax.set_ylim(-.5, len(inds) - .5)
ax.set_xlabel('Effect vs 300–900 CE trend (z, 95% CI)'); ax.legend(loc='upper center', bbox_to_anchor=(.45, -.16), fontsize=12, frameon=False, ncol=2)
ax.set_title(f"All sites (model M2, {int(R[(R.model == 'M2') & (R.scope == 'All sites') & (R.indicator == 'anthro')].n_sites.iloc[0])} sites)", loc='left', fontsize=15)
ax = axs[1]
regs = ['All sites'] + REG
r = R[(R.model == 'M2') & (R.term == 'plague_first') & (R.indicator == 'anthro')].set_index('scope').loc[regs]
y = np.arange(len(regs))[::-1]
ax.errorbar(r.coef, y, xerr=[r.coef - r.ci_lo, r.ci_hi - r.coef], fmt='o', color='#762a83', ms=9, capsize=4, lw=2.2)
for yy, (s_, rr) in zip(y, r.iterrows()):
    if rr.p < .05:
        ax.text(rr.ci_hi + .02, yy, '*', fontsize=20, va='center', color='#762a83')
ax.axvline(0, color=INK, lw=1); ax.set_yticks(y); ax.set_yticklabels([{EM: 'E. Mediterranean'}.get(s, s) for s in regs])
ax.set_xlabel('Farming in 550–650 vs trend (z)'); ax.set_title('By region', loc='left', fontsize=15)
save(fig, 'slide_regression')

# 5. Eastern Mediterranean timing
fig, ax = plt.subplots(figsize=(11.5, 5.4))
h = shade(ax, True)
e = SB[SB.region == EM]
band(ax, comp(e, 'arbor'), RED, 'Cultivated trees (olive, walnut, chestnut, vine)')
band(ax, comp(e, 'anthro'), INK, 'All farming indicators', 2.2)
ax.axhline(0, color=MUTED, lw=.7); ax.set_ylabel(f'Site z-score, {int((core.region == EM).sum())} sites'); ax.set_xlabel('Year CE')
a2 = ax.twinx(); a2.spines['right'].set_visible(True)
v = E[(E.record == 'Kocain') & (E.age_ce >= 150) & (E.age_ce <= 1050)].set_index('age_ce').d18O
zb = (-(v - v.mean()) / v.std()).groupby(binc(v.index)).mean().rolling(2, min_periods=1).mean()
a2.plot(zb.index, zb, color='#8c510a', lw=2.2, ls='--', label='Kocain Cave moisture (right axis)')
a2.set_ylabel('Kocain δ¹⁸O z, up = wetter', color='#8c510a'); a2.tick_params(axis='y', colors='#8c510a')
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = a2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc='upper center', bbox_to_anchor=(.5, -.16), fontsize=12, frameon=False, ncol=3)
save(fig, 'slide_emed_timing')

# 6. Eastern Mediterranean sites
re_ = W[(W.n_pre >= 1) & (W.n_post >= 1) & (W.region == EM)]
mid = set(pd.read_csv(f'{T}/mideval/site_window_means.csv').query('region == @EM').datasetid)
mid_s = set(S[S.datasetid.isin(mid)].siteid)
fig, ax = plt.subplots(figsize=(7.4, 4.9))
land(ax, G)
cats = [(re_[~re_.index.isin(core.index)], dict(s=60, facecolor='white', edgecolor='#d95f02', lw=1.8), 'relaxed rule only'),
        (core[(core.region == EM) & core.index.isin(mid_s)], dict(s=90, c='#4d4d4d', edgecolor='k', lw=.5), 'mid-term core sites'),
        (core[(core.region == EM) & ~core.index.isin(mid_s)], dict(s=90, c='#d95f02', edgecolor='k', lw=.5), 'added core sites')]
for d, kw, lab in cats:
    ax.scatter(d.lon, d.lat, zorder=3, label=f'{lab} ({len(d)})', **kw)
ax.set_xlim(17, 51); ax.set_ylim(30, 44.5); ax.set_aspect(1 / np.cos(np.radians(37))); ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values():
    s.set_visible(False)
ax.legend(loc='lower left', fontsize=14, frameon=True, framealpha=.9)
save(fig, 'slide_emed_map')

# 7. HYDE trajectory
H = pd.read_csv(f'{D}/hyde_sites.csv'); H = H[H.datasetid.isin(core.index)]
h_ = H.groupby('year')[['crop_50', 'graz_50', 'popd_50']].mean(); h_ = 100 * h_ / h_.loc[500]
fig, ax = plt.subplots(figsize=(7.8, 5.6))
shade(ax)
ax.plot(h_.index, h_.crop_50, '-o', color='#8c510a', lw=2.8, ms=6, label='HYDE cropland')
ax.plot(h_.index, h_.popd_50, ':o', color='#8c510a', lw=2.2, ms=5, label='HYDE population')
ax.set_ylabel('HYDE around the sites, % of 500 CE'); ax.set_xlabel('Year CE'); ax.set_ylim(80, 145)
a2 = ax.twinx(); a2.spines['right'].set_visible(True)
q = comp(SB, 'anthro', 5); a2.plot(q.index, q['mean'].rolling(3, center=True, min_periods=1).mean(), color=INK, lw=2.8, label='Pollen: farming indicators')
a2.set_ylabel('Pollen composite, z-score')
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = a2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc='upper center', bbox_to_anchor=(.5, -.15), ncol=2, fontsize=13, frameon=False)
save(fig, 'slide_hyde')
# 8. change map for the regional slide
W2 = pd.read_csv(f'{T}/site_window_means.csv')
ch = W2.anthro_post - W2.anthro_pre; v = np.nanpercentile(np.abs(ch), 90)
fig, ax = plt.subplots(figsize=(6.6, 6.4))
land(ax, G)
sc = ax.scatter(W2.lon, W2.lat, c=ch, cmap='RdBu', vmin=-v, vmax=v, s=40, edgecolor='k', lw=.35, zorder=3)
ax.set_xlim(-11, 50); ax.set_ylim(30, 57); ax.set_aspect(1 / np.cos(np.radians(43))); ax.set_xticks([]); ax.set_yticks([])
for s_ in ax.spines.values():
    s_.set_visible(False)
cb = fig.colorbar(sc, ax=ax, orientation='horizontal', fraction=.05, pad=.03, extend='both')
cb.set_label('Change in farming indicators, pp\n(541–750 minus 400–540; blue = rise)', fontsize=14)
save(fig, 'slide_change_map')
print('slide charts written to', OUT)
