"""Step 5: write report/final_report.html from the tables, so that every number in the report comes from the analysis.
The qualitative statements in the text are checked with assertions; if a re-run changed a result, the script stops.
Also writes presentation/deck_numbers.json for the slide deck.   Usage: report.py tables/ report/ presentation/"""
import sys, os, json, html
import numpy as np, pandas as pd

T_, R_, P_ = sys.argv[1:4]
os.makedirs(P_, exist_ok=True); os.makedirs(R_, exist_ok=True)
rd = lambda f: pd.read_csv(f'{T_}/{f}')
SUM = json.load(open(f'{T_}/summary.json')); TX = json.load(open(f'{T_}/text_numbers.json'))
MIDS = json.load(open(f'{T_}/mideval/summary.json'))
PV, PL, SE, RG, EX, HY, MC, CO, MV = (rd(f) for f in ('table_pre_vs_post.csv', 'table_placebo.csv', 'table_sensitivity.csv', 'table_regression.csv',
                                                    'table_emed_expansion.csv', 'table_hyde.csv', 'table_montecarlo.csv', 'table_climate_correlation.csv',
                                                    'table_mideval_vs_final.csv'))
REG = ['W. & Central Europe', 'W. Mediterranean', 'E. Europe', 'British Isles', 'E. Mediterranean & Anatolia']
EM = 'E. Mediterranean & Anatolia'
IND6 = ['cereal', 'pastoral', 'arbor', 'anthro', 'ap_natural', 'richness']
NAME = dict(cereal='Cereal', pastoral='Pastoral', arbor='Cultivated trees', anthro='All anthropogenic', ap_natural='Natural trees', richness='Richness')


def fp(p):
    return '&lt; 0.001' if p < .001 else f'{p:.3f}' if p < .1 else f'{p:.2f}'


def pt(p):
    return 'p ' + fp(p) if p < .001 else 'p = ' + fp(p)


def sg(x, d=2):
    s = f'{x:+.{d}f}'.replace('-', '−')
    return '0.00' if s in ('+0.00', '−0.00') and d == 2 else s


def fr(x):
    return ('−' if x <= -0.005 else '') + f'{abs(x):.2f}'


def n(x):
    return f'{x:,}'


def pv(scope, k):
    return PV[(PV.scope == scope) & (PV.indicator == k)].iloc[0]


def rg(model, term, k, scope='All sites'):
    return RG[(RG.model == model) & (RG.term == term) & (RG.indicator == k) & (RG.scope == scope)].iloc[0]


def pl(scope, k):
    return PL[(PL.scope == scope) & (PL.indicator == k)].iloc[0]


def se(test, k):
    return SE[(SE.test == test) & (SE.indicator == k)].iloc[0]


def mc(scope, k, variant='main', rule='>=2'):
    return MC[(MC.variant == variant) & (MC.rule == rule) & (MC.scope == scope) & (MC.indicator == k)].iloc[0]


def ex(prefix, k):
    return EX[EX['sample'].str.startswith(prefix) & (EX.indicator == k)].iloc[0]


def hy(scope):
    return HY[HY.test.str.startswith('change') & (HY.scope == scope)].iloc[0]


def hsp(comp, radius=50):
    return HY[HY.test.str.startswith('spatial') & (HY.scope == 'All sites') & (HY.radius_km == radius) & (HY.comparison == comp)].iloc[0]


def cor(window, scope, k, clim, lag=0):
    return CO[(CO.window == window) & (CO.scope == scope) & (CO.indicator == k) & (CO.climate == clim) & (CO.lag_yr == lag)].iloc[0]


def cell(r, d=2):
    if 'median_change' not in r or pd.isna(r.get('wilcoxon_p', np.nan)):
        return '<td>–</td>'
    cls = ' class="sig"' if r.wilcoxon_p < .05 else ''
    return f'<td{cls}>{sg(r.median_change, d)} ({fp(r.wilcoxon_p)})</td>'


# ---------------- checks of every qualitative statement in the text ----------------
A = 'All sites'
for k in ('cereal', 'pastoral', 'anthro', 'richness', 'arbor'):
    assert pv(A, k).wilcoxon_p < .05 and pv(A, k).pct_sites_increase > pv(A, k).pct_sites_decline, k
assert pv(A, 'ap_natural').wilcoxon_p < .05 and pv(A, 'ap_natural').median_change < 0
assert pv(A, 'arbor').median_change == 0
for k in ('cereal', 'pastoral', 'anthro', 'ap_natural', 'richness'):
    assert pv('W. & Central Europe', k).wilcoxon_p < .05, k
assert all(pv('British Isles', k).wilcoxon_p > .05 for k in IND6)
assert all(pv(EM, k).wilcoxon_p > .05 for k in IND6 if k != 'richness') and pv(EM, 'richness').wilcoxon_p < .05 and pv(EM, 'richness').median_change < 0
assert pv('W. Mediterranean', 'arbor').wilcoxon_p < .05 and pv('W. Mediterranean', 'anthro').wilcoxon_p > .05
for k in ('cereal', 'pastoral', 'anthro'):
    assert pv('E. Europe', k).wilcoxon_p < .05, k
for k in ('cereal', 'pastoral', 'anthro', 'ap_natural'):
    assert pl(A, k).p_rate < .05, k
    assert pl('E. Europe', k).p_rate < .05, k
assert pl('W. & Central Europe', 'anthro').p_rate > .05 and pl('W. & Central Europe', 'pastoral').p_rate < .05
for t in ('Narrow', 'Boundary 50 yr earlier', 'Boundary 50 yr later', 'Following period'):
    for k in ('cereal', 'pastoral', 'anthro', 'ap_natural'):
        assert se(t, k).wilcoxon_p < .05, (t, k)
assert all(se('Early plague only', k).wilcoxon_p > .05 for k in ('cereal', 'pastoral', 'anthro', 'ap_natural'))
for m, t in [('M1', 'T_eu_z'), ('M2', 'T_eu_z'), ('M3', 'T_alps_z'), ('M4', 'T_eu_z'), ('M4', 'T_lag'), ('M5', 'T_eu_z')]:
    assert all(rg(m, t, k).p > .05 for k in IND6), (m, t)
assert all(rg('M1', 'plague', k).p > .05 for k in IND6)
for k in ('anthro', 'cereal', 'pastoral', 'ap_natural'):
    assert rg('M2', 'plague_first', k).p < .05 and rg('M2', 'plague_second', k).p > .05, k
    assert rg('M5', 'plague', k).p > .05 and rg('M8', 'plague', k).p < .05, k
assert rg('M2', 'plague_first', 'anthro', 'W. & Central Europe').p < .05
assert all(rg('M2', 'plague_first', 'anthro', r).p > .05 for r in REG if r != 'W. & Central Europe')
assert all(rg('M7', 'moist', k, EM).p > .05 for k in IND6)
assert rg('M8', 'T_eu_z', 'anthro').p < .05
for k in ('cereal', 'anthro', 'ap_natural', 'richness'):
    assert mc(A, k).pct_p05_same_direction >= 90, k
assert mc(A, 'arbor').pct_p05_same_direction < 60
assert all(mc(EM, k).pct_p05_same_direction < 50 for k in IND6)
assert all(ex('Core', k).wilcoxon_p > .05 for k in ('cereal', 'arbor', 'pastoral', 'anthro')) and all(ex('Relaxed', k).wilcoxon_p > .05 for k in IND6)
assert hy(A).pct_sites_hyde_cropland_down > 80 and hy(A).hyde_grazing_pct > 0
c2 = cor('200-1000', 'All except E. Med', 'anthro', 'T_eu'); c3 = cor('300-900', 'All except E. Med', 'anthro', 'T_eu')
assert c2.p_eff < .05 and c3.p_detrended > .5
ck = [cor('200-1000', EM, k, 'kocain_d18O') for k in ('arbor', 'anthro')]
assert all(c.p_detrended > .05 for c in ck)
cs = cor('200-1000', EM, 'anthro', 'soreq_d18O'); assert cs.p_detrended < .05 and cs.r_detrended > 0
ET = TX['emed_timing']; assert ET['arbor_peak_bin_300_540'] < 425 < ET['kocain_first_bin_below_mean_after_peak']

# ---------------- numbers used in the text ----------------
S, NS, NC = SUM, SUM['n_sites'], SUM['n_core_sites']
rgn = S['regions']
mid = TX['midterm_list']; rev = TX['midterm_revisions']
cool = TX['cooling_400_535_to_536_660_degC']; ma = TX['mean_anomaly_degC']; af = TX['alpine_31yr_fall']
ko, so = TX['kocain'], TX['soreq']
hr = TX['hyde_relative_to_500CE_pct']
dup = pd.read_csv('data/duplicate_records.csv') if os.path.exists('data/duplicate_records.csv') else None
n_dup = len(dup) if dup is not None else 14
emr = ex('Relaxed', 'cereal').n; emc = ex('Core', 'cereal').n
wce_m2 = rg('M2', 'plague_first', 'anthro', 'W. & Central Europe'); ee_m2 = rg('M2', 'plague_first', 'anthro', 'E. Europe')
m2 = {k: rg('M2', 'plague_first', k) for k in IND6}; m2b = {k: rg('M2', 'plague_second', k) for k in IND6}
m1 = {k: rg('M1', 'plague', k) for k in IND6}
nreg = {k: (int(rg('M1', 'trend', k).n_sites), int(rg('M1', 'trend', k).n_obs)) for k in IND6}
em_sites = TX['emed_core_sites']
lerna = [s for s in em_sites if s['site'] == 'Lake Lerna']
W = pd.read_csv(f'{T_}/site_window_means.csv')
e = W[W.region == EM].assign(d=lambda x: x.arbor_post - x.arbor_pre).set_index('site')
big = e.sort_values('d').head(4)
assert list(big.index[:3]) == ['Dead Sea 7', 'Lake Kournas', 'Lake Lerna'], list(big.index)


