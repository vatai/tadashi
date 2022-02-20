#include <assert.h>

#include <isl/aff.h>
#include <isl/arg.h>
#include <isl/id_to_pw_aff.h>
#include <isl/options.h>
#include <isl/schedule_node.h>
#include <isl/set.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <pet.h>

const char filename[] = "../src/hello.c";

struct options {
  struct isl_options *isl;
  struct pet_options *pet;
  char *schedule;
  char *code;
  unsigned tree;
};

ISL_ARGS_START(struct options, options_args)
ISL_ARG_CHILD(struct options, isl, "isl", &isl_options_args, "isl options")
ISL_ARG_CHILD(struct options, pet, NULL, &pet_options_args, "pet options")
ISL_ARG_ARG(struct options, schedule, "schedule", NULL)
ISL_ARG_ARG(struct options, code, "code", NULL)
ISL_ARG_BOOL(struct options, tree, 0, "tree", 0,
             "input schedule is specified as schedule tree")
ISL_ARGS_END

ISL_ARG_DEF(options, struct options, options_args)

int main(int argc, char *argv[]) {

  struct options *options = options_new_with_defaults();
  isl_ctx *ctx = isl_ctx_alloc_with_options(&options_args, options);
  assert(ctx != NULL);

  pet_scop *scop = pet_scop_extract_from_C_source(ctx, filename, NULL);
  assert(scop != NULL);

  isl_printer *p = isl_printer_to_str(ctx);
  assert(p != NULL);

  p = isl_printer_print_set(p, scop->context_value);
  // char *output = isl_printer_get_str(isl_prn);
  // std::cout << output << std::endl;
  // isl_printer_free(isl_prn);

  // isl_ctx_free(ctx);

  return 0;
}
