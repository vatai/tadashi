#!/usr/bin/bash

all=(
    correlation
    covariance
    gemm
    gemver
    gesummv
    symm
    syr2k
    syrk
    trmm
    2mm
    3mm
    atax
    bicg
    doitgen
    mvt
    cholesky
    durbin
    gramschmidt
    lu
    ludcmp
    trisolv
    deriche
    floyd-warshall
    nussinov
    adi
    fdtd-2d
    heat-3d
    jacobi-1d
    jacobi-2d
    seidel-2d
)

for benchmark in "${all[@]}"; do
    echo sbatch -J ${benchmark} genoa.sh
done