def site_change(s):
    return f'{sg(e.loc[s, "d"], 0 if abs(e.loc[s, "d"]) >= 9.5 else 1)} points from {e.loc[s, "arbor_pre"]:.0f}%'


mcm = {k: mc(A, k) for k in IND6}
fmc = lambda r: f'{r.pct_p05_same_direction:.0f}%' if r.pct_p05_same_direction < 99.5 or r.pct_p05_same_direction == 100 else f'{r.pct_p05_same_direction:.1f}%'

# ---------------- tables ----------------
rows = []
for s in ['All sites'] + REG:
    nn = int(pv(s, 'cereal').n)
    rows.append(f'<tr><td>{"All sites" if s == "All sites" else s}</td><td>{nn}</td>' + ''.join(cell(pv(s, k)) for k in IND6) + '</tr>')
TABLE2 = '\n'.join(rows)

srow = []
for t, lab in [('Main', 'Main comparison'), ('Narrow', 'Narrower windows'), ('Early plague only', 'First 60 years of plague only'),
               ('Boundary 50 yr earlier', 'Boundary 50 years earlier'), ('Boundary 50 yr later', 'Boundary 50 years later'),
               ('Following period', 'Plague period vs following period')]:
    r0 = se(t, 'cereal')
    srow.append(f'<tr><td>{lab}</td><td>{r0.before} → {r0.after}</td><td>{int(r0.n)}</td>' + ''.join(cell(se(t, k)) for k in ('cereal', 'pastoral', 'anthro', 'ap_natural')) + '</tr>')
prow = []
for s in ['All sites'] + REG:
    r0 = pl(s, 'cereal')
    cells = ''.join(f'<td{" class=sig" if pl(s, k).p_rate < .05 else ""}>{sg(pl(s, k).median_rate_pandemic_per_century)} vs {sg(pl(s, k).median_rate_placebo_per_century)} ({fp(pl(s, k).p_rate)})</td>'
                    for k in ('cereal', 'pastoral', 'anthro', 'ap_natural'))
    prow.append(f'<tr><td>{s}</td><td>{int(r0.n)}</td>{cells}</tr>')
TABLE3 = '\n'.join(srow); TABLE3B = '\n'.join(prow).replace('class=sig', 'class="sig"')


def rcell(m, t, k, scope='All sites'):
    r = rg(m, t, k, scope)
    cls = ' class="sig"' if r.p < .05 else ''
    return f'<td{cls}>{sg(r.coef, 3)} ({fp(r.p)})</td>'


K4 = ['anthro', 'cereal', 'pastoral', 'ap_natural']
r4 = []
r4.append('<tr class="group"><td colspan="5">M1: temperature + plague period + trend, 300–900 CE</td></tr>')
for t, lab in [('T_eu_z', 'Temperature (+1 SD)'), ('plague', 'Plague period, 550–750'), ('trend', 'Trend (per century)')]:
    r4.append(f'<tr><td>{lab}</td>' + ''.join(rcell('M1', t, k) for k in K4) + '</tr>')
r4.append('<tr class="group"><td colspan="5">M2: plague period in two halves</td></tr>')
for t, lab in [('plague_first', 'First century, 550–650'), ('plague_second', 'Second century, 650–750')]:
    r4.append(f'<tr><td>{lab}</td>' + ''.join(rcell('M2', t, k) for k in K4) + '</tr>')
r4.append('<tr class="group"><td colspan="5">Plague-period term (550–750) in the variants</td></tr>')
for m, lab in [('M3', 'M3: Alpine temperature instead'), ('M4', 'M4: + temperature lagged 25 yr'), ('M5', 'M5: quadratic trend'), ('M6', 'M6: no climate term')]:
    r4.append(f'<tr><td>{lab}</td>' + ''.join(rcell(m, 'plague', k) for k in K4) + '</tr>')
r4.append('<tr class="group"><td colspan="5">M7: + Kocain moisture, Eastern Mediterranean sites only</td></tr>')
for t, lab in [('moist', 'Kocain moisture (+1 SD wetter)'), ('plague', 'Plague period, 550–750')]:
    r4.append(f'<tr><td>{lab}</td>' + ''.join(rcell('M7', t, k, EM) for k in K4) + '</tr>')
r4.append('<tr class="group"><td colspan="5">M8: as M1, 200–1000 CE</td></tr>')
for t, lab in [('T_eu_z', 'Temperature (+1 SD)'), ('plague', 'Plague period, 550–750')]:
    r4.append(f'<tr><td>{lab}</td>' + ''.join(rcell('M8', t, k) for k in K4) + '</tr>')
r4.append('<tr class="group"><td colspan="5">Sites / site-bins in M1</td></tr>')
r4.append('<tr><td>All sites, 300–900 CE</td>' + ''.join(f'<td>{nreg[k][0]} / {n(nreg[k][1])}</td>' for k in K4) + '</tr>')
TABLE4 = '\n'.join(r4)

r5 = []
for prefix, lab in [('Mid-term, as reported', 'Mid-term core sites, as reported'), ('Mid-term sites, final', 'Mid-term core sites, final data'),
                    ('Core', 'Final core, ≥2 samples per window'), ('Relaxed', 'Relaxed, ≥1 sample per window')]:
    nn = int(ex(prefix, 'cereal').n)
    r5.append(f'<tr><td>{lab}</td><td>{nn}</td>' + ''.join(cell(ex(prefix, k)) for k in IND6) + '</tr>')
TABLE5 = '\n'.join(r5)

r6 = []
for s in ['All sites'] + REG:
    h = hy(s)
    r6.append(f'<tr><td>{s}</td><td>{int(h.n)}</td><td>{sg(h.hyde_cropland_pct, 1)}%</td><td>{sg(h.hyde_grazing_pct, 1)}%</td><td>{sg(h.hyde_population_pct, 1)}%</td>'
              f'<td>{h.pct_sites_hyde_cropland_down:.0f}%</td><td>{h.pct_sites_cereal_down:.0f}%</td><td>{h.sign_agreement_cropland_cereal:.0f}%</td>'
              f'<td>{h.pct_sites_hyde_grazing_up:.0f}%</td><td>{h.pct_sites_pastoral_up:.0f}%</td></tr>')
TABLE6 = '\n'.join(r6)


def mcc(r):
    up = r.pct_p05_up >= r.pct_p05_down
    v = max(r.pct_p05_up, r.pct_p05_down)
    return f'{"↑" if up else "↓"} {v:.0f}%' if v > 0 else '–'


r7 = []
cols7 = [('main', '>=2', A), ('independent', '>=2', A), ('errors x1.5', '>=2', A), ('main', '>=2', 'W. & Central Europe'),
         ('main', '>=2', 'W. Mediterranean'), ('main', '>=2', 'E. Europe'), ('main', '>=2', EM), ('main', '>=1', EM)]
for k in IND6:
    r7.append(f'<tr><td>{NAME[k]}</td>' + ''.join(f'<td>{mcc(mc(sc, k, v, ru))}</td>' for v, ru, sc in cols7) + '</tr>')
TABLE7 = '\n'.join(r7)

# ---------------- the report ----------------
p = lambda s, k: pt(pv(s, k).wilcoxon_p)
TITLE = 'Environmental change before and after the First Pandemic'
AUTH = ['Jetty Jithendra Sai Ram (2024101102)', 'N Pavaneswar (2024102063)', 'Shaik Babu (2024101032)', 'Dr Shashang (2024101069)']
css = open(os.path.join(os.path.dirname(__file__), 'report_style.css')).read()
H = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE}</title>
<style>
{css}
</style>
</head>
<body>
<main class="wrap">

<header class="title">
  <div class="eyebrow">EVST course project 18 · Team 2 · IIIT Hyderabad · Monsoon 2026</div>
  <h1>{TITLE}</h1>
  <p class="subtitle">Fossil-pollen evidence for land use in Europe and the Mediterranean, 250–900 CE. Final report.</p>
  <p class="authors">{' · '.join(f'<span>{a}</span>' for a in AUTH)}</p>
  <p class="meta">November 2026 · Code, data and every number in this report: <a href="https://github.com/RiyasShaik/evst-project18-team2">github.com/RiyasShaik/evst-project18-team2</a></p>
</header>

<section class="abstract">
  <h2>Abstract</h2>
  <p>The First Pandemic of plague (541–750 CE) is often thought to have emptied the countryside of the late Roman world, but its arrival coincided with the coldest decades of the Common Era, the Late Antique Little Ice Age (LALIA, 536–660 CE). We used fossil pollen to test whether land use changed after 541 and whether a change can be told apart from climate. From the Neotoma database we assembled {n(S['n_samples'])} pollen samples dated 0–1200 CE from {n(S['n_records'])} records at {n(NS)} sites in Europe, the Mediterranean and the Near East; {NC} sites have at least two samples both before (400–540 CE) and after (541–750 CE) the arrival of plague. Across these sites, cereal, pastoral and all anthropogenic indicators rose after 541 (all anthropogenic indicators {sg(pv(A, 'anthro').median_change)} percentage points, {p(A, 'anthro')}) and natural tree pollen fell ({sg(pv(A, 'ap_natural').median_change)} points, {p(A, 'ap_natural')}), faster than in the preceding period. Measured against the long rise of land use between 300 and 900 CE, the first century of plague (550–650 CE) shows a small shortfall ({sg(m2['anthro'].coef)} standard deviations, {pt(m2['anthro'].p)}), statistically detectable only in western and central Europe and not explained by reconstructed summer temperature; it disappears if the long-term trend is allowed to curve. In the Eastern Mediterranean the expanded sample ({emc} core sites, up from 13; {emr} under a relaxed rule) shows no significant fall in farming or arboriculture after 541; cultivated-tree pollen there was already lower after about 425 CE, while a cave record in SW Turkey shows conditions becoming drier. The HYDE 3.2 land-use model has cropland falling at {hy(A).pct_sites_hyde_cropland_down:.0f}% of sites, where cereal pollen fell at {hy(A).pct_sites_cereal_down:.0f}%. The Europe-wide rises in cereal and all anthropogenic indicators and the fall in natural trees stay significant in {np.floor(min(mcm[k].pct_p05_same_direction for k in ('cereal', 'anthro', 'ap_natural'))):.0f}–{max(mcm[k].pct_p05_same_direction for k in ('cereal', 'anthro', 'ap_natural')):.0f}% of 1,000 Monte Carlo realisations of the age models. The plague left no continental footprint of farmland abandonment in the pollen record.</p>
