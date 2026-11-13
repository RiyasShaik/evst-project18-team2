"""Step 3: final-evaluation analyses. Regional climate (Fig. 6), fixed-effects regression (Fig. 7), the expanded
Eastern Mediterranean sample (Fig. 8), HYDE 3.2 against the pollen (Fig. 10) and the Monte Carlo on age-model
uncertainty (Fig. 11); every other number quoted in the report goes to tables/text_numbers.json.

Usage: final.py data/ tables/mideval/ tables/ figures/ [n_monte_carlo]"""
import sys, os, json
import numpy as np, pandas as pd
from scipy import stats, sparse
from common import IND, REG, EM, COL, PRE, POST, PLACEBO, inwin, binc, shade, style, land, plt

D, MID, OT, OF = sys.argv[1:5]
NMC = int(sys.argv[5]) if len(sys.argv) > 5 else 1000
for d in (OT, OF):
    os.makedirs(d, exist_ok=True)
rng = np.random.default_rng(42)
style()
K = list(IND)
S = pd.read_csv(f'{D}/samples.csv')
G = np.load(f'{D}/hyde_grid.npz')
TXT = {}


def scopes(df):
    return [('All sites', df)] + [(r, df[df.region == r]) for r in REG]


def wilcox(d):
    return stats.wilcoxon(d).pvalue if len(d) >= 5 and (d != 0).any() else np.nan


def test(df, k):
    d = (df[f'{k}_post'] - df[f'{k}_pre']).dropna()
    if len(d) < 5:
        return dict(n=len(d))
    boot = np.median(rng.choice(d.values, (2000, len(d))), axis=1)
    return dict(n=len(d), median_change=np.median(d), ci_lo=np.percentile(boot, 2.5), ci_hi=np.percentile(boot, 97.5),
                pct_sites_increase=100 * (d > 0).mean(), pct_sites_decline=100 * (d < 0).mean(), wilcoxon_p=wilcox(d))


# ---------- sites, core and relaxed samples, site z-scores in 25-yr bins ----------
W = S.groupby('siteid').agg(site=('site', 'first'), lon=('lon', 'first'), lat=('lat', 'first'), region=('region', 'first'))
for tag, w in dict(pre=PRE, post=POST, plc=PLACEBO).items():
    x = S[inwin(S.age_ce, w)].groupby('siteid')
    W = W.join(x[K].mean().add_suffix('_' + tag)).join(x.size().rename('n_' + tag))
W = W.fillna({'n_pre': 0, 'n_post': 0, 'n_plc': 0})
core = W[(W.n_pre >= 2) & (W.n_post >= 2)]
relaxed = W[(W.n_pre >= 1) & (W.n_post >= 1)]

Z = S[S.siteid.isin(core.index)].copy()
for k in K:
    g = Z.groupby('siteid')[k]
    Z[k] = (Z[k] - g.transform('mean')) / g.transform('std').replace(0, np.nan)
Z['bin'] = binc(Z.age_ce)
SB = Z.groupby(['siteid', 'region', 'bin'])[K].mean().reset_index()


def comp(sb, k, nmin=3):
    c = sb.groupby('bin')[k].agg(['mean', 'count', 'std'])
    c = c[(c['count'] >= nmin) & (c.index >= 200) & (c.index <= 1000)]
    return c.assign(se=c['std'] / np.sqrt(c['count']))


# ---------- 1. regional climate ----------
B = pd.read_csv(f'{D}/buentgen.csv'); P2 = pd.read_csv(f'{D}/pages2k_euromed.csv'); E = pd.read_csv(f'{D}/emed_climate.csv')
Ko, So = E[E.record == 'Kocain'], E[E.record == 'Soreq']


def binmean(t, v):
    return pd.Series(np.asarray(v, float), index=binc(t)).groupby(level=0).mean()


C = pd.DataFrame({'T_alps': binmean(B.year, B.tempJJA), 'T_eu': binmean(P2.year, P2.cps), 'T_eu_bhm': binmean(P2.year, P2.bhm),
                  'kocain_d18O': binmean(Ko.age_ce, Ko.d18O), 'kocain_d13C': binmean(Ko.age_ce, Ko.d13C), 'soreq_d18O': binmean(So.age_ce, So.d18O)})
C = C.loc[112.5:1087.5]
C_obs = C.notna()                                   # bins with at least one measurement
C = C.interpolate(limit_area='inside')              # gaps inside a record are filled linearly (Soreq has long gaps)


def corr_eff(x, y):
    """Pearson r with p from the effective sample size of two autocorrelated series (Bretherton et al. 1999)."""
    n = len(x); r = np.corrcoef(x, y)[0, 1]
    a1, a2 = [max(np.corrcoef(v[:-1], v[1:])[0, 1], 0) for v in (np.asarray(x), np.asarray(y))]
    ne = max(3, n * (1 - a1 * a2) / (1 + a1 * a2))
    return r, 2 * stats.t.sf(abs(r) * np.sqrt((ne - 2) / (1 - r ** 2)), ne - 2), ne


def detrend(v):
    t = v.index.values
    return v - np.polyval(np.polyfit(t, v.values, 1), t)


crow = []
for lo, hi in ((200, 1000), (300, 900)):
    for scope, sb in [('All sites', SB), ('All except E. Med', SB[SB.region != EM])] + [(r, SB[SB.region == r]) for r in REG]:
        for k in K:
            y = comp(sb, k)['mean']; y = y[(y.index > lo) & (y.index < hi)]
            for c in C:
                for lag in (0, 1):
                    j = pd.concat([y, C[c].shift(lag)], axis=1).dropna()
                    if len(j) >= 10:
                        r, p, ne = corr_eff(j.iloc[:, 0], j.iloc[:, 1])
                        rd, pd_, _ = corr_eff(detrend(j.iloc[:, 0]), detrend(j.iloc[:, 1]))
                        crow.append(dict(window=f'{lo}-{hi}', scope=scope, indicator=k, climate=c, lag_yr=25 * lag, n_bins=len(j),
                                         n_bins_measured=int(C_obs.loc[j.index, c].sum()), r=r, n_eff=ne, p_eff=p, r_detrended=rd, p_detrended=pd_))
