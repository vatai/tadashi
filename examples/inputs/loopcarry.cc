#include "common.h"

void loopcarry(size_t N, double *A) {
#pragma scop
  for (int i = 1; i < N; ++i) {
    A[i] += A[i-1];
  }
#pragma endscop
}

MAIN(loopcarry)