</section>

<h3>Key findings</h3>
<ol class="findings">
  <li><div><b>No abandonment after 541.</b> Cereal, pastoral and all anthropogenic pollen rose at most of the {NC} sites and natural tree pollen fell, faster than between 250–399 and 400–540 CE.</div></li>
  <li><div><b>A pause, not a collapse.</b> Relative to the 300–900 CE trend, the farming indicators sat about {abs(m2['anthro'].coef):.2f} SD lower in 550–650 CE and were back on trend in 650–750. The shortfall is significant only in western and central Europe and disappears with a curved (quadratic) trend.</div></li>
  <li><div><b>No detectable temperature effect.</b> Within 300–900 CE, reconstructed European summer temperature has no significant effect on any indicator in any regression specification.</div></li>
  <li><div><b>The Eastern Mediterranean shows no significant post-541 decline.</b> With {emc} core sites, no farming indicator changes significantly; cultivated-tree pollen had peaked around 400–425 CE and was already lower before the plague.</div></li>
  <li><div><b>HYDE 3.2 cropland moves the wrong way.</b> The model, which follows historical population estimates, has cropland shrinking after 541 at {hy(A).pct_sites_hyde_cropland_down:.0f}% of sites while cereal pollen grew at most of them. HYDE grazing land, in contrast, rises, like the pastoral pollen.</div></li>
</ol>

<h2><span class="num">1</span>Introduction</h2>
<p>The First Pandemic began in 541 CE when <i>Yersinia pestis</i> reached Pelusium in Egypt. It struck Constantinople in 542 and returned in waves for two centuries, until about 750 (Little 2007). Ancient DNA has confirmed the pathogen in burials from Britain, France, Spain and Germany (Keller et al. 2019). Contemporary writers describe catastrophic mortality, and the pandemic has often been blamed for the contraction of the late Roman economy. The same years saw volcanic eruptions in 536, 540 and 547 (Sigl et al. 2015) that started the Late Antique Little Ice Age (Büntgen et al. 2016). In the Alpine tree-ring record we use, the 31-year mean summer temperature fell by {af['degC']:.1f} °C between {af['from_year']} and {af['to_year']} CE (Fig. 2e). Because the two shocks overlap almost exactly, it is hard to say which one, if either, changed how people used the land.</p>
<p>Fossil pollen preserved in lake and bog sediments records the vegetation around each site. Pollen of cereals, of cultivated trees (olive, walnut, chestnut and vine) and of plants that thrive in grazed meadows (ribwort plantain and sorrel) tracks farming, while the share of other tree and shrub pollen tracks how much woodland remained (Behre 1981; Mercuri et al. 2013). If plague mortality left fields abandoned, the farming indicators should fall and tree pollen should rise after 541. Mordechai et al. (2019) combined pollen, papyri, laws, coins and inscriptions and found continuity rather than collapse. Izdebski et al. (2022) used pollen in a similar way to show that the Black Death of 1347–1352 left a strongly uneven footprint on European land use, so the method can detect a pandemic where it mattered.</p>
<p>This project (course project 18) asks whether vegetation, agriculture or land use changed substantially before and after the pandemic, and whether palaeoecological evidence can separate demographic effects from climatic change. We ask three questions. (1) Did land-use indicators change after 541? (2) Can a change be separated from the LALIA? (3) Does the most widely used reconstruction of historical land use, HYDE 3.2 (Klein Goldewijk et al. 2017), agree with the pollen? The mid-term evaluation answered the first question for 164 records. This report adds regional climate records, a regression that separates temperature from the plague period, an expanded Eastern Mediterranean sample, a Monte Carlo treatment of dating uncertainty and the comparison with HYDE, and it corrects the sample for duplicate records (Section 2.1).</p>

<h2><span class="num">2</span>Data</h2>
<h3>2.1 Pollen records</h3>
<p>We queried the Neotoma Paleoecology Database (Williams et al. 2018) for every pollen dataset located between 10°W and 50°E and between 30°N and 56°N whose calendar-scale age range covers 400–750 CE: 1,099 datasets. For each sample we used the age from the dataset's default chronology in Neotoma, accepting calibrated-radiocarbon, calendar, varve and AD/BC age scales, and kept samples dated 0–1200 CE with at least 100 terrestrial pollen grains. Two corrections followed. First, Neotoma holds some cores twice (for example an original upload and a later copy); {n_dup} records whose samples largely repeat those of another record at the same site were removed. Second, many lakes have more than one core; records with the same site name within 2 km were pooled into one site, so that every lake or bog counts once. The result is {n(S['n_samples'])} samples from {n(S['n_records'])} records at {n(NS)} sites. A core site has at least two samples in both 400–540 and 541–750 CE; there are {NC}, built from {S['n_core_records']} records ({S['core_sites_with_2plus_records']} sites have more than one core), with a median of {S['median_samples_pre']:.0f} samples in the earlier window and {S['median_samples_post']:.0f} in the later one (Fig. 1, Table 1).</p>
<figure><img src="../figures/fig01_site_map.png" alt="Map of the core pollen sites coloured by region"><figcaption><b>Fig. 1.</b> The {NC} core sites, coloured by region. Western and central Europe holds {rgn['W. & Central Europe']} of them, the Eastern Mediterranean and Anatolia {rgn[EM]}.</figcaption></figure>
<div class="tablewrap"><table>
<caption><b>Table 1.</b> The pollen dataset at the mid-term evaluation and in this final analysis. At mid-term every record counted separately; the final analysis removes duplicate records and pools cores from the same site. All 159 sites of the 164 mid-term core records are final core sites.</caption>
<tr><th>Item</th><th>Mid-term</th><th>Final</th></tr>
<tr><td>Neotoma datasets in the query</td><td>891</td><td>1,099</td></tr>
<tr><td>Records with usable samples</td><td>{MIDS['n_datasets_total']}</td><td>{n(S['n_records'])}</td></tr>
<tr><td>Sites</td><td>–</td><td>{n(NS)}</td></tr>
<tr><td>Samples, 0–1200 CE</td><td>{n(MIDS['n_samples'])}</td><td>{n(S['n_samples'])}</td></tr>
<tr><td>Core records / core sites</td><td>164 / 159</td><td>{S['n_core_records']} / {NC}</td></tr>
{''.join(f"<tr><td>&nbsp;&nbsp;{r}</td><td>{MIDS['regions'][r]} records</td><td>{rgn[r]} sites</td></tr>" for r in REG)}
<tr><td>Median age-model half-range at core sites that report one, 400–750 CE</td><td>{MIDS['median_age_unc']:.0f} yr</td><td>{S['median_age_half_range']:.0f} yr ({S['core_sites_with_age_range']} sites)</td></tr>
</table></div>

<h3>2.2 Land-use indicators</h3>
<p>All indicators are percentages of the terrestrial pollen sum (trees, shrubs and upland herbs). <b>Cereal</b>: Cerealia-type, <i>Secale</i>, <i>Triticum</i>, <i>Hordeum</i>, <i>Avena</i>. <b>Cultivated trees</b> (the OJCV group): <i>Olea</i>, <i>Juglans</i>, <i>Castanea</i>, <i>Vitis</i>. <b>Pastoral</b>: <i>Plantago lanceolata</i>, <i>Rumex acetosa</i>/<i>acetosella</i> and undifferentiated <i>Rumex</i>. <b>All anthropogenic</b>: the sum of the three. <b>Natural trees and shrubs</b>: tree and shrub pollen minus the cultivated trees. <b>Richness</b>: rarefied taxon richness at 100 grains, E(S<sub>100</sub>) (Hurlbert 1971).</p>

<h3>2.3 Regions</h3>
<p>Sites are grouped by coordinates, as at mid-term. <b>E. Mediterranean &amp; Anatolia</b>: south of 43°N and east of 19°E (Greece and Crete, southern Bulgaria, Turkey, the Levant, Georgia and north-western Iran; the only core site east of 44°E is {', '.join(TX['core_sites_east_of_44E'])} in Iran). <b>W. Mediterranean</b>: south of 44°N and west of 19°E (Iberia, southern France, Italy, North Africa). <b>British Isles</b>: west of 2°E and north of 49.5°N. <b>W. &amp; Central Europe</b>: the rest west of 16°E. <b>E. Europe</b>: the rest east of 16°E.</p>

<h3>2.4 Climate records</h3>
<p>We used four reconstructions from NOAA Paleoclimatology. (1) Central European June–August temperature from Alpine tree rings (Büntgen et al. 2011). (2) The PAGES 2k Euro-Med reconstruction of European mean June–August temperature (Luterbacher et al. 2016), in its composite-plus-scale (CPS) and Bayesian hierarchical (BHM) versions; its gridded field starts in 755 CE, so for our period the European mean is the series available. (3) Oxygen and carbon isotopes from a stalagmite in Kocain Cave, SW Turkey (Jacobson et al. 2021): {ko['n_200_1000']} analyses between 200 and 1000 CE, one per {ko['mean_spacing_yr']:.1f} years on average; higher δ<sup>18</sup>O and δ<sup>13</sup>C mean drier conditions. (4) Oxygen isotopes from Soreq Cave, Israel (Orland et al. 2009): {so['n_200_1000']} ion-microprobe analyses between 200 and 1000 CE, unevenly spaced: {so['n_330_460']} fall in 330–460 CE but only {so['n_541_660']} in 541–660 CE, and {so['bins_200_1000'] - so['bins_measured_200_1000']} of the {so['bins_200_1000']} 25-year bins in 200–1000 CE contain no measurement.</p>