CT = pd.DataFrame(crow)
CT.to_csv(f'{OT}/table_climate_correlation.csv', index=False)

per = lambda s, a, b: s[(s.index >= a) & (s.index < b)].mean()
b_, p_ = B.set_index('year').tempJJA, P2.set_index('year')
TXT['cooling_400_535_to_536_660_degC'] = {n: round(per(s, 400, 536) - per(s, 536, 661), 3) for n, s in
                                         [('alpine', b_), ('pages2k_cps', p_.cps), ('pages2k_bhm', p_.bhm)]}
TXT['mean_anomaly_degC'] = {n: {'300-399': round(per(s, 300, 400), 3), '536-660': round(per(s, 536, 661), 3)} for n, s in
                            [('alpine', b_), ('pages2k_cps', p_.cps), ('pages2k_bhm', p_.bhm)]}
t31 = b_.rolling(31, center=True).mean()
y0, y1 = t31.loc[500:540].idxmax(), t31.loc[540:580].idxmin()
TXT['alpine_31yr_fall'] = dict(from_year=int(y0), to_year=int(y1), degC=round(t31[y0] - t31[y1], 2))
TXT['pages2k_bhm_95pct_halfwidth_300_900_degC'] = round(float(((p_.bhm_hi - p_.bhm_lo) / 2).loc[300:900].median()), 2)
TXT['kocain'] = dict(n_200_1000=int(Ko.age_ce.between(200, 1000).sum()),
                     mean_spacing_yr=round(float(np.diff(Ko[Ko.age_ce.between(200, 1000)].age_ce).mean()), 1),
                     d18O_330_460=round(float(Ko[Ko.age_ce.between(330, 460)].d18O.mean()), 2),
                     d18O_541_660=round(float(Ko[Ko.age_ce.between(541, 660)].d18O.mean()), 2))
TXT['soreq'] = dict(n_200_1000=int(So.age_ce.between(200, 1000).sum()), n_330_460=int(So.age_ce.between(330, 460).sum()),
                    n_541_660=int(So.age_ce.between(541, 660).sum()),
                    d18O_330_460=round(float(So[So.age_ce.between(330, 460)].d18O.mean()), 2),
                    d18O_541_660=round(float(So[So.age_ce.between(541, 660)].d18O.mean()), 2),
                    bins_measured_200_1000=int(C_obs.loc[200:1000, 'soreq_d18O'].sum()), bins_200_1000=int(len(C_obs.loc[200:1000])))

fig, axs = plt.subplots(4, 1, figsize=(9, 14), sharex=True)
sm = lambda s: s.rolling(31, center=True).mean()
ax = axs[0]
ax.fill_between(p_.index, sm(p_.bhm_lo), sm(p_.bhm_hi), color='grey', alpha=.18, lw=0, label='PAGES 2k BHM, 95% range')
ax.plot(b_.index, sm(b_), color='#2166ac', lw=1.8, label='Central Europe (Alpine tree rings; Büntgen et al. 2011)')
ax.plot(p_.index, sm(p_.cps), color='k', lw=1.8, label='European mean, PAGES 2k CPS')
ax.plot(p_.index, sm(p_.bhm), color='k', lw=1, ls='--', label='European mean, PAGES 2k BHM')
h = shade(ax, legend=True); ax.set_ylabel('°C anomaly (31-yr mean)')
ax.legend(handles=ax.get_legend_handles_labels()[0] + h, fontsize=7.5, loc='upper center', bbox_to_anchor=(.5, -.04), ncol=3, frameon=False)
ax.set_title('a  Summer (June–August) temperature', loc='left', fontsize=10)
ax = axs[1]
for nm, v, col in [('Kocain δ¹⁸O', Ko.set_index('age_ce').d18O, '#8c510a'), ('Kocain δ¹³C', Ko.set_index('age_ce').d13C, '#dfc27d'),
                   ('Soreq δ¹⁸O', So.set_index('age_ce').d18O, '#01665e')]:
    w = v[(v.index >= 150) & (v.index <= 1050)]; z = -(w - w.mean()) / w.std()
    ax.plot(z.index, z, 'o', color=col, ms=2.2, alpha=.45)
    zb = binmean(z.index, z); ax.plot(zb.index, zb.rolling(2, min_periods=1).mean(), color=col, lw=2, label=nm + ', 50-yr mean')
shade(ax); ax.axhline(0, color='grey', lw=.5); ax.set_ylabel('z-score, inverted\n(up = wetter)')
ax.legend(fontsize=7.5, loc='upper center', bbox_to_anchor=(.5, -.04), ncol=3, frameon=False)
ax.set_title('b  Eastern Mediterranean speleothems: Kocain Cave (SW Turkey) and Soreq Cave (Israel); dots = measurements', loc='left', fontsize=10)
n_out = int((core.region != EM).sum()); n_em = int((core.region == EM).sum())
for ax, sb, title, ks in [(axs[2], SB[SB.region != EM], f'c  All regions except the E. Mediterranean ({n_out} sites)', ['anthro', 'ap_natural', 'cereal']),
                          (axs[3], SB[SB.region == EM], f'd  E. Mediterranean & Anatolia ({n_em} sites)', ['anthro', 'ap_natural', 'arbor'])]:
    for k, c in zip(ks, ['k', '#1b7837', '#b8860b' if ks[2] == 'cereal' else '#b2182b']):
        q = comp(sb, k); ax.fill_between(q.index, q['mean'] - 1.96 * q.se, q['mean'] + 1.96 * q.se, color=c, alpha=.12, lw=0)
        ax.plot(q.index, q['mean'], '-o', color=c, ms=2.5, lw=1.3, label=IND[k])
    shade(ax); ax.axhline(0, color='grey', lw=.5); ax.set_ylabel('z-score')
    ax.legend(fontsize=7.5, loc='upper center', bbox_to_anchor=(.5, -.04 if ax is axs[2] else -.16), ncol=3, frameon=False); ax.set_title(title + ': pollen composites, mean and 95% interval', loc='left', fontsize=10)
