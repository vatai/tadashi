#include <string>
#include <vector>

#include <gtest/gtest.h>

#include <isl/aff.h>
#include <isl/ctx.h>
#include <isl/set.h>

#include "../include/legality.h"

// Demonstrate some basic assertions.
TEST(LegalityTest, PkieceLexpos) {
  struct test_data_t {
    std::string input;
    int output;
  };

  isl_ctx *ctx = isl_ctx_alloc();
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
  size_t nbtests = sizeof(data) / sizeof(data[0]);
  for (size_t i = 0; i < data.size(); i++) {
    isl_multi_aff *ma = isl_multi_aff_read_from_str(ctx, data[i].input.c_str());
    isl_set *set = isl_set_read_from_str(ctx, "{ : }");
    int rv;
    isl_stat stat = piece_lexpos(set, ma, &rv);
    assert(stat == isl_stat_ok);
    SCOPED_TRACE("i = " + std::to_string(i));
    EXPECT_EQ(rv, data[i].output);
  }
}
