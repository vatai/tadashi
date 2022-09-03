# polyhedral-tutor

Build instructions:

```
git clone --recursive https://github.com/vatai/polyhedral-tutor.git
cd polyhedral-tutor/src/pet
./autogen.sh && ./configure && make -j
cd ../..
mkdir build
cd build
cmake ..
cmake --build .
```