axs[3].set_xlabel('Year CE'); axs[3].set_xlim(190, 1010)
fig.tight_layout(); fig.savefig(f'{OF}/fig06_climate.png'); plt.close()

# ---------- 2. fixed-effects regression ----------
CB = C.loc[200:1000].copy()
REF = CB.loc[300:900]
for c in ('T_eu', 'T_alps'):
    CB[c + '_z'] = (CB[c] - REF[c].mean()) / REF[c].std()
CB['T_lag'] = ((C['T_eu'] - REF['T_eu'].mean()) / REF['T_eu'].std()).shift(1).loc[200:1000]
CB['moist'] = -(CB.kocain_d18O - REF.kocain_d18O.mean()) / REF.kocain_d18O.std()
c_ = CB.index.values      # bin centres; the plague period is the eight bins 550-750 CE
CB['plague'] = ((c_ > 550) & (c_ < 750)).astype(float)
CB['plague_first'] = ((c_ > 550) & (c_ < 650)).astype(float)
CB['plague_second'] = ((c_ > 650) & (c_ < 750)).astype(float)
CB['trend'] = (c_ - 600) / 100
CB['trend2'] = CB.trend ** 2
RB_wide = SB.merge(CB, left_on='bin', right_index=True)
RB = RB_wide[(RB_wide.bin > 300) & (RB_wide.bin < 900)]


def fe_ols(d, y, xs):
    """Site fixed effects (within transform); SEs two-way clustered by site and 25-yr bin (Cameron, Gelbach & Miller 2011),
    never smaller than either one-way clustered SE; t distribution with min(sites, bins) - 1 degrees of freedom."""
    d = d.dropna(subset=[y] + xs)
    d = d[d.groupby('siteid')[y].transform('size') >= 3]
    if d.siteid.nunique() < 5:
        return None
    g = d.groupby('siteid')
    Y = (d[y] - g[y].transform('mean')).values
    X = (d[xs] - g[xs].transform('mean')).values
    A = np.linalg.pinv(X.T @ X); b = A @ X.T @ Y; e = Y - X @ b
    V, n = {}, {}
    for lab, key in (('site', d.siteid.values), ('bin', d['bin'].values), ('obs', np.arange(len(d)))):
        u = pd.DataFrame(X * e[:, None]).groupby(key).sum().values; n[lab] = len(u)
        V[lab] = n[lab] / (n[lab] - 1) * A @ (u.T @ u) @ A
    v = np.maximum.reduce([np.diag(V['site'] + V['bin'] - V['obs']), np.diag(V['site']), np.diag(V['bin'])])
    se = np.sqrt(v); dof = min(n['site'], n['bin']) - 1
    return dict(coef=b, se=se, p=2 * stats.t.sf(np.abs(b / se), dof), dof=dof, n_obs=len(d), n_sites=n['site'], n_bins=n['bin'])


SPEC = {'M1': ('temperature + plague period + trend', ['T_eu_z', 'plague', 'trend']),
        'M2': ('plague period split at 650 CE', ['T_eu_z', 'plague_first', 'plague_second', 'trend']),
        'M3': ('Alpine temperature', ['T_alps_z', 'plague', 'trend']),
        'M4': ('+ temperature lagged 25 yr', ['T_eu_z', 'T_lag', 'plague', 'trend']),
        'M5': ('quadratic trend', ['T_eu_z', 'plague', 'trend', 'trend2']),
        'M6': ('no climate term', ['plague', 'trend']),
        'M7': ('+ Kocain moisture, E. Mediterranean sites', ['T_eu_z', 'moist', 'plague', 'trend']),
        'M8': ('as M1, 200-1000 CE', ['T_eu_z', 'plague', 'trend'])}
rrow = []
for m, (desc, xs) in SPEC.items():
    sc = [(EM, RB[RB.region == EM])] if m == 'M7' else scopes(RB) if m in ('M1', 'M2') else [('All sites', RB_wide)] if m == 'M8' else [('All sites', RB)]
    for scope, df in sc:
        for k in K:
            f = fe_ols(df, k, xs)
            if f is None:
                continue
            tq = stats.t.ppf(.975, f['dof'])
            for i, x in enumerate(xs):
                rrow.append(dict(model=m, description=desc, scope=scope, indicator=k, term=x, coef=f['coef'][i], se=f['se'][i], p=f['p'][i],
                                 ci_lo=f['coef'][i] - tq * f['se'][i], ci_hi=f['coef'][i] + tq * f['se'][i],
                                 n_obs=f['n_obs'], n_sites=f['n_sites'], n_bins=f['n_bins']))
RT = pd.DataFrame(rrow)
RT.to_csv(f'{OT}/table_regression.csv', index=False)
TXT['temperature_sd_degC_300_900'] = round(float(REF.T_eu.std()), 3)
TXT['corr_temperature_plague_dummy'] = round(float(np.corrcoef(CB.loc[300:900].T_eu_z, CB.loc[300:900].plague)[0, 1]), 2)
TXT['n_regression_coefficients'] = int(len(RT))

