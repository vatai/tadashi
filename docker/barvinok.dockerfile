FROM ubuntu:23.10

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y git build-essential python-is-python3 autoconf pkg-config libgmp-dev libntl-dev libtool llvm clang llvm-dev libc++-dev libclang-dev llvm-dev libyaml-dev bash-completion ninja-build cmake

RUN git clone git://repo.or.cz/barvinok.git
WORKDIR barvinok
RUN ./get_submodules.sh
RUN ./autogen.sh
RUN ./configure --with-pet=bundled --with-clang=system --enable-shared-barvinok --prefix=/usr
RUN make -j
RUN make isl.py
RUN make install

RUN echo 'export LD_LIBRARY_PATH=/barvinok/.libs:/barvinok/pet/.libs${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}' >> ~/.bashrc
RUN echo 'export PYTHONPATH=/barvinok:/barvinok/pet/interface${PYTHONPATH:+:${PYTHONPATH}}' >> ~/.bashrc
RUN echo 'export LIBRARY_PATH=/barvinok/.libs:/barvinok/pet/.libs:/barvinok/isl/.libs${LIBRARY_PATH:+:${LIBRARY_PATH}}' >> ~/.bashrc
