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

__isl_give isl_schedule_node *tadashi_tile(__isl_take isl_schedule_node *node,
                                           int tile_size);

__isl_give isl_schedule_node *
tadashi_interchange(__isl_take isl_schedule_node *node);

__isl_give isl_schedule_node *
tadashi_complete_fuse(__isl_take isl_schedule_node *node);

__isl_give isl_schedule_node *tadashi_fuse(__isl_take isl_schedule_node *node,
                                           int idx1, int idx2);

__isl_give isl_schedule_node *tadashi_scale(__isl_take isl_schedule_node *node,
                                            long scale);

__isl_give isl_schedule_node *
tadashi_partial_shift_var(__isl_take isl_schedule_node *node, int pa_idx,
                          long id_idx);

__isl_give isl_schedule_node *
tadashi_partial_shift_val(__isl_take isl_schedule_node *node, int pa_idx,
                          long id_idx);

__isl_give isl_schedule_node *
tadashi_full_shift_var(__isl_take isl_schedule_node *node, int pa_idx,
                       long id_idx);

__isl_give isl_schedule_node *
tadashi_full_shift_val(__isl_take isl_schedule_node *node, int pa_idx,
                       long id_idx);

#if defined(__cplusplus)
}
#endif

#endif // _TRANSFORMATIONS_H_
