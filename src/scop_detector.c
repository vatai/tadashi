#include <stddef.h>
#include <stdio.h>

#include <isl/ctx.h>
#include <pet.h>

isl_printer *
transform(isl_printer *, pet_scop *, void *) {}
int
main(int argc, char *argv[]) {
  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  FILE *dev_null = fopen("/dev/null", "w");
  pet_transform_C_source(ctx, argv[1], dev_null, transform, NULL);
  return 0;
}
