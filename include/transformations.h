#ifndef _TRANSFORMATIONS_H_
#define _TRANSFORMATIONS_H_

#include <isl/schedule.h>
#include <isl/schedule_type.h>
#include <pet.h>

#include "tadashi.h"

#if defined(__cplusplus)
extern "C" {
#endif

__isl_give isl_schedule *interactive_transform(isl_ctx *ctx,
                                               __isl_keep struct pet_scop *scop,
                                               struct user_t *user);

isl_schedule_node *tadashi_tile_1d(isl_schedule_node *node, int si);

#if defined(__cplusplus)
}
#endif

#endif // _TRANSFORMATIONS_H_
