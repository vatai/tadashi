#include <cassert>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <isl/aff_type.h>
#include <isl/id_to_ast_expr.h>
#include <isl/point.h>
#include <isl/space_type.h>
#include <isl/union_map_type.h>
#include <sstream>

#include <nlohmann/json.hpp>

#include <isl/aff.h>
#include <isl/ctx.h>
#include <isl/id.h>
#include <isl/map.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/set.h>
#include <isl/space.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <isl/val.h>

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
    union_schedule = isl_union_map_union(union_schedule, schedule);
  }

  // ==========

  isl_schedule *schedule = isl_schedule_from_domain(union_domain);
  isl_multi_union_pw_aff *mupa =
      isl_multi_union_pw_aff_from_union_map(union_schedule);
  // MUPA
  // std::cout << "MUPA: " << isl_multi_union_pw_aff_to_str(mupa) << std::endl;
  isl_schedule_node *root = isl_schedule_get_root(schedule);
  root = isl_schedule_node_first_child(root);
  isl_size dim = isl_multi_union_pw_aff_dim(mupa, isl_dim_all);
  // std::cout << "dim: " << dim << std::endl;
  for (isl_size pos = 0; pos < dim; pos++) {
    if (100 < pos)
      continue;
    std::cout << "\npos: " << pos << std::endl;

    isl_union_pw_aff *upa = isl_multi_union_pw_aff_get_at(mupa, pos);
    // // UPA
    // isl_size n_pa = isl_union_pw_aff_n_pw_aff(upa);
    // std::cout << "UPA: " << isl_union_pw_aff_to_str(upa) << std::endl;
    // // isl_union_pw_aff_foreach_pw_aff(isl_union_pw_aff *upa, isl_stat
    // // (*fn)(isl_pw_aff *, void *), void *user)

    if (isl_union_pw_aff_every_pw_aff(upa, pw_aff_is_cst, NULL)) {
      isl_union_map *map = isl_union_map_from_union_pw_aff(upa);
      map = isl_union_map_reverse(map);
      // std::cout << "MAP: " << isl_union_map_to_str(map) << std::endl;
      isl_union_set *steps = isl_union_map_domain(isl_union_map_copy(map));
      // std::cout << "STEPS: " << isl_union_set_to_str(steps) << std::endl;
      isl_union_set_list *filters = isl_union_set_list_alloc(ctx, 1);
      isl_union_set_foreach_point(steps, add_singleton_to_list, &filters);
      filters = isl_union_set_list_sort(filters, filter_cmp, map);
      std::cout << "FILTERS: " << isl_union_set_list_to_str(filters)
                << std::endl;

      isl_union_set_list_map(filters, idx_to_domain, map);
      std::cout << "FILTERS: " << isl_union_set_list_to_str(filters)
                << std::endl;
      isl_union_set_list_free(filters);
      isl_union_set_free(steps);
      isl_union_map_free(map);
    } else {
      isl_union_pw_aff_free(upa);
    }
    // root = isl_schedule_node_insert_sequence(root,
    // filter_results.filters);

    // isl_union_set_list *filters = isl_union_set_to_list(steps);
    // filters = isl_union_set_list_map(filters, fn, isl_union_map_copy(map));
    // std::cout << "MAPPED: " << isl_union_set_list_to_str(filters) <<
    // std::endl;

    // isl_pw_aff_list *pa_list = isl_union_pw_aff_get_pw_aff_list(upa);
    // // isl_union_set *filter_list = isl_union_set_list_alloc(ctx, n_pa);
    // // PA_LIST
    // for (isl_size pa_idx = 0; pa_idx < n_pa; pa_idx++) {
    //   isl_pw_aff *pa = isl_pw_aff_list_get_at(pa_list, pa_idx);
    //   // PA
    //   std::cout << "--pa_idx: " << pa_idx << ": ";
    //   std::cout << isl_pw_aff_to_str(pa) << "; ";
    //   isl_set *domain_set = isl_pw_aff_domain(pa);

    //   std::cout << "DOMAIN: " << isl_set_to_str(domain_set) << "; ";
    //   // isl_union_set *intersection = isl_union_set_list_
    //   isl_union_set *intersection = isl_union_set_intersect(
    //       isl_union_set_copy(union_domain),
    //       isl_union_set_from_set(domain_set));

    //   std::cout << "SET:" << isl_union_set_to_str(intersection) << "; ";
    //   assert(isl_pw_aff_n_piece(pa) == 1);
    //   assert(isl_pw_aff_isa_aff(pa));
    //   // if (isl_pw_aff_is_cst(pa)) {
    //   //   isl_aff *aff = isl_pw_aff_as_aff(pa);
    //   //   assert(isl_aff_dim(aff, isl_dim_out) == 1);
    //   //   isl_val *v = isl_aff_get_constant_val(aff);
    //   //   std::cout << "CONST: " << isl_val_to_str(v) << "; ";
    //   //   std::cout << isl_id_to_str(isl_pw_aff_get_tuple_id(pa,
    //   isl_dim_in))
    //   //             << "; ";
    //   // } else {
    //   //   std::cout << "VAR:"
    //   //             /* << isl_aff_get_dim_name(isl_pw_aff_as_aff(pa),
    //   //             isl_dim_out,
    //   //                1) //*/
    //   //             << std::endl;
    //   // }
    //   std::cout << std::endl;
    // }
  }
  //*/
  isl_multi_union_pw_aff_free(mupa);
  isl_schedule_node_free(root);
  isl_schedule_free(schedule);
  isl_ctx_free(ctx);
  std::printf("Done!\n");
  return 0;
}
