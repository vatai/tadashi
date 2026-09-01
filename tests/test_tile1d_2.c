/// TRANSFORMATION: 0, 2, "TILE_1D", 4
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   #define min(x,y)    ((x) < (y) ? (x) : (y))
///   for(int i = 1; i < N; i += 1)
///     for(int j = 0; j < N; j += 4)
///       for(int j_1 = 0; j_1 <= min(3, N - j - 1); j_1 += 1)
///         {
///           for(int k1 = 0; k1 < N; k1 += 1)
///             A[i][j + j_1] = (A[i][j + j_1] + (A[i - 1][j + j_1] * (k1)));
///           for(int k1 = 0; k1 < N; k1 += 1)
///             A[i][j + j_1] = ((A[i][j + j_1] + A[i - 1][j + j_1]) + (k1));
///         }
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
