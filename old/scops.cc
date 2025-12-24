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
