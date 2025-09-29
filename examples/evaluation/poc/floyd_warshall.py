
import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench


base = "PolyBenchC-4.2.1/"
app_name = "medley/floyd-warshall"

app = Polybench(
	app_name,
	base,
	compiler_options=["-DEXTRALARGE_DATASET", "-DLARGE_DATASET", "-O3"][::2],
)

print(app_name)
print(f"{app.user_compiler_options=}")

app.compile()

#print(f"{app.measure()=}")


if False:
	scops = app.scops 
	print(len(scops[0].schedule_tree))
	for si in range(len(scops[0].schedule_tree)):
		s = scops[0].schedule_tree[si]
		av = s.available_transformations
		for t in av:
			print(si, t)


for tile_size in [32, 64, 128]: 
	app.reset_scops()

	print("TILING")

	
	trs=[ 
	[0, 1, TrEnum.TILE3D, tile_size, tile_size, tile_size],
	]

	app.transform_list(trs)

	tiled = app.generate_code(alt_infix="_tiled%d"%tile_size, ephemeral=False)
	tiled.compile()

	print("Tiling with size %d: %f" % (tile_size, tiled.measure()) )






#medley/floyd-warshall
#app.user_compiler_options=['-DEXTRALARGE_DATASET', '-O3']
#app.measure()=103.855394

# tile 3D
trs=[ 
	[0, 1, TrEnum.TILE3D, tile_size, tile_size, tile_size],
]
# tile_size=64: tiled.measure()=14.037779


