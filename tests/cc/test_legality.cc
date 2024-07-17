/*
 * Emil VATAI, Riken, R-CCS, HPAIS. All rights reserved.
 *
 * Date: 2023-11-24
 */

#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include <isl/aff.h>
#include <isl/constraint.h>
#include <isl/ctx.h>
#include <isl/options.h>
#include <isl/point.h>
#include <isl/schedule_type.h>
#include <isl/set.h>
#include <isl/space_type.h>
#include <isl/union_map_type.h>
#include <isl/val.h>

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

// TEST_F(LegalityTest, DeltaSetLexpos) {
//   std::vector<struct test_data_t> data = {
//       {"{ [ i ] : 10 <= i and i <= 15 }", isl_stat_ok},
//       {"{[i]: i>=0 and (i mod 2)=0 and i<10;"
//        "[i]: -10<i< 0 and (i mod 2)=1}",
//        -1}, //
//       {"{[i]: exists(a: i = 2a) and 0<=i<=15}", isl_stat_error},
//       /*
//         02 12 22 32 42
//         01 11    31 41
//         00          40
//        */
//       {"{[i,j]: 0 <= i <= j and 1 <= j < 3;"
//        "[i,j]: 4-j <= i <= 4 and 0 <= j < 3 }",
//        isl_stat_ok},
//   };
//   isl_set *set;
//   // TODO(vatai): try isl_basic_set_partial_lexmin et al
//   for (auto d : data) {
//     set = isl_set_read_from_str(ctx, d.input.c_str());
//     isl_set_dump(set);
//     isl_stat stat = __delta_set_lexpos(set, NULL);
//     SCOPED_TRACE("Failed set: " + d.input);
//     EXPECT_EQ(stat, d.output);
//   }
// }

TEST_F(LegalityTest, DISABLED_CalculateDelta) {
  isl_schedule_node *node;
  isl_union_map *dep;
  isl_union_set *delta;
  isl_schedule *schedule;

  // schedule = isl_schedule_read_from_str(ctx, "");
  // node = isl_schedule_get_root(schedule);
  // isl_schedule_free(schedule);
  // dep = isl_union_map_read_from_str(ctx, "");
  // delta = calculate_delta(node, dep);
  // isl_schedule_node_free(node);
  // isl_union_map_free(dep);
  // isl_union_set_free(delta);
  EXPECT_TRUE(0); // TODO: implement the above
};
