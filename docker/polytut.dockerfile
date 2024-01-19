FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y git build-essential autoconf pkg-config libgmp-dev libntl-dev libtool llvm clang llvm-dev libc++-dev libclang-dev llvm-dev libyaml-dev bash-completion ninja-build cmake isl-dev
# RUN apt-get install -y llvm-15 clang-15 llvm-15-dev libclang-15-dev

RUN git clone git://repo.or.cz/barvinok.git
WORKDIR barvinok
RUN ./get_submodules.sh

ENV PATH=/usr/lib/llvm-15/bin:$PATH
ENV LD_LIBRARY_PATH=/usr/lib/llvm-15/lib:/usr/lib/clang/15/lib
ENV LIBRARY_PATH=/usr/lib/llvm-15/lib:/usr/lib/clang/15/lib
ENV C_INCLUDE_PATH=/usr/lib/llvm-15/include
ENV CPLUS_INCLUDE_PATH=/usr/lib/llvm-15/include

RUN ./autogen.sh
RUN ./configure --with-pet=bundled --with-clang=system --enable-shared-barvinok --prefix=/usr
RUN make -j
# RUN make isl.py
# RUN make install
RUN echo $LD_LIBRARY_PATH

# COPY ex.c .
# RUN LD_LIBRARY_PATH=/barvinok/.libs:/barvinok/pet/.libs${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}} PYTHONPATH=/barvinok:/barvinok/pet/interface${PYTHONPATH:+:${PYTHONPATH}} python -c 'import isl; import pet; pet.scop.extract_from_C_source("ex.c", "f")'

# COPY ../deps/ .

# RUN apk add --no-cache openssh-client
# RUN mkdir -p -m 0700 ~/.ssh && ssh-keyscan gitlab.com >> ~/.ssh/known_hosts
# RUN --mount=type=ssh ssh -q -T git@gitlab.com 2>&1 | tee /hello
# RUN --mount=type=ssh git clone git@github.com:vatai/polyhedral-tutor.git
