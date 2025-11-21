cdef extern from "isl/schedule.h":
    ctypedef struct isl_schedule: pass
    isl_schedule *isl_schedule_free(isl_schedule *sched)

cdef extern from "isl/printer.h":
    ctypedef struct isl_printer: pass

cdef extern from "isl/ctx.h":
    ctypedef struct isl_ctx: pass
    isl_ctx* isl_ctx_alloc()
    void isl_ctx_free(isl_ctx* ctx)

cdef extern from "isl/ctx.h":
    const char *isl_schedule_to_str(isl_schedule *sched)
