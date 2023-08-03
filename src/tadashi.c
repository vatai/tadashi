#include <stdio.h>

#include <isl/arg.h>
#include <isl/ctx.h>
#include <isl/map.h>
#include <isl/options.h>
#include <isl/printer.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <pet.h>

struct options {
  struct isl_options *isl;
  struct pet_options *pet;
  char *schedule;
  char *source_file;
  unsigned tree;
};

ISL_ARGS_START(struct options, options_args)
ISL_ARG_CHILD(struct options, isl, "isl", &isl_options_args, "isl options")
ISL_ARG_CHILD(struct options, pet, NULL, &pet_options_args, "pet options")
ISL_ARGS_END
ISL_ARG_DEF(options, struct options, options_args)

isl_printer *transform(isl_printer *p, pet_scop *scop, void *usr) {
  isl_schedule *schedule = pet_scop_get_schedule(scop);
  isl_schedule_node *root = isl_schedule_get_root(schedule);
  p = isl_printer_start_line(p);
  p = isl_printer_print_str(p, "!!!!!!!!!!! SCOP begin !!!!!!!!!!!");
  p = isl_printer_end_line(p);
  printf("%s \n", isl_schedule_node_to_str(root));
  // p = isl_printer_print_schedule_node(p, root);
  p = isl_printer_start_line(p);
  p = isl_printer_print_str(p, "!!!!!!!!!!! SCOP end !!!!!!!!!!!");
  p = isl_printer_end_line(p);
  return p;
}

int main(int argc, char *argv[]) {
  struct options *options = options_new_with_defaults();
  isl_ctx *ctx = isl_ctx_alloc_with_options(&options_args, options);
  isl_args_parse(&options_args, argc, argv, options, ISL_ARG_ALL);
  char *input = "../examples/many.c";
  FILE *output = stdout;
  pet_transform_C_source(ctx, input, output, transform, NULL);
  printf("%s Done\n", argv[0]);
  return 0;
}