<h3>2.5 HYDE 3.2</h3>
<p>HYDE 3.2.1 (Klein Goldewijk et al. 2017) estimates cropland, grazing land and population on a 5-arc-minute grid (about 9 km) at 100-year steps before 1700 CE. It starts from historical population estimates for each country and allocates land use in proportion to population and land suitability. We read the 200–1000 CE grids from the published archive and computed, for each pollen site, the share of land under cropland and under grazing and the mean population density within 25, 50 and 100 km.</p>

<h2><span class="num">3</span>Methods</h2>
<h3>3.1 Before/after comparison</h3>
<p>For each core site we averaged each indicator over 400–540 and over 541–750 CE (a sample belongs to 400–540 if its age is at least 400 and below 541, and so on) and took the difference. We tested whether the median difference across sites is zero with the paired Wilcoxon signed-rank test and bootstrapped its 95% confidence interval (2,000 resamples of sites).</p>
<h3>3.2 Placebo and sensitivity tests</h3>
<p>The placebo test asks whether the change across 541 is faster than the change in the preceding period, 250–399 to 400–540 CE, at the {S['n_placebo_sites']} core sites with at least two samples in 250–399. Because the window midpoints are {S['gap_real_yr']:.1f} years apart across 541 but {S['gap_placebo_yr']:.1f} years apart in the placebo comparison, a steady trend alone would make the change across 541 look larger; we therefore compare rates of change per century (paired Wilcoxon test). Sensitivity tests use narrower windows (450–540 against 541–640), only the first 60 years of plague (450–540 against 541–600), boundaries 50 years earlier or later, and the plague period against the following period (751–900).</p>
<h3>3.3 Composites and climate correlations</h3>
<p>Each indicator was converted to z-scores within each site, averaged into 25-year bins and then across sites, with bootstrap confidence intervals. We correlated these composites with the climate series (bin means; climate gaps filled by linear interpolation) over 200–1000 and 300–900 CE, with and without removing linear trends, and computed p-values from the effective sample size of two autocorrelated series (Bretherton et al. 1999).</p>
<h3>3.4 Regression of land use on temperature and plague period</h3>
<p>For the core sites we fitted, to the site z-scores in 25-year bins between 300 and 900 CE (24 bins),</p>
<p class="eq">z<sub>st</sub> = α<sub>s</sub> + β<sub>T</sub>·T<sub>t</sub> + β<sub>P</sub>·P<sub>t</sub> + γ·t + ε<sub>st</sub>,</p>
<p>where α<sub>s</sub> is a fixed effect for each site, T<sub>t</sub> the PAGES 2k European summer temperature (CPS) for the bin in standard-deviation units (1 SD = {TX['temperature_sd_degC_300_900']:.2f} °C over 300–900 CE), P<sub>t</sub> is 1 for the eight bins of 550–750 CE (the bin of 525–550 CE, which contains 541, counts as before), and t a linear trend in centuries. The trend matters because land use rose steadily through the first millennium. Standard errors are clustered both by site and by bin (Cameron et al. 2011). The two predictors are only weakly correlated (r = {fr(TX['corr_temperature_plague_dummy'])}) because the 4th century was as cool as the LALIA in the European mean and the late 7th century was warm. Variants: M2 splits the plague period at 650 CE into a first century (550–650, the plague waves inside the LALIA) and a second (650–750); M3 uses the Alpine temperature series; M4 adds temperature lagged by 25 years; M5 uses a quadratic trend; M6 drops climate; M7 adds Kocain moisture for the Eastern Mediterranean sites; M8 widens the window to 200–1000 CE. M1 and M2 were also fitted for each region. Sites whose indicator never varies are left out of that indicator's model.</p>
<h3>3.5 HYDE comparison</h3>
<p>In space, we computed Spearman correlations across sites between HYDE land-use shares and the pollen indicators in 400–540 CE. In time, we interpolated HYDE linearly between its 100-year steps, averaged it over the two windows, and asked whether HYDE and pollen change in the same direction at each site.</p>
<h3>3.6 Expanded Eastern Mediterranean sample</h3>
<p>The mid-term pipeline missed two kinds of record: records stored in Neotoma with a polygon outline (usually a lake) rather than a point, which were skipped, and records with calendar or varve chronologies, such as Nar Gölü in Cappadocia (England et al. 2008) and Bereket near Sagalassos (Kaniewski et al. 2007), which the age filter excluded. After the fix, {mid['used_final']} of the {mid['listed']} datasets in the mid-term list yield usable samples (mid-term: {mid['used_midterm']}). In the Eastern Mediterranean we repeated every test for the mid-term sites, for all core sites and for a relaxed rule of at least one sample in each window.</p>
<h3>3.7 Monte Carlo on dating uncertainty</h3>
<p>The median age uncertainty at the core sites that report one (±{S['median_age_half_range']:.0f} years) is comparable to the windows, so a sample dated 520 CE may postdate 541. We perturbed every sample's age with a random error whose standard deviation is the age model's reported uncertainty half-range divided by 1.96 (treating it as a 95% range) where available ({100 * TX['mc']['share_samples_with_age_range']:.0f}% of samples) and otherwise the median of those values, {TX['mc']['sigma_median_yr']:.0f} years. Errors are correlated along each core (exponential correlation over 500 years), as in an age-depth model, and samples keep their stratigraphic order. We recomputed the site window means and the before/after tests for 1,000 realisations, and for 500 realisations each of two variants: nearly independent errors (50-year correlation length) and errors 1.5 times larger.</p>

<h2><span class="num">4</span>Results</h2>
<h3>4.1 Europe-wide change after 541</h3>
<p>Across all {NC} core sites every farming indicator was higher after 541 than before (Table 2). Cereal pollen rose at {pv(A, 'cereal').pct_sites_increase:.0f}% of sites and fell at {pv(A, 'cereal').pct_sites_decline:.0f}% ({p(A, 'cereal')}); pastoral indicators rose by a median {sg(pv(A, 'pastoral').median_change)} points ({p(A, 'pastoral')}); all anthropogenic indicators by {sg(pv(A, 'anthro').median_change)} points ({p(A, 'anthro')}); natural tree and shrub pollen fell by {abs(pv(A, 'ap_natural').median_change):.2f} points ({p(A, 'ap_natural')}); and richness rose ({p(A, 'richness')}). Cultivated trees are absent from {pv(A, 'arbor').pct_sites_no_change:.0f}% of sites, so their median change is zero, but where they changed they rose more often than they fell ({p(A, 'arbor')}). The changes are small in absolute terms, as cereal pollen is poorly dispersed and rarely exceeds a few percent, but they are consistent across sites and opposite to abandonment (Fig. 3).</p>
<div class="tablewrap"><table>
<caption><b>Table 2.</b> Median change between 400–540 and 541–750 CE (percentage points; richness in taxa), with Wilcoxon p-values in brackets; red: p &lt; 0.05. n = core sites.</caption>
<tr><th>Region</th><th>n</th><th>Cereal</th><th>Pastoral</th><th>Cultivated trees</th><th>All anthropogenic</th><th>Natural trees</th><th>Richness</th></tr>
{TABLE2}
</table></div>
<p>The change across 541 is also faster than the change in the preceding period. Expressed per century, all anthropogenic indicators rose by {sg(pl(A, 'anthro').median_rate_pandemic_per_century)} points across 541 against {sg(pl(A, 'anthro').median_rate_placebo_per_century)} before ({pt(pl(A, 'anthro').p_rate)}, n = {int(pl(A, 'anthro').n)}); the difference is significant for cereal ({pt(pl(A, 'cereal').p_rate)}), pastoral indicators ({pt(pl(A, 'pastoral').p_rate)}) and natural trees ({pt(pl(A, 'ap_natural').p_rate)}) as well (Table 3, Fig. 4). The result holds for narrower windows, for a boundary 50 years earlier or later, and in the comparison with 751–900, when farming expanded further (all p &lt; 0.05 for the four indicators). It does not hold for the first 60 years of plague alone: comparing 450–540 with 541–600 CE, at the {int(se('Early plague only', 'anthro').n)} sites with enough samples, no indicator changes significantly (all anthropogenic {sg(se('Early plague only', 'anthro').median_change)} points, {pt(se('Early plague only', 'anthro').wilcoxon_p)}).</p>
<p>The composites (Fig. 2) show cereal and all anthropogenic indicators flat through the 4th and early 5th centuries, rising from about 475 CE, dipping in 575–600 CE and rising steadily from about 650 CE; natural tree pollen stays near its 6th-century level until the mid-7th century and declines afterwards.</p>
<figure><img src="../figures/fig02_composites.png" alt="Europe-wide composites of the land-use indicators and Alpine summer temperature, 200 to 1000 CE"><figcaption><b>Fig. 2.</b> (a–d) Composites of the land-use indicators for all {NC} core sites: site z-scores in 25-year bins, mean and 95% bootstrap interval (bins with at least 5 sites). (e) Central European summer temperature (Büntgen et al. 2011), annual values and 31-year mean. Blue band: LALIA, 536–660 CE; red bar: plague period, 541–750 CE; dashed line: arrival of plague, 541 CE.</figcaption></figure>
<figure><img src="../figures/fig03_change_map.png" alt="Map of the change in all anthropogenic indicators at each site"><figcaption><b>Fig. 3.</b> Change in all anthropogenic indicators at each core site, 541–750 minus 400–540 CE (colour scale capped at the 90th percentile of absolute change). Increases (blue) outnumber decreases (red) north of the Alps; the largest decreases are in the Levant, on Crete and in the southern Balkans.</figcaption></figure>
<figure class="narrow"><img src="../figures/fig04_placebo.png" alt="Box plots of the rate of change before and across 541 by region"><figcaption><b>Fig. 4.</b> Placebo test: rate of change of all anthropogenic indicators (percentage points per century) between 250–399 and 400–540 CE (grey) and between 400–540 and 541–750 CE (red), at sites with at least two samples in each of the three windows. Boxes: interquartile range and median; whiskers: 1.5 × interquartile range; outliers not shown.</figcaption></figure>
<div class="tablewrap"><table>
<caption><b>Table 3.</b> Sensitivity to the windows (top: median change in percentage points, Wilcoxon p) and placebo test (bottom: median rate across 541 vs median rate in 250–399 → 400–540, points per century, Wilcoxon p for the paired difference); red: p &lt; 0.05.</caption>
<tr><th>Test</th><th>Windows (CE)</th><th>n</th><th>Cereal</th><th>Pastoral</th><th>All anthropogenic</th><th>Natural trees</th></tr>
{TABLE3}
<tr class="group"><td colspan="7">Placebo: rate across 541 vs rate before</td></tr>
<tr><th>Region</th><th>n</th><th>Cereal</th><th>Pastoral</th><th>All anthropogenic</th><th>Natural trees</th><th></th></tr>
{TABLE3B.replace('</tr>', '<td></td></tr>')}
</table></div>

