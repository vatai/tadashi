#!/bin/bash
cmake --build build --target test
python -m unittest
