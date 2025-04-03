#include <cassert>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <sstream>

#include <nlohmann/json.hpp>

#include <isl/aff.h>
#include <isl/ctx.h>
#include <isl/id.h>
#include <isl/map.h>
#include <isl/point.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/set.h>
#include <isl/space.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <isl/val.h>

#include "legality.h"

using json = nlohmann::json;

extern "C" __isl_give isl_schedule *
umap_to_schedule_tree(__isl_take isl_union_set *domain,
                      __isl_take isl_union_map *umap);

__isl_give isl_union_map *get_dependencies_from_json();

struct tadashi_scop *
allocate_tadashi_scop_from_json(isl_ctx *ctx, json &statements) {
  isl_union_map *union_schedule = isl_union_map_empty_ctx(ctx);
  isl_union_set *union_domain = isl_union_set_empty_ctx(ctx);
  std::map<std::string, isl_union_map *> acc_map;
  acc_map["read"] = isl_union_map_empty_ctx(ctx);
  acc_map["write"] = isl_union_map_empty_ctx(ctx);

  for (auto &s : statements) {
    json accesses = s["accesses"];
    for (auto av : accesses) {
      std::string k = av["kind"].template get<std::string>();
      std::string rel = av["relation"].template get<std::string>();
      isl_union_map *acc_rel = isl_union_map_read_from_str(ctx, rel.c_str());
      acc_map[k] = isl_union_map_union(acc_map[k], acc_rel);
    }

    auto name = s["name"];

    isl_union_set *domain = isl_union_set_read_from_str(
        ctx, s["domain"].template get<std::string>().c_str());
    union_domain = isl_union_set_union(union_domain, domain);

    isl_union_map *schedule = isl_union_map_read_from_str(
        ctx, s["schedule"].template get<std::string>().c_str());
    union_schedule = isl_union_map_union(union_schedule, schedule);
  }
  isl_union_map *must_write = acc_map["write"];
  isl_union_map *may_read = acc_map["read"];

  struct tadashi_scop *ts = (struct tadashi_scop *)malloc(sizeof(*ts));
  ts->domain = isl_union_set_copy(union_domain);
  ts->call = NULL;
  ts->may_writes = NULL;
  ts->must_writes = must_write;
  ts->must_kills = NULL;
  ts->may_reads = may_read;
  ts->schedule = umap_to_schedule_tree(union_domain, union_schedule);
  ts->dep_flow;
  ts->live_out = NULL;
  ts->pet_scop = NULL;
  return ts;
}

int
main(int argc, char *argv[]) {
  isl_ctx *ctx = isl_ctx_alloc();

  std::string path("./examples/jscop/"
                   "_QMbiharmonic_wk_scalar_cpuPdivergence_sphere_wk___%."
                   "preheader19---%56.jscop");
  std::ifstream istream(path);
  json data;
  istream >> data;
  // data.keys: arrays,context,name,statements,
  // json stmts = data["statements"];
  struct tadashi_scop *ts =
      allocate_tadashi_scop_from_json(ctx, data["statements"]);
  isl_schedule_node *node = isl_schedule_get_root(ts->schedule);
  isl_schedule_node_dump(node);
  isl_schedule_node_free(node);
  free_tadashi_scop(ts);

  isl_ctx_free(ctx);
  std::printf("Done!\n");
  return 0;
}
