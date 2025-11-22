/**
 * @date 2024, January
 * @author Emil VATAI, Riken R-CCS
 *
 * @mainpage
 * @brief CTadashi is the backend of Tadashi.
 *
 * @section overview Overview
 *
 * The entry-point of CTadashi, that exposes the functionality of
 * CTadashi is ctadashi.cc (and ctadashi.h).
 *
 * @subsection app-creation Creation of a (Python) App object
 *
 * - Python invokes @ref init_scops and creates a @ref Scops object;
 *
 * - Each @ref Scops object stores the @ref Scop "Scop"s of a (Python)
 *   App object (with the corresponding @ref Scops::ctx);
 *
 * -
 */

/**
 * @file ctadashi.h
 * @brief Header for ctadashi.cc.
 *
 * @todo The functions here can be grouped.
 */

#include <cstddef>
#include <vector>

#include "scops.h"
/**
 * @brief Entry point of CTadashi which creates a @ref Scops object
 * (PET backend).
 *
 * @param input Location of the source file.
 *
 * @returns Pointer to the new @ref Scops object.
 */
Scops *init_scops(char *input, const std::vector<std::string> &defines);

/**
 * @brief Entry point of CTadashi which creates a @ref Scops object
 * (LLVM/Polly backend).
 *
 * @param compiler LLVM compiler used (usually clang or flang).
 *
 * @param input Location of the source file.
 *
 * @returns Pointer to the new @ref Scops object.
 */
PollyApp *init_scops_from_json(char *compiler, char *input);

/**
 * @brief Return the number of @ref Scop "Scop"s in the @ref Scops
 * object.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @returns Number of @ref Scop "Scop"s.
 */
size_t num_scops(Scops *app);

/**
 * @brief Free the @ref Scops object.
 *
 * @param app Pointer to the @ref Scops object to be released.
 */
void free_scops(Scops *app);

/**
 * @brief Get the type of the current schedule node.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @returns Type identifier of the node.
 */
int get_type(Scops *app, size_t scop_idx);

/**
 * @brief Get the number of children under the current schedule node.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @returns Child count of the node.
 */
size_t get_num_children(Scops *app, size_t scop_idx);

/**
 * @brief Retrieve the textual representation of the partial schedule
 * of the current schedule node.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @returns Pointer to a read-only C string containing the expression.
 */
const char *get_expr(Scops *app, size_t scop_idx);

/**
 * @brief Obtain the label of the current schedule node.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @returns Pointer to a read-only C string containing the label.
 */
const char *get_label(Scops *app, size_t scop_idx);

/**
 * @brief Retrieve the loop signature string of the current schedule
 * node.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @returns Pointer to a read-only C string containing the loop signature.
 */
const char *get_loop_signature(Scops *app, size_t scop_idx);

/**
 * @brief Print the current schedule node.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @returns Pointer to a read-only C string containing the printed
 * node.
 */
const char *print_schedule_node(Scops *app, size_t scop_idx);

/**
 * @brief Navigate to the root schedule node of the @ref Scop.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 */
void goto_root(Scops *app, size_t scop_idx);

/**
 * @brief Navigate to the parent of the current schedule node.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 */
void goto_parent(Scops *app, size_t scop_idx);

/**
 * @brief Navigate to a specific child schedule node.
 *
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @param child_idx Zero-based index of the child to visit.
 */
void goto_child(Scops *app, size_t scop_idx, size_t child_idx);

/**
 * @brief Get the legality of the current state.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 */
extern "C" int get_legal(Scops *app, size_t scop_idx);

/**
 * @brief Roll back the latest transformation(s).
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 */
void rollback(Scops *app, size_t scop_idx);

/**
 * @brief Reset the SCoP to its pristine state.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 */
void reset_scop(Scops *app, size_t scop_idx);

/**
 * @brief Generate transformed source code.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param input_path Path to the original input file.
 *
 * @param output_path Path for the generated output file.
 *
 * @returns Zero on success, non-zero on error.
 */
int generate_code(Scops *app, const char *input_path, const char *output_path);

/**
 * @brief Apply a 1-D tiling transformation.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @param tile_size Desired tile size.
 *
 * @returns Zero on if the transformation is illegal, non-zero if
 * legal.
 */
int tile1d(Scops *app, size_t scop_idx, size_t tile_size);

/**
 * @brief Apply a 2-D tiling transformation.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @param size1 Tile size of the first dimension.
 *
 * @param size2 Tile size of the second dimension.
 *
 * @returns Zero on if the transformation is illegal, non-zero if
 * legal.
 */
int tile2d(Scops *app, size_t scop_idx, size_t size1, size_t size2);

