cmake_minimum_required(VERSION 3.18.4)

project(polyhedral-tutor)

set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)


# list(APPEND CMAKE_PREFIX_PATH ${PROJECT_BINARY_DIR})


include(FetchContent)

FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/03597a01ee50ed33e9dfd640b249b4be3799d395.zip
)
# For Windows: Prevent overriding the parent project's compiler/linker settings
# set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

FetchContent_Declare(
  libpet
  GIT_REPOSITORY https://repo.or.cz/pet.git
  GIT_TAG pet-0.11.7
  GIT_SHALLOW ON
  # GIT_SUBMODULES ""
  # GIT_SUBMODULES_RECURSE False
  # UPDATE_DISCONNECTED ON
)

find_package(PkgConfig REQUIRED)

pkg_check_modules(ISL IMPORTED_TARGET isl pet)

if(NOT libpet_POPULATED AND NOT PET_FOUND)
  message("Package 'pet' not found, so we're building it")
  FetchContent_Populate(libpet)

  set(ENV${CC} ${CMAKE_C_COMPILER})
  set(ENV{CXX} ${CMAKE_CXX_COMPILER})

  execute_process(
    # OUTPUT_QUIET
    COMMAND ./autogen.sh --host=${CMAKE_SYSTEM_PROCESSOR}
    WORKING_DIRECTORY ${libpet_SOURCE_DIR}
  )

  execute_process(
    # OUTPUT_QUIET
    COMMAND ./configure --prefix=${libpet_BINARY_DIR}
    WORKING_DIRECTORY ${libpet_SOURCE_DIR}
  )

  execute_process(
    # OUTPUT_QUIET
    COMMAND make -j
    WORKING_DIRECTORY ${libpet_SOURCE_DIR}
  )

  message(">>>>>>>> ENV DIR :$ENV{PKG_CONFIG_PATH}")
  execute_process(
    # OUTPUT_QUIET
    COMMAND ls isl
    WORKING_DIRECTORY ${libpet_SOURCE_DIR}
  )

  set(ENV{PKG_CONFIG_PATH} "${libpet_SOURCE_DIR}:${libpet_SOURCE_DIR}/isl}")
  pkg_check_modules(PET REQUIRED IMPORTED_TARGET pet)
  message("PET_FOUND ${PET_FOUND}")
  pkg_check_modules(PET REQUIRED IMPORTED_TARGET isl)
  message("ISL_FOUND ${ISL_FOUND}")

  # list(APPEND CMAKE_INSTALL_RPATH "${libpet_SOURCE_DIR}/isl/.libs")
endif()



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

include_directories(include)

add_library(legality src/legality.c)
target_link_libraries(legality PUBLIC PkgConfig::ISL PkgConfig::PET)

add_library(codegen src/codegen.c)
target_link_libraries(codegen PUBLIC PkgConfig::ISL PkgConfig::PET)

add_library(transformations src/transformations.c)
target_link_libraries(transformations PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(seq_legality src/seq_legality.c)
target_link_libraries(seq_legality PUBLIC PkgConfig::ISL PkgConfig::PET legality codegen)

add_executable(tile_and_interchange src/tile_and_interchange.c)
target_link_libraries(tile_and_interchange PUBLIC PkgConfig::ISL PkgConfig::PET legality codegen)

add_executable(get_dim_name src/get_dim_name.c)
target_link_libraries(get_dim_name PUBLIC PkgConfig::ISL PkgConfig::PET legality codegen)

add_executable(sink_and_order src/sink_and_order.c)
target_link_libraries(sink_and_order PUBLIC PkgConfig::ISL PkgConfig::PET legality codegen)

add_executable(scale_and_shift src/scale_and_shift.c)
target_link_libraries(scale_and_shift PUBLIC PkgConfig::ISL PkgConfig::PET legality codegen)

add_executable(scratch src/scratch.c)
target_link_libraries(scratch PUBLIC PkgConfig::ISL PkgConfig::PET legality codegen)

enable_testing()
include(GoogleTest)

add_executable(tadashi src/tadashi.c)
target_link_libraries(tadashi PUBLIC PkgConfig::ISL PkgConfig::PET legality codegen transformations)

add_executable(legality_test tests/legality_test.cc)
target_link_libraries(legality_test PUBLIC PkgConfig::ISL GTest::gtest_main legality)

gtest_discover_tests(legality_test)