fig, axs = plt.subplots(1, 3, figsize=(16, 5.6), gridspec_kw=dict(width_ratios=[1, 1, 1.25]))
yk = K[::-1]
for ax, m, terms, title in [(axs[0], 'M1', [('T_eu_z', '#2166ac', 'Temperature, +1 SD'), ('plague', '#b2182b', 'Plague period, 550–750 CE')],
                             'a  All sites (M1): temperature and plague period'),
                            (axs[1], 'M2', [('plague_first', '#762a83', 'First century, 550–650 CE'), ('plague_second', '#e08214', 'Second century, 650–750 CE')],
                             'b  All sites (M2): plague period in two halves')]:
    for j, (t, c, lab) in enumerate(terms):
        r = RT[(RT.model == m) & (RT.scope == 'All sites') & (RT.term == t)].set_index('indicator').reindex(yk)
        yy = np.arange(len(yk)) + (.14 if j == 0 else -.14)
        ax.errorbar(r.coef, yy, xerr=[r.coef - r.ci_lo, r.ci_hi - r.coef], fmt='o', color=c, ms=5, capsize=2, label=lab)
        for v, yv, p in zip(r.ci_hi, yy, r.p):
            if p < .05:
                ax.text(v + .006, yv, '*', va='center', fontsize=12, color=c)
    ax.axvline(0, color='k', lw=.6); ax.set_yticks(range(len(yk))); ax.set_yticklabels([IND[k] for k in yk]); ax.set_ylim(-1.5, len(yk) - .5)
    ax.set_xlabel('Effect, site z-score units (95% CI)'); ax.legend(fontsize=8, loc='lower left', frameon=False); ax.set_title(title, loc='left', fontsize=10)
ax = axs[2]
ks = ['anthro', 'cereal', 'pastoral', 'ap_natural']
for j, k in enumerate(ks):
    r = RT[(RT.model == 'M2') & (RT.term == 'plague_first') & (RT.indicator == k)].set_index('scope').reindex(['All sites'] + REG[::-1])
    yy = np.arange(len(r)) + (1.5 - j) * .18
    ax.errorbar(r.coef, yy, xerr=[r.coef - r.ci_lo, r.ci_hi - r.coef], fmt='os^D'[j], color=['k', '#b8860b', '#7570b3', '#1b7837'][j], ms=4, capsize=2, label=IND[k])
ax.axvline(0, color='k', lw=.6); ax.set_yticks(range(len(REG) + 1)); ax.set_yticklabels(['All sites'] + REG[::-1])
lim = 1.05 * np.nanmax(np.abs(RT[(RT.model == 'M2') & (RT.term == 'plague_first') & RT.indicator.isin(ks)][['ci_lo', 'ci_hi']].values))
ax.set_xlim(-lim, lim); ax.set_ylim(-1.5, len(REG) + .5)
ax.set_xlabel('First-century effect, 550–650 CE (z units, 95% CI)'); ax.legend(fontsize=8, loc='lower right', ncol=2, frameon=False)
ax.set_title('c  M2 by region: 550–650 CE relative to trend', loc='left', fontsize=10)
fig.tight_layout(); fig.savefig(f'{OF}/fig07_regression.png'); plt.close()

# ---------- 3. expanded Eastern Mediterranean sample ----------
mid = pd.read_csv(f'{MID}/site_window_means.csv')
midT = pd.read_csv(f'{MID}/table_pre_vs_post.csv')
mid_ids = set(mid[mid.region == EM].datasetid)
mid_em = core[core.index.isin(S[S.datasetid.isin(mid_ids)].siteid.unique())]
EV = [('Mid-term, as reported (13)', None), (f'Mid-term sites, final data ({len(mid_em)})', mid_em),
      (f"Core, ≥2 samples per window ({(core.region == EM).sum()})", core[core.region == EM]),
      (f"Relaxed, ≥1 sample per window ({(relaxed.region == EM).sum()})", relaxed[relaxed.region == EM])]
erow = []
for lab, df in EV:
    for k in K:
        t = midT[(midT.scope == EM) & (midT.indicator == k)].iloc[0].drop(['scope', 'indicator']).to_dict() if df is None else test(df, k)
        erow.append(dict(sample=lab, indicator=k, **t))
ET = pd.DataFrame(erow)
ET.to_csv(f'{OT}/table_emed_expansion.csv', index=False)


def wilson(p, n, z=1.96):
    c = (p + z * z / (2 * n)) / (1 + z * z / n); h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


fig, axs = plt.subplots(1, 2, figsize=(15, 6), gridspec_kw=dict(width_ratios=[1.2, 1]))
ax = axs[0]; land(ax, G)
re_ = relaxed[relaxed.region == EM]
added = core[(core.region == EM) & ~core.index.isin(mid_em.index)]
for d, kw in [(re_[~re_.index.isin(core.index)], dict(s=34, facecolor='white', edgecolor='#d95f02', lw=1.3, label=f'relaxed rule only ({(~re_.index.isin(core.index)).sum()})')),
              (mid_em, dict(s=48, c='#4d4d4d', edgecolor='k', lw=.4, label=f'mid-term core sites ({len(mid_em)})')),
              (added, dict(s=48, c='#d95f02', edgecolor='k', lw=.4, label=f'added core sites ({len(added)})'))]:
    ax.scatter(d.lon, d.lat, zorder=3, **kw)
added = added.sort_values(['lat'], ascending=False)
cluster = added[(added.lon < 26) & (added.lat > 41.4)].sort_values('lon')      # the Rila-Rhodope lakes, a few km apart
xs_ = np.linspace(18.3, 26.5, len(cluster))
key = []
for i, (sid, r) in enumerate(added.iterrows(), 1):
    key.append(f'{i}  {r.site}')
    if sid in cluster.index:
        x0 = xs_[list(cluster.index).index(sid)]
        ax.annotate(str(i), (r.lon, r.lat), xytext=(x0, 43.75), textcoords='data', fontsize=8, ha='center', va='center', zorder=4,
                    fontweight='bold', arrowprops=dict(arrowstyle='-', color='#555', lw=.6),
                    bbox=dict(boxstyle='circle,pad=.2', fc='white', ec='#d95f02', lw=.8))
    else:
        ax.annotate(str(i), (r.lon, r.lat), xytext=(7, 6), textcoords='offset points', fontsize=8, fontweight='bold', zorder=4,
                    bbox=dict(boxstyle='circle,pad=.2', fc='white', ec='#d95f02', lw=.8))
