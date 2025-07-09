#ifndef _LEGALITY_H_
#define _LEGALITY_H_

#include <isl/aff.h>
#include <isl/set.h>

#include <pet.h>

#if defined(__cplusplus)
extern "C" {
#endif

struct tadashi_scop {
  isl_union_set *domain;
  isl_union_set *call;
  isl_union_map *may_writes;
  isl_union_map *must_writes;
  isl_union_map *must_kills;
  isl_union_map *may_reads;
  isl_schedule *schedule;
  isl_union_map *dep_flow;
  isl_union_map *live_out;
  pet_scop *pet_scop;
};

__isl_give isl_union_map *get_dependencies(__isl_keep struct pet_scop *scop);

struct tadashi_scop *allocate_tadashi_scop(struct pet_scop *ps);

struct tadashi_scop *allocate_tadashi_scop_from_json(isl_union_set *domain,
                                                     isl_union_map *schedule,
                                                     isl_union_map *must_writes,
                                                     isl_union_map *may_reads);

void free_tadashi_scop(struct tadashi_scop *ts);

isl_bool tadashi_check_legality(__isl_keep isl_schedule *schedule,
                                __isl_take isl_union_map *dep);

isl_bool tadashi_check_legality_parallel(isl_ctx *ctx,
                                         __isl_keep isl_schedule_node *node,
                                         __isl_take isl_union_map *dep);
#if defined(__cplusplus)
}
#endif

#endif // _LEGALITY_H_
