FROM ubuntu:latest

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y git build-essential autoconf pkg-config libtool libc++-dev libyaml-dev libntl-dev libgmp-dev llvm clang llvm-dev libclang-dev swig openmpi-bin openmpi-common libopenmpi-dev cmake python3 python3-dev ninja-build

RUN git clone https://github.com/vatai/tadashi.git
WORKDIR tadashi

RUN mkdir build
RUN cmake -S . -B build -G Ninja
RUN cmake --build build

WORKDIR /workdir

