/// TRANSFORMATION: 0, 1, "TILE_2D", 8, 4
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   #define min(x,y)    ((x) < (y) ? (x) : (y))
///   for(int i = 0; i < N; i += 8)
///     for(int j = 0; j < N; j += 4)
///       for(int i_1 = 0; i_1 <= min(7, N - i - 1); i_1 += 1)
///         for(int j_1 = 0; j_1 <= min(3, N - j - 1); j_1 += 1)
///           A[i + i_1][j + j_1] = (A[i + i_1][j + j_1] + 1.0);
/// #pragma endscop
/// }
///
/// legality=True
#include <stdlib.h>

void f(size_t N, double A[N][N]) {
#pragma scop
  for (size_t i = 0; i < N; i++)
    for (size_t j = 0; j < N; j++)
      A[i][j] = A[i][j] + 1.0;
#pragma endscop
}
