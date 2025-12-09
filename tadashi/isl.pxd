# -*- mode:cython -*-

# ---
# ctx
# ---
cdef extern from "isl/ctx.h":
    ctypedef struct isl_ctx: pass
    #
    isl_ctx* isl_ctx_alloc()
    void isl_ctx_free(isl_ctx* ctx)
ctypedef isl_ctx* ctx

# -------
# printer
# -------
cdef extern from "isl/printer.h":
    ctypedef struct isl_printer: pass
    #
    isl_printer *isl_printer_free(isl_printer *p)
ctypedef isl_printer* printer

# --------
# schedule
# --------
cdef extern from "isl/schedule.h":
    ctypedef struct isl_schedule: pass
    #
    isl_schedule *isl_schedule_free(isl_schedule *sched)
    isl_schedule_node *isl_schedule_get_root(isl_schedule *sched)
    const char *isl_schedule_to_str(isl_schedule *sched)
ctypedef isl_schedule* schedule

# ---
# set
# ---
cdef extern from "isl/set.h":
    ctypedef struct isl_set: pass
    #
    isl_set *isl_set_free(isl_set *set)
    int isl_set_dim(isl_set *set, isl_dim_type dim_type)
    const char *isl_set_get_dim_name(isl_set *set, isl_dim_type dim_type, int idx)
    ###
    ctypedef struct isl_set_list: pass
    #
    isl_set_list *isl_set_list_free(isl_set_list* sel_list)
    isl_set *isl_set_list_get_at(isl_set_list *set_list, int idx)
ctypedef isl_set* set

# ---------
# union_set
# ---------
cdef extern from "isl/union_set.h":
    ctypedef struct isl_union_set: pass
    #
    isl_union_set *isl_union_set_free(isl_union_set *uset)
    int isl_union_set_n_set(isl_union_set *uset)
    isl_set_list *isl_union_set_get_set_list(isl_union_set *uset)
ctypedef isl_union_set* union_set

# ---
# aff
# ---
cdef extern from "isl/aff.h":
    ctypedef struct isl_multi_union_pw_aff: pass
    cdef enum isl_dim_type:
            isl_dim_cst
            isl_dim_param
            isl_dim_in
            isl_dim_out
            isl_dim_set = isl_dim_out
            isl_dim_div
            isl_dim_all
    #
    const char *isl_multi_union_pw_aff_to_str(isl_multi_union_pw_aff *mupa)
    isl_multi_union_pw_aff *isl_multi_union_pw_aff_free(isl_multi_union_pw_aff *mupa)
    const char *isl_multi_union_pw_aff_get_tuple_name(isl_multi_union_pw_aff *mupa, isl_dim_type dim_type)
    int isl_multi_union_pw_aff_dim(isl_multi_union_pw_aff *mupa, isl_dim_type dim_type)
    isl_union_set *isl_multi_union_pw_aff_domain(isl_multi_union_pw_aff *mupa)
ctypedef isl_multi_union_pw_aff* multi_union_pw_aff

# -------------
# schedule_node
# -------------
cdef extern from "isl/schedule_node.h":
    ctypedef struct isl_schedule_node: pass
    enum isl_schedule_node_type: pass
    #
    isl_schedule_node *isl_schedule_node_free(isl_schedule_node *node)
    isl_schedule_node *isl_schedule_node_root(isl_schedule_node *node)
    isl_schedule_node *isl_schedule_node_parent(isl_schedule_node *node)
    isl_schedule_node *isl_schedule_node_child(isl_schedule_node *node, int pos)
    isl_schedule_node *isl_schedule_node_first_child(isl_schedule_node *node)
    isl_schedule *isl_schedule_node_get_schedule(isl_schedule_node *node)
    const char *isl_schedule_node_to_str(isl_schedule_node *node)
    int isl_schedule_node_n_children(isl_schedule_node *node)
    isl_schedule_node_type isl_schedule_node_get_type(isl_schedule_node *node)
    isl_multi_union_pw_aff* isl_schedule_node_band_get_partial_schedule(isl_schedule_node *node)
ctypedef isl_schedule_node* schedule_node

