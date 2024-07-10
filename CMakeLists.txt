cmake_minimum_required(VERSION 3.18.4)

project(polyhedral-tutor)

set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)


# list(APPEND CMAKE_PREFIX_PATH ${PROJECT_BINARY_DIR})


include(FetchContent)

FetchContent_Declare(
  polybench
  DOWNLOAD_EXTRACT_TIMESTAMP On
  URL https://github.com/MatthiasJReisinger/PolyBenchC-4.2.1/archive/refs/heads/master.zip
)
# For Windows: Prevent overriding the parent project's compiler/linker settings
# set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(polybench)

FetchContent_Declare(
  googletest
  DOWNLOAD_EXTRACT_TIMESTAMP On
  URL https://github.com/google/googletest/archive/03597a01ee50ed33e9dfd640b249b4be3799d395.zip
)
# For Windows: Prevent overriding the parent project's compiler/linker settings
# set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

FetchContent_Declare(
  pet
  GIT_REPOSITORY https://repo.or.cz/pet.git
  GIT_TAG master
  GIT_SHALLOW ON
  # GIT_SUBMODULES ""
  # GIT_SUBMODULES_RECURSE False
  # UPDATE_DISCONNECTED ON
)

FetchContent_MakeAvailable(pet)

set(ENV{PKG_CONFIG_PATH} "${pet_SOURCE_DIR}:${pet_SOURCE_DIR}/isl:$ENV{PKG_CONFIG_PATH}")
list(APPEND CMAKE_LIBRARY_PATH "${pet_BINARY_DIR}/lib")
list(APPEND CMAKE_INSTALL_RPATH "${pet_BINARY_DIR}/lib")

find_package(PkgConfig REQUIRED)
pkg_check_modules(ISL IMPORTED_TARGET isl)
pkg_check_modules(PET IMPORTED_TARGET pet)

if(ISL_FOUND)
  message("ISL found")
  set(PET_CONFIGURE_WITH_ISL system)
else()
  message("ISL NOT found")
  set(PET_CONFIGURE_WITH_ISL build)
endif()

if(NOT PET_FOUND)
  message("Package 'pet' not found, but don't worry, I know how to build it!")

  set(ENV{CC} ${CMAKE_C_COMPILER})
  set(ENV{CXX} ${CMAKE_CXX_COMPILER})

  execute_process(
    # OUTPUT_QUIET
    COMMAND ./autogen.sh
    WORKING_DIRECTORY ${pet_SOURCE_DIR}
  )

  execute_process(
    # OUTPUT_QUIET
    COMMAND ./configure --prefix=${pet_BINARY_DIR} --with-isl=${PET_CONFIGURE_WITH_ISL}
    WORKING_DIRECTORY ${pet_SOURCE_DIR}
  )

  execute_process(
    # OUTPUT_QUIET
    COMMAND make -j
    WORKING_DIRECTORY ${pet_SOURCE_DIR}
  )

  execute_process(
    # OUTPUT_QUIET
    COMMAND make -j install
    WORKING_DIRECTORY ${pet_SOURCE_DIR}
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

add_executable(test_legality tests/cc/test_legality.cc)
target_link_libraries(test_legality PUBLIC PkgConfig::ISL GTest::gtest_main legality)

gtest_discover_tests(test_legality)
