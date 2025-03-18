cmake_minimum_required(VERSION 3.18.4)
project(tadashi)

# C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# cmake_policy(SET CMP0078 NEW)
# cmake_policy(SET CMP0086 NEW)

# Common installation directories
include(GNUInstallDirs)

# ============
# Dependencies
# ============

include(FetchContent)

# FetchContent_Declare(
#   googletest
#   DOWNLOAD_EXTRACT_TIMESTAMP On
#   URL https://github.com/google/googletest/archive/03597a01ee50ed33e9dfd640b249b4be3799d395.zip
# )
# # For Windows: Prevent overriding the parent project's compiler/linker settings
# # set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
# FetchContent_MakeAvailable(googletest)

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

# =======
# Options
# =======

# Use -fPIC even if statically compiled
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE) # didn't help
set(CMAKE_BUILD_RPATH_USE_ORIGIN TRUE)

# list(APPEND CMAKE_PREFIX_PATH ${PROJECT_BINARY_DIR})


set(ENV{PKG_CONFIG_PATH} "${pet_SOURCE_DIR}:${pet_SOURCE_DIR}/isl:$ENV{PKG_CONFIG_PATH}")
list(APPEND CMAKE_LIBRARY_PATH "${pet_BINARY_DIR}/lib")
list(APPEND CMAKE_INSTALL_RPATH "${pet_BINARY_DIR}/lib")

set(INSTALL_SCRIPTS "${CMAKE_SOURCE_DIR}/deps/install_scripts")

find_package(PkgConfig REQUIRED)
pkg_check_modules(PET IMPORTED_TARGET pet)

if(NOT PET_FOUND)
  message("Package 'pet' not found, but don't worry, I know how to build it!")
  set(ENV{CC} ${CMAKE_C_COMPILER})
  set(ENV{CXX} ${CMAKE_CXX_COMPILER})
  execute_process(
    # OUTPUT_QUIET 
    COMMAND ${INSTALL_SCRIPTS}/pet.sh ${pet_BINARY_DIR} bundled ${CMAKE_SOURCE_DIR}/deps/opt
    WORKING_DIRECTORY ${pet_SOURCE_DIR}
  )
  pkg_check_modules(PET REQUIRED IMPORTED_TARGET pet)
  pkg_check_modules(ISL REQUIRED IMPORTED_TARGET isl)
endif()

include_directories(include)

add_library(legality SHARED src/legality.c)
target_link_libraries(legality PUBLIC PkgConfig::ISL PkgConfig::PET)

add_library(code_gen SHARED src/codegen.c)
target_link_libraries(code_gen PUBLIC PkgConfig::ISL PkgConfig::PET)

add_library(transformations SHARED src/transformations.c)
target_link_libraries(transformations PUBLIC PkgConfig::ISL PkgConfig::PET)

add_library(scops SHARED src/scops.cc)
target_link_libraries(scops PUBLIC PkgConfig::ISL PkgConfig::PET)

add_library(ctadashi SHARED src/ctadashi.cc)
target_link_libraries(ctadashi PUBLIC PkgConfig::ISL PkgConfig::PET legality code_gen transformations scops)
add_library(CTadashi::ctadashi ALIAS ctadashi)

install(TARGETS legality code_gen transformations scops ctadashi
  EXPORT CTadashiTargets
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})

install(
  EXPORT CTadashiTargets
  FILE CTadashiTargets.cmake
  NAMESPACE CTadashi::
  DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/CTadashi)

# install(PROGRAMS ${PET_LINK_LIBRARIES}
#   DESTINATION ${CMAKE_INSTALL_PREFIX})

###

find_package(Python3 COMPONENTS Interpreter Development REQUIRED )
find_package(SWIG 4.0 REQUIRED)
set(UseSWIG_MODULE_VERSION 2)
include(${SWIG_USE_FILE})

# Handle where to install the resulting Python package
if(CALL_FROM_SETUP_PY)
    # The CMakeExtension will set CMAKE_INSTALL_PREFIX to the root
    # of the resulting wheel archive
    set(CTADASHI_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX})
else()
    # The Python package is installed directly in the folder of the
    # detected interpreter (system, user, or virtualenv)
    set(CTADASHI_INSTALL_PREFIX ${Python3_SITELIB})
    # set(CTADASHI_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX})
endif()

# The name of the shared library must match the module name
set_property(SOURCE src/ctadashi.i
  PROPERTY CPLUSPLUS ON
  PROPERTY SWIG_INCLUDE_DIRECTORIES
  SWIG_MODULE_NAME "pytadashi")
swig_add_library(ctadashi_swig
  TYPE MODULE
  LANGUAGE python
  OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR}
  OUTFILE_DIR ${CMAKE_CURRENT_BINARY_DIR}
  SOURCES src/ctadashi.i)
swig_link_libraries(ctadashi_swig PUBLIC ctadashi Python3::Python PkgConfig::PET legality code_gen transformations)
set_target_properties(ctadashi_swig PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
  INSTALL_RPATH ${CMAKE_INSTALL_PREFIX}
  SWIG_USE_TARGET_INCLUDE_DIRECTORIES TRUE
  SWIG_COMPILE_OPTIONS -doxygen
  SWIG_DEPENDS src/ctadashi.i)

get_property(WRAPPER_PY_FILE
    TARGET ctadashi_swig
    PROPERTY SWIG_SUPPORT_FILES)
install(
    FILES ${WRAPPER_PY_FILE}
    DESTINATION ${CTADASHI_INSTALL_PREFIX}
    COMPONENT pytadashi)

install(
    TARGETS ctadashi_swig legality code_gen transformations scops ctadashi
    COMPONENT pytadashi
    LIBRARY DESTINATION ${CTADASHI_INSTALL_PREFIX}
    ARCHIVE DESTINATION ${CTADASHI_INSTALL_PREFIX}
    RUNTIME DESTINATION ${CTADASHI_INSTALL_PREFIX})

add_executable(goodbadtest src/goodbadtest.c)

add_executable(tadashi src/tadashi.c)
target_link_libraries(tadashi PUBLIC PkgConfig::ISL PkgConfig::PET legality code_gen transformations)

# enable_testing()
# include(GoogleTest)

# add_executable(test_legality tests/cc/test_legality.cc)
# target_link_libraries(test_legality PUBLIC PkgConfig::ISL GTest::gtest_main legality)

# gtest_discover_tests(test_legality)
