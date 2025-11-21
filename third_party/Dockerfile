# build with one of the following commands:

#  podman build <dir_where_this_file_is>
#
#  docker build <dir_where_this_file_is> -t manylinux-mod
FROM quay.io/pypa/manylinux_2_28_x86_64
RUN yum install -y gmp-c++ gmp-devel clang-devel-19.1.7 llvm-devel-19.1.7

WORKDIR /project/third_party
RUN curl https://repo.or.cz/isl.git/snapshot/15f1e39bed3997f773056d3fd127f38967adaa8a.tar.gz -o isl.tgz
RUN curl https://repo.or.cz/pet.git/snapshot/b85d6e89cfd95c7228216307faa6e95caecbecf9.tar.gz -o pet.tgz
RUN tar xzf isl.tgz && mv isl-* isl
RUN tar xzf pet.tgz && mv pet-* pet

WORKDIR /project/third_party/isl
RUN ./autogen.sh
RUN ./configure --prefix=/project/third_party/opt
RUN make -j install

WORKDIR /project/third_party/pet
RUN ./autogen.sh
RUN ./configure --prefix=/project/third_party/opt --with-isl-prefix=/project/third_party/opt
RUN make -j install
