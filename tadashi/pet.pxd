include "isl.pxd"
cdef extern from "stdio.h":
    ctypedef struct FILE: pass

cdef extern from "pet.h":
    ctypedef struct pet_scop: pass
    isl_ctx *isl_ctx_alloc_with_pet_options()
    isl_schedule *pet_scop_get_schedule(pet_scop *scop)
    pet_scop *pet_scop_free(pet_scop* scop)
    int pet_transform_C_source(isl_ctx *ctx,
                               const char *input,
                               FILE *output,
                               isl_printer *(*transform)(isl_printer *p,
                                                         pet_scop *scop,
                                                         void *user),
                               void *user)

ctypedef pet_scop* pet_scop_p
