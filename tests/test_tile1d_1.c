/// TRANSFORMATION: 0, 1, "TILE_1D", 4
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   #define min(x,y)    ((x) < (y) ? (x) : (y))
///   #define max(x,y)    ((x) > (y) ? (x) : (y))
///   for(int i = 0; i < N; i += 4)
///     for(int i_1 = max(0, -i + 1); i_1 <= min(3, N - i - 1); i_1 += 1)
///       for(int j = 0; j < N; j += 1)
///         {
///           for(int k1 = 0; k1 < N; k1 += 1)
///             A[i + i_1][j] = (A[i + i_1][j] + (A[i + i_1 - 1][j] * (k1)));
///           for(int k1 = 0; k1 < N; k1 += 1)
///             A[i + i_1][j] = ((A[i + i_1][j] + A[i + i_1 - 1][j]) + (k1));
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
