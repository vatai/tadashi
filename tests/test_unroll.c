/// TRANSFORMATION: 0, 2, "UNROLL", 4
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
/// #pragma endscop
/// }
///
/// legality=False
#include <stdlib.h>

void f(size_t N, size_t M, double A[N][M]) {
#pragma scop
  for (size_t i = 1; i < N; i++) {
    for (size_t j = 0; j < M; j++) {
        A[i][j] = A[i][j] + A[i - 1][j];
    }
  }
#pragma endscop
}
