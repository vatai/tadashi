# As of now, this Makefile is for compiling prototype, a quick isl
# executable aimed at fast prototyping.

PREFIX=${PWD}/../../third_party/opt
CFLAGS=-g -I${PREFIX}/include
CXXFLAGS=$(CFLAGS)
LDLIBS=-g -L${PREFIX}/lib -lpet -lisl -lstdc++ -Wl,-rpath,${PREFIX}/lib
prototype: prototype.o ccscop.o

run: prototype
	./prototype