half = (len(key) + 1) // 2
ax.text(0, -.13, 'Added core sites:   ' + '    '.join(key[:half]) + '\n' + ' ' * 34 + '    '.join(key[half:]), transform=ax.transAxes,
        ha='left', va='top', fontsize=7.5)
ax.set_xlim(17, 51); ax.set_ylim(30, 44.5); ax.set_aspect(1 / np.cos(np.radians(37)))
ax.legend(fontsize=8, loc='lower left', frameon=True); ax.set_xlabel('Longitude (°E)'); ax.set_ylabel('Latitude (°N)')
ax.set_title('a  Eastern Mediterranean & Anatolia records', loc='left', fontsize=10)
ax = axs[1]
for j, (lab, df) in enumerate(EV[1:]):
    r = ET[ET['sample'] == lab].set_index('indicator').loc[K[::-1]]
    p = r.pct_sites_decline / 100; lo, hi = wilson(p, r.n)
    yy = np.arange(len(r)) + (1 - j) * .25
    ax.errorbar(100 * p, yy, xerr=[100 * (p - lo), 100 * (hi - p)], fmt='o', ms=5, capsize=2, color=['#4d4d4d', '#d95f02', '#fdae6b'][j], label=lab)
ax.axvline(50, color='k', lw=.6, ls=':'); ax.set_xlim(0, 100); ax.set_ylim(-1.6, len(K) - .5)
ax.set_yticks(range(len(K))); ax.set_yticklabels([IND[k] for k in K[::-1]])
ax.set_xlabel('% of sites lower in 541–750 than in 400–540 CE (95% Wilson interval)'); ax.legend(fontsize=8, loc='lower left', frameon=False)
ax.set_title('b  Share of sites declining, by sample', loc='left', fontsize=10)
fig.tight_layout(); fig.savefig(f'{OF}/fig08_emed_sample.png'); plt.close()

# ---------- 4. HYDE 3.2 against the pollen ----------
H = pd.read_csv(f'{D}/hyde_sites.csv')
H = H[H.datasetid.isin(core.index)].rename(columns={'datasetid': 'siteid'}).sort_values(['siteid', 'year'])   # siteid = a record id
for k in (25, 50, 100):
    H[f'lu_{k}'] = H[f'crop_{k}'] + H[f'graz_{k}']
HC = [c for c in H if c not in ('siteid', 'year')]


def hwin(g, w):   # window mean of HYDE, linearly interpolated between its 100-yr time slices
    t = np.arange(w[0], w[1] + 1)
    return {c: np.interp(t, g.year, g[c]).mean() for c in HC}


HV = core.join(pd.DataFrame({s: {**{c + '_pre': v for c, v in hwin(g, PRE).items()}, **{c + '_post': v for c, v in hwin(g, POST).items()}}
                             for s, g in H.groupby('siteid')}).T)
for c in ('crop_50', 'graz_50', 'lu_50', 'popd_50'):
    HV['d_' + c] = 100 * (HV[c + '_post'] / HV[c + '_pre'] - 1)
for k in K:
    HV['d_' + k] = HV[k + '_post'] - HV[k + '_pre']


def agree(a, b):
    m = (a != 0) & (b != 0) & a.notna() & b.notna()
    return 100 * (np.sign(a[m]) == np.sign(b[m])).mean()


hrow = []
for scope, df in scopes(HV):
    for k in (25, 50, 100):
        for lab, h, p in [('cropland vs cereal', f'crop_{k}', 'cereal'), ('grazing vs pastoral', f'graz_{k}', 'pastoral'),
                          ('cropland+grazing vs all anthropogenic', f'lu_{k}', 'anthro'), ('cropland+grazing vs natural trees', f'lu_{k}', 'ap_natural')]:
            x = df[[h + '_pre', p + '_pre']].dropna()
            if len(x) >= 8:
                rho, pv = stats.spearmanr(x.iloc[:, 0], x.iloc[:, 1])
                hrow.append(dict(test='spatial 400-540 CE', scope=scope, radius_km=k, comparison=lab, n=len(x), spearman_rho=rho, p=pv))
    rc, pc = stats.spearmanr(df.d_crop_50, df.d_cereal, nan_policy='omit')
    rg, pg = stats.spearmanr(df.d_graz_50, df.d_pastoral, nan_policy='omit')
    hrow.append(dict(test='change 400-540 -> 541-750', scope=scope, radius_km=50, n=len(df),
                     hyde_cropland_pct=df.d_crop_50.median(), hyde_grazing_pct=df.d_graz_50.median(), hyde_population_pct=df.d_popd_50.median(),
                     pct_sites_hyde_cropland_down=100 * (df.d_crop_50 < 0).mean(), pct_sites_cereal_down=100 * (df.d_cereal < 0).mean(),
                     pct_sites_hyde_grazing_up=100 * (df.d_graz_50 > 0).mean(), pct_sites_pastoral_up=100 * (df.d_pastoral > 0).mean(),
                     sign_agreement_cropland_cereal=agree(df.d_crop_50, df.d_cereal), sign_agreement_grazing_pastoral=agree(df.d_graz_50, df.d_pastoral),
                     spearman_change_cropland_cereal=rc, p_change_cropland_cereal=pc, spearman_change_grazing_pastoral=rg, p_change_grazing_pastoral=pg))
