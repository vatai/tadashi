
import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench


base = "PolyBenchC-4.2.1/"
app_name = "datamining/correlation"

app = Polybench(
	app_name,
	base,
	compiler_options=["-DEXTRALARGE_DATASET", "-DLARGE_DATASET", "-O3"][::2],
)

print(app_name)
print(f"{app.user_compiler_options=}")

app.compile()

print(f"{app.measure()=}")




for tile_size in [32, 64, 128, 256]: 
	app.reset_scops()

	print("TILING")

	
	trs=[ 
	[0, 41, TrEnum.FULL_SPLIT],
	[0, 36, TrEnum.FULL_SPLIT],
	[0, 29, TrEnum.FULL_SPLIT],
	[0, 14, TrEnum.FULL_SPLIT],
	[0, 4, TrEnum.FULL_SPLIT],
	[0, 53, TrEnum.TILE2D, tile_size, tile_size],
	[0, 20, TrEnum.TILE2D, tile_size, tile_size],
	[0, 8, TrEnum.TILE2D, tile_size, tile_size],
	[0, 52, TrEnum.FULL_FUSE],
	[0, 46, TrEnum.FULL_FUSE],
	[0, 38, TrEnum.FULL_FUSE],
	[0, 17, TrEnum.FULL_FUSE],
	[0, 3, TrEnum.FULL_FUSE],
	]

	app.transform_list(trs)

	if False:
		scops = app.scops 
		print(len(scops[0].schedule_tree))
		for si in range(len(scops[0].schedule_tree)):
			s = scops[0].schedule_tree[si]
			av = s.available_transformations
			for t in av:
				if "tile" in t or "split" in t or "fuse" in t:
					print(si, t)


	tiled = app.generate_code(alt_infix="_tiled%d"%tile_size, ephemeral=False)
	tiled.compile()

	print("Tiling with size %d: %f" % (tile_size, tiled.measure()) )






#datamining/correlation
#app.user_compiler_options=['-DEXTRALARGE_DATASET', '-O3']
#app.measure()=33.517485

# tile 2D
	trs=[ 
	[0, 41, TrEnum.FULL_SPLIT],
	[0, 36, TrEnum.FULL_SPLIT],
	[0, 29, TrEnum.FULL_SPLIT],
	[0, 14, TrEnum.FULL_SPLIT],
	[0, 4,  TrEnum.FULL_SPLIT],
	[0, 53, TrEnum.TILE2D, tile_size, tile_size],
	[0, 20, TrEnum.TILE2D, tile_size, tile_size],
	[0, 8,  TrEnum.TILE2D, tile_size, tile_size],
	[0, 52, TrEnum.FULL_FUSE],
	[0, 46, TrEnum.FULL_FUSE],
	[0, 38, TrEnum.FULL_FUSE],
	[0, 17, TrEnum.FULL_FUSE],
	[0, 3,  TrEnum.FULL_FUSE],
	]

# Tiling with size 32: 1.974256
# Tiling with size 64: 2.009392
# Tiling with size 128: 2.137372
# Tiling with size 256: 2.188174


