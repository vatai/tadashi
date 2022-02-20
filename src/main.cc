#include <iostream>

#include <isl/aff.h>
#include <pet.h>

int main(int argc, char *argv[]) {
  std::cout << "Hello, world" << std::endl;
  isl_ctx *ctx;
  ctx = isl_ctx_alloc_with_pet_options();
  return 0;
}