HT = pd.DataFrame(hrow)
HT.to_csv(f'{OT}/table_hyde.csv', index=False)
hts = H.groupby('year')[['crop_50', 'graz_50', 'popd_50']].mean()
hts = 100 * hts / hts.loc[500]
TXT['hyde_relative_to_500CE_pct'] = hts.round(0).astype(int).to_dict()

fig, axs = plt.subplots(2, 2, figsize=(14.5, 11))
ax = axs[0, 0]
ext = [G['lon'][0] - .125, G['lon'][-1] + .125, G['lat'][-1] - .125, G['lat'][0] + .125]
ax.set_facecolor('#e8f1f8')
im = ax.imshow(100 * G['crop500'], extent=ext, cmap='YlOrBr', vmin=0, vmax=30, zorder=0)
ax.scatter(core.lon, core.lat, s=9, c='k', lw=0, zorder=2, label=f'pollen sites ({len(core)})')
ax.set_xlim(-11, 50); ax.set_ylim(30, 57); ax.set_aspect(1 / np.cos(np.radians(43)))
ax.legend(loc='upper center', bbox_to_anchor=(.5, -.08), fontsize=8, frameon=False)
plt.colorbar(im, ax=ax, shrink=.7, extend='max', label='HYDE cropland in 500 CE, % of land')
ax.set_title('a  HYDE 3.2 cropland in 500 CE and the pollen sites', loc='left', fontsize=10)
ax = axs[0, 1]
for r in REG:
    d = HV[HV.region == r]; ax.scatter(100 * d.crop_50_pre, d.cereal_pre, s=16, c=COL[r], edgecolor='k', lw=.3, label=r)
ax.set_xscale('symlog', linthresh=.1); ax.set_yscale('symlog', linthresh=.1)
x = HT[(HT.test.str.startswith('spatial')) & (HT.scope == 'All sites') & (HT.radius_km == 50)].set_index('comparison')
ax.set_xlabel('HYDE cropland within 50 km, % of land (400–540 CE)'); ax.set_ylabel('Cereal pollen, % (400–540 CE)')
ax.set_title(f"b  Where: HYDE cropland vs cereal pollen, 400–540 CE (Spearman ρ = {x.loc['cropland vs cereal', 'spearman_rho']:.2f})", loc='left', fontsize=10)
ax.legend(fontsize=7.5, loc='upper left', frameon=False)
ax = axs[1, 0]
for c, lab, ls in [('crop_50', 'HYDE cropland', '-'), ('graz_50', 'HYDE grazing land', '--'), ('popd_50', 'HYDE population density', ':')]:
    ax.plot(hts.index, hts[c], ls, color='#8c510a', lw=2, marker='o', ms=3, label=lab)
shade(ax); ax.set_ylabel('HYDE around the sites, % of its 500 CE value'); ax.set_xlim(190, 1010)
a2 = ax.twinx(); a2.spines['right'].set_visible(True)
for k, c in [('cereal', '#1a1a1a'), ('anthro', '#2166ac')]:
    q = comp(SB, k, 5); a2.plot(q.index, q['mean'].rolling(3, center=True, min_periods=1).mean(), color=c, lw=1.6, label=f'Pollen: {IND[k].lower()}')
a2.set_ylabel('Pollen composite, z-score (75-yr running mean)')
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = a2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, fontsize=8, loc='upper left', frameon=False); ax.set_xlabel('Year CE')
ax.set_title('c  When: HYDE around the pollen sites vs pollen composites', loc='left', fontsize=10)
ax = axs[1, 1]
for r in REG:
    d = HV[HV.region == r]; ax.scatter(d.d_crop_50, d.d_cereal, s=16, c=COL[r], edgecolor='k', lw=.3)
ax.axhline(0, color='k', lw=.6); ax.axvline(0, color='k', lw=.6); ax.set_yscale('symlog', linthresh=.1)
y = HT[(HT.test.str.startswith('change')) & (HT.scope == 'All sites')].iloc[0]
qd = [(HV.d_crop_50 < 0) & (HV.d_cereal > 0), (HV.d_crop_50 < 0) & (HV.d_cereal < 0), (HV.d_crop_50 > 0) & (HV.d_cereal > 0), (HV.d_crop_50 > 0) & (HV.d_cereal < 0)]
for m_, (xx, yy, ha) in zip(qd, [(.02, .97, 'left'), (.02, .03, 'left'), (.98, .97, 'right'), (.98, .03, 'right')]):
    ax.text(xx, yy, f'{100 * m_.mean():.0f}% of sites', transform=ax.transAxes, ha=ha, va='top' if yy > .5 else 'bottom', fontsize=9,
            bbox=dict(fc='white', ec='none', alpha=.8))
ax.set_xlabel('HYDE cropland change within 50 km, % (541–750 vs 400–540 CE)'); ax.set_ylabel('Change in cereal pollen, percentage points')
ax.set_title(f"d  Direction: HYDE cropland falls at {y.pct_sites_hyde_cropland_down:.0f}% of sites, cereal pollen at {y.pct_sites_cereal_down:.0f}%",
             loc='left', fontsize=10)
fig.tight_layout(); fig.savefig(f'{OF}/fig10_hyde.png'); plt.close()

# ---------- 5. Monte Carlo on age-model uncertainty ----------
M = S[S.siteid.isin(S[(S.age_ce >= 200) & (S.age_ce <= 950)].siteid)].sort_values(['datasetid', 'age_ce']).reset_index(drop=True)
rcode = pd.factorize(M.datasetid)[0]                 # record (core): errors are correlated, and order kept, within a core
scode, sids = pd.factorize(M.siteid)                 # site: window means pool the cores of one site, as in the main analysis
ns, X, age0 = len(sids), M[K].values, M.age_ce.values
reg_s = M.groupby(scode).region.first().values
sig = (M.age_unc / 1.96).values
SIG_MED = np.nanmedian(sig[(age0 >= 250) & (age0 <= 900)])
TXT['mc'] = dict(share_samples_with_age_range=round(float(np.isfinite(sig).mean()), 3), sigma_median_yr=round(float(SIG_MED), 1))
sig = np.where(np.isnan(sig), SIG_MED, sig)


