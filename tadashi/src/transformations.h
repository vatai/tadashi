/** @file */
#ifndef TRANSFORMATIONS_H
#define TRANSFORMATIONS_H

#include <isl/schedule.h>
#include <isl/schedule_node.h>

#if defined(__cplusplus)
extern "C" {
#endif

isl_schedule_node *tadashi_tile_1d(isl_schedule_node * node, int tile_size);
isl_schedule_node *tadashi_tile_2d(isl_schedule_node * node, int size1, int size2);
isl_schedule_node *tadashi_tile_3d(isl_schedule_node * node, int size1, int size2, int size3);
isl_schedule_node *tadashi_interchange(isl_schedule_node * node);
isl_schedule_node *tadashi_full_fuse(isl_schedule_node * node);
isl_schedule_node *tadashi_fuse(isl_schedule_node * node, int idx1, int idx2);
isl_schedule_node *tadashi_full_split(isl_schedule_node * node);
isl_schedule_node *tadashi_split(isl_schedule_node * node, int split_idx);
isl_schedule_node *tadashi_scale(isl_schedule_node * node, long scale);
isl_schedule_node *tadashi_full_shift_val(isl_schedule_node * node, long val);
isl_schedule_node *tadashi_partial_shift_val(isl_schedule_node * node, int pa_idx, long val);
isl_schedule_node *tadashi_full_shift_var(isl_schedule_node * node, long var_idx, long coeff);
isl_schedule_node *tadashi_partial_shift_var(isl_schedule_node * node, int pa_idx, long id_idx, long coeff);
isl_schedule_node *tadashi_full_shift_param(isl_schedule_node * node, long param_idx, long coeff);
isl_schedule_node *tadashi_partial_shift_param(isl_schedule_node * node, int pa_idx, long param_idx, long coeff);
isl_schedule_node *tadashi_set_parallel(isl_schedule_node * node, int num_threads);
isl_schedule_node *tadashi_set_loop_opt(isl_schedule_node * node, int pos, int opt);

#if defined(__cplusplus)
}
#endif

#endif // TRANSFORMATIONS_H
