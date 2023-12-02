#include <stdio.h>

#include <isl/ctx.h>
int main() {
  printf("Hello\n");
  isl_ctx *ctx = isl_ctx_alloc();
  isl_ctx_free(ctx);
  printf("Bye!\n");
  return 0;
}
