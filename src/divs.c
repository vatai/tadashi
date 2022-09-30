#include <isl/ctx.h>
#include <isl/set.h>
#include <stdio.h>

int main(int argc, char *argv[]) {
  isl_ctx *ctx = isl_ctx_alloc();
  isl_set *set = isl_set_read_from_str(
      ctx,
      /* "{[i] : exists (a : i = 2a and ((10 <= " */
      /* "i <= 42) or (100 <= i <= 120)))}" // */
      /* "[n] -> { [i] : exists (a = [i/10] : 0 <= i " */
      /* "<= n and i - 10 a <= 6) }}" // */
      "[n] -> {[i, j] : 0 <= 4 * i + j < n and 0 <= j < i}");
  printf("set: %s\n", isl_set_to_str(set));
  set = isl_set_compute_divs(set);
  printf("div: %s\n", isl_set_to_str(set));
  isl_set_free(set);
  isl_ctx_free(ctx);
  printf("Done!\n");
  return 0;
}
