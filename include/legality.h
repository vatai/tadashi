#ifndef _LEGALITY_H_
#define _LEGALITY_H_

#include <isl/aff.h>
#include <isl/set.h>

#include <pet.h>

#if defined(__cplusplus)
extern "C" {
#endif

struct tadashi_scop {
  pet_scop *scop;
  isl_union_map *dependency;
};

__isl_give isl_union_map *get_dependencies(__isl_keep struct pet_scop *scop);

void populate_tadashi_scop(struct tadashi_scop *ts, struct pet_scop *ps);

isl_bool tadashi_check_legality(isl_ctx *ctx, __isl_keep isl_schedule *schedule,
                                __isl_take isl_union_map *dep);

isl_bool tadashi_check_legality_parallel(isl_ctx *ctx,
                                         __isl_keep isl_schedule_node *node,
                                         __isl_take isl_union_map *dep);
#if defined(__cplusplus)
}
#endif

#endif // _LEGALITY_H_
