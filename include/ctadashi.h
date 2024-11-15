#include <isl/printer.h>
#include <pet.h>

#ifdef __cplusplus
extern "C" {
#endif

struct scop_info_t {
  pet_scop *scop;
  isl_union_map *dependency;
  isl_schedule_node *current_node;
  isl_schedule_node *tmp_node;
  int modified;
};

int init_scops(char *input);

void free_scops();

int get_type(size_t scop_idx);

size_t get_num_children(size_t scop_idx);

const char *get_expr(size_t idx);

const char *get_loop_signature(size_t scop_idx);

const char *print_schedule_node(size_t scop_idx);

void goto_root(size_t scop_idx);

void goto_parent(size_t scop_idx);

void goto_child(size_t scop_idx, size_t child_idx);

struct scop_info_t *pre_transform(size_t scop_idx);

int post_transform(size_t scop_idx);

int tile(size_t scop_idx, size_t tile_size);

int interchange(size_t scop_idx);

int fuse(size_t scop_idx, int idx1, int idx2);

int full_fuse(size_t scop_idx);

int partial_shift_var(size_t scop_idx, int pa_idx, long coeff, long var_idx);

int partial_shift_val(size_t scop_idx, int pa_idx, long val);

int full_shift_var(size_t scop_idx, long coeff, long var_idx);

int full_shift_val(size_t scop_idx, long val);

int full_shift_param(size_t scop_idx, long coeff, long param_idx);

int partial_shift_param(size_t scop_idx, int pa_idx, long coeff,
                        long param_idx);

int set_loop_opt(size_t scop_idx, int pos, int opt);

void rollback(size_t scop_idx);

int generate_code(const char *input_path, const char *output_path);

#ifdef __cplusplus
}
#endif
