FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y git python-is-python3 \
    build-essential autoconf pkg-config libtool libc++-dev libyaml-dev \
    libntl-dev libgmp-dev llvm clang llvm-dev libclang-dev cmake ninja-build

RUN mkdir -p -m 0700 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts
RUN --mount=type=ssh git clone git@github.com:vatai/tadashi.git
WORKDIR tadashi

RUN mkdir build
WORKDIR build
RUN cmake .. -G Ninja
RUN cmake --build .
RUN cmake --build . -t install

ARG USER
ARG UID
ARG GROUP
ARG GID
RUN groupadd -g $GID $GROUP
RUN useradd -u $UID -g $GID $USER
WORKDIR /workdir

