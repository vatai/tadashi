/// TRANSFORMATION: 0, 1, "TILE2D", 13, 25
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   #define min(x,y)    ((x) < (y) ? (x) : (y))
///   #define max(x,y)    ((x) > (y) ? (x) : (y))
///   for(int c0 = 0; c0 < N; c0 += 13)
///     for(int c1 = 0; c1 < N; c1 += 25)
///       for(int c2 = max(0, -c0 + 1); c2 <= min(12, N - c0 - 1); c2 += 1)
///         for(int c3 = 0; c3 <= min(24, N - c1 - 1); c3 += 1)
///           {
///             for(int c4 = 0; c4 < N; c4 += 1)
///               A[c0 + c2][c1 + c3] = (A[c0 + c2][c1 + c3] + (A[c0 + c2 - 1][c1 + c3] * (c4)));
///             for(int c4 = 0; c4 < N; c4 += 1)
///               A[c0 + c2][c1 + c3] = ((A[c0 + c2][c1 + c3] + A[c0 + c2 - 1][c1 + c3]) + (c4));
///           }
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
