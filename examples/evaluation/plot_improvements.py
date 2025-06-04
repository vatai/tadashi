
#f = open("output_ALL_XL.txt").readlines()
f = open("results_ScriptPolybench.txt").readlines()


names = []
bl = []
post = []


for line_i in range(len(f)):

	if "[STARTING NEW APP]" in f[line_i]:
		app_name = f[line_i+1]

		app_baseline = f[line_i+3]

		i = line_i
		while not "32:" in f[i]:
			i += 1

		app_post = f[i]

		#print("---------")
		#print(app_name)
		#print(app_baseline)
		#print(app_post)

		names.append( app_name.strip().split("/")[-1] )
		bl.append( float(app_baseline.strip().split(": ")[1]) )
		post.append( float(app_post.strip().split(": ")[1]) )

	


import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as colors
import json
from pathlib import Path

plt.rcParams["text.latex.preamble"] = (
    r"\usepackage{libertine}\usepackage{zi4}\usepackage{newtxmath}"
)
params = {
    "axes.titlesize": 16,
    "axes.labelsize": 16,
    "legend.fontsize": 16,
    "text.usetex": True,
    "font.size": 11,
    "font.family": "libertine",
    # "text.latex.unicode": True,
}
plt.rcParams.update(params)


fontsize = 12

# Example data
array1 = np.array(bl)
array2 = np.array(post)
labels = np.array(names)

# Filter: keep only values where at least one is >= 0.01
mask = ~((array1 < 0.01) & (array2 < 0.01))

for l in sorted(labels):
	if not l in np.array(labels)[mask]:
		print(l)

array1 = array1[mask]
array2 = array2[mask]
labels = np.array(labels)[mask]

ratios = array1 / array2

sorted_indices = np.argsort(labels)
labels = labels[sorted_indices]
ratios = ratios[sorted_indices]
ratios = np.array([r if r>1 else 1 for r in ratios])
print(ratios)

# Normalize with midpoint at 1
norm = colors.TwoSlopeNorm(vmin=0, vcenter=1.0, vmax=np.max(ratios)/5)
cmap = cm.RdYlGn
bar_colors = cmap(norm(ratios))

x = np.arange(len(labels))
width = 0.6

fig, ax = plt.subplots()


# Reference line at ratio = 1
ax.axhline(y=1.0, color='#ff6961', linestyle='--', linewidth=2)
ax.axhline(y=2.0, color='lightgray', linestyle='-', linewidth=1)
ax.axhline(y=5.0, color='lightgray', linestyle='-', linewidth=1)
ax.axhline(y=10.0, color='lightgray', linestyle='-', linewidth=1)

# Plot colored ratio bars
bars = ax.bar(x, ratios, width, color=bar_colors, edgecolor='black', zorder=2)



# Labels and formatting
ax.set_ylabel('Speedup (log scale)', fontsize=fontsize)
ax.set_title('')
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=90, fontsize=fontsize-2)
ax.set_yticks([0.5,1,2,5,10,20])
#ax.legend()


ax.set_yscale('log')
# Log scale (optional)
ax.set_yticks([1, 2, 5, 10, 20])  # You can adjust the range as needed
ax.get_yaxis().set_major_formatter(plt.ScalarFormatter()) 

# Display the plot
plt.tight_layout()
plt.savefig("poc_improvements.pdf")


