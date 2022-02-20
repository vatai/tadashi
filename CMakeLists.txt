cmake_minimum_required(VERSION 3.18.4)

project(spin-chem)

set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)

# Remove the lines below if you do not wish to have PETSc determine the compilers
# execute_process ( COMMAND pkg-config PETSc --variable=ccompiler COMMAND tr -d '\n' OUTPUT_VARIABLE C_COMPILER)
# SET(CMAKE_C_COMPILER ${C_COMPILER})
# execute_process ( COMMAND pkg-config PETSc --variable=cxxcompiler COMMAND tr -d '\n' OUTPUT_VARIABLE CXX_COMPILER)
# if (CXX_COMPILER)
#   SET(CMAKE_CXX_COMPILER ${CXX_COMPILER})
# endif (CXX_COMPILER)
# execute_process ( COMMAND pkg-config PETSc --variable=fcompiler COMMAND tr -d '\n' OUTPUT_VARIABLE FORTRAN_COMPILER)

# set(CMAKE_PREFIX_PATH "${CMAKE_SOURCE_DIR}/src/pet;${CMAKE_SOURCE_DIR}/src/isl")
set(ENV{PKG_CONFIG_PATH} "${CMAKE_SOURCE_DIR}/src/pet;${CMAKE_SOURCE_DIR}/src/pet/isl")
message("CMAKE_PREFIX_PATH is " ${CMAKE_PREFIX_PATH})

find_package(PkgConfig REQUIRED)
pkg_search_module(PET REQUIRED IMPORTED_TARGET pet)
pkg_search_module(ISL REQUIRED IMPORTED_TARGET isl)

# if (PKG_CONFIG_FOUND)
#   pkg_check_modules(PETSC PETSc)
# endif()
# if(NOT ${PETSC_FOUND})
#   message(FATAL_ERROR "PETSc not found.")
# endif()
# include_directories(${PETSC_INCLUDE_DIRS})

message("PET_INCLUDE_DIRS is ${PET_INCLUDE_DIRS}")

add_executable(main src/main.cc)
target_include_directories(main PUBLIC ${ISL_INCLUDE_DIRS})
target_link_libraries(main PkgConfig::ISL)
target_include_directories(main PUBLIC ${PET_INCLUDE_DIRS})
target_link_directories(main PUBLIC ${PET_LIBRARY_DIRS})
target_link_libraries(main PkgConfig::PET)
