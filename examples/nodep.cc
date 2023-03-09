#include "common.h"

void square(size_t N, double *A) {
#pragma scop
  for (int i = 0; i < N; ++i) {
    A[i] = A[i] * A[i];
  }
#pragma endscop
}

MAIN(square)
