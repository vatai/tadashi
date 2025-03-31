/// TRANSFORMATION: 0, 2, "TILE", 4
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   #define min(x,y)    ((x) < (y) ? (x) : (y))
///   for(int c0 = 1; c0 < N; c0 += 1)
///     for(int c1 = 0; c1 < N; c1 += 4)
///       for(int c2 = 0; c2 <= min(3, N - c1 - 1); c2 += 1)
///         {
///           for(int c3 = 0; c3 < N; c3 += 1)
///             A[c0][c1 + c2] = (A[c0][c1 + c2] + (A[c0 - 1][c1 + c2] * (c3)));
///           for(int c3 = 0; c3 < N; c3 += 1)
///             A[c0][c1 + c2] = ((A[c0][c1 + c2] + A[c0 - 1][c1 + c2]) + (c3));
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
