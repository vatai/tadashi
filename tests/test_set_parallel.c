/// TRANSFORMATION: 0, 2, "SET_PARALLEL", 42
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   for(int i = 1; i < N; i += 1)
/// #pragma omp parallel for num_threads(42)
///     for(int j = 0; j < N; j += 1)
///       {
///         for(int k = 0; k < N; k += 1)
///           A[i][j] = (A[i][j] + (A[i - 1][j] * (k)));
///         for(int k = 0; k < N; k += 1)
///           A[i][j] = ((A[i][j] + A[i - 1][j]) + (k));
///         for(int k = 0; k < N; k += 1)
///           A[i][j] = (A[i][j] + (A[i - 1][j] / (k)));
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
