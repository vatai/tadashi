#!/bin/bash

TADASHI_BIN=$(dirname $0)/../build/tadashi
rm $1.*.yaml
$TADASHI_BIN $1 > /dev/null 2>&1
ls $1.*.yaml | while read origfile; do
    inputfile=$(echo ${origfile} | sed s/orig\.yaml/input.yaml/)
    cp ${origfile} ${inputfile}
done
$TADASHI_BIN $1
