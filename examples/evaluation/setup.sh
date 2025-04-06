#!/usr/bin/bash

[ -e SNAP ] || git clone https://github.com/lanl/SNAP.git
git apply snap.patch
