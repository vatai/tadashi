
import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench


base = "PolyBenchC-4.2.1/"


gemm = Polybench(
	"stencils/jacobi-2d",
	base,
	compiler_options=["-DEXTRALARGE_DATASET", "-O3"],
)

print(f"{gemm.user_compiler_options=}")

gemm.compile()

print(f"{gemm.measure()=}")

#For jacobi-2d -DEXTRALARGE, the best tile_size i found in my machine was 31
for tile_size in [5, 6, 7, 16, 64, 128]: 
	gemm.reset_scops()
	
	trs=[ 
	[0,2, TrEnum.FULL_SPLIT],
	[0, 4, TrEnum.TILE, tile_size],
	[0, 6, TrEnum.TILE, tile_size],
	[0, 3, TrEnum.INTERCHANGE],
	[0, 5, TrEnum.INTERCHANGE],
	[0, 4, TrEnum.INTERCHANGE],
	[0, 11, TrEnum.TILE, tile_size],
	[0, 13, TrEnum.TILE, tile_size],
	[0, 10, TrEnum.INTERCHANGE],
	[0, 12, TrEnum.INTERCHANGE],
	[0, 11, TrEnum.INTERCHANGE],
	]

	# Also works, not as good but has 5 operations instead of 11
	trs=[ 
	[0,2, TrEnum.FULL_SPLIT],
	[0, 4, TrEnum.TILE, tile_size],
	[0, 3, TrEnum.INTERCHANGE],
	[0, 10, TrEnum.TILE, tile_size],
	[0, 9, TrEnum.INTERCHANGE],
	]


	gemm.transform_list(trs)

	tiled = gemm.generate_code(alt_infix="_tiled%d"%tile_size, ephemeral=False)
	tiled.compile()

	print(f"{tile_size=} : {tiled.measure()=}")

print("DONE")