/**
 * @brief Apply a 3-D tiling transformation.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @param size1 Tile size of the first dimension.
 *
 * @param size2 Tile size of the second dimension.
 *
 * @param size3 Tile size of the third dimension.
 *
 * @returns Zero on if the transformation is illegal, non-zero if
 * legal.
 */
int tile3d(Scops *app, size_t scop_idx, size_t size1, size_t size2,
           size_t size3);

/**
 * @brief Perform loop interchange.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @returns Zero on if the transformation is illegal, non-zero if
 * legal.
 *
 * Interchange swaps the loop (band node to be specific) with the one
 * below it in the schedule tree.
 */
int interchange(Scops *app, size_t scop_idx);

/**
 * @brief Fuse two loops in a sequence.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @param idx1 Zero-based index of the first loop.
 *
 * @param idx2 Zero-based index of the second loop.
 *
 * @returns Zero on if the transformation is illegal, non-zero if
 * legal.
 */
int fuse(Scops *app, size_t scop_idx, int idx1, int idx2);

/**
 * @brief Fully fuse all loops in the sequence.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @returns Zero on if the transformation is illegal, non-zero if
 * legal.
 */
int full_fuse(Scops *app, size_t scop_idx);

/**
 * @brief Split a sequence (in a loop) into two sequences (in two
 * loops).
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @param split Split position.
 *
 * @returns Zero on if the transformation is illegal, non-zero if
 * legal.
 *
 * The \p split parameter is the index of the first child of the
 * sequence that will belong to the second loop, i.e., split
 * <tt>child[0], ..., child[N-1]</tt> into <tt>child[0], ...,
 * child[split-1]</tt> and <tt>child[split], ..., child[N-1]</tt>.
 */
int split(Scops *app, size_t scop_idx, int split);

/**
 * @brief Fully split a sequence (in a loop) into a sequence of loops.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @returns Zero on if the transformation is illegal, non-zero if
 * legal.
 */
int full_split(Scops *app, size_t scop_idx);

/**
 * @brief @todo Apply a partial affine shift involving a variable.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @param pa_idx @todo Partial set index.
 *
 * @param coeff Coefficient for the variable.
 *
 * @param var_idx Index of the variable.
 *
 * @returns Zero on if the transformation is illegal, non-zero if
 * legal.
 */
int partial_shift_var(Scops *app, size_t scop_idx, int pa_idx, long coeff,
                      long var_idx);

/**
 * @brief @todo Apply a partial affine shift with a constant value.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @param pa_idx @todo Partial set index.
 *
 * @param val Constant shift value.
 *
 * @returns Zero on if the transformation is illegal, non-zero if
 * legal.
 */
int partial_shift_val(Scops *app, size_t scop_idx, int pa_idx, long val);

/**
 * @brief @todo Apply a partial affine shift involving a parameter.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @param pa_idx @todo Partial set index.
 *
 * @param coeff Coefficient for the parameter.
 *
 * @param param_idx Index of the parameter.
 *
 * @returns Zero on if the transformation is illegal, non-zero if
 * legal.
 */
int partial_shift_param(Scops *app, size_t scop_idx, int pa_idx, long coeff,
                        long param_idx);

/**
 * @brief @todo Apply a full affine shift involving a variable.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @param coeff Coefficient for the variable.
 *
 * @param var_idx Index of the variable.
 *
 * @returns Zero on if the transformation is illegal, non-zero if
 * legal.
 */
int full_shift_var(Scops *app, size_t scop_idx, long coeff, long var_idx);

/**
 * @brief @todo Apply a global constant affine shift.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @param val Constant shift value.
 *
 * @returns Zero on if the transformation is illegal, non-zero if
 * legal.
 */
int full_shift_val(Scops *app, size_t scop_idx, long val);

/**
 * @brief @todo Apply a full affine shift involving a parameter.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @param coeff Coefficient for the parameter.
 *
 * @param param_idx Index of the parameter.
 *
 * @returns Zero on if the transformation is illegal, non-zero if
 * legal.
 */
int full_shift_param(Scops *app, size_t scop_idx, long coeff, long param_idx);

/**
 * @brief Set code generation option on a specific loop.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @param pos Zero-based position of the loop.
 *
 * @param opt Optimization flag to set.
 *
 * @returns @todo Always return -1 indicating that the legality of the
 * previous state is not changed.
 */
int set_loop_opt(Scops *app, size_t scop_idx, int pos, int opt);

/**
 * @brief Parallelize a loop with OpenMP.
 *
 * @param app Pointer to the @ref Scops object.
 *
 * @param scop_idx Index of the @ref Scop Object in the @ref Scops.
 *
 * @param num_threads @todo Number of threads requested; 0 for default.
 *
 * @returns Zero on if the transformation is illegal, non-zero if
 * legal.
 */
int set_parallel(Scops *app, size_t scop_idx, int num_threads);
