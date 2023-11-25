/*
 * Emil VATAI, Riken, R-CCS, HPAIS. All rights reserved.
 *
 * Date: 2023-11-24
 */

#include <isl/options.h>
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
    isl_options_set_on_error(ctx, ISL_ON_ERROR_ABORT);
  }
  virtual ~LegalityTest() { isl_ctx_free(ctx); }

  isl_ctx *ctx;
};

TEST_F(LegalityTest, PieceLexpos) {
  struct test_data_t {
    std::string input;
    int output;
  };

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
  for (size_t i = 0; i < data.size(); i++) {
    ma = isl_multi_aff_read_from_str(ctx, data[i].input.c_str());
    set = isl_set_read_from_str(ctx, "{ : }");
    isl_stat stat = piece_lexpos(set, ma, &rv);
    assert(stat == isl_stat_ok);
    SCOPED_TRACE("i = " + std::to_string(i));
    EXPECT_EQ(rv, data[i].output);
  }
}

// TEST_F(LegalityTest, DeltaSetLexpos) {}
