
f = open("output_ALL_XL.txt").readlines()


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
    "text.usetex": False, #True,
    "font.size": 11,
    "font.family": "serif", #"libertine",
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

# Normalize with midpoint at 1
norm = colors.TwoSlopeNorm(vmin=np.min(ratios), vcenter=1.0, vmax=np.max(ratios)/10)
cmap = cm.RdYlGn
bar_colors = cmap(norm(ratios))

x = np.arange(len(labels))
width = 0.6

fig, ax = plt.subplots()


# Reference line at ratio = 1
ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=1, label='Ratio = 1')
ax.axhline(y=2.0, color='lightgray', linestyle='-', linewidth=1)
ax.axhline(y=5.0, color='lightgray', linestyle='-', linewidth=1)
ax.axhline(y=10.0, color='lightgray', linestyle='-', linewidth=1)

# Plot colored ratio bars
bars = ax.bar(x, ratios, width, color=bar_colors, edgecolor='black', zorder=2)



# Labels and formatting
ax.set_ylabel('Ratio of baseline execution time to TADASHI', fontsize=fontsize)
ax.set_title('')
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=90, fontsize=fontsize-2)
ax.set_yticks([0,1,2,5,10,20,30,40,50,60])
ax.legend()


ax.set_yscale('log')
# Log scale (optional)
ax.set_yticks([1, 2, 5, 10, 20, 50, 100])  # You can adjust the range as needed
ax.get_yaxis().set_major_formatter(plt.ScalarFormatter()) 

# Display the plot
plt.tight_layout()
plt.savefig("poc_improvements.pdf")


