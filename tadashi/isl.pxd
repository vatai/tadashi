# ---
# ctx
# ---
cdef extern from "isl/ctx.h":
    ctypedef struct isl_ctx: pass
    isl_ctx* isl_ctx_alloc()
    void isl_ctx_free(isl_ctx* ctx)

# -------
# printer
# -------
cdef extern from "isl/printer.h":
    ctypedef struct isl_printer: pass
    isl_printer *isl_printer_free(isl_printer *p)
ctypedef isl_printer* p_isl_printer

# --------
# schedule
# --------
cdef extern from "isl/schedule.h":
    ctypedef struct isl_schedule: pass
    const char *isl_schedule_to_str(isl_schedule *sched)
    isl_schedule_node *isl_schedule_get_root(isl_schedule *sched)
    isl_schedule *isl_schedule_free(isl_schedule *sched)
ctypedef isl_schedule* schedule


# -------------
# schedule_node
# -------------
cdef extern from "isl/schedule_node.h":
    ctypedef struct isl_schedule_node: pass
    isl_schedule_node *isl_schedule_node_free(isl_schedule_node *node)
    isl_schedule_node *isl_schedule_node_first_child(isl_schedule_node *node)
    const char *isl_schedule_node_to_str(isl_schedule_node *node)
ctypedef isl_schedule_node* schedule_node
