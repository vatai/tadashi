#ifndef _LEGALITY_H_
#define _LEGALITY_H_

#include <isl/aff.h>
#include <isl/set.h>

#include <pet.h>

#if defined(__cplusplus)
extern "C" {
#endif

__isl_give isl_union_map *get_dependencies(__isl_keep struct pet_scop *scop);

isl_stat piece_lexpos(isl_set *set, isl_multi_aff *ma, void *user);

isl_stat delta_set_lexpos(isl_set *set, void *user);

isl_bool check_schedule_legality(isl_ctx *ctx,
                                 __isl_keep isl_schedule *schedule,
                                 __isl_take isl_union_map *dep);
#if defined(__cplusplus)
}
#endif

#endif // _LEGALITY_H_
