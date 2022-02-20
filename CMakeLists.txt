cmake_minimum_required(VERSION 3.18.4)

project(polyhedral-tutor)

set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)


# set(CMAKE_PREFIX_PATH "${CMAKE_SOURCE_DIR}/src/pet;${CMAKE_SOURCE_DIR}/src/isl")
set(ENV{PKG_CONFIG_PATH} "${CMAKE_SOURCE_DIR}/src/pet;${CMAKE_SOURCE_DIR}/src/pet/isl")
# message("CMAKE_PREFIX_PATH is " ${CMAKE_PREFIX_PATH})

find_package(PkgConfig REQUIRED)
pkg_search_module(PET REQUIRED IMPORTED_TARGET pet)
pkg_search_module(ISL REQUIRED IMPORTED_TARGET isl)

# message(WARNING "PET_INCLUDE_DIRS is ${PET_INCLUDE_DIRS}")
# message(WARNING "PET_FOUND is ${PET_FOUND}")
# message(WARNING "ISL_FOUND is ${ISL_FOUND}")
# message(WARNING "ISL_LIBRARY_DIRS is ${ISL_LIBRARY_DIRS}")

add_executable(main src/main.c)
target_link_libraries(main PUBLIC PkgConfig::ISL PkgConfig::PET)
target_link_directories(main PUBLIC ${PET_LIBRARY_DIRS}  ${ISL_LIBRARY_DIRS})
target_include_directories(main PUBLIC ${PET_INCLUDE_DIRS} ${ISL_INCLUDE_DIRS})
