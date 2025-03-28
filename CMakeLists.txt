cmake_minimum_required(VERSION 3.18.4)
project(tadashi VERSION 0.2.2)


# ==============
# Notes on RPATH
# ==============

# https://gitlab.kitware.com/cmake/community/-/wikis/doc/cmake/RPATH-handling

# C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Common installation directories
include(GNUInstallDirs)


# =======
# Options
# =======

set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)


# ============
# Dependencies
# ============

set(INSTALL_SCRIPTS "${CMAKE_SOURCE_DIR}/deps/install_scripts")
set(CMAKE_INSTALL_RPATH_USE_ORIGIN TRUE)

find_package(Python3 COMPONENTS Interpreter Development REQUIRED )

# Handle where to install the resulting Python package
if(CALL_FROM_SETUP_PY)
    # The CMakeExtension will set CMAKE_INSTALL_PREFIX to the root
    # of the resulting wheel archive
    set(CTADASHI_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX})
else()
    # The Python package is installed directly in the folder of the
    # detected interpreter (system, user, or virtualenv)
    set(CTADASHI_INSTALL_PREFIX ${Python3_SITELIB})
endif()
include(FetchContent)

FetchContent_Declare(
  pet
  PATCH_COMMAND git apply "${INSTALL_SCRIPTS}/pet.patch" || true
  GIT_REPOSITORY https://repo.or.cz/pet.git
  GIT_TAG master
  GIT_SHALLOW ON
  # GIT_SUBMODULES ""
  # GIT_SUBMODULES_RECURSE False
  # UPDATE_DISCONNECTED ON
)

FetchContent_MakeAvailable(pet)

FetchContent_Declare(json URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz)
FetchContent_MakeAvailable(json)

set(ENV{PKG_CONFIG_PATH} "${CTADASHI_INSTALL_PREFIX}/lib/pkgconfig:$ENV{PKG_CONFIG_PATH}")
list(APPEND CMAKE_LIBRARY_PATH "${CTADASHI_INSTALL_PREFIX}/lib")
list(APPEND CMAKE_INSTALL_RPATH "$ORIGIN")

set(ENV{CC} ${CMAKE_C_COMPILER})
set(ENV{CXX} ${CMAKE_CXX_COMPILER})
set(ENV{CFLAGS} ${CMAKE_C_FLAGS})
set(ENV{CXXFLAGS} ${CMAKE_CXX_FLAGS})

find_package(PkgConfig REQUIRED)
pkg_check_modules(PET IMPORTED_TARGET pet)
if(NOT PET_FOUND)
  execute_process(
    # TODO: remove "bundled"
    COMMAND ${INSTALL_SCRIPTS}/pet.sh ${CTADASHI_INSTALL_PREFIX} bundled ${CMAKE_SOURCE_DIR}/deps/opt
    WORKING_DIRECTORY ${pet_SOURCE_DIR}
  )
  pkg_check_modules(PET REQUIRED IMPORTED_TARGET pet)
endif()
pkg_check_modules(ISL REQUIRED IMPORTED_TARGET isl)


# ========
# ctadashi
# ========

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

add_executable(goodbadtest src/goodbadtest.c)

add_executable(tadashi src/tadashi.c)
target_link_libraries(tadashi PUBLIC PkgConfig::ISL PkgConfig::PET legality code_gen transformations)

add_executable(scop_detector src/scop_detector.c)
target_link_libraries(scop_detector PUBLIC PkgConfig::ISL PkgConfig::PET)

add_executable(raiser src/raiser.cc)
target_link_libraries(raiser PUBLIC PkgConfig::ISL PkgConfig::PET legality code_gen transformations nlohmann_json::nlohmann_json)

# enable_testing()
# include(GoogleTest)

# add_executable(test_legality tests/cc/test_legality.cc)
# target_link_libraries(test_legality PUBLIC PkgConfig::ISL GTest::gtest_main legality)

