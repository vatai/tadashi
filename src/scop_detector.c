#include <bits/posix2_lim.h>
#include <isl/printer.h>
#include <limits.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

#include <isl/ctx.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <pet.h>

#include "legality.h"

/*
 * This is a utility which helps finding good candidates for tadashi
 * to optimise.
 *
 * Output:
 *
 * scop_detector prints the scops one by one as they are detected. A
 * /tmp/scops_<original_filename>.c is also created, with comments
 * marking the begin/end of the detected scops inserted.
 *
 * Usage is:
 *
 * $ scop_detector some_c_or_cpp_file.c [-a]
 *
 * The `-a` disables the scop autodetection and must be the second
 * parameter (i.e. scop_detector -a file.c doesn't work).  If header
 * files are found, you need to set the C_INCLUDE_PATH and/or
 * CPLUS_INCLUDE_PATH.
 *
 * Practical usage:
 *
 * If (one of) the detected scops look big, the file and the scops are
 * a good candidate!  Then we should inspect/read the code (possibly
 * the one in /tmp with the begin/end scop comments). If the code
 * looks good, we can insert proper `#pragma scop` and `#pragma
 * endscop` and switch to using tadashi's `tadashi.apps.Simple` to
 * transform the file.  Since `tadashi.apps.Simple` is aimed for
 * single .c file apps, `app.compile()` and `app.measure()` probably
 * won't work, i.e. you need manually (from the terminal) to compile
 * the transformed code (by `app.generate_code()`).
 *
 */
isl_printer *
transform(isl_printer *p, pet_scop *scop, void *user) {
  size_t *num_scops = user;
  char line[LINE_MAX];
  struct tadashi_scop *ts = allocate_tadashi_scop(scop);
  isl_schedule_node *root = isl_schedule_get_root(ts->schedule);
  printf("scop[%d]:\n%s\n", *num_scops, isl_schedule_node_to_str(root));
  sprintf(line, "// #pragma scop // [%zu] //////////////////\n", *num_scops);
  p = isl_printer_print_str(p, line);
  p = pet_scop_print_original(scop, p);
  sprintf(line, "\n// #pragma endscop // [%zu] //////////////////\n",
          *num_scops);
  p = isl_printer_print_str(p, line);
  (*num_scops)++;
  return p;
}

int
main(int argc, char *argv[]) {
  char *input = argv[1];
  printf(">>>>>>>>>>>>>>>>> %s\n", input);
  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  char out[PATH_MAX];
  char *outfile = strrchr(input, '/');
  outfile = outfile ? outfile + 1 : input;
  sprintf(out, "/tmp/scops_detect_%s", outfile);
  printf("out %s\n", out);
  FILE *output = fopen(out, "w");
  size_t num_scops = 0;
  pet_options_set_autodetect(ctx, 1);
  if (argc > 2 && strncmp(argv[2], "-a", 3) == 0) {
    printf("Disabling auto detection\n");
    pet_options_set_autodetect(ctx, 0);
  }
  pet_transform_C_source(ctx, input, output, transform, &num_scops);
  if (num_scops) {
    printf("Number of scops in %s: %d\n", input, num_scops);
    printf("Based on this we generated: %s\n", out);
  }
  return !num_scops;
}
