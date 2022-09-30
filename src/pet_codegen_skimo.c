#include <isl/arg.h>
#include <isl/id.h>
#include <isl/id_to_id.h>
#include <isl/options.h>
#include <isl/printer.h>

#include <pet.h>

struct options {
	struct isl_options	*isl;
	struct pet_options	*pet;
	char			*input;
};

ISL_ARGS_START(struct options, options_args)
ISL_ARG_CHILD(struct options, isl, "isl", &isl_options_args, "isl options")
ISL_ARG_CHILD(struct options, pet, NULL, &pet_options_args, "pet options")
ISL_ARG_ARG(struct options, input, "input", NULL)
ISL_ARGS_END

ISL_ARG_DEF(options, struct options, options_args)

static __isl_give isl_multi_pw_aff *pullback(__isl_take isl_multi_pw_aff *mpa,
	__isl_keep isl_id *id, void *user)
{
	isl_pw_multi_aff *fn = user;

	fn = isl_pw_multi_aff_copy(fn);
	return isl_multi_pw_aff_pullback_pw_multi_aff(mpa, fn);
}

static void free_isl_id_to_ast_expr(void *user)
{
	isl_id_to_ast_expr *id_to_ast_expr = user;

	isl_id_to_ast_expr_free(id_to_ast_expr);
}

static struct pet_stmt *node_stmt(__isl_keep isl_ast_node *node,
	isl_id_to_id *id2stmt)
{
	isl_ast_expr *expr, *arg;
	isl_id *id;
	struct pet_stmt *stmt;

	expr = isl_ast_node_user_get_expr(node);
	arg = isl_ast_expr_get_op_arg(expr, 0);
	isl_ast_expr_free(expr);
	id = isl_ast_expr_get_id(arg);
	isl_ast_expr_free(arg);

	id = isl_id_to_id_get(id2stmt, id);
	stmt = isl_id_get_user(id);
	isl_id_free(id);

	return stmt;
}

static __isl_give isl_ast_node *at_domain(__isl_take isl_ast_node *node,
	__isl_keep isl_ast_build *build, void *user)
{
	isl_id_to_id *id2stmt = user;
	isl_id *id;
	struct pet_stmt *stmt;
	isl_map *schedule;
	isl_pw_multi_aff *reverse;
	isl_id_to_ast_expr *ref2expr;

	stmt = node_stmt(node, id2stmt);

	schedule = isl_map_from_union_map(isl_ast_build_get_schedule(build));
	reverse = isl_pw_multi_aff_from_map(isl_map_reverse(schedule));
	ref2expr = pet_stmt_build_ast_exprs(stmt, build, &pullback, reverse,
		NULL, NULL);
	isl_pw_multi_aff_free(reverse);

	id = isl_id_alloc(isl_ast_node_get_ctx(node), NULL, ref2expr);
	id = isl_id_set_free_user(id, &free_isl_id_to_ast_expr);
	node = isl_ast_node_set_annotation(node, id);
	return node;
}

static __isl_give isl_printer *print_user(__isl_take isl_printer *p,
	__isl_take isl_ast_print_options *options,
	__isl_keep isl_ast_node *node, void *user)
{
	isl_id_to_id *id2stmt = user;
	struct pet_stmt *stmt;
	isl_id *id;
	isl_id_to_ast_expr *ref2expr;

	stmt = node_stmt(node, id2stmt);

	id = isl_ast_node_get_annotation(node);
	ref2expr = isl_id_get_user(id);
	isl_id_free(id);

	p = isl_ast_node_print_macros(node, p);
	p = pet_stmt_print_body(stmt, p, ref2expr);

	isl_ast_print_options_free(options);

	return p;
}

static __isl_give isl_id_to_id *set_up_id2stmt(struct pet_scop *scop)
{
	int i;
	isl_ctx *ctx;
	isl_id_to_id *id2stmt;

	ctx = isl_set_get_ctx(scop->context);
	id2stmt = isl_id_to_id_alloc(ctx, scop->n_stmt);

	for (i = 0; i < scop->n_stmt; ++i) {
		struct pet_stmt *stmt = scop->stmts[i];
		isl_id *tuple_id, *id;
		const char *name;

		tuple_id = isl_set_get_tuple_id(stmt->domain);
		name = isl_id_get_name(tuple_id);
		id = isl_id_alloc(ctx, name, stmt);
		id2stmt = isl_id_to_id_set(id2stmt, tuple_id, id);
	}

	return id2stmt;
}

static __isl_give isl_printer *transform(__isl_take isl_printer *p,
	struct pet_scop *scop, void *user)
{
	isl_ctx *ctx;
	isl_schedule *schedule;
	isl_ast_build *build;
	isl_ast_node *node;
	isl_ast_print_options *print_options;
	isl_id_to_id *id2stmt;

	ctx = isl_printer_get_ctx(p);
	schedule = isl_schedule_copy(scop->schedule);
	id2stmt = set_up_id2stmt(scop);
	build = isl_ast_build_alloc(ctx);
	build = isl_ast_build_set_at_each_domain(build, &at_domain, id2stmt);
	node = isl_ast_build_node_from_schedule(build, schedule);
	print_options = isl_ast_print_options_alloc(ctx);
	print_options = isl_ast_print_options_set_print_user(print_options,
		&print_user, id2stmt);
	p = isl_ast_node_print(node, p, print_options);
	isl_ast_node_free(node);
	isl_ast_build_free(build);
	isl_id_to_id_free(id2stmt);
	pet_scop_free(scop);
	return p;
}

int main(int argc, char *argv[])
{
	isl_ctx *ctx;
	struct options *options;
	int r;

	options = options_new_with_defaults();
	ctx = isl_ctx_alloc_with_options(&options_args, options);
	pet_options_set_encapsulate_dynamic_control(ctx, 1);
	argc = options_parse(options, argc, argv, ISL_ARG_ALL);

	r = pet_transform_C_source(ctx, options->input, stdout,
		&transform, NULL);

	isl_ctx_free(ctx);
	return r;
}
