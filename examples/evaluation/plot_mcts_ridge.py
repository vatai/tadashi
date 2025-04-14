# import pandas as pd
import json
# import os
# import glob
from pathlib import Path

import matplotlib as mpl
import matplotlib.gridspec as grid_spec
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.lines import Line2D

plt.style.use('seaborn-v0_8-paper')
sns.set_theme(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})


def parse_jsonl(filepath):
    cnt_evals = []
    speedups = []
    with open(filepath, 'r') as f:
        for line in f:
            # Trim whitespace and check if line is empty
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            # Check if required keys exist
            if 'cnt_evals' in data and 'speedup' in data:
                cnt_evals.append(data['cnt_evals'])
                speedups.append(data['speedup'])
            else:
                print(f"Warning: Skipping line in {filepath} due to missing keys: {line}")
    # Ensure lists are sorted by cnt_evals for proper plotting
    return cnt_evals, speedups

class AnchoredScaleBar(mpl.offsetbox.AnchoredOffsetbox):
    """ size: length of bar in data units
        extent : height of bar ends in axes units """
    def __init__(self, size=1, extent = 0.02, label="", loc=2, ax=None,
                 pad=0.4, borderpad=0.5, ppad = 0, sep=2, prop=None, 
                 frameon=True, linekw={}, **kwargs):
        if not ax:
            ax = plt.gca()
        trans = ax.get_yaxis_transform()
        size_bar = mpl.offsetbox.AuxTransformBox(trans)
        line = Line2D([0,0], [0,size], **linekw)
        vline1 = Line2D([-extent/2.,extent/2.], [0,0], **linekw)
        vline2 = Line2D([-extent/2.,extent/2.], [size,size], **linekw)
        size_bar.add_artist(line)
        size_bar.add_artist(vline1)
        size_bar.add_artist(vline2)
        txt = mpl.offsetbox.TextArea(label,
                                    # minimumdescent=False
                                    )
        self.vpac = mpl.offsetbox.VPacker(children=[size_bar,txt],  
                                 align="center", pad=ppad, sep=sep) 
        mpl.offsetbox.AnchoredOffsetbox.__init__(self, loc, pad=pad, 
                 borderpad=borderpad, child=self.vpac, prop=prop, frameon=frameon,
                 **kwargs)


fig = plt.figure(figsize=(6,12))
i = 0
ax_objs = []
directory = Path("./data")
json_files = list(sorted(directory.glob("*.jsonl")))

#cmap = plt.colormaps['brg']
#cmap = plt.colormaps['ocean']

cmap = sns.color_palette("blend:#21599c,#b59610", as_cmap=True)
#cmap = sns.color_palette("blend:#7AB,#EDA", as_cmap=True)
colors = [cmap(i) for i in np.linspace(0, 1, len(json_files)+3)] # Evenly spaced
#colors = sns.color_palette('tab20', n_colors=len(json_files))
#colors = sns.cubehelix_palette(len(json_files), rot=-.25, light=.7)

gs = grid_spec.GridSpec(len(json_files),1)
for f in json_files:
    cnt_evals, speedups = parse_jsonl(f)
    ax_objs.append(fig.add_subplot(gs[i:i+1, 0:]))
    ax = ax_objs[-1]
    # ax.plot(cnt_evals, speedups,
    #         drawstyle="steps-post",
    #         color="#000000")
    ax.fill_between(cnt_evals, speedups, 
                             alpha=0.9,
                             step="post",
                             color=colors[i])
    ax.set_xlim(0,3000)
    ax.set_ylim(0,100)

    # make background transparent
    rect = ax_objs[-1].patch
    rect.set_alpha(0)

    # remove borders, axis ticks, and labels
    ax_objs[-1].set_yticklabels([])

    if i == len(json_files)-1:
        ax_objs[-1].set_xlabel("Number of Evaluations",
                              # fontsize=16,
                               #fontweight="bold"
                              )
    else:
        ax_objs[-1].set_xticklabels([])

    #spines = ["top","right","left","bottom"]
    #ax.spines[['right', 'top', 'left', 'bottom']].
    spines = ["top","right","left"]
    for s in spines:
        ax.spines[s].set_visible(False)
    #ax.spines["bottom"].set_linestyle(":")
    ax.spines['bottom'].set_linestyle((0,(4,4)))
    ax.spines["bottom"].set_linewidth(0.5)
    kernel = f.name.split(".")[0]
    #print(f)
    ax_objs[-1].text(-20, 0,
                     kernel + f"\n({speedups[-1]:0.1F}x)",
                     fontsize=12,
                     ha="right",
                    # color=colors[i]
                    )
    i += 1

gs.update(hspace=-0.57)
ob = AnchoredScaleBar(size=50, label="50x", loc=4, frameon=True,
                       pad=0.6, sep=4, linekw=dict(color="black", linewidth=0.5),) 
ax.add_artist(ob)
#fig.text(0.07,0.85,"Distribution of Aptitude Test Results from 18 – 24 year-olds",fontsize=20)

plt.tight_layout()
#plt.show()
plt.savefig("mcts_ridge.pdf", bbox_inches="tight")


#sns.color_palette("blend:#21599c,#b59610", as_cmap=True)
#sns.color_palette("dark:#5A9_r", as_cmap=True)