# gtest_discover_tests(test_legality)


# =======
# Install
# =======

install(
  TARGETS legality code_gen transformations scops ctadashi
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

# Create a CMake package
include(CMakePackageConfigHelpers)

# Prepare the Config.cmake.in content
set(PACKAGE_INIT_MACRO "@PACKAGE_INIT@")
set(CONFIG_CMAKE_IN "\
@PACKAGE_INIT_MACRO@\n\
include(\"\${CMAKE_CURRENT_LIST_DIR}/CTadashiTargets.cmake\")\n\
check_required_components(CTadashi)\n"
)

# Create Config.cmake.in
file(CONFIGURE
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/Config.cmake.in
    CONTENT ${CONFIG_CMAKE_IN}
    @ONLY)

# Create CTadashiConfig.cmake
configure_package_config_file(
    ${CMAKE_CURRENT_BINARY_DIR}/Config.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/CTadashiConfig.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/CTadashi)

# Create CTadashiConfigVersion.cmake
write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/CTadashiConfigVersion.cmake"
    VERSION "${version}"
    COMPATIBILITY AnyNewerVersion
)

# Install CMake package files
install(FILES
    "${CMAKE_CURRENT_BINARY_DIR}/CTadashiConfig.cmake"
    "${CMAKE_CURRENT_BINARY_DIR}/CTadashiConfigVersion.cmake"
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/CTadashi
)


# ===============
# Python bindings
# ===============

cmake_policy(SET CMP0078 NEW)
cmake_policy(SET CMP0086 NEW)

find_package(SWIG 4.0 REQUIRED)
set(UseSWIG_MODULE_VERSION 2)
include(${SWIG_USE_FILE})


# =======
# Library
# =======

# The name of the shared library must match the module name
set_source_files_properties(src/ctadashi.i PROPERTIES
  CPLUSPLUS ON
  SWIG_MODULE_NAME "ctadashi")

# Create the SWIG library
swig_add_library(ctadashi_swig
  TYPE MODULE
  LANGUAGE python
  OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR}/ctadashi
  OUTFILE_DIR ${CMAKE_CURRENT_BINARY_DIR}
  SOURCES src/ctadashi.i)

swig_link_libraries(ctadashi_swig
  PRIVATE CTadashi::ctadashi Python3::Python PkgConfig::PET)

set_target_properties(ctadashi_swig PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/ctadashi
  INSTALL_RPATH $ORIGIN/lib
  # SWIG_USE_TARGET_INCLUDE_DIRECTORIES TRUE
  # SWIG_COMPILE_OPTIONS -doxygen
  # SWIG_DEPENDS src/ctadashi.i
)

set_property(TARGET ctadashi_swig PROPERTY
    SWIG_USE_TARGET_INCLUDE_DIRECTORIES TRUE)

# Enable parsing the doxygen comments
set_property(TARGET ctadashi_swig
    PROPERTY SWIG_COMPILE_OPTIONS -doxygen)

# Add dependency to numpy.i
set_property(
    TARGET ctadashi_swig
    PROPERTY SWIG_DEPENDS src/ctadashi.i)


# =======
# Install
# =======

# Get the autogenerated Python file
get_property(WRAPPER_PY_FILE
    TARGET ctadashi_swig
    PROPERTY SWIG_SUPPORT_FILES)

# Install the autogenerated Python file
install(
    FILES ${WRAPPER_PY_FILE}
    DESTINATION ${CTADASHI_INSTALL_PREFIX}
    COMPONENT ctadashi)

# Install the SWIG library
install(
    TARGETS ctadashi_swig
    COMPONENT ctadashi
    LIBRARY DESTINATION ${CTADASHI_INSTALL_PREFIX}
    ARCHIVE DESTINATION ${CTADASHI_INSTALL_PREFIX}
    RUNTIME DESTINATION ${CTADASHI_INSTALL_PREFIX})

