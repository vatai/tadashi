/* Test/debug code to experintem with C-python interaction.
 *
 * Emil Vatai
 */

#include <isl/printer.h>
#include <stdio.h>

#include <isl/ctx.h>
#include <isl/schedule.h>
#include <pet.h>

int main(int argc, char *argv[]) {
  isl_ctx *ctx;
  isl_schedule *sched[4];
  char str1[] = "{ domain: \" [N] -> {S_0[i] : 0 <= i < N} \", child: { "
                "schedule: \"[N] -> L_0[{S_0[i]->[(i)]}] \" } }";

  char str2[] = "{ domain: \"[N, i] -> { S_0[] }\" }";
  ctx = isl_ctx_alloc_with_pet_options();

  // isl_printer *p = isl_printer_to_file(ctx, stdout);
  // p = isl_printer_print_schedule(p, sched[0]);
  sched[0] = isl_schedule_read_from_str(ctx, str1);
  printf("# sched[0]: \n%s\n", isl_schedule_to_str(sched[0]));
  sched[1] = isl_schedule_read_from_file(ctx, stdin);
  printf("# sched[1]: \n%s\n", isl_schedule_to_str(sched[1]));

  // p = isl_printer_print_schedule(p, sched[2]);
  sched[2] = isl_schedule_read_from_str(ctx, str2);
  printf("sched[2]: %s\n", isl_schedule_to_str(sched[2]));
  sched[3] = isl_schedule_read_from_file(ctx, stdin);
  printf("sched[3]: %s\n", isl_schedule_to_str(sched[3]));

  // isl_printer_free(p);
  isl_schedule_free(sched[0]);
  isl_schedule_free(sched[1]);
  isl_schedule_free(sched[2]);
  isl_schedule_free(sched[3]);
  isl_ctx_free(ctx);
  return 0;
}