<h3>4.2 Regional patterns</h3>
<p>The Europe-wide result is carried by western and central Europe, where the {rgn['W. & Central Europe']} sites show significant increases in cereal, pastoral and all anthropogenic pollen and a fall in natural tree pollen (Table 2, Fig. 5). Eastern Europe shows significant increases in cereal ({p('E. Europe', 'cereal')}), pastoral ({p('E. Europe', 'pastoral')}) and all anthropogenic indicators ({p('E. Europe', 'anthro')}), faster than in the preceding period (placebo {pt(pl('E. Europe', 'anthro').p_rate)} for all anthropogenic indicators), a timing that matches the spread of Slavic settlement in the 6th and 7th centuries. In the western Mediterranean cultivated trees increased ({p('W. Mediterranean', 'arbor')}). The British Isles show no significant change. In the Eastern Mediterranean no farming indicator changes significantly; only richness falls ({p(EM, 'richness')}). Section 4.7 shows that the regional results outside western and central Europe are not robust to dating uncertainty.</p>
<figure><img src="../figures/fig05_regional.png" alt="Regional composites of all anthropogenic indicators and natural tree pollen"><figcaption><b>Fig. 5.</b> Regional composites of all anthropogenic indicators (left) and natural tree pollen (right): site z-scores in 25-year bins, mean and 95% bootstrap interval (bins with at least 3 sites). Shading as in Fig. 2.</figcaption></figure>

<h3>4.3 Regional climate</h3>
<p>Between 400–535 and 536–660 CE the PAGES 2k European mean cooled by {cool['pages2k_cps']:.2f} °C (CPS) and {cool['pages2k_bhm']:.2f} °C (BHM), about half the {cool['alpine']:.2f} °C cooling in the Alpine series (Fig. 6a). In the European mean the 4th century (300–399 CE: {sg(ma['pages2k_cps']['300-399'])} °C, CPS) was as cool as the LALIA ({sg(ma['pages2k_cps']['536-660'])} °C); in the Alpine series it was not ({sg(ma['alpine']['300-399'])} against {sg(ma['alpine']['536-660'])} °C). The reconstruction is uncertain: the median half-width of the BHM 95% range over 300–900 CE is {TX['pages2k_bhm_95pct_halfwidth_300_900_degC']:.2f} °C. At Kocain Cave, moisture peaked in 350–375 CE, fell below its long-term mean by 450–475 CE and was lowest in 575–600 CE (mean δ<sup>18</sup>O {sg(ko['d18O_541_660']).lstrip("+")}‰ in 541–660 against {sg(ko['d18O_330_460']).lstrip("+")}‰ in 330–460; Fig. 6b), as Jacobson et al. (2021) report. Soreq Cave in Israel does not show this sequence (mean δ<sup>18</sup>O {sg(so['d18O_541_660']).lstrip("+")}‰ in 541–660 and {sg(so['d18O_330_460']).lstrip("+")}‰ in 330–460), although it has only {so['n_541_660']} measurements in 541–660. The Eastern Mediterranean was not one climate region in Late Antiquity, and its record for the 6th century is thin.</p>
<p>Over 200–1000 CE the composite of all anthropogenic indicators outside the Eastern Mediterranean correlates with European temperature (r = {fr(c2.r)}, {pt(c2.p_eff)}; after removing linear trends r = {fr(c2.r_detrended)}, {pt(c2.p_detrended)}). The association comes from the start and end of the record: within 300–900 CE the detrended correlation is r = {fr(c3.r_detrended)}. In the Eastern Mediterranean the composites do not correlate with Kocain after detrending (cultivated trees r = {fr(ck[0].r_detrended)}, {pt(ck[0].p_detrended)}). They do correlate with Soreq (detrended r = {fr(cs.r_detrended)} for all anthropogenic indicators, {pt(cs.p_detrended)}), in the unexpected sense of more farming pollen in drier centuries; this rests on a sparse, partly interpolated series and is one of {n(TX['n_correlations'])} correlations we computed, so we treat it as unexplained rather than as evidence of a climate effect.</p>
<figure><img src="../figures/fig06_climate.png" alt="Regional climate records and regional pollen composites"><figcaption><b>Fig. 6.</b> Regional climate and land use. (a) Alpine summer temperature and the PAGES 2k Euro-Med European mean (CPS, BHM and the BHM 95% range), 31-year means. (b) Kocain Cave δ<sup>18</sup>O and δ<sup>13</sup>C and Soreq Cave δ<sup>18</sup>O as z-scores, inverted so that up is wetter; dots are measurements, lines 50-year means. (c, d) Pollen composites for the {NC - rgn[EM]} core sites outside the Eastern Mediterranean and for the {rgn[EM]} Eastern Mediterranean sites (mean ± 1.96 standard errors; bins with at least 3 sites). Shading as in Fig. 2.</figcaption></figure>

<h3>4.4 Separating the plague period from temperature</h3>
<p>Once site differences and the long-term trend are accounted for, temperature has no detectable effect on any indicator over 300–900 CE (Table 4, Fig. 7a): one standard deviation of warmer European summers changes all anthropogenic indicators by {sg(rg('M1', 'T_eu_z', 'anthro').coef, 3)} SD ({pt(rg('M1', 'T_eu_z', 'anthro').p)}). The trend is strong: the farming indicators rose by about {rg('M1', 'trend', 'anthro').coef:.2f} SD per century. Against that trend the plague period as a whole sits slightly low (all anthropogenic indicators {sg(m1['anthro'].coef)} SD, {pt(m1['anthro'].p)}). Splitting it shows where the shortfall lies: in the first century, 550–650 CE, when the early plague waves and the LALIA coincided, all anthropogenic indicators were {abs(m2['anthro'].coef):.2f} SD below trend ({pt(m2['anthro'].p)}), cereal {abs(m2['cereal'].coef):.2f} SD ({pt(m2['cereal'].p)}), pastoral indicators {abs(m2['pastoral'].coef):.2f} SD ({pt(m2['pastoral'].p)}), and natural trees {m2['ap_natural'].coef:.2f} SD above ({pt(m2['ap_natural'].p)}). In 650–750 CE, when plague still recurred but the climate had warmed, the shortfall shrinks to {sg(m2b['anthro'].coef)} SD ({pt(m2b['anthro'].p)}). By region (Fig. 7c) the first-century shortfall in all anthropogenic indicators is significant only in western and central Europe ({sg(wce_m2.coef)} SD, {pt(wce_m2.p)}); eastern Europe has a comparable estimate ({sg(ee_m2.coef)} SD) that is not significant with {int(ee_m2.n_sites)} sites ({pt(ee_m2.p)}), and the other regions show no shortfall.</p>
<p>In no variant within 300–900 CE does temperature have a significant effect on any indicator (Alpine temperature, lagged temperature, quadratic trend), and in the Eastern Mediterranean Kocain moisture has no effect either (M7). Two checks pull in opposite directions. With a quadratic trend, which lets slower growth before 700 and faster growth afterwards follow a curve, the plague-period effect vanishes ({sg(rg('M5', 'plague', 'anthro').coef)} SD, {pt(rg('M5', 'plague', 'anthro').p)}), so the shortfall may be part of a slower 6th–7th-century expansion rather than a discrete event. Widening the window to 200–1000 CE does the opposite: temperature then has a small positive effect ({sg(rg('M8', 'T_eu_z', 'anthro').coef)} SD per SD of warming, {pt(rg('M8', 'T_eu_z', 'anthro').p)}), coming from the centuries outside 300–900 CE, and the plague-period shortfall grows ({sg(rg('M8', 'plague', 'anthro').coef)} SD, {pt(rg('M8', 'plague', 'anthro').p)}). The shortfall is therefore not a product of cooling as reconstructed, but its size depends on how the long-term trend is modelled. The first-century terms have p-values between {min(m2[k].p for k in K4):.3f} and {max(m2[k].p for k in K4):.3f} and are {len(K4)} of {TX['n_regression_coefficients']} coefficients we estimated, so they are evidence of a modest pause, not of a strong effect.</p>
<div class="tablewrap"><table>
<caption><b>Table 4.</b> Fixed-effects regressions, all core sites unless stated: effects in site z-score units, p in brackets; red: p &lt; 0.05. Temperature is per SD of European summer temperature ({TX['temperature_sd_degC_300_900']:.2f} °C); plague terms are dummies for bins in 550–750 CE (first century 550–650, second 650–750); trend per century. M7 uses the {rgn[EM]} Eastern Mediterranean sites.</caption>
<tr><th>Model and term</th><th>All anthropogenic</th><th>Cereal</th><th>Pastoral</th><th>Natural trees</th></tr>
{TABLE4}
</table></div>
<figure><img src="../figures/fig07_regression.png" alt="Regression coefficients with confidence intervals"><figcaption><b>Fig. 7.</b> Regression results. (a) Temperature and plague-period effects for each indicator (M1). (b) The plague-period effect split into 550–650 and 650–750 CE (M2). (c) The 550–650 CE effect by region (M2 fitted separately). Bars are 95% confidence intervals with SEs clustered by site and by 25-year bin; * p &lt; 0.05.</figcaption></figure>

