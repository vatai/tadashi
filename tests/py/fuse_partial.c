/// TRANSFORMATION: 0, 3, "FUSE", 0, 1
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   for (size_t i = 1; i < N; i++) {
///     for (size_t j = 0; j < N; j++) {
///       for (size_t k1 = 0; k1 < N; k1++)
///         A[i][j] = A[i][j] + A[i - 1][j] * k1;
///       for (size_t k2 = 0; k2 < N; k2++)
///         A[i][j] = A[i][j] + A[i - 1][j] + k2;
///       for (size_t k3 = 0; k3 < N; k3++)
///         A[i][j] = A[i][j] + A[i - 1][j] / k3;
///     }
///   }
/// #pragma endscop
/// }
///
#include <stdlib.h>

void f(size_t N, double A[N][N]) {
#pragma scop
  for (size_t i = 1; i < N; i++) {
    for (size_t j = 0; j < N; j++) {
      for (size_t k = 0; k < N; k++)
        A[i][j] = A[i][j] + A[i - 1][j] * k;
      for (size_t k = 0; k < N; k++)
        A[i][j] = A[i][j] + A[i - 1][j] + k;
      for (size_t k = 0; k < N; k++)
        A[i][j] = A[i][j] + A[i - 1][j] / k;
    }
  }
#pragma endscop
}
