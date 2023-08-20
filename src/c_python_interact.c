/* Test/debug code to experintem with C-python interaction.
 *
 * Emil Vatai
 */

#include <isl/printer.h>
#include <stdio.h>

#include <isl/ctx.h>
#include <isl/schedule.h>
#include <pet.h>

void print_schedule(isl_schedule *sched, isl_size idx) {
  printf("### sched[%d] begin ###\n", idx);
  printf("%s\n", isl_schedule_to_str(sched));
  printf("### sched[%d] end ###\n", idx);
}

int main(int argc, char *argv[]) {
  isl_ctx *ctx;
  isl_schedule *sched[4];
  char str1[] = "{ domain: \" [N] -> {S_0[i] : 0 <= i < N} \", child: { "
                "schedule: \"[N] -> L_0[{S_0[i]->[(i)]}] \" } }";
  char str2[] = "{ domain: \"[N, i] -> { S_0[] }\" }";

  ctx = isl_ctx_alloc_with_pet_options();

  sched[0] = isl_schedule_read_from_str(ctx, str1);
  print_schedule(sched[0], 0);
  sched[1] = isl_schedule_read_from_file(ctx, stdin);
  print_schedule(sched[1], 1);

  sched[2] = isl_schedule_read_from_str(ctx, str2);
  print_schedule(sched[2], 1);
  sched[3] = isl_schedule_read_from_file(ctx, stdin);
  print_schedule(sched[3], 1);

  isl_schedule_free(sched[0]);
  isl_schedule_free(sched[1]);
  isl_schedule_free(sched[2]);
  isl_schedule_free(sched[3]);
  isl_ctx_free(ctx);
  return 0;
}
