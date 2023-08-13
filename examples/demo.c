#include "common.h"
void demo(size_t N, size_t M, size_t K, double **A, double **B, double **C) {
#pragma scop
  for (int i = 0; i < N; ++i) {
    for(int j = 0; j < M; j++)
        C[i][j] = A[i][j] + B[i][j];
    }
  // for (int i = 0; i < N; ++i) {
  //   for(int j = 0; j < M; j++)
  //       C[i][j] = A[i][j] + B[i][j];
  //   }
#pragma endscop

// #pragma scop

//   for (int i = 0; i < M; i++)
// 		for (int j = 0; j < N; j++) {
// 			C[i][j] = 0;
// 			for (int k = 0; k < K; k++)
// 				C[i][j] += A[i][k] * B[k][j];
// 		}
// #pragma endscop
// for(int i = 0; i < M; i++){
//     C[i] = A[i] + B[i];
// }
// for(int i = 0; i < M; i+=32){
//   for(int i0 = 0; i0+i<M; i0++){
//       C[i+i0] = A[i+i0] + B[i+i0];
//   }
// }
}
