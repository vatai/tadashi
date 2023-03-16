#!/usr/bin/bash

PLUTO_SRC="build/pluto"
CFLOW_ARGS=(
	-f dot
	-I ${PLUTO_SRC}
	-I ${PLUTO_SRC}/include
	-I ${PLUTO_SRC}/lib
	-I ${PLUTO_SRC}/openscop/include
	-I ${PLUTO_SRC}/pet/include
	-I ${PLUTO_SRC}/clan/include
	${PLUTO_SRC}/lib/plutolib.c
	${PLUTO_SRC}/lib/pluto.c
	${PLUTO_SRC}/tool/main.cpp
)
cflow ${CFLOW_ARGS[@]} | dot -Txlib -Ksfdp

