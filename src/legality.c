#include <assert.h>
#include <stdio.h>

#include <isl/aff.h>
#include <isl/ctx.h>
#include <isl/set.h>
#include <isl/val.h>

isl_stat piece_lexpos(__isl_take isl_set *set, __isl_take isl_multi_aff *ma,
                      void *user) {
  isl_size dim = isl_multi_aff_dim(ma, isl_dim_set);
  int *retval = user;
  *retval = 0;
  for (isl_size pos = 0; pos < dim; pos++) {
    isl_aff *aff = isl_multi_aff_get_at(ma, pos);
    // check if aff has always dim == 1
    assert(isl_aff_is_cst(aff));

    isl_val *cst = isl_aff_get_constant_val(aff);
    isl_bool is_zero = isl_val_is_zero(cst);
    isl_bool is_pos = isl_val_is_pos(cst);
    isl_val_free(cst);
    if (is_zero) {
      isl_aff_free(aff);
      continue;
    }

    isl_val *denom = isl_aff_get_denominator_val(aff);
    isl_bool denom_pos = isl_val_is_pos(denom);
    isl_val_free(denom);

    if (is_pos && denom_pos)
      *retval = +1;
    else
      *retval = -1;

    isl_aff_free(aff);
    break;
  }
  isl_set_free(set);
  isl_multi_aff_free(ma);
  return isl_stat_ok;
}

isl_stat delta_set_lexpos(__isl_take isl_set *set, void *user) {
  int *retval = user;
  *retval = -1;
  isl_pw_multi_aff *pma;
  pma = isl_set_lexmin_pw_multi_aff(set);
  printf("PMA: %s\n", isl_pw_multi_aff_to_str(pma));
  fflush(stdout);
  // TODO(vatai): check for an "exists" instead of "forall" sets in
  // union_set
  int rv;
  isl_stat stat = isl_pw_multi_aff_foreach_piece(pma, piece_lexpos, &rv);
  isl_pw_multi_aff_free(pma);
  return stat;
}