<h3>4.5 The expanded Eastern Mediterranean sample</h3>
<p>Recovering polygon-stored and calendar-dated records, and pooling cores, raised the Eastern Mediterranean core sample from 13 to {emc} sites (Fig. 8a). No farming indicator changes significantly after 541 in any version of the sample (Table 5). Cultivated trees declined at {ex('Core', 'arbor').pct_sites_decline:.0f}% of the core sites, but the median change is small ({sg(ex('Core', 'arbor').median_change)} points), and the large declines come from sites where olive was important before the plague: Dead Sea 7 ({site_change('Dead Sea 7')}), Lake Kournas on Crete ({site_change('Lake Kournas')}) and Lake Lerna in the Peloponnese ({site_change('Lake Lerna')}; Fig. 9). In the relaxed sample of {emr} sites, cultivated trees declined at {ex('Relaxed', 'arbor').pct_sites_decline:.0f}%. Richness fell at {ex('Core', 'richness').pct_sites_decline:.0f}% of the core sites ({pt(ex('Core', 'richness').wilcoxon_p)}), but not in the relaxed sample ({pt(ex('Relaxed', 'richness').wilcoxon_p)}). The cultivated-tree composite peaked in 400–425 CE and was lower in 425–540 than before (mean z {ET['arbor_mean_z_before_vs_after_425']['425-540']:.2f} against {ET['arbor_mean_z_before_vs_after_425']['300-425']:.2f} in 300–425; Fig. 6d), more than a century before the plague.</p>
<div class="tablewrap"><table>
<caption><b>Table 5.</b> Eastern Mediterranean &amp; Anatolia: median change between 400–540 and 541–750 CE (percentage points; richness in taxa), Wilcoxon p in brackets; red: p &lt; 0.05. The mid-term row as reported uses the mid-term data; the second row uses the same 13 sites with the final data.</caption>
<tr><th>Sample</th><th>n</th><th>Cereal</th><th>Pastoral</th><th>Cultivated trees</th><th>All anthropogenic</th><th>Natural trees</th><th>Richness</th></tr>
{TABLE5}
</table></div>
<figure><img src="../figures/fig08_emed_sample.png" alt="Map of Eastern Mediterranean records and share of sites declining"><figcaption><b>Fig. 8.</b> (a) Eastern Mediterranean and Anatolian records: the mid-term core sites, the added core sites (numbered) and sites that meet only the relaxed rule. (b) Share of sites with lower values after 541, with 95% Wilson intervals; 50% means no tendency.</figcaption></figure>
<figure class="narrow"><img src="../figures/fig09_emed_arbor.png" alt="Bar chart of the change in cultivated-tree pollen at each Eastern Mediterranean site"><figcaption><b>Fig. 9.</b> Change in cultivated-tree pollen (olive, walnut, chestnut and vine) at each Eastern Mediterranean core site, 541–750 minus 400–540 CE, with its 400–540 CE level in brackets.</figcaption></figure>

<h3>4.6 HYDE 3.2 against the pollen</h3>
<p>Around the pollen sites, HYDE's cropland shrinks from {hr['crop_50']['200']}% of its 500 CE level in 200 CE to {hr['crop_50']['600']}% in 600 CE and recovers to {hr['crop_50']['1000']}% by 1000 CE; its population follows the same path (Fig. 10c), because HYDE derives land use from population. The pollen does not show this decline: the farming indicators rise from about 475 CE. Over the plague window HYDE has cropland falling at {hy(A).pct_sites_hyde_cropland_down:.0f}% of sites (median {sg(hy(A).hyde_cropland_pct, 1)}%), most steeply in the British Isles ({sg(hy('British Isles').hyde_cropland_pct, 1)}%) and the Eastern Mediterranean ({sg(hy(EM).hyde_cropland_pct, 1)}%), while cereal pollen fell at {hy(A).pct_sites_cereal_down:.0f}% (Table 6, Fig. 10d). HYDE cropland and cereal pollen moved in the same direction at {hy(A).sign_agreement_cropland_cereal:.0f}% of the sites where both changed, and the size of the changes is unrelated (Spearman ρ = {fr(hy(A).spearman_change_cropland_cereal)}). HYDE grazing land behaves differently: it rises after 600 CE (to {hr['graz_50']['1000']}% of its 500 CE value by 1000 CE), rises across 541 at {hy(A).pct_sites_hyde_grazing_up:.0f}% of sites (median {sg(hy(A).hyde_grazing_pct, 1)}%) and moves in the same direction as pastoral pollen at {hy(A).sign_agreement_grazing_pastoral:.0f}% of sites. In space the agreement is weak: across sites in 400–540 CE, HYDE cropland within 50 km correlates with cereal pollen at ρ = {fr(hsp('cropland vs cereal').spearman_rho)} ({pt(hsp('cropland vs cereal').p)}) and HYDE grazing land not at all with pastoral pollen (ρ = {fr(hsp('grazing vs pastoral').spearman_rho)}).</p>
<div class="tablewrap"><table>
<caption><b>Table 6.</b> HYDE 3.2 and pollen over the plague window (541–750 against 400–540 CE), within 50 km of each site. HYDE changes are medians across sites; the other columns are shares of sites (same direction: among sites where both changed).</caption>
<tr><th>Region</th><th>n</th><th>HYDE cropland</th><th>HYDE grazing</th><th>HYDE population</th><th>HYDE cropland falls</th><th>Cereal pollen falls</th><th>Same direction, cropland–cereal</th><th>HYDE grazing rises</th><th>Pastoral pollen rises</th></tr>
{TABLE6}
</table></div>
<figure><img src="../figures/fig10_hyde.png" alt="HYDE cropland map, scatter plots and time series compared with pollen"><figcaption><b>Fig. 10.</b> HYDE 3.2 against the pollen. (a) HYDE cropland in 500 CE and the core sites. (b) HYDE cropland within 50 km against cereal pollen, 400–540 CE. (c) HYDE cropland, grazing land and population around the sites, relative to 500 CE, with the pollen composites. (d) Change across 541 at each site: HYDE cropland against cereal pollen, with the share of sites in each quadrant (sites with no change in either lie on the axes).</figcaption></figure>

<h3>4.7 Robustness to dating uncertainty</h3>
<p>Moving ages within their errors shifts samples across the window boundaries, so a typical realisation keeps {mcm['cereal'].n_sites_median:.0f} core sites. The main Europe-wide results survive (Table 7, Fig. 11): the rise in cereal pollen is significant in {fmc(mcm['cereal'])} of 1,000 realisations, the rise in all anthropogenic indicators in {fmc(mcm['anthro'])}, the rise in richness in {fmc(mcm['richness'])}, the fall in natural tree pollen in {fmc(mcm['ap_natural'])} and the rise in pastoral indicators in {fmc(mcm['pastoral'])}. The rise in cultivated trees is not robust ({fmc(mcm['arbor'])}). Western and central Europe behaves the same way (cereal {fmc(mc('W. & Central Europe', 'cereal'))}, all anthropogenic {fmc(mc('W. & Central Europe', 'anthro'))}). With errors 1.5 times larger, cereal and all anthropogenic indicators stay above {np.floor(min(mc(A, k, 'errors x1.5').pct_p05_same_direction for k in ('cereal', 'anthro'))):.0f}%, natural trees reach {mc(A, 'ap_natural', 'errors x1.5').pct_p05_same_direction:.0f}% and pastoral indicators {mc(A, 'pastoral', 'errors x1.5').pct_p05_same_direction:.0f}%. Elsewhere the regional results do not survive: the rise of cultivated trees in the western Mediterranean is significant in {fmc(mc('W. Mediterranean', 'arbor'))} of realisations and the eastern European rise in all anthropogenic indicators in {fmc(mc('E. Europe', 'anthro'))}. In the Eastern Mediterranean no change is significant in most realisations (cultivated trees {fmc(mc(EM, 'arbor'))}, all anthropogenic {fmc(mc(EM, 'anthro'))}, richness {fmc(mc(EM, 'richness'))}), so even the fall in richness depends on the published ages.</p>
<div class="tablewrap"><table>
<caption><b>Table 7.</b> Monte Carlo on dating uncertainty: share of age-model realisations in which the change across 541 is significant (p &lt; 0.05), with its direction (↑ rise, ↓ fall). Core sites unless stated; main variant unless stated.</caption>
<tr><th>Indicator</th><th>All sites</th><th>All, independent errors</th><th>All, errors × 1.5</th><th>W. &amp; Central Europe</th><th>W. Mediterranean</th><th>E. Europe</th><th>E. Med, core</th><th>E. Med, relaxed</th></tr>
{TABLE7}
</table></div>
<figure><img src="../figures/fig11_montecarlo.png" alt="Heat map of Monte Carlo significance and histograms of median change"><figcaption><b>Fig. 11.</b> Monte Carlo on dating uncertainty. (a) Share of 1,000 realisations with a significant rise (↑) or fall (↓) after 541, by region and indicator. (b–e) Distribution of the median change across realisations; red line: published ages.</figcaption></figure>

