#include "common.h"
void GEMM(size_t N, size_t M, size_t K, double **A, double **B, double **C) {
#pragma scop

  for (int i = 0; i < M; i++)
		for (int j = 0; j < N; j++) {
			C[i][j] = 0;
			for (int k = 0; k < K; k++)
				C[i][j] += A[i][k] * B[k][j];
		}
#pragma endscop
}
