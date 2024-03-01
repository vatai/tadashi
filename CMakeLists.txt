cmake_minimum_required(VERSION 3.18.4)

project(polyhedral-tutor)

set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)


# list(APPEND CMAKE_PREFIX_PATH ${PROJECT_BINARY_DIR})


include(FetchContent)

FetchContent_Declare(
  polybench
  URL https://github.com/MatthiasJReisinger/PolyBenchC-4.2.1/archive/refs/heads/master.zip
)
# For Windows: Prevent overriding the parent project's compiler/linker settings
# set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(polybench)

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

FetchContent_Populate(libpet)

set(ENV{PKG_CONFIG_PATH} "${libpet_SOURCE_DIR}:${libpet_SOURCE_DIR}/isl:$ENV{PKG_CONFIG_PATH}")
list(APPEND CMAKE_LIBRARY_PATH "${libpet_BINARY_DIR}/lib")
list(APPEND CMAKE_INSTALL_RPATH "${libpet_BINARY_DIR}/lib")

find_package(PkgConfig REQUIRED)
pkg_check_modules(ISL IMPORTED_TARGET isl)
pkg_check_modules(PET IMPORTED_TARGET pet)

if(NOT PET_FOUND)
  message("Package 'pet' not found, but don't worry, I know how to build it!")

  set(ENV${CC} ${CMAKE_C_COMPILER})
  set(ENV{CXX} ${CMAKE_CXX_COMPILER})

  execute_process(
    # OUTPUT_QUIET
    COMMAND ./autogen.sh
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

  execute_process(
    # OUTPUT_QUIET
    COMMAND make -j install
    WORKING_DIRECTORY ${libpet_SOURCE_DIR}
  )

  pkg_check_modules(PET REQUIRED IMPORTED_TARGET pet)
  pkg_check_modules(ISL REQUIRED IMPORTED_TARGET isl)

endif()

include(src/archive/CMakeLists.txt)

add_library(legality SHARED src/legality.c)
target_link_libraries(legality PUBLIC PkgConfig::ISL PkgConfig::PET)

add_library(codegen SHARED src/codegen.c)
target_link_libraries(codegen PUBLIC PkgConfig::ISL PkgConfig::PET)

add_library(transformations SHARED src/transformations.c)
target_link_libraries(transformations PUBLIC PkgConfig::ISL PkgConfig::PET)

add_library(ctadashi SHARED src/ctadashi.cc)
target_link_libraries(ctadashi PUBLIC PkgConfig::ISL PkgConfig::PET legality codegen transformations)

add_executable(goodbadtest src/goodbadtest.c)

include_directories(include)

add_executable(tadashi src/tadashi.c)
target_link_libraries(tadashi PUBLIC PkgConfig::ISL PkgConfig::PET legality codegen transformations)

enable_testing()
include(GoogleTest)

add_executable(legality_test tests/legality_test.cc)
target_link_libraries(legality_test PUBLIC PkgConfig::ISL GTest::gtest_main legality)

gtest_discover_tests(legality_test)
