
import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench


base = "PolyBenchC-4.2.1/"


app_names = [
"medley/floyd-warshall",
"medley/nussinov",
"medley/deriche",
"linear-algebra/blas/syr2k",
"linear-algebra/blas/gesummv",
"linear-algebra/blas/gemver",
"linear-algebra/blas/trmm",
"linear-algebra/blas/symm",
"linear-algebra/blas/syrk",
"linear-algebra/blas/gemm",
"linear-algebra/kernels/atax",
"linear-algebra/kernels/bicg",
"linear-algebra/kernels/2mm",
"linear-algebra/kernels/doitgen",
"linear-algebra/kernels/3mm",
"linear-algebra/kernels/mvt",
"linear-algebra/solvers/lu",
"linear-algebra/solvers/durbin",
"linear-algebra/solvers/ludcmp",
"linear-algebra/solvers/cholesky",
"linear-algebra/solvers/trisolv",
"linear-algebra/solvers/gramschmidt",
"stencils/heat-3d",
"stencils/jacobi-1d",
"stencils/fdtd-2d",
"stencils/adi",
"stencils/jacobi-2d",
"stencils/seidel-2d",
"datamining/covariance",
"datamining/correlation",
]


def searchFor(app, tr_name):
	scops = app.scops 
	ret = []
	for si in range(len(scops[0].schedule_tree)):
		s = scops[0].schedule_tree[si]
		av = s.available_transformations
		for t in av:
			if t == tr_name:
				ret.append(si)
	return ret


for app_name in app_names:

	print("-----------------------------------------\n\n[STARTING NEW APP]")

	print(app_name)

	app = Polybench(
		app_name,
		base,
		compiler_options=["-DEXTRALARGE_DATASET", "-DLARGE_DATASET", "-O3"][1::],
	)


	print(f"{app.user_compiler_options=}")

	app.compile()

	print("Baseline measure: %f" % app.measure() )


	full_tr_list = []

	tile_size = 32


	trs = searchFor(app, "full_split")
	trs = [ [0, index, TrEnum.FULL_SPLIT] for index in trs ]
	app.transform_list(trs[::-1])
	full_tr_list.extend(trs[::-1])

	trs = searchFor(app, "tile3d")
	toRemoveFrom2D = [ a for a in trs]
	toRemoveFrom2D.extend([ a+1 for a in trs])
	toRemoveFrom2D = list(set(toRemoveFrom2D))
	for t in trs:
		if t-1 in trs:
			trs.pop(trs.index(t-1))		
	trs3D = [ [0, index, TrEnum.TILE3D, tile_size, tile_size, tile_size] for index in trs[::-1] ]
	trs2 = searchFor(app, "tile2d")
	for t in toRemoveFrom2D:
		if t in trs2:
			trs2.pop(trs2.index(t))
	trs2D = [ [0, index, TrEnum.TILE2D, tile_size, tile_size] for index in trs2[::-1] ]
	trs3D.extend(trs2D)
	trs3D.sort()
	app.transform_list(trs3D[::-1])
	full_tr_list.extend(trs3D[::-1])

	#trs = searchFor(app, "full_fuse")
	#trs = [ [0, index, TrEnum.FULL_FUSE] for index in trs ]
	#app.transform_list(trs[::-1])
	#full_tr_list.extend(trs[::-1])

	print("transformation_list=[")
	[print('   %s,'%str(t) ) for t in full_tr_list]
	print("]")

	for tile_size in [32]: 
		app.reset_scops()

		print("Tiling with size %d ..." % tile_size)

		app.transform_list(full_tr_list)


		tiled = app.generate_code(alt_infix="_tiled%d"%tile_size, ephemeral=False)
		tiled.compile()

		print("Tiling with size %d: %f" % (tile_size, tiled.measure()) )


	print("[FINISHED APP]\n\n")


