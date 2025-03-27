#include <cassert>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <isl/aff_type.h>
#include <isl/id_to_ast_expr.h>
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

  std::cout << "MUPA: " << isl_multi_union_pw_aff_to_str(mupa) << std::endl;
  isl_schedule_node *root = isl_schedule_get_root(schedule);
  root = isl_schedule_node_first_child(root);
  isl_size dim = isl_multi_union_pw_aff_dim(mupa, isl_dim_all);
  std::cout << "dim: " << dim << std::endl;
  std::cout << isl_multi_union_pw_aff_to_str(mupa) << std::endl;
  for (isl_size pos = 0; pos < dim; pos++) {
    if (1 < pos)
      continue;
    std::cout << "pos: " << pos << std::endl;

    isl_union_pw_aff *upa = isl_multi_union_pw_aff_get_at(mupa, pos);
    // UPA
    isl_size n_pa = isl_union_pw_aff_n_pw_aff(upa);
    std::cout << "UPA: " << isl_union_pw_aff_to_str(upa) << std::endl;
    // isl_union_pw_aff_foreach_pw_aff(isl_union_pw_aff *upa, isl_stat
    // (*fn)(isl_pw_aff *, void *), void *user)

    isl_pw_aff_list *pa_list = isl_union_pw_aff_get_pw_aff_list(upa);
    // isl_union_set *filter_list = isl_union_set_list_alloc(ctx, n_pa);
    // PA_LIST
    for (isl_size pa_idx = 0; pa_idx < n_pa; pa_idx++) {
      isl_pw_aff *pa = isl_pw_aff_list_get_at(pa_list, pa_idx);
      // PA
      std::cout << "--pa_idx: " << pa_idx << ": ";
      std::cout << isl_pw_aff_to_str(pa) << "; ";
      isl_set *domain_set = isl_pw_aff_domain(pa);
      std::cout << "DOMAIN: " << isl_set_to_str(domain_set) << "; ";
      // isl_union_set *intersection = isl_union_set_list_
      isl_union_set *intersection = isl_union_set_intersect(
          isl_union_set_copy(union_domain), isl_union_set_from_set(domain_set));

      std::cout << "SET:" << isl_union_set_to_str(intersection) << "; ";
      assert(isl_pw_aff_n_piece(pa) == 1);
      assert(isl_pw_aff_isa_aff(pa));
      // if (isl_pw_aff_is_cst(pa)) {
      //   isl_aff *aff = isl_pw_aff_as_aff(pa);
      //   assert(isl_aff_dim(aff, isl_dim_out) == 1);
      //   isl_val *v = isl_aff_get_constant_val(aff);
      //   std::cout << "CONST: " << isl_val_to_str(v) << "; ";
      //   std::cout << isl_id_to_str(isl_pw_aff_get_tuple_id(pa, isl_dim_in))
      //             << "; ";
      // } else {
      //   std::cout << "VAR:"
      //             /* << isl_aff_get_dim_name(isl_pw_aff_as_aff(pa),
      //             isl_dim_out,
      //                1) //*/
      //             << std::endl;
      // }
      std::cout << std::endl;
    }
  }
  //*/
  isl_schedule_node_free(root);
  isl_schedule_free(schedule);
  isl_ctx_free(ctx);
  std::printf("Done!\n");
  return 0;
}
