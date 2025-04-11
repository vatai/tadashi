
import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench


base = "PolyBenchC-4.2.1/"
app_name = "stencils/heat-3d"

app = Polybench(
	app_name,
	base,
	compiler_options=["-DEXTRALARGE_DATASET", "-DLARGE_DATASET", "-O3"][::2],
)

print(app_name)
print(f"{app.user_compiler_options=}")

app.compile()

#print(f"{app.measure()=}")


doOnlySplit
if doOnlySplit: 
	app.reset_scops()

	print("ONLY FULL SPLIT")

	
	trs=[ 
	[0, 2, TrEnum.FULL_SPLIT],
	]

	app.transform_list(trs)

	tiled = app.generate_code(alt_infix="_onlySplit", ephemeral=False)
	tiled.compile()

	print(f"Only Split: {tiled.measure()=}")





for tile_size in [8,10,16, 32]: 
	app.reset_scops()

	trs=[ 
		[0, 2, TrEnum.FULL_SPLIT],
		[0, 4, TrEnum.TILE3D, tile_size, tile_size, tile_size],
		[0, 3, TrEnum.INTERCHANGE],
		[0, 4, TrEnum.INTERCHANGE],
		[0, 5, TrEnum.INTERCHANGE],
		[0, 13, TrEnum.TILE3D, tile_size, tile_size, tile_size],
		[0, 12, TrEnum.INTERCHANGE],
		[0, 13, TrEnum.INTERCHANGE],
		[0, 14, TrEnum.INTERCHANGE],
	]

	app.transform_list(trs)

	if False:
		scops = app.scops 
		print(len(scops[0].schedule_tree))
		for si in range(len(scops[0].schedule_tree)):
			s = scops[0].schedule_tree[si]
			av = s.available_transformations
			for t in av:
				print(si, t)

	tiled = app.generate_code(alt_infix="_tiled%d"%tile_size, ephemeral=False)
	tiled.compile()

	print(f"{tile_size=} : {tiled.measure()=}")

print("DONE")




#stencils/heat-3d
#app.user_compiler_options=['-DEXTRALARGE_DATASET', '-O3']
#app.measure()=19.512852

# Only full split
trs=[ 
	[0, 2, TrEnum.FULL_SPLIT],
]
# tiled.measure()=2.792987

# full split + tile
trs=[ 
	[0, 2, TrEnum.FULL_SPLIT],
	[0, 4, TrEnum.TILE3D, tile_size, tile_size, tile_size],
	[0, 13, TrEnum.TILE3D, tile_size, tile_size, tile_size],
]
# tile_size=8 : tiled.measure()=3.651312


# full split + tile + send n_steps to the inner loop
trs=[ 
	[0, 2, TrEnum.FULL_SPLIT],
	[0, 4, TrEnum.TILE3D, tile_size, tile_size, tile_size],
	[0, 3, TrEnum.INTERCHANGE],
	[0, 4, TrEnum.INTERCHANGE],
	[0, 5, TrEnum.INTERCHANGE],
	[0, 13, TrEnum.TILE3D, tile_size, tile_size, tile_size],
	[0, 12, TrEnum.INTERCHANGE],
	[0, 13, TrEnum.INTERCHANGE],
	[0, 14, TrEnum.INTERCHANGE],
]
# tile_size=10 : tiled.measure()=2.603448
