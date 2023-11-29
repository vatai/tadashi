#include <isl/ctx.h>
#include <stdio.h>

#include <pet.h>

#include <isl/set.h>

int main(int argc, char *argv[]) {
  isl_ctx *ctx = isl_ctx_alloc();

  printf("Hello");
  isl_set *set, *lm;
  isl_basic_set *bset;
  set = isl_set_read_from_str(ctx, "{[i,j]: 0<=i and 0<=j<=5 }");
  isl_set_dump(set);
  printf("Bounded:%d\n", isl_set_is_bounded(set));
  lm = isl_set_lexmin(set);
  // isl_multi_val *mv = isl_set_get_plain_multi_val_if_fixed(lm);
  // isl_multi_val_dump(mv);
  // isl_multi_val_free(mv);
  // std::cout << "Size: " << isl_multi_val_size(mv) << std::endl;
  // isl_set_foreach_basic_set(lm, fn, NULL);
  // isl_set_free(set);
  isl_set_free(lm);

  isl_ctx_free(ctx);
}

void f() {
  // const char *testName =
  //     ::testing::UnitTest::GetInstance()->current_test_info()->name();
  // FILE *output_file = fopen(opt->output_file_path, "w");
  // r = pet_transform_C_source(ctx, opt->source_file_path, output_file,
  //                            &foreach_scop_callback, &counter);
  // fprintf(stderr, "Number of scops: %lu\n", counter);
  // fclose(output_file);
}