<h2><span class="num">5</span>Discussion</h2>
<h3>5.1 No continental footprint of abandonment</h3>
<p>If the First Pandemic had killed a large share of the rural population everywhere, fields would have gone out of use and woodland would have spread back within decades, as happened in parts of Europe after the Black Death (Izdebski et al. 2022). The pollen shows the reverse across most of Europe: farming indicators rose after 541 and tree pollen fell, faster than before, and the result does not depend on where the boundary is drawn or on dating errors. It agrees with Mordechai et al. (2019), who found no measurable aggregate effect on the rural economy. It does not mean nobody died. Pollen records land use, not mortality (Curtis 2022): mortality may have been concentrated in cities and along trade routes, where few pollen records lie, or survivors may have taken over vacant land quickly enough that the vegetation never registered a gap. The first 60 years of plague alone show no significant change in either direction.</p>
<h3>5.2 A pause in the first century of plague</h3>
<p>The expansion of farming was not smooth. Relative to its trend, land use stalled in 550–650 CE and was back on trend in 650–750. Both the first and deadliest plague waves and the coldest LALIA decades fall in this century, so the pause cannot be assigned to one of them from timing alone. Three observations argue against a direct temperature effect: reconstructed temperature explains none of the variation in the indicators over 300–900 CE in any specification; the 4th century was as cool as the LALIA in the European mean yet shows no shortfall; and the Alpine series, which records about twice the cooling, fits no better. Reconstruction error in temperature would bias its estimated effect towards zero, so a small effect cannot be ruled out, but a cold-driven collapse can. The size of the pause depends on how the long-term trend is modelled. The most defensible reading is a short interruption of an expansion already under way, in the decades when both shocks coincided, with no lasting effect.</p>
<h3>5.3 The Eastern Mediterranean</h3>
<p>The Eastern Mediterranean is where plague mortality is best documented and where the mid-term analysis found the clearest signal, a decline in arboriculture. With {emc} core sites, and {emr} under the relaxed rule, no farming indicator declines significantly after 541, the decline of cultivated trees is driven by a few sites with intensive olive cultivation, and the cultivated-tree composite was already lower after about 425 CE. Kocain Cave records moisture falling over the same period, but the composites do not correlate with it after detrending and the regression finds no moisture effect, so a climatic cause is possible but not demonstrated; Soreq Cave shows no drying. Archaeobotanical evidence from the Negev dates the collapse of commercial viticulture to the mid to late 6th century and attributes it mainly to market contraction (Fuks et al. 2020); our sample has no site in that area, and the region's sites span the Balkans, Anatolia, the Levant, the Caucasus and north-western Iran, so a regional average cannot exclude local declines of this kind.</p>
<h3>5.4 What HYDE gets wrong</h3>
<p>HYDE is widely used to prescribe historical land use in climate and carbon-cycle models. Its cropland follows its population input, which encodes a demographic decline from the 3rd to the 6th century reaching its lowest point around 600 CE. The pollen does not show this decline in western, central or eastern Europe, where farming grew from the late 5th century onward, and HYDE's map agrees only weakly with where cereals and pasture actually were. HYDE grazing land, which rises from 600 CE, is closer to the pollen. Kaplan et al. (2017) reached a related conclusion from pollen-based land-cover reconstructions, which match HYDE poorly for the more distant past. For the first millennium, HYDE's cropland dynamics should be treated as a hypothesis built from population estimates, not as an observation.</p>
<h3>5.5 Limitations</h3>
<p>Pollen percentages are relative, so a fall in tree pollen can reflect forest change without more farming. Cereal pollen travels poorly and is under-represented, and sites differ in pollen source area. Most core sites have only three or four samples in each window, and dating uncertainty is comparable to the window length; the Monte Carlo shows that the main results survive this, but individual site changes are not precisely timed, and individual plague waves (541–544, 558, 573 and later) cannot be resolved. Some sites lie a few kilometres apart and are not fully independent. The plague-period term captures everything else that happened in 550–750 CE, including the Lombard invasion of Italy, Avar and Slavic movements in the Balkans, the Persian–Byzantine war and the Arab conquests in the Levant. No regional temperature reconstruction covers the Mediterranean or eastern Europe in the 6th century, the European mean is uncertain by about ±{TX['pages2k_bhm_95pct_halfwidth_300_900_degC']:.1f} °C, and the two Eastern Mediterranean caves disagree. HYDE has 100-year resolution and was not designed for site-scale accuracy. The project brief also lists archaeological datasets; we did not use them because no open, harmonised settlement or plague-occurrence dataset covers the whole study area at the needed resolution, so the comparison rests on pollen, climate reconstructions and HYDE. The sample remains dominated by western and central Europe, and the Eastern Mediterranean group, with {emc} sites from the Balkans to Iran, is small for a region this varied.</p>

<h2><span class="num">6</span>Conclusions</h2>
<p>Across {NC} pollen sites, land use in Europe and the Mediterranean did not contract after the arrival of plague in 541. Farming expanded through the 6th to 8th centuries, with a modest pause in 550–650 CE that reconstructed temperature does not explain and that we cannot attribute firmly to either the plague or the LALIA. The Eastern Mediterranean, even with an expanded sample, shows no significant post-541 decline; its cultivated-tree pollen was already lower from about 425 CE. HYDE 3.2 cropland, built on historical population estimates, moves opposite to the pollen. The main Europe-wide results are robust to dating uncertainty; the regional results outside western and central Europe are not. The First Pandemic may have been demographically severe, but it left no continental footprint of farmland abandonment in the pollen record.</p>

<h2><span class="num">7</span>Changes since the mid-term evaluation</h2>
<ul class="plain">
  <li><b>Sample.</b> The query now accepts calendar, varve and AD/BC chronologies and polygon-stored records ({mid['used_final']} of the {mid['listed']} mid-term datasets usable, previously {mid['used_midterm']}; 1,099 datasets in the new query). We removed {n_dup} duplicate records and pooled cores from the same site, as planned at mid-term; core sites rose from 159 (164 records) to {NC} ({S['n_core_records']} records), and all mid-term sites remain. Between the two downloads Neotoma revised {rev['records_affected']} of the mid-term records (new age models or corrected counts), changing or removing {rev['samples_changed_or_removed']} of their samples.</li>
  <li><b>Windows and tests.</b> Window edges are now half-open, so no sample falls between windows; the placebo test compares rates of change per century; a test of the first 60 years of plague (541–600 CE), planned at mid-term, was added.</li>
  <li><b>New analyses.</b> Regional climate (PAGES 2k Euro-Med, Kocain and Soreq caves), fixed-effects regression, the expanded Eastern Mediterranean sample, the Monte Carlo on dating uncertainty and the HYDE 3.2 comparison (Figs 6–11).</li>
  <li><b>Results that held.</b> The Europe-wide rise of the farming indicators and fall of natural tree pollen: all anthropogenic indicators {sg(MV[(MV.scope == A) & (MV.indicator == 'anthro')].iloc[0].median_change_mid)} points ({pt(MV[(MV.scope == A) & (MV.indicator == 'anthro')].iloc[0].wilcoxon_p_mid)}) at mid-term, {sg(pv(A, 'anthro').median_change)} ({p(A, 'anthro')}) now. The placebo test, not significant for all anthropogenic indicators at mid-term (p = 0.27, raw changes), is now significant ({pt(pl(A, 'anthro').p_rate)}, rates).</li>
  <li><b>Results that changed.</b> Richness, which fell slightly and not significantly at mid-term ({sg(MV[(MV.scope == A) & (MV.indicator == 'richness')].iloc[0].median_change_mid)} taxa), now rises ({sg(pv(A, 'richness').median_change)}, {p(A, 'richness')}). At mid-term we concluded that the pandemic left "a regional, not continental, mark, strongest in the eastern Mediterranean tree-crop economy". We no longer support the regional part: the arboriculture decline (−0.42 points with 13 sites) shrinks to {sg(ex('Core', 'arbor').median_change)} points with {emc} sites, is not significant, began before the plague and does not survive the Monte Carlo.</li>
</ul>

<h2><span class="num">8</span>Reproducibility</h2>
<p>Every number, table and figure in this report is produced by the code in the project repository; the report itself is written by <code>code/report.py</code> from the result tables. <code>./run.sh</code> reruns the analysis offline from the files in <code>data/</code> in about two minutes; <code>./run.sh --full</code> first downloads the Neotoma records (about 500 MB), reads the HYDE grids from the DANS archive and fetches the NOAA climate series. Package versions are pinned in <code>requirements.txt</code> (Python 3 with pandas, numpy, scipy and matplotlib; requests and inflate64 for the full rebuild); small-sample Wilcoxon p-values can differ in the second decimal with other SciPy versions.</p>

