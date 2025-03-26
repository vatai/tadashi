#include <cstdio>
#include <fstream>
#include <iostream>
#include <isl/union_map_type.h>
#include <nlohmann/json.hpp>

#include <isl/ctx.h>
#include <isl/map.h>
#include <isl/schedule.h>
#include <isl/union_map.h>
#include <sstream>

using json = nlohmann::json;
int
main(int argc, char *argv[]) {
  isl_ctx *ctx = isl_ctx_alloc();

  std::ifstream istream("./examples/jscop/"
                        "_QMbiharmonic_wk_scalar_cpuPdivergence_sphere_wk___%."
                        "preheader19---%56.jscop");
  json data;
  istream >> data;
  auto stmts = data["statements"];
  for (auto stmt : stmts.items()) {
    auto name = stmt.value()["name"];
    auto schedule = stmt.value()["schedule"];
    std::stringstream ss;
    ss << schedule.template get<std::string>();
    isl_union_map *theta = isl_union_map_read_from_str(
        ctx, schedule.template get<std::string>().c_str());
    std::cout << "Isl schedule: " << isl_union_map_to_str(theta) << std::endl;
  }
  std::printf("Done!\n");
  return 0;
}
