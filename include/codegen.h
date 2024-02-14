#ifndef _CODEGEN_H_
#define _CODEGEN_H_

#include <isl/schedule.h>
#include <pet.h>

#if defined(__cplusplus)
extern "C" {
#endif

__isl_give isl_printer *codegen(isl_ctx *ctx, __isl_take isl_printer *p,
                                struct pet_scop *scop, isl_schedule *schedule);

#if defined(__cplusplus)
}
#endif

#endif // _CODEGEN_H_
