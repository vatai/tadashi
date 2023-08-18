#include "common.h"
const int N = 10;

void f(int N, double** A,double** B, double** C) {
#pragma scop
  for (int i = 0; i < N; i++) {
    for (int j = 0; j < N; j++) {
      A[i][j] = B[i][j] + C[i][j];
    }
  }
#pragma endscop
}