def updown(d):   # +1 if more sites rise than fall, -1 if more fall (robust when most changes are zero)
    return np.sign((d > 0).sum() - (d < 0).sum())


obs = {(rule, sc, k): (updown(d), d.median()) for rule, base in (('>=2', core), ('>=1', relaxed))
       for sc, df in scopes(base) for k in K for d in [(df[f'{k}_post'] - df[f'{k}_pre']).dropna()]}


def chol(L):
    return sparse.block_diag([np.linalg.cholesky(np.exp(-np.abs(a[:, None] - a[None, :]) / L) + 1e-6 * np.eye(len(a)))
                              for a in (age0[rcode == i] for i in range(rcode.max() + 1))], format='csr')


def mc(L, scale, n):
    """Perturb every core's ages with errors correlated along the core (exponential kernel, length L years), keep the
    stratigraphic order, recompute the site window means and the paired before/after tests."""
    Kc, out = chol(L), []
    ok_cnt = np.isfinite(X).astype(float); Xn = np.nan_to_num(X)
    for it in range(n):
        a = age0 + scale * sig * (Kc @ rng.standard_normal(len(age0)))
        a = a[np.lexsort((a, rcode))]
        mean, cnt = {}, {}
        for lab, w in (('pre', PRE), ('post', POST)):
            m = inwin(a, w)
            cnt[lab] = np.bincount(scode[m], minlength=ns)
            s = np.stack([np.bincount(scode[m], weights=Xn[m, j], minlength=ns) for j in range(X.shape[1])], 1)
            c = np.stack([np.bincount(scode[m], weights=ok_cnt[m, j], minlength=ns) for j in range(X.shape[1])], 1)
            with np.errstate(invalid='ignore', divide='ignore'):
                mean[lab] = s / c
        dl = mean['post'] - mean['pre']
        for rule, ok in (('>=2', (cnt['pre'] >= 2) & (cnt['post'] >= 2)), ('>=1', (cnt['pre'] >= 1) & (cnt['post'] >= 1))):
            for sc in (['All sites'] + REG if rule == '>=2' else [EM]):
                sel = ok if sc == 'All sites' else ok & (reg_s == sc)
                for j, k in enumerate(K):
                    d = dl[sel, j]; d = d[np.isfinite(d)]
                    out.append((it, rule, sc, k, len(d), np.median(d) if len(d) else np.nan, wilcox(d), updown(d)))
    return pd.DataFrame(out, columns=['it', 'rule', 'scope', 'indicator', 'n', 'median_change', 'p', 'dir'])


