#include <assert.h>
#include <isl/set.h>
#include <stdio.h>

#include <isl/options.h>
#include <pet.h>

struct options {
  struct isl_options *isl;
  struct pet_options *pet;
  char *source_file;
};

ISL_ARGS_START(struct options, options_args)
ISL_ARG_CHILD(struct options, isl, "isl", &isl_options_args, "isl options")
ISL_ARG_CHILD(struct options, pet, NULL, &pet_options_args, "pet options")
ISL_ARG_ARG(struct options, source_file, "source file", NULL)
ISL_ARGS_END
ISL_ARG_DEF(options, struct options, options_args)

int main(int argc, char *argv[]) {
  struct options *opt = options_new_with_defaults();
  isl_ctx *ctx = isl_ctx_alloc_with_options(&options_args, opt);
  argc = options_parse(opt, argc, argv, ISL_ARG_ALL);
  printf("%d : %s\n", argc, opt->source_file);
  assert(argc == 1);

  pet_scop_extract_from_C_source(ctx, opt->source_file, NULL);

  return 0;
}
