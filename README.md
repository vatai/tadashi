# Tadashi

## Documentation:

Documentation will be made available on https://tadashi.readthedocs.io/ (or a similar website).  For now it can be built manually:

```bash
cd docs
make html
```

[[Docs are in progress]]


## Build instructions:

Before building, install LLVM and other (system) packages (check [dockerfile](docker/tadashi.dockerfile) for an exact list of `apt-get` packages).

```bash
git clone --recursive https://github.com/vatai/tadashi.git
mkdir tadashi/build
cd tadashi/build
cmake ..
cmake --build .
```

## Run from docker

```bash
mk_dot_env.sh  # create .env file with USER, UID, GROUP, GID
docker compose build # build images
docker compose run --rm -it tadashi
```

The tadashi binds the host repo to `/workdir` inside the
container.

Tadashi should be rebuilt from the container:
```bash
mkdir /workdir/build
cd /workdir/build
cmake ..
cmake --build .
```
The dependencies are built
during the `docker compose build` command under `/tadashi/build/_deps`
and the environment is set up that these dependencies are used
(i.e. not rebuilt again).
