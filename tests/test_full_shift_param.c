/// TRANSFORMATION: 0, 2, "FULL_SHIFT_PARAM", 0, 42
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   for(int i = 1; i < N; i += 1)
///     for(int j = 42 * N; j < 43 * N; j += 1)
///       {
///         for(int k1 = 0; k1 < N; k1 += 1)
///           A[i][-42 * N + j] = (A[i][-42 * N + j] + (A[i - 1][-42 * N + j] * (k1)));
///         for(int k1 = 0; k1 < N; k1 += 1)
///           A[i][-42 * N + j] = ((A[i][-42 * N + j] + A[i - 1][-42 * N + j]) + (k1));
///       }
/// #pragma endscop
/// }
///
/// legality=True
#include <stdlib.h>

void f(size_t N, double A[N][N]) {
#pragma scop
  for (size_t i = 1; i < N; i++) {
    for (size_t j = 0; j < N; j++) {
      for (size_t k1 = 0; k1 < N; k1++)
        A[i][j] = A[i][j] + A[i - 1][j] * k1;
      for (size_t k2 = 0; k2 < N; k2++)
        A[i][j] = A[i][j] + A[i - 1][j] + k2;
    }
  }
#pragma endscop
}
