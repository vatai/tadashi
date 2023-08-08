#include "common.h"
void demo(size_t N, size_t M, double *A, double *B, double *C) {
#pragma scop
//   for (int i = 0; i < N/4; ++i) {
//     for (int i0 = 0; i0 < 4; ++i) {
//     for(int j = 0; j < M; j++)
//         C[i][j] = A[i][j] + B[i][j];
//     }
// }
for(int i = 0; i < M; i++){
    C[i] = A[i] + B[i];
}
// for(int i = 0; i < M; i+=32){
//   for(int i0 = 0; i0+i<M; i0++){
//       C[i+i0] = A[i+i0] + B[i+i0];
//   }
// }
#pragma endscop

}