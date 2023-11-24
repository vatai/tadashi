#include <assert.h>

#include <isl/aff.h>
#include <isl/set.h>
#include <isl/val.h>

isl_stat piece_lexpos(isl_set *set, isl_multi_aff *ma, void *user) {
  isl_set_free(set);
  isl_size dim = isl_multi_aff_dim(ma, isl_dim_set);
  int *retval = user;
  *retval = 0;
  for (isl_size pos = 0; pos < dim; pos++) {
    isl_aff *aff = isl_multi_aff_get_at(ma, pos);
    // check if aff has always dim == 1
    assert(isl_aff_is_cst(aff));

    isl_val *cst = isl_aff_get_constant_val(aff);
    isl_bool is_zero = isl_val_is_zero(cst);
    isl_bool is_pos = isl_val_is_pos(cst);
    isl_val_free(cst);
    if (is_zero)
      continue;

    isl_val *denom = isl_aff_get_denominator_val(aff);
    isl_bool denom_pos = isl_val_is_pos(denom);
    isl_val_free(denom);

    if (is_pos && denom_pos)
      *retval = +1;
    else
      *retval = -1;

    isl_aff_free(aff);
    break;
  }
  isl_multi_aff_free(ma);
  return isl_stat_ok;
}

struct test_data_t {
  char *input;
  int output;
};

void test_piece_lexpos(isl_ctx *ctx) {
  struct test_data_t data[] = {
      {"{ [ i ] -> [ -1 ]  }", -1}, //
      {"{ [ i ] -> [ 0 ]  }", 0},   //
      {"{ [ i ] -> [ 1 ]  }", 1},   //
      //
      {"{ [ i ] -> [ -1, -1 ]  }", -1}, //
      {"{ [ i ] -> [ -1, 0 ]  }", -1},  //
      {"{ [ i ] -> [ -1, 1 ]  }", -1},  //
      {"{ [ i ] -> [ 0, -1 ]  }", -1},  //
      {"{ [ i ] -> [ 0, 0 ]  }", 0},    //
      {"{ [ i ] -> [ 0, 1 ]  }", 1},    //
      {"{ [ i ] -> [ 1, -1 ]  }", 1},   //
      {"{ [ i ] -> [ 1, 0 ]  }", 1},    //
      {"{ [ i ] -> [ 1, 1 ]  }", 1},    //
      //
      {"{ [ i ] -> [ -1, -1, -1 ]  }", -1}, //
      {"{ [ i ] -> [ -1, -1, 0 ]  }", -1},  //
      {"{ [ i ] -> [ -1, -1, 1 ]  }", -1},  //
      {"{ [ i ] -> [ -1, 0, -1 ]  }", -1},  //
      {"{ [ i ] -> [ -1, 0, 0 ]  }", -1},   //
      {"{ [ i ] -> [ -1, 0, 1 ]  }", -1},   //
      {"{ [ i ] -> [ -1, 1, -1 ]  }", -1},  //
      {"{ [ i ] -> [ -1, 1, 0 ]  }", -1},   //
      {"{ [ i ] -> [ -1, 1, 1 ]  }", -1},   //
      {"{ [ i ] -> [ 0, -1, -1 ]  }", -1},  //
      {"{ [ i ] -> [ 0, -1, 0 ]  }", -1},   //
      {"{ [ i ] -> [ 0, -1, 1 ]  }", -1},   //
      {"{ [ i ] -> [ 0, 0, -1 ]  }", -1},   //
      {"{ [ i ] -> [ 0, 0, 0 ]  }", 0},     //
      {"{ [ i ] -> [ 0, 0, 1 ]  }", 1},     //
      {"{ [ i ] -> [ 0, 1, -1 ]  }", 1},    //
      {"{ [ i ] -> [ 0, 1, 0 ]  }", 1},     //
      {"{ [ i ] -> [ 0, 1, 1 ]  }", 1},     //
      {"{ [ i ] -> [ 1, -1, -1 ]  }", 1},   //
      {"{ [ i ] -> [ 1, -1, 0 ]  }", 1},    //
      {"{ [ i ] -> [ 1, -1, 1 ]  }", 1},    //
      {"{ [ i ] -> [ 1, 0, -1 ]  }", 1},    //
      {"{ [ i ] -> [ 1, 0, 0 ]  }", 1},     //
      {"{ [ i ] -> [ 1, 0, 1 ]  }", 1},     //
      {"{ [ i ] -> [ 1, 1, -1 ]  }", 1},    //
      {"{ [ i ] -> [ 1, 1, 0 ]  }", 1},     //
      {"{ [ i ] -> [ 1, 1, 1 ]  }", 1},     //
  };
  size_t nbtests = sizeof(data) / sizeof(data[0]);
  for (size_t i = 0; i < nbtests; i++) {
    isl_multi_aff *ma = isl_multi_aff_read_from_str(ctx, data[i].input);
    isl_set *set = isl_set_read_from_str(ctx, "{ : }");
    int rv;
    isl_stat stat = piece_lexpos(set, ma, &rv);
    assert(stat == isl_stat_ok);
    printf("test %d: %s\n", i, rv == data[i].output ? "OK" : data[i].input);
  }
};
