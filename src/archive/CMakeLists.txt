
add_executable(main src/archive/main.c)
target_link_libraries(main PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(poly-scan src/archive/poly-scan.c)
target_link_libraries(poly-scan PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(functions src/archive/functions.c)
target_link_libraries(functions PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(advanced_shift src/archive/advanced_shift.c)
target_link_libraries(advanced_shift PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(annotated_pet_loopback src/archive/annotated_pet_loopback.c)
target_link_libraries(annotated_pet_loopback PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(depanalysis src/archive/depanalysis.c)
target_link_libraries(depanalysis PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(polegality src/archive/polegality.c)
target_link_libraries(polegality PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(tree_manipulation src/archive/tree_manipulation.c)
target_link_libraries(tree_manipulation PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(astgen src/archive/astgen.c)
target_link_libraries(astgen PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(understanding_loopback_0 src/archive/understanding_loopback_0.c)
target_link_libraries(understanding_loopback_0 PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(seq_legality src/archive/seq_legality.c)
target_link_libraries(seq_legality PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(tile_and_interchange src/archive/tile_and_interchange.c)
target_link_libraries(tile_and_interchange PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(get_dim_name src/archive/get_dim_name.c)
target_link_libraries(get_dim_name PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(sink_and_order src/archive/sink_and_order.c)
target_link_libraries(sink_and_order PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(scale_and_shift src/archive/scale_and_shift.c)
target_link_libraries(scale_and_shift PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(scratch src/archive/scratch.c)
target_link_libraries(scratch PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(fuse src/archive/fuse.c)
target_link_libraries(fuse PUBLIC PkgConfig::ISL PkgConfig::PET legality codegen transformations)
