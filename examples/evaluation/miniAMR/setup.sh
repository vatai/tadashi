#!/usr/bin/bash

[ -e miniAMR ] || git clone https://github.com/Mantevo/miniAMR
git -C miniAMR apply ../patch
