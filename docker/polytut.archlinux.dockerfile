FROM archlinux


RUN pacman -Syu --noconfirm
RUN pacman -S --noconfirm git make cmake gcc less vim pkgconf automake autoconf libtool gmp ntl llvm clang python
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

