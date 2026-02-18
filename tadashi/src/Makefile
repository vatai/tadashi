PREFIX=${PWD}/../../third_party/opt
CXXFLAGS=-I${PREFIX}/include
CFLAGS=-I${PREFIX}/include
LDLIBS=-L${PREFIX}/lib -lpet -lisl -lstdc++
tmp: tmp.o ccscop.o

run: tmp
	LD_LIBRARY_PATH=${PREFIX}/lib ./tmp
