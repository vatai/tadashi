#include "common.h"
void demo(size_t N, size_t M, size_t K, double *A, double *B, double *C) {
#pragma scop
  for(int i = 1; i < M; i++){
     A[i] = A[i-1] + B[i];
}
#pragma endscop
}