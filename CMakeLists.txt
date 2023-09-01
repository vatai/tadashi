cmake_minimum_required(VERSION 3.18.4)

project(polyhedral-tutor)

set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)

set(ENV{PKG_CONFIG_PATH} "${CMAKE_SOURCE_DIR}/deps/build/pet;${CMAKE_SOURCE_DIR}/deps/build/pet/isl")

find_package(PkgConfig REQUIRED)
pkg_search_module(PET REQUIRED IMPORTED_TARGET pet)
pkg_search_module(ISL REQUIRED IMPORTED_TARGET isl)

# message(WARNING "PET_INCLUDE_DIRS is ${PET_INCLUDE_DIRS}")
# message(WARNING "PET_FOUND is ${PET_FOUND}")
# message(WARNING "ISL_FOUND is ${ISL_FOUND}")
# message(WARNING "ISL_LIBRARY_DIRS is ${ISL_LIBRARY_DIRS}")

add_executable(main src/main.c)
target_link_libraries(main PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(poly-scan src/poly-scan.c)
target_link_libraries(poly-scan PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(functions src/functions.c)
target_link_libraries(functions PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(divs src/divs.c)
target_link_libraries(divs PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(annotated_pet_loopback src/annotated_pet_loopback.c)
target_link_libraries(annotated_pet_loopback PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(depanalysis src/depanalysis.c)
target_link_libraries(depanalysis PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(polegality src/polegality.c)
target_link_libraries(polegality PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(tree_manipulation src/tree_manipulation.c)
target_link_libraries(tree_manipulation PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(goodbadtest src/goodbadtest.c)

add_executable(astgen src/astgen.c)
target_link_libraries(astgen PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(understanding_loopback_0 src/understanding_loopback_0.c)
target_link_libraries(understanding_loopback_0 PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(tadashi src/tadashi.c)
target_link_libraries(tadashi PUBLIC PkgConfig::ISL PkgConfig::PET)
