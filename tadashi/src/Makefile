# As of now, this Makefile is for compiling prototype, a quick isl
# executable aimed at fast prototyping.

PREFIX=${PWD}/../../third_party/opt
CXXFLAGS=-I${PREFIX}/include
CFLAGS=-I${PREFIX}/include
LDLIBS=-L${PREFIX}/lib -lpet -lisl -lstdc++
prototype: prototype.o ccscop.o

run: prototype
	LD_LIBRARY_PATH=${PREFIX}/lib ./prototype
