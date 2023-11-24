#ifndef _LEGALITY_H_
#define _LEGALITY_H_

#include <isl/aff.h>
#include <isl/set.h>

#if defined(__cplusplus)
extern "C" {
#endif

isl_stat piece_lexpos(isl_set *set, isl_multi_aff *ma, void *user);

isl_stat delta_set_lexpos(isl_set *set, void *user);

#if defined(__cplusplus)
}
#endif

#endif // _LEGALITY_H_
