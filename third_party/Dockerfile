# build with one of the following commands:

#  podman build <dir_where_this_file_is>
#
#  docker build <dir_where_this_file_is> -t manylinux-mod
FROM quay.io/pypa/manylinux_2_28_x86_64
RUN yum install -y gmp-c++ gmp-devel clang-devel-19.1.7 llvm-devel-19.1.7

ADD isl.bundle /project/third_party/
RUN git init /project/third_party/isl
WORKDIR /project/third_party/isl
RUN git remote add origin ../isl.bundle
RUN git fetch
RUN git checkout master
RUN ./autogen.sh
RUN ./configure --prefix=/project/third_party/opt
RUN make -j install

ADD pet.bundle /project/third_party/
RUN git init /project/third_party/pet
WORKDIR /project/third_party/pet
RUN git remote add origin ../pet.bundle
RUN git fetch
RUN git checkout master
RUN ./autogen.sh
RUN ./configure --prefix=/project/third_party/opt --with-isl-prefix=/project/third_party/opt
RUN make -j install
