"""Definitions shared by analyse.py, final.py and slide_figs.py, so that every script uses the same windows,
indicators, regions and plot conventions."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

IND = {'cereal': 'Cereal', 'arbor': 'Cultivated trees (OJCV)', 'pastoral': 'Pastoral',
       'anthro': 'All anthropogenic', 'ap_natural': 'Natural trees & shrubs', 'richness': 'Richness E(S100)'}
REG = ['E. Mediterranean & Anatolia', 'W. Mediterranean', 'W. & Central Europe', 'British Isles', 'E. Europe']
EM = REG[0]
COL = dict(zip(REG, ['#d95f02', '#e7298a', '#1b9e77', '#7570b3', '#66a61e']))

# Windows are calendar years, first and last year included; ages are continuous, so a sample belongs to a window
# when start <= age < last + 1 (an age of 540.6 CE is in 400-540, one of 750.4 CE in 541-750).
PRE, POST, PLACEBO, REC = (400, 540), (541, 750), (250, 399), (751, 900)


def inwin(age, w):
    return (age >= w[0]) & (age < w[1] + 1)


def mid(w):
    return (w[0] + w[1] + 1) / 2


def binc(age):
    """Centre of the 25-year bin (0-25 CE -> 12.5)."""
    return (np.asarray(age) // 25) * 25 + 12.5


LALIA_C, PLAGUE_C = '#9ecae1', '#b2182b'


def shade(ax, legend=False, loc='upper left', fontsize=8):
    """LALIA as a blue band; the plague period as a red bar along the top of the panel and a dashed line at 541."""
    ax.axvspan(536, 660, color=LALIA_C, alpha=.45, lw=0, zorder=0)
    ax.axvspan(541, 750, ymin=.965, ymax=1, color=PLAGUE_C, alpha=.85, lw=0, zorder=5)
    ax.axvline(541, color=PLAGUE_C, lw=1.2, ls='--', zorder=1)
    if legend:
        return [Patch(color=LALIA_C, alpha=.45, label='LALIA cooling, 536–660'),
                Line2D([], [], color=PLAGUE_C, lw=4, label='Plague period, 541–750 (dashed: arrival 541)')]


def style():
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                         'savefig.dpi': 200, 'figure.dpi': 100})


def land(ax, G):
    """Land/sea background from the HYDE 3.2 land mask (0.25-degree grid written by hyde.py)."""
    ext = [G['lon'][0] - .125, G['lon'][-1] + .125, G['lat'][-1] - .125, G['lat'][0] + .125]
    ax.set_facecolor('#dbe9f4')
    ax.imshow(np.where(np.isnan(G['crop500']), np.nan, 1), cmap='Greys', vmin=0, vmax=5, zorder=0, aspect='auto', extent=ext)
    return ext
