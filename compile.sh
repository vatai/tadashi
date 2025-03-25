#!/usr/bin/bash

set -x

clang -S -emit-llvm ./examples/inputs/depnodep.c -O1 -o - | opt -load LLVMPolly.so -polly-canonicalize -polly-import-jscop -o depnodep.mod.ll && clang depnodep.mod.ll  -o depnodep.mod
./depnodep.orig > out.orig
./depnodep.mod  > out.mod
diff out.orig out.mod
echo DONE
