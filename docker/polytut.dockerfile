FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y git python build-essential autoconf pkg-config libgmp-dev libntl-dev libtool llvm clang llvm-dev libc++-dev libclang-dev llvm-dev libyaml-dev

RUN git clone git://repo.or.cz/barvinok.git
WORKDIR barvinok
RUN ./get_submodules.sh
RUN ./autogen.sh


# RUN ./configure --prefix=$HOME/.local/opt --with-isl=bundled --with-pet=bundled --with-clang=system --with-libyaml=system --enable-shared-barvinok
RUN ./configure --with-isl=bundled --with-pet=bundled --with-clang=system --with-libyaml=system --enable-shared-barvinok
RUN make -j
RUN make isl.py
RUN make install

ADD diagonal.c .
ADD run.sh .
ADD run.py .

RUN bash run.sh
