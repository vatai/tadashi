/*
 * Emil VATAI, Riken, R-CCS, HPAIS. All rights reserved.
 *
 * Date: 2023-11-24
 */

#include <isl/space_type.h>
#include <isl/val.h>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include <isl/aff.h>
#include <isl/constraint.h>
#include <isl/ctx.h>
#include <isl/options.h>
#include <isl/point.h>
#include <isl/set.h>

#include "legality.h"

class LegalityTest : public testing::Test {
protected:
  LegalityTest() : ctx{isl_ctx_alloc()} {
    isl_options_set_on_error(ctx, ISL_ON_ERROR_ABORT);
  }
  virtual ~LegalityTest() { isl_ctx_free(ctx); }

  isl_ctx *ctx;
};

struct test_data_t {
  std::string input;
  int output;
};

TEST_F(LegalityTest, PieceLexpos) {
  std::vector<struct test_data_t> data = {
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
  isl_multi_aff *ma;
  isl_set *set;
  int rv;
  for (auto d : data) {
    ma = isl_multi_aff_read_from_str(ctx, d.input.c_str());
    set = isl_set_read_from_str(ctx, "{ : }");
    isl_stat stat = piece_lexpos(set, ma, &rv);
    assert(stat == isl_stat_ok);
    SCOPED_TRACE("input = " + d.input);
    EXPECT_EQ(rv, d.output);
    EXPECT_EQ(stat, isl_stat_ok);
  }
}

TEST_F(LegalityTest, DeltaSetLexpos) {
  std::vector<struct test_data_t> data = {
      {"{ [ i ] : 10 <= i and i <= 15 }", 1},
      {"{[i]: i>=0 and (i mod 2)=0 and i<10;"
       "[i]: -10<i< 0 and (i mod 2)=1}",
       -1}, //
      {"{[i]: exists(a: i = 2a) and 0<=i<=15}", 0},
      /*
        02 12 22 32 42
        01 11    31 41
        00          40
       */
      {"{[i,j]: 0 <= i <= j and 1 <= j < 3;"
       "[i,j]: 4-j <= i <= 4 and 0 <= j < 3 }",
       0},
  };
  isl_set *set;
  int rv;
  // TODO(vatai): try isl_basic_set_partial_lexmin et al
  for (auto d : data) {
    set = isl_set_read_from_str(ctx, d.input.c_str());
    isl_set_dump(set);
    isl_stat stat = delta_set_lexpos(set, &rv);
  }
}

isl_stat fn(isl_basic_set *bset, void *user) {
  isl_constraint_list *lst = isl_basic_set_get_constraint_list(bset);
  isl_basic_set_free(bset);
  isl_constraint *cst = isl_constraint_list_get_at(lst, 0);
  isl_constraint_list_free(lst);

  isl_constraint_dump(cst);
  isl_val *v = isl_constraint_get_coefficient_val(cst, isl_dim_set, 0);
  isl_constraint_free(cst);
  isl_val_dump(v);
  isl_val_free(v);
  return isl_stat_ok;
}

TEST_F(LegalityTest, Scratch) {
  std::cout << "Hello" << std::endl;
  isl_set *set, *lm;
  isl_basic_set *bset;
  set = isl_set_read_from_str(ctx, "{[i,j]: 0<=i<=j and 0<=j<=5 }");
  isl_set_dump(set);
  lm = isl_set_lexmin(set);
  isl_multi_val *mv = isl_set_get_plain_multi_val_if_fixed(lm);
  isl_multi_val_dump(mv);
  isl_multi_val_free(mv);
  std::cout << "Size: " << isl_multi_val_size(mv) << std::endl;
  // isl_set_foreach_basic_set(lm, fn, NULL);
  isl_set_free(lm);
}
