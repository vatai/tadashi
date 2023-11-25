/*
 * Emil VATAI, Riken, R-CCS, HPAIS. All rights reserved.
 *
 * Date: 2023-11-24
 */

#include <algorithm>
#include <isl/options.h>
#include <isl/point.h>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include <isl/aff.h>
#include <isl/ctx.h>
#include <isl/set.h>

#include "legality.h"

class LegalityTest : public testing::Test {
protected:
  LegalityTest() : ctx{isl_ctx_alloc()} {
    // isl_options_set_on_error(ctx, ISL_ON_ERROR_ABORT);
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
isl_stat fn(isl_point *p, void *user) {
  // printf("p: %s\n", isl_point_to_str(p));
  isl_point_dump(p);
  return isl_stat_ok;
}

TEST_F(LegalityTest, DeltaSetLexpos) {
  std::vector<struct test_data_t> data = {
      {"{ [ i ] : 10 <= i and i <= 15 }", -1},
      {"{[i]: i>=0 and (i mod 2)=0 and i<10;"
       "[i]: -10<i< 0 and (i mod 2)=1}",
       -1}, //
      {"{[i]: exists(a: i = 2a) and 10<=i<=15}", -1},

  };
  isl_set *set;
  int rv;
  for (auto d : data) {
    set = isl_set_read_from_str(ctx, d.input.c_str());
    isl_set_dump(set);
    isl_stat stat = delta_set_lexpos(set, &rv);
  }
}
