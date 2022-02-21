#include <assert.h>
#include <stdio.h>

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
  struct options *options;
  char *output;
  isl_ctx *ctx;
  pet_scop *scop;
  isl_printer *p;

  options = options_new_with_defaults();
  ctx = isl_ctx_alloc_with_options(&options_args, options);
  assert(ctx != NULL);

  scop = pet_scop_extract_from_C_source(ctx, filename, NULL);
  assert(scop != NULL);

  p = isl_printer_to_str(ctx);
  assert(p != NULL);
  output = isl_printer_get_str(p);
  printf("%s\n", output);

  printf("n_arrays: %d\n", scop->n_array);
  for (int i = 0; i < scop->n_array; ++i) {
    struct pet_array *array = scop->arrays[i];
    p = isl_printer_print_set(p, array->context);
    output = isl_printer_get_str(p);
    printf("arrays[i]->context: %s\n", output);
    p = isl_printer_print_set(p, array->extent);
    output = isl_printer_get_str(p);
    printf("arrays[i]->extent: %s\n", output);
  }

  printf("n_implication: %d\n", scop->n_implication);
  for (int i = 0; i < scop->n_implication; ++i) {
    p = isl_printer_print_map(p, scop->implications[i]->extension);
    output = isl_printer_get_str(p);
    printf("implications[i]->extension: %s\n", output);
    printf("satisfied: %d\n", scop->implications[i]->satisfied);
  }

  printf("n_independence: %d\n", scop->n_independence);
  for (int i = 0; i < scop->n_independence; ++i) {
    p = isl_printer_print_union_map(p, scop->independences[i]->filter);
    output = isl_printer_get_str(p);
    printf("independences[i]->filter: %s\n", output);
    p = isl_printer_print_union_set(p, scop->independences[i]->local);
    output = isl_printer_get_str(p);
    printf("independences[i]->local: %s\n", output);
  }

  // std::cout << output << std::endl;
  // isl_printer_free(isl_prn);

  // isl_ctx_free(ctx);

  return 0;
}
