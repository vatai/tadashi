#!/usr/bin/bash

set -x

ls $1/**/*.c* $1/**/*.C* | while read -r file; do ../../build/scop_detector "$file"; done 2>/dev/null
