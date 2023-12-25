#ifndef _TADASHI_H_
#define _TADASHI_H_

#include <isl/schedule.h>
#include <pet.h>

#if defined(__cplusplus)
extern "C" {
#endif

struct options {
  struct isl *isl;
  struct pet *pet;
  char *source_file_path;
  char *output_file_path;
  char *original_schedule_suffix;
  char *dependencies_suffix;
  char *schedule_source;
  isl_bool legality_check;
};

struct user_t {
  size_t counter;
  struct options *opt;
};

#if defined(__cplusplus)
}
#endif

#endif // _TADASHI_H_
