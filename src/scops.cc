#include <algorithm>
#include <climits>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <isl/ctx.h>
#include <sstream>
#include <string>
#include <vector>

#include <isl/union_map.h>
#include <isl/union_set.h>
#include <pet.h>

#include "legality.h"
#include "scops.h"

Scop::Scop(pet_scop *ps)
    : tmp_node(nullptr), modified(false), current_legal(true) {
  scop = allocate_tadashi_scop(ps);
  current_node = isl_schedule_get_root(scop->schedule);
}

Scop::Scop(isl_ctx *ctx, std::string &jscop_path)
    : tmp_node(nullptr), modified(false), current_legal(true),
      jscop_path(jscop_path) {

  std::ifstream istream(jscop_path);
  istream >> jscop;
  isl_union_map *sched = isl_union_map_empty_ctx(ctx);
  isl_union_set *domain = isl_union_set_empty_ctx(ctx);
  std::map<std::string, isl_union_map *> acc_map;
  for (auto &stmt : jscop["statements"]) {
    const char *str;
    std::string name = stmt["name"];
    str = stmt["domain"].get_ref<const std::string &>().c_str();
    domain = isl_union_set_union(domain, isl_union_set_read_from_str(ctx, str));
    str = stmt["schedule"].get_ref<const std::string &>().c_str();
    sched = isl_union_map_union(sched, isl_union_map_read_from_str(ctx, str));
  }
  scop = allocate_tadashi_scop_from_json(domain, sched);
  current_node = isl_schedule_get_root(scop->schedule);
}

Scop::~Scop() {
  isl_schedule_node_free(current_node);
  if (tmp_node != nullptr)
    isl_schedule_node_free(tmp_node);
  free_tadashi_scop(scop);
}

const char *
Scop::add_string(char *str) {
  strings.push_back(str);
  free(str);
  return strings.back().c_str();
};

const char *
Scop::add_string(std::stringstream &ss) {
  strings.push_back(ss.str());
  return strings.back().c_str();
}

void
Scop::rollback() {
  if (!modified)
    return;
  std::swap(current_legal, tmp_legal);
  std::swap(current_node, tmp_node);
}

void
Scop::reset() {
  if (!modified)
    return;
  current_node = isl_schedule_node_free(current_node);
  current_node = isl_schedule_get_root(scop->schedule);
  current_legal = true;
  tmp_node = isl_schedule_node_free(tmp_node);
  tmp_node = nullptr;
  tmp_legal = false;
  modified = false;
}

// Scops

__isl_give isl_printer *
get_scop_callback(__isl_take isl_printer *p, pet_scop *scop, void *user) {
  std::vector<Scop *> *scops = (std::vector<Scop *> *)user;
  scops->push_back(new Scop(scop));
  return p;
}

Scops::Scops(isl_ctx *ctx) : ctx(ctx) {};

Scops::Scops(char *input, const std::vector<std::string> &defines)
    : ctx(isl_ctx_alloc_with_pet_options()) {
  for (const auto &s : defines)
    pet_options_append_defines(ctx, s.c_str());
  // printf("Scops::Scops(ctx=%p)\n", ctx);
  FILE *output = fopen("/dev/null", "w");
  // pet_options_set_autodetect(ctx, 1);
  // pet_options_set_signed_overflow(ctx, 1);
  // pet_options_set_encapsulate_dynamic_control(ctx, 1);
  pet_transform_C_source(ctx, input, output, get_scop_callback, &scops);
  fclose(output);
  // printf("Scops::Scops(ctx=%p)\n", ctx);
};

Scops::~Scops() {
  for (Scop *p : scops)
    delete p;
  scops.clear();
  isl_ctx_free(ctx);
};

int
Scops::num_scops() {
  return scops.size();
}

PollyApp::PollyApp(char *compiler, char *input)
    : Scops(isl_ctx_alloc()), input(input), compiler(compiler) {
  char cmd[LINE_MAX];
  snprintf(
      cmd, LINE_MAX,
      "%s -S -emit-llvm %s -O1 -o - "
      "| opt -load LLVMPolly.so -disable-polly-legality -polly-canonicalize "
      "-polly-export-jscop -o %s.ll 2>&1",
      compiler, input, input);

  std::vector<std::string> json_paths;

  size_t size = 0;
  char *line = NULL;
  FILE *out = popen(cmd, "r");
  while (getline(&line, &size, out) != -1) {
    char *ptr = strstr(line, "command not found");
    if (ptr) {
      std::cout << line << std::endl;
      // TODO throw an exception here!
#warning "TODO"
    }

    ptr = line;
    ptr = strstr(ptr, "' to '");
    if (ptr) {
      ptr += 6;
      *strchr(ptr, '\'') = '\0';
      json_paths.emplace_back(ptr);
    }
  }
  free(line);
  pclose(out);

  for (std::string json_path : json_paths) {
    scops.emplace_back(new Scop(ctx, json_path));
  }
}

int
PollyApp::generate_code(const char *input_path, const char *output_path) {
  for (auto &scop : scops) {
    isl_schedule *sched = isl_schedule_node_get_schedule(scop->current_node);
    isl_union_map *map = isl_schedule_get_map(sched);
    isl_schedule_free(sched);
    printf("[cg] %s map: %s\n", scop->jscop_path.c_str(),
           isl_union_map_to_str(map));

    for (auto &stmt : scop->jscop["statements"]) {
      const char *name = stmt["name"].get_ref<std::string &>().c_str();
      printf("[cg] name: %s\n", name);
      printf("DO THIS HERE\n");
      std::filesystem::copy(scop->jscop_path,
                            scop->jscop_path + std::string(".bak"),
                            std::filesystem::copy_options::overwrite_existing);
      std::ofstream of(scop->jscop_path);
      stmt["schedule"] = isl_union_map_to_str(map);
      of << scop->jscop;
    }
    isl_union_map_free(map);
  }
  char cmd[LINE_MAX];
  snprintf(cmd, LINE_MAX,
           "%s -S -emit-llvm %s -O1 -o - "
           "| opt -load LLVMPolly.so -disable-polly-legality "
           "-polly-canonicalize "
           "-polly-import-jscop -o %s.ll 2>&1",
           compiler.c_str(), input.c_str(), input.c_str());

  printf("[cg] cmd1: %s\n", cmd);
  system(cmd);
  snprintf(cmd, LINE_MAX, "%s %s.ll -O3 -o %s", compiler.c_str(), input.c_str(),
           "OUTPUT.x");
  printf("[cg] cmd2: %s\n", cmd);
  system(cmd);

  // finish compilation
  //
  // [ ] find example with multiple statements in one scop and make
  // sure it works.
  //
  // [ ] "project out" the statement
  return 0;
}
