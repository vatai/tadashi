# Tadashi

## Build instructions:

Before building, install LLVM and other (system) packages (check [dockerfile](docker/tadashi.dockerfile) for an exact list of `apt-get` packages).

```
git clone --recursive https://github.com/vatai/tadashi.git
mkdir tadashi/build
cd tadashi/build
cmake ..
cmake --build .
```
