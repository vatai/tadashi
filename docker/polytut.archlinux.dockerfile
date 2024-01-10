# FROM ubuntu:22.04
FROM archlinux


RUN pacman -Syu --noconfirm
RUN pacman -S --noconfirm git make cmake gcc less vim pkgconf automake autoconf libtool gmp ntl
RUN pacman -S --noconfirm llvm clang
RUN git clone git://repo.or.cz/barvinok.git
WORKDIR barvinok
RUN ./get_submodules.sh

RUN ./autogen.sh
RUN ./configure --with-pet=bundled --with-clang=system --enable-shared-barvinok --prefix=/usr
RUN make -j
RUN make isl.py
RUN make install

COPY ex.c .
RUN pacman -S --noconfirm python
RUN LD_LIBRARY_PATH=/barvinok/.libs:/barvinok/pet/.libs${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}} PYTHONPATH=/barvinok:/barvinok/pet/interface${PYTHONPATH:+:${PYTHONPATH}} python -c 'import isl; import pet; pet.scop.extract_from_C_source("ex.c", "f")'

# COPY ../deps/ .

# RUN apk add --no-cache openssh-client
# RUN mkdir -p -m 0700 ~/.ssh && ssh-keyscan gitlab.com >> ~/.ssh/known_hosts
# RUN --mount=type=ssh ssh -q -T git@gitlab.com 2>&1 | tee /hello
# RUN --mount=type=ssh git clone git@github.com:vatai/polyhedral-tutor.git