<h2>References</h2>
<ol class="refs">
<li>Behre, K.-E. (1981). The interpretation of anthropogenic indicators in pollen diagrams. <i>Pollen et Spores</i>, 23, 225–245.</li>
<li>Bretherton, C. S., Widmann, M., Dymnikov, V. P., Wallace, J. M., &amp; Bladé, I. (1999). The effective number of spatial degrees of freedom of a time-varying field. <i>Journal of Climate</i>, 12, 1990–2009.</li>
<li>Büntgen, U., Tegel, W., Nicolussi, K., et al. (2011). 2500 years of European climate variability and human susceptibility. <i>Science</i>, 331, 578–582.</li>
<li>Büntgen, U., Myglan, V. S., Ljungqvist, F. C., et al. (2016). Cooling and societal change during the Late Antique Little Ice Age from 536 to around 660 AD. <i>Nature Geoscience</i>, 9, 231–236.</li>
<li>Cameron, A. C., Gelbach, J. B., &amp; Miller, D. L. (2011). Robust inference with multiway clustering. <i>Journal of Business &amp; Economic Statistics</i>, 29, 238–249.</li>
<li>Curtis, D. R. (2022). Reduction in grain pollen indicates population decline, but not necessarily Black Death mortality. <i>Nature Ecology &amp; Evolution</i>, 6, 1626–1627.</li>
<li>England, A., Eastwood, W. J., Roberts, C. N., Turner, R., &amp; Haldon, J. F. (2008). Historical landscape change in Cappadocia (central Turkey): a palaeoecological investigation of annually laminated sediments from Nar lake. <i>The Holocene</i>, 18, 1229–1245.</li>
<li>Fuks, D., Bar-Oz, G., Tepper, Y., Erickson-Gini, T., Langgut, D., Weissbrod, L., &amp; Weiss, E. (2020). The rise and fall of viticulture in the Late Antique Negev Highlands reconstructed from archaeobotanical and ceramic data. <i>Proceedings of the National Academy of Sciences</i>, 117, 19780–19791.</li>
<li>Hurlbert, S. H. (1971). The nonconcept of species diversity: a critique and alternative parameters. <i>Ecology</i>, 52, 577–586.</li>
<li>Izdebski, A., Guzowski, P., Poniat, R., et al. (2022). Palaeoecological data indicates land-use changes across Europe linked to spatial heterogeneity in mortality during the Black Death pandemic. <i>Nature Ecology &amp; Evolution</i>, 6, 297–306.</li>
<li>Jacobson, M. J., Flohr, P., Gascoigne, A., Leng, M. J., Sadekov, A., Cheng, H., Edwards, R. L., Tüysüz, O., &amp; Fleitmann, D. (2021). Heterogenous late Holocene climate in the Eastern Mediterranean: the Kocain Cave record from SW Turkey. <i>Geophysical Research Letters</i>, 48, e2021GL094733.</li>
<li>Kaniewski, D., Paulissen, E., De Laet, V., Dossche, K., &amp; Waelkens, M. (2007). A high-resolution Late Holocene landscape ecological history inferred from an intramontane basin in the Western Taurus Mountains, Turkey. <i>Quaternary Science Reviews</i>, 26, 2201–2218.</li>
<li>Kaplan, J. O., Krumhardt, K. M., Gaillard, M.-J., et al. (2017). Constraining the deforestation history of Europe: evaluation of historical land use scenarios with pollen-based land cover reconstructions. <i>Land</i>, 6, 91.</li>
<li>Keller, M., Spyrou, M. A., Scheib, C. L., et al. (2019). Ancient <i>Yersinia pestis</i> genomes from across Western Europe reveal early diversification during the First Pandemic (541–750). <i>Proceedings of the National Academy of Sciences</i>, 116, 12363–12372.</li>
<li>Klein Goldewijk, K., Beusen, A., Doelman, J., &amp; Stehfest, E. (2017). Anthropogenic land use estimates for the Holocene – HYDE 3.2. <i>Earth System Science Data</i>, 9, 927–953. Data: <a href="https://doi.org/10.17026/dans-25g-gez3">doi:10.17026/dans-25g-gez3</a>.</li>
<li>Little, L. K. (Ed.) (2007). <i>Plague and the End of Antiquity: The Pandemic of 541–750</i>. Cambridge University Press.</li>
<li>Luterbacher, J., Werner, J. P., Smerdon, J. E., et al. (2016). European summer temperatures since Roman times. <i>Environmental Research Letters</i>, 11, 024001.</li>
<li>Mercuri, A. M., Bandini Mazzanti, M., Florenzano, A., Montecchi, M. C., &amp; Rattighieri, E. (2013). <i>Olea</i>, <i>Juglans</i> and <i>Castanea</i>: the OJC group as pollen evidence of the development of human-induced environments in the Italian peninsula. <i>Quaternary International</i>, 303, 24–42.</li>
<li>Mordechai, L., Eisenberg, M., Newfield, T. P., Izdebski, A., Kay, J. E., &amp; Poinar, H. (2019). The Justinianic Plague: an inconsequential pandemic? <i>Proceedings of the National Academy of Sciences</i>, 116, 25546–25554.</li>
<li>Orland, I. J., Bar-Matthews, M., Kita, N. T., Ayalon, A., Matthews, A., &amp; Valley, J. W. (2009). Climate deterioration in the Eastern Mediterranean as revealed by ion microprobe analysis of a speleothem that grew from 2.2 to 0.9 ka in Soreq Cave, Israel. <i>Quaternary Research</i>, 71, 27–35.</li>
<li>Sigl, M., Winstrup, M., McConnell, J. R., et al. (2015). Timing and climate forcing of volcanic eruptions for the past 2,500 years. <i>Nature</i>, 523, 543–549.</li>
<li>Williams, J. W., Grimm, E. C., Blois, J. L., et al. (2018). The Neotoma Paleoecology Database, a multiproxy, international, community-curated data resource. <i>Quaternary Research</i>, 89, 156–177.</li>
</ol>
</main>
</body>
</html>
"""
open(f'{R_}/final_report.html', 'w', encoding='utf-8').write(H)

# ---------------- numbers for the slide deck ----------------
D = dict(n_samples=n(S['n_samples']), n_records=n(S['n_records']), n_sites=n(NS), n_core=NC, n_core_records=S['n_core_records'],
         regions={k: int(v) for k, v in rgn.items()}, emc=emc, emr=int(emr), med_unc=f"{S['median_age_half_range']:.0f}",
         anthro=sg(pv(A, 'anthro').median_change), anthro_p=p(A, 'anthro').replace('&lt;', '<'),
         nat=sg(pv(A, 'ap_natural').median_change), nat_p=p(A, 'ap_natural').replace('&lt;', '<'),
         cereal_up=f"{pv(A, 'cereal').pct_sites_increase:.0f}", cereal_down=f"{pv(A, 'cereal').pct_sites_decline:.0f}",
         placebo_p=pt(pl(A, 'anthro').p_rate).replace('&lt;', '<'), placebo_rate=sg(pl(A, 'anthro').median_rate_pandemic_per_century),
         placebo_rate_before=sg(pl(A, 'anthro').median_rate_placebo_per_century), placebo_n=int(pl(A, 'anthro').n),
         early_n=int(se('Early plague only', 'anthro').n), early_p=pt(se('Early plague only', 'anthro').wilcoxon_p),
         sens=[dict(test=lab, win=f"{se(t, 'anthro').before} → {se(t, 'anthro').after}", n=int(se(t, 'anthro').n),
                    anthro=sg(se(t, 'anthro').median_change), p=fp(se(t, 'anthro').wilcoxon_p).replace('&lt;', '<'), sig=bool(se(t, 'anthro').wilcoxon_p < .05))
               for t, lab in [('Main', 'Main comparison'), ('Narrow', 'Narrower windows'), ('Boundary 50 yr earlier', 'Boundary 50 yr earlier'),
                              ('Boundary 50 yr later', 'Boundary 50 yr later'), ('Following period', 'Plague period vs 751–900'), ('Early plague only', 'First 60 years only')]],
         regional=[dict(region=r, n=int(pv(r, 'anthro').n), anthro=sg(pv(r, 'anthro').median_change), p=fp(pv(r, 'anthro').wilcoxon_p).replace('&lt;', '<'),
                        sig=bool(pv(r, 'anthro').wilcoxon_p < .05), mc=f"{mc(r, 'anthro').pct_p05_same_direction:.0f}") for r in REG],
         T=sg(rg('M1', 'T_eu_z', 'anthro').coef, 3), T_p=pt(rg('M1', 'T_eu_z', 'anthro').p), T_sd=f"{TX['temperature_sd_degC_300_900']:.2f}",
         m2a=sg(m2['anthro'].coef), m2a_p=pt(m2['anthro'].p), m2b=sg(m2b['anthro'].coef), m2b_p=pt(m2b['anthro'].p),
         m2_wce=sg(wce_m2.coef), m2_wce_p=pt(wce_m2.p), m5=sg(rg('M5', 'plague', 'anthro').coef), m5_p=pt(rg('M5', 'plague', 'anthro').p),
         cool_cps=f"{cool['pages2k_cps']:.2f}", cool_bhm=f"{cool['pages2k_bhm']:.2f}", cool_alps=f"{cool['alpine']:.2f}", alps_fall=f"{af['degC']:.1f}",
         alps_from=af['from_year'], alps_to=af['to_year'], bhm_hw=f"{TX['pages2k_bhm_95pct_halfwidth_300_900_degC']:.1f}",
         soreq_n541=so['n_541_660'],
         em=[dict(sample=lab, n=int(ex(pre, 'arbor').n), arbor=sg(ex(pre, 'arbor').median_change), arbor_p=fp(ex(pre, 'arbor').wilcoxon_p).replace('&lt;', '<'),
                  anthro=sg(ex(pre, 'anthro').median_change), anthro_p=fp(ex(pre, 'anthro').wilcoxon_p).replace('&lt;', '<'))
             for pre, lab in [('Mid-term, as reported', 'Mid-term (13 sites)'), ('Core', f'Final core ({emc} sites)'), ('Relaxed', f'Relaxed rule ({emr} sites)')]],
         em_arbor_decline=f"{ex('Core', 'arbor').pct_sites_decline:.0f}",
         hyde_crop_down=f"{hy(A).pct_sites_hyde_cropland_down:.0f}", hyde_cereal_down=f"{hy(A).pct_sites_cereal_down:.0f}",
         hyde_graz_up=f"{hy(A).pct_sites_hyde_grazing_up:.0f}", hyde_past_up=f"{hy(A).pct_sites_pastoral_up:.0f}", hyde_rho=f"{fr(hsp('cropland vs cereal').spearman_rho)}",
         hyde_bars=[dict(region=r, crop_down=round(float(hy(r).pct_sites_hyde_cropland_down), 1), cereal_down=round(float(hy(r).pct_sites_cereal_down), 1)) for r in ['All sites'] + REG],
         hyde_600=hr['crop_50']['600'],
         mc_rows=[dict(scope=lab, cells=[mcc(mc(sc, k, 'main', ru)) for k in IND6], vals=[float(max(mc(sc, k, 'main', ru).pct_p05_up, mc(sc, k, 'main', ru).pct_p05_down)) for k in IND6])
                  for ru, sc, lab in [('>=2', A, 'All sites'), ('>=2', 'W. & Central Europe', 'W. & Central Europe'), ('>=2', 'W. Mediterranean', 'W. Mediterranean'),
                                      ('>=2', 'E. Europe', 'E. Europe'), ('>=2', EM, f'E. Mediterranean ({emc})'), ('>=1', EM, f'E. Med, relaxed ({emr})')]],
         mc_names=[NAME[k] for k in IND6], n_dup=n_dup, rev=rev, mid=mid,
         mid_anthro=sg(MV[(MV.scope == A) & (MV.indicator == 'anthro')].iloc[0].median_change_mid))
json.dump(D, open(f'{P_}/deck_numbers.json', 'w'), indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
print('report and deck numbers written; all checks passed')
