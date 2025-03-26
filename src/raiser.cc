#include <cassert>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <isl/space_type.h>
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

  root = isl_schedule_node_first_child(root);
  isl_multi_union_pw_aff *partial =
      isl_schedule_node_band_get_partial_schedule(root);
  std::cout << isl_multi_union_pw_aff_to_str(partial) << std::endl;
  isl_size dim = isl_multi_union_pw_aff_dim(partial, isl_dim_all);
  std::cout << "dim: " << dim << std::endl;
  for (isl_size pos = 0; pos < dim; pos++) {
    std::cout << "pos: " << pos << std::endl;
    isl_union_pw_aff *upa = isl_multi_union_pw_aff_get_at(partial, pos);
    isl_size n_pa = isl_union_pw_aff_n_pw_aff(upa);
    isl_pw_aff_list *pa_list = isl_union_pw_aff_get_pw_aff_list(upa);

    for (isl_size pa_idx = 0; pa_idx < n_pa; pa_idx++) {
      isl_pw_aff *pa = isl_pw_aff_list_get_at(pa_list, pa_idx);
      std::cout << "--pa_idx: " << pa_idx << ": " << isl_pw_aff_to_str(pa)
                << std::endl;
      assert(isl_pw_aff_n_piece(pa) == 1);
      assert(isl_pw_aff_isa_aff(pa));
      isl_aff *aff = isl_pw_aff_as_aff(pa);
      assert(isl_aff_dim(aff, isl_dim_out) == 1);
      if (isl_aff_is_cst(aff)) {
        std::cout << "CONST: " << isl_val_to_str(isl_aff_get_constant_val(aff))
                  << std::endl;

      } else {
        // std::cout << ">>> > > > >  NOT CONST:"
        //           << isl_pw_aff_is_c
        //           << std::endl;
      }
    }
  }

  isl_schedule_node_free(root);
  isl_schedule_free(schedule);
  isl_ctx_free(ctx);
  std::printf("Done!\n");
  return 0;
}
