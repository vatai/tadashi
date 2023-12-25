#include <isl/schedule.h>
#include <pet.h>
#include <transformations.h>

__isl_give isl_schedule *interactive_transform(isl_ctx *ctx,
                                               __isl_keep struct pet_scop *scop,
                                               struct user_t *user) {

  return pet_scop_get_schedule(scop);
}
