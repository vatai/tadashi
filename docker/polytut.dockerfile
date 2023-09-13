FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y git build-essential autoconf pkg-config libgmp-dev libntl-dev libtool llvm clang llvm-dev libc++-dev libclang-dev llvm-dev libyaml-dev

RUN git clone git://repo.or.cz/barvinok.git
WORKDIR barvinok
RUN ./get_submodules.sh
RUN ./autogen.sh
RUN ./configure --with-pet=bundled --with-clang=system --enable-shared-barvinok --prefix=/usr
RUN make -j
RUN make isl.py
RUN make install

COPY ../. .
