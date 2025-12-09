#ifndef _TRANSFORMATIONS_H_
#define _TRANSFORMATIONS_H_

#include <isl/schedule.h>
#include <pet.h>

#if defined(__cplusplus)
extern "C" {
#endif

__isl_give isl_schedule_node *tadashi_tile_1d(isl_schedule_node *node,
                                              int tile_size);

__isl_give isl_schedule_node *tadashi_tile_2d(isl_schedule_node *node,
                                              int size1, int size2);

__isl_give isl_schedule_node *tadashi_tile_3d(isl_schedule_node *node,
                                              int size1, int size2, int size3);

__isl_give isl_schedule_node *
tadashi_interchange(__isl_take isl_schedule_node *node);

__isl_give isl_schedule_node *tadashi_fuse(__isl_take isl_schedule_node *node,
                                           int idx1, int idx2);

__isl_give isl_schedule_node *
tadashi_full_fuse(__isl_take isl_schedule_node *node);

__isl_give isl_schedule_node *tadashi_split(__isl_take isl_schedule_node *node,
                                            int idx);

__isl_give isl_schedule_node *
tadashi_full_split(__isl_take isl_schedule_node *node);

__isl_give isl_schedule_node *tadashi_scale(__isl_take isl_schedule_node *node,
                                            long scale);

__isl_give isl_schedule_node *
tadashi_full_shift_val(__isl_take isl_schedule_node *node, long val);

__isl_give isl_schedule_node *
tadashi_partial_shift_val(__isl_take isl_schedule_node *node, int pa_idx,
                          long val);

__isl_give isl_schedule_node *
tadashi_full_shift_var(__isl_take isl_schedule_node *node, long var_idx,
                       long coeff);

__isl_give isl_schedule_node *
tadashi_partial_shift_var(__isl_take isl_schedule_node *node, int pa_idx,
                          long id_idx, long coeff);

__isl_give isl_schedule_node *
tadashi_full_shift_param(__isl_take isl_schedule_node *node, long param_idx,
                         long coeff);

__isl_give isl_schedule_node *
tadashi_partial_shift_param(__isl_take isl_schedule_node *node, int pa_idx,
                            long param_idx, long coeff);

__isl_give isl_schedule_node *
tadashi_set_parallel(__isl_take isl_schedule_node *node, int num_threads);

#if defined(__cplusplus)
}
#endif

#endif // _TRANSFORMATIONS_H_
