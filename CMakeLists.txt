cmake_minimum_required(VERSION 3.18.4)

project(polyhedral-tutor)

set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)


# list(APPEND CMAKE_PREFIX_PATH ${PROJECT_BINARY_DIR})


include(FetchContent)

FetchContent_Declare(
  libpet
  GIT_REPOSITORY https://repo.or.cz/pet.git
  GIT_TAG pet-0.11.7
  GIT_SUBMODULES ""
  GIT_SUBMODULES_RECURSE False
  GIT_SHALLOW ON
  UPDATE_DISCONNECTED ON
)

set(ENV{PKG_CONFIG_PATH} ${libpet_SOURCE_DIR})
find_package(PkgConfig REQUIRED)
pkg_search_module(pet IMPORTED_TARGET libpet)

if(NOT libpet_POPULATED AND NOT pet_FOUND)
  message("Package 'pet' not found, so we're building it")
  FetchContent_Populate(libpet)

  set(ENV${CC} ${CMAKE_C_COMPILER})
  set(ENV{CXX} ${CMAKE_CXX_COMPILER})

  execute_process(
    OUTPUT_QUIET
    COMMAND ./autogen.sh --host=${CMAKE_SYSTEM_PROCESSOR}
    WORKING_DIRECTORY ${libpet_SOURCE_DIR}
  )

  execute_process(
    OUTPUT_QUIET
    COMMAND ./configure --prefix=${libpet_BINARY_DIR}
    WORKING_DIRECTORY ${libpet_SOURCE_DIR}
  )

  execute_process(
    OUTPUT_QUIET
    COMMAND make -j
    WORKING_DIRECTORY ${libpet_SOURCE_DIR}
  )

  pkg_search_module(PET REQUIRED IMPORTED_TARGET pet)
  pkg_search_module(ISL REQUIRED IMPORTED_TARGET isl)
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

add_executable(c_python_interact src/c_python_interact.c)
target_link_libraries(c_python_interact PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(understanding_loopback_0 src/understanding_loopback_0.c)
target_link_libraries(understanding_loopback_0 PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(tadashi src/tadashi.c)
target_link_libraries(tadashi PUBLIC PkgConfig::ISL PkgConfig::PET)
