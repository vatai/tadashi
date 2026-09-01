/// TRANSFORMATION: 0, 1, "TILE_3D", 13, 17, 25
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   #define min(x,y)    ((x) < (y) ? (x) : (y))
///   #define max(x,y)    ((x) > (y) ? (x) : (y))
///   for(int t = 0; t < N; t += 13)
///     for(int i = 0; i < N; i += 17)
///       for(int j = 0; j < N; j += 25)
///         for(int t_1 = 0; t_1 <= min(12, N - t - 1); t_1 += 1)
///           for(int i_1 = max(0, -i + 1); i_1 <= min(16, N - i - 1); i_1 += 1)
///             for(int j_1 = 0; j_1 <= min(24, N - j - 1); j_1 += 1)
///               {
///                 for(int k1 = 0; k1 < N; k1 += 1)
///                   A[i + i_1][j + j_1] = (A[i + i_1][j + j_1] + (A[i + i_1 - 1][j + j_1] * (k1)));
///                 for(int k1 = 0; k1 < N; k1 += 1)
///                   A[i + i_1][j + j_1] = ((A[i + i_1][j + j_1] + A[i + i_1 - 1][j + j_1]) + (k1));
///               }
/// #pragma endscop
/// }
///
/// legality=False
#include <stdlib.h>

void f(size_t N, double A[N][N]) {
#pragma scop
  for(size_t t = 0; t < N; t++)
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
