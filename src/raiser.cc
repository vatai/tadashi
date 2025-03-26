#include <cstdio>
#include <fstream>
#include <iostream>
#include <isl/aff.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <sstream>

#include <nlohmann/json.hpp>

#include <isl/ctx.h>
#include <isl/map.h>
#include <isl/schedule.h>
#include <isl/union_map.h>
#include <isl/union_set.h>

using json = nlohmann::json;
int
main(int argc, char *argv[]) {
  isl_ctx *ctx = isl_ctx_alloc();

  std::ifstream istream("./examples/jscop/"
                        "_QMbiharmonic_wk_scalar_cpuPdivergence_sphere_wk___%."
                        "preheader19---%56.jscop");
  json data;
  istream >> data;
  // data.keys: arrays,context,name,statements,
  auto stmts = data["statements"];
  isl_union_map *union_schedule = isl_union_map_empty_ctx(ctx);
  isl_union_set *union_domain = isl_union_set_empty_ctx(ctx);
  for (auto &stmt : stmts) {
    auto accesses = stmt["accesses"];
    auto name = stmt["name"];

    isl_union_set *domain = isl_union_set_read_from_str(
        ctx, stmt["domain"].template get<std::string>().c_str());
    union_domain = isl_union_set_union(union_domain, domain);

    isl_union_map *schedule = isl_union_map_read_from_str(
        ctx, stmt["schedule"].template get<std::string>().c_str());
    std::cout << "Isl schedule: " << isl_union_map_to_str(schedule)
              << std::endl;
    union_schedule = isl_union_map_union(union_schedule, schedule);
  }
  std::cout << "Union Theta: " << isl_union_map_to_str(union_schedule)
            << std::endl;
  isl_schedule *schedule = isl_schedule_from_domain(union_domain);
  schedule = isl_schedule_insert_partial_schedule(
      schedule, isl_multi_union_pw_aff_from_union_map(union_schedule));
  std::cout << isl_schedule_to_str(schedule) << std::endl;
  isl_schedule_node *root = isl_schedule_get_root(schedule);
  std::cout << isl_schedule_node_to_str(root) << std::endl;

  isl_schedule_node_free(root);
  isl_schedule_free(schedule);
  isl_ctx_free(ctx);
  std::printf("Done!\n");
  return 0;
}