MCV = {'main': (500, 1, NMC), 'independent': (50, 1, NMC // 2), 'errors x1.5': (500, 1.5, NMC // 2)}
mrow, MCR = [], {}
for v, (L, scale, n) in MCV.items():
    R = MCR[v] = mc(L, scale, n)
    for (rule, sc, k), g in R.groupby(['rule', 'scope', 'indicator']):
        od, om = obs[(rule, sc, k)]
        p05 = g.p < .05
        mrow.append(dict(variant=v, correlation_length_yr=L, error_scale=scale, rule=rule, scope=sc, indicator=k, iterations=len(g),
                         n_sites_median=g.n.median(), observed_direction=od, observed_median_change=om, mc_median=g.median_change.median(),
                         mc_lo=g.median_change.quantile(.025), mc_hi=g.median_change.quantile(.975),
                         pct_p05_same_direction=100 * (p05 & (g.dir == od)).mean(),
                         pct_p05_up=100 * (p05 & (g.dir > 0)).mean(), pct_p05_down=100 * (p05 & (g.dir < 0)).mean()))
MT = pd.DataFrame(mrow)
MT.to_csv(f'{OT}/table_montecarlo.csv', index=False)

fig = plt.figure(figsize=(15.5, 6.6))
gs = fig.add_gridspec(2, 3, width_ratios=[1.7, 1, 1], wspace=.32, hspace=.6)
ax = fig.add_subplot(gs[:, 0])
mm = MT[MT.variant == 'main']
rows = [('>=2', 'All sites')] + [('>=2', r) for r in REG] + [('>=1', EM)]
hm = np.array([[mm[(mm.rule == a) & (mm.scope == b) & (mm.indicator == k)][['pct_p05_up', 'pct_p05_down']].max(axis=1).iloc[0] for k in K] for a, b in rows])
ax.imshow(hm, cmap='Greys', vmin=0, vmax=130, aspect='auto')
for i, (a, b) in enumerate(rows):
    for j, k in enumerate(K):
        r = mm[(mm.rule == a) & (mm.scope == b) & (mm.indicator == k)].iloc[0]
        arrow = '–' if r.pct_p05_up == r.pct_p05_down == 0 else '↑' if r.pct_p05_up >= r.pct_p05_down else '↓'
        ax.text(j, i, f'{arrow} {hm[i, j]:.0f}%', ha='center', va='center', fontsize=9, color='w' if hm[i, j] > 70 else 'k')
ax.set_xticks(range(len(K))); ax.set_xticklabels([IND[k] for k in K], rotation=30, ha='right', fontsize=8.5)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([b + (' (≥1 sample per window)' if a == '>=1' else '') for a, b in rows], fontsize=8.5)
ax.set_title(f'a  % of {NMC} age-model realisations with a significant\n(p < 0.05) rise (↑) or fall (↓) across 541', loc='left', fontsize=10)
R = MCR['main']
for i, (rule, sc, k) in enumerate([('>=2', 'All sites', 'cereal'), ('>=2', 'All sites', 'anthro'), ('>=2', 'All sites', 'ap_natural'), ('>=2', EM, 'arbor')]):
    ax = fig.add_subplot(gs[i // 2, 1 + i % 2])
    g = R[(R.rule == rule) & (R.scope == sc) & (R.indicator == k)].median_change
    ax.hist(g, bins=30, color='#bdbdbd', edgecolor='w'); ax.axvline(obs[(rule, sc, k)][1], color='#b2182b', lw=2, label='published ages')
    ax.axvline(0, color='k', lw=.6); ax.set_title(f"{'bcde'[i]}  {'E. Mediterranean' if sc == EM else 'All sites'}: {IND[k]}", loc='left', fontsize=9.5)
    ax.set_xlabel('Median change (pp), 541–750 minus 400–540', fontsize=8.5); ax.set_ylabel('Realisations', fontsize=8.5)
    if i == 0:
        ax.legend(fontsize=7.5, frameon=False)
fig.savefig(f'{OF}/fig11_montecarlo.png', bbox_inches='tight'); plt.close()

# ---------- mid-term comparison and the numbers quoted in the text ----------
FT = pd.DataFrame([dict(scope=sc, indicator=k, **test(df, k)) for sc, df in scopes(core) for k in K])
CMP = midT.merge(FT, on=['scope', 'indicator'], suffixes=('_mid', '_final'))[
    ['scope', 'indicator', 'n_mid', 'median_change_mid', 'wilcoxon_p_mid', 'n_final', 'median_change_final', 'ci_lo_final', 'ci_hi_final', 'wilcoxon_p_final']]
CMP.to_csv(f'{OT}/table_mideval_vs_final.csv', index=False)

MS = pd.read_csv(f'{MID}/samples.csv'); ML = json.load(open(f'{MID}/neotoma_dataset_list.json'))
keep = MS[MS.datasetid.isin(S.datasetid)]
A_, B_ = keep.copy(), S[S.datasetid.isin(keep.datasetid)].copy()
for d in (A_, B_):
    d['k1'], d['k2'], d['k3'] = d.pollensum.round(1), d.cereal.round(4), d.ap_natural.round(4)
mg = A_.merge(B_[['datasetid', 'k1', 'k2', 'k3', 'age_ce']], on=['datasetid', 'k1', 'k2', 'k3'], how='left', suffixes=('', '_new'))
changed = mg.age_ce_new.isna() | ((mg.age_ce - mg.age_ce_new).abs() > 1)
TXT['midterm_revisions'] = dict(midterm_records_in_final=int(keep.datasetid.nunique()), midterm_samples_in_those=int(len(keep)),
                                samples_changed_or_removed=int(changed.sum()), records_affected=int(mg[changed].datasetid.nunique()))
used_mid, used_fin = set(MS.datasetid), set(S.datasetid)
listed = {x[0] for x in ML}
TXT['midterm_list'] = dict(listed=len(listed), used_midterm=len(used_mid & listed), used_final=len(used_fin & listed))
TXT['midterm_core_sites_in_final_core'] = int(core.index.isin(S[S.datasetid.isin(mid.datasetid)].siteid.unique()).sum())
TXT['midterm_core_records'] = int(len(mid))

y = CT[(CT.window == '300-900') & (CT.scope == 'All except E. Med') & (CT.indicator == 'anthro') & (CT.climate == 'T_eu') & (CT.lag_yr == 0)].iloc[0]
TXT['corr_anthro_Teu_300_900_all_except_EMed'] = dict(r=round(y.r, 2), r_detrended=round(y.r_detrended, 2), p_detrended=round(y.p_detrended, 2))
TXT['n_correlations'] = int(len(CT))
# timing in the Eastern Mediterranean (25-yr bins; bin centres): peak of the cultivated-tree and all-anthropogenic composites
# before 541, and the 4th-5th-century course of Kocain moisture (inverted delta-18O z-score, 50-yr running mean as in Fig. 6b)
ce = {k: comp(SB[SB.region == EM], k)['mean'] for k in ('arbor', 'anthro')}
kz = Ko[(Ko.age_ce >= 150) & (Ko.age_ce <= 1050)].set_index('age_ce').d18O
kz = binmean(kz.index, -(kz - kz.mean()) / kz.std()).rolling(2, min_periods=1).mean()
kpk = kz.loc[300:500].idxmax()
TXT['emed_timing'] = dict(arbor_peak_bin_300_540=float(ce['arbor'].loc[300:540].idxmax()), anthro_peak_bin_300_540=float(ce['anthro'].loc[300:540].idxmax()),
                          arbor_mean_z_before_vs_after_425={'300-425': round(float(ce['arbor'].loc[300:425].mean()), 2), '425-540': round(float(ce['arbor'].loc[425:540].mean()), 2)},
                          kocain_moisture_peak_bin=float(kpk), kocain_first_bin_below_mean_after_peak=float(kz.loc[kpk:][kz.loc[kpk:] < 0].index[0]),
                          kocain_driest_bin_400_800=float(kz.loc[400:800].idxmin()))
em_core = core[core.region == EM]
TXT['emed_core_sites'] = em_core[['site', 'lon', 'lat']].round(2).reset_index().to_dict('records')
TXT['core_sites_east_of_44E'] = core[core.lon > 44].site.tolist()
TXT['relaxed_emed_east_of_44E'] = relaxed[(relaxed.region == EM) & (relaxed.lon > 44)].site.tolist()
json.dump(TXT, open(f'{OT}/text_numbers.json', 'w'), indent=1, ensure_ascii=False, default=float)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30); pd.set_option('display.max_rows', 500)
print(json.dumps(TXT, indent=1, ensure_ascii=False, default=float))
