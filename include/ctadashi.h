#include <isl/printer.h>
#include <pet.h>

#ifdef __cplusplus
extern "C" {
#endif

size_t init_scops(char *input);

size_t num_scops(size_t pool_idx);

void free_scops(size_t pool_idx);

int get_type(size_t pool_idx, size_t scop_idx);

size_t get_num_children(size_t pool_idx, size_t scop_idx);

const char *get_expr(size_t pool_idx, size_t idx);

const char *get_loop_signature(size_t pool_idx, size_t scop_idx);

const char *print_schedule_node(size_t pool_idx, size_t scop_idx);

void goto_root(size_t pool_idx, size_t scop_idx);

void goto_parent(size_t pool_idx, size_t scop_idx);

void goto_child(size_t pool_idx, size_t scop_idx, size_t child_idx);

void rollback(size_t pool_idx, size_t scop_idx);

void reset_scop(size_t pool_idx, size_t scop_idx);

int generate_code(size_t pool_idx, const char *input_path,
                  const char *output_path);

int tile(size_t pool_idx, size_t scop_idx, size_t tile_size);

int interchange(size_t pool_idx, size_t scop_idx);

int fuse(size_t pool_idx, size_t scop_idx, int idx1, int idx2);

int full_fuse(size_t pool_idx, size_t scop_idx);

int split(size_t pool_idx, size_t scop_idx, int split);

int full_split(size_t pool_idx, size_t scop_idx);

int partial_shift_var(size_t pool_idx, size_t scop_idx, int pa_idx, long coeff,
                      long var_idx);

int partial_shift_val(size_t pool_idx, size_t scop_idx, int pa_idx, long val);

int full_shift_var(size_t pool_idx, size_t scop_idx, long coeff, long var_idx);

int full_shift_val(size_t pool_idx, size_t scop_idx, long val);

int full_shift_param(size_t pool_idx, size_t scop_idx, long coeff,
                     long param_idx);

int partial_shift_param(size_t pool_idx, size_t scop_idx, int pa_idx,
                        long coeff, long param_idx);

int set_loop_opt(size_t pool_idx, size_t scop_idx, int pos, int opt);

int set_parallel(size_t pool_idx, size_t scop_idx, int num_threads);

#ifdef __cplusplus
}
#endif
