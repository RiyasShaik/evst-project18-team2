"""Step 1c: regional climate series from NOAA Paleoclimatology.
PAGES 2k Euro-Med European-mean JJA temperature (Luterbacher et al. 2016; CPS and BHM versions) and two
Eastern Mediterranean speleothem records: Kocain Cave, SW Turkey (Jacobson et al. 2021) and Soreq Cave, Israel (Orland et al. 2009)."""
import io, sys, requests
import pandas as pd

OUT = sys.argv[1] if len(sys.argv) > 1 else 'data'
NOAA = 'https://www.ncei.noaa.gov/pub/data/paleo/'


def noaa(path):
    t = requests.get(NOAA + path, timeout=120).text
    return pd.read_csv(io.StringIO(''.join(l + '\n' for l in t.splitlines() if not l.startswith('#'))), sep='\t')


cps = noaa('pages2k/EuroMed2k/eujja_2krecon_nested_cps-noaa.txt')
bhm = noaa('pages2k/EuroMed2k/EuMeanDist_noInst-noaa.txt')
P = pd.DataFrame(dict(year=cps.age_CE, cps=cps.temp_mean, cps_lo=cps['temp-Lower2s'], cps_hi=cps['temp-Upper2s'])).merge(
    pd.DataFrame(dict(year=bhm.age_CE, bhm=bhm.temp_mean, bhm_lo=bhm['temp-2.5_perc'], bhm_hi=bhm['temp-97.5_perc'])), on='year')
P = P[(P.year >= 0) & (P.year <= 1200)]
P.to_csv(f'{OUT}/pages2k_euromed.csv', index=False, float_format='%.4f')

k = noaa('speleothem/asia/turkey/kocain2021iso.txt')
s = noaa('speleothem/asia/israel/soreq2009d18o.txt')
E = pd.concat([pd.DataFrame(dict(record='Kocain', age_ce=k.age_AD, d18O=k.d18O, d13C=k.d13C)),
               pd.DataFrame(dict(record='Soreq', age_ce=1950 - s.age_yrBP, d18O=s.d18O_VPDB))])
E = E[(E.age_ce >= 0) & (E.age_ce <= 1200)].sort_values(['record', 'age_ce'])
E.to_csv(f'{OUT}/emed_climate.csv', index=False, float_format='%.3f')
print(len(P), 'PAGES 2k years;', E.record.value_counts().to_dict())
