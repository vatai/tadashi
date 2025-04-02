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

isl_bool
pw_aff_is_cst(__isl_keep isl_pw_aff *pa, void *_) {
  return isl_pw_aff_is_cst(pa);
}

isl_union_set *
idx_to_domain(isl_union_set *set, void *user) {
  isl_union_map *map = (isl_union_map *)user;
  return isl_union_set_apply(set, isl_union_map_copy(map));
}

isl_stat
add_singleton_to_list(__isl_take isl_point *pnt, void *user) {
  isl_union_set_list **filters = (isl_union_set_list **)user;
  isl_union_set *singleton = isl_union_set_from_point(pnt);
  *filters = isl_union_set_list_add(*filters, singleton);
  return isl_stat_ok;
}

int

filter_cmp(struct isl_union_set *set1, struct isl_union_set *set2, void *_) {
  isl_point *p1 = isl_union_set_sample_point(isl_union_set_copy(set1));
  isl_val *v1 = isl_point_get_coordinate_val(p1, isl_dim_all, 0);
  isl_point *p2 = isl_union_set_sample_point(isl_union_set_copy(set2));
  isl_val *v2 = isl_point_get_coordinate_val(p2, isl_dim_all, 0);
  int result = isl_val_get_num_si(v1) - isl_val_get_num_si(v2);
  isl_point_free(p1);
  isl_point_free(p2);
  isl_val_free(v1);
  isl_val_free(v2);
  return result;
}

__isl_give isl_schedule *
umap_to_schedule_tree(__isl_take isl_union_set *domain,
                      __isl_take isl_union_map *umap) {

  isl_multi_union_pw_aff *mupa;
  isl_schedule *schedule;
  isl_schedule_node *root;
  isl_union_map *map;
  isl_ctx *ctx = isl_union_set_get_ctx(domain);
  schedule = isl_schedule_from_domain(domain);
  mupa = isl_multi_union_pw_aff_from_union_map(umap);
  root = isl_schedule_get_root(schedule);
  root = isl_schedule_node_first_child(root);
  isl_size dim = isl_multi_union_pw_aff_dim(mupa, isl_dim_all);
  for (isl_size pos = dim - 1; pos >= 0; pos--) {
    isl_union_pw_aff *upa = isl_multi_union_pw_aff_get_at(mupa, pos);
    if (isl_union_pw_aff_every_pw_aff(upa, pw_aff_is_cst, NULL)) {
      map = isl_union_map_from_union_pw_aff(upa);
      map = isl_union_map_reverse(map);
      isl_union_set *steps = isl_union_map_domain(isl_union_map_copy(map));
      isl_union_set_list *filters = isl_union_set_list_alloc(ctx, 1);
      isl_union_set_foreach_point(steps, add_singleton_to_list, &filters);
      filters = isl_union_set_list_sort(filters, filter_cmp, map);
      isl_union_set_list_map(filters, idx_to_domain, map);
      root = isl_schedule_node_insert_sequence(root, filters);
      isl_union_set_free(steps);
      isl_union_map_free(map);
    } else {
      isl_multi_union_pw_aff *mupa =
          isl_multi_union_pw_aff_from_union_pw_aff(upa);
      root = isl_schedule_node_insert_partial_schedule(root, mupa);
    }
  }

  isl_multi_union_pw_aff_free(mupa);
  schedule = isl_schedule_free(schedule);
  schedule = isl_schedule_node_get_schedule(root);
  isl_schedule_node_free(root);
  return schedule;
}

__isl_give isl_union_map *
get_dependencies_from_json() {}

struct tadashi_scop *
allocate_tadashi_scop_from_json(isl_ctx *ctx, json &statements) {
  struct tadashi_scop *ts = (struct tadashi_scop *)malloc(sizeof(*ts));
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
  ts->may_reads = acc_map["read"];
  ts->must_writes = acc_map["write"];
  ts->domain = isl_union_set_copy(union_domain);
  ts->schedule = umap_to_schedule_tree(union_domain, union_schedule);
  return ts;
}

void
free_tadashi_scop_from_json(struct tadashi_scop *ts) {
  isl_union_map_free(ts->may_reads);
  isl_union_map_free(ts->must_writes);
  isl_union_set_free(ts->domain);
  isl_schedule_free(ts->schedule);
  free(ts);
}

int
main(int argc, char *argv[]) {
  isl_ctx *ctx = isl_ctx_alloc();

  std::ifstream istream("./examples/jscop/"
                        "_QMbiharmonic_wk_scalar_cpuPdivergence_sphere_wk___%."
                        "preheader19---%56.jscop");
  json data;
  istream >> data;
  // data.keys: arrays,context,name,statements,
  json stmts = data["statements"];
  struct tadashi_scop *ts =
      allocate_tadashi_scop_from_json(ctx, data["statements"]);
  isl_schedule_node *node = isl_schedule_get_root(ts->schedule);
  isl_schedule_node_dump(node);
  isl_schedule_node_free(node);
  free_tadashi_scop_from_json(ts);

  isl_ctx_free(ctx);
  std::printf("Done!\n");
  return 0;
}
