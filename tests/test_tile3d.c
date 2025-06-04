/// TRANSFORMATION: 0, 1, "TILE3D", 13, 17, 25
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   #define min(x,y)    ((x) < (y) ? (x) : (y))
///   #define max(x,y)    ((x) > (y) ? (x) : (y))
///   for(int c0 = 0; c0 < N; c0 += 13)
///     for(int c1 = 0; c1 < N; c1 += 17)
///       for(int c2 = 0; c2 < N; c2 += 25)
///         for(int c3 = 0; c3 <= min(12, N - c0 - 1); c3 += 1)
///           for(int c4 = max(0, -c1 + 1); c4 <= min(16, N - c1 - 1); c4 += 1)
///             for(int c5 = 0; c5 <= min(24, N - c2 - 1); c5 += 1)
///               {
///                 for(int c6 = 0; c6 < N; c6 += 1)
///                   A[c1 + c4][c2 + c5] = (A[c1 + c4][c2 + c5] + (A[c1 + c4 - 1][c2 + c5] * (c6)));
///                 for(int c6 = 0; c6 < N; c6 += 1)
///                   A[c1 + c4][c2 + c5] = ((A[c1 + c4][c2 + c5] + A[c1 + c4 - 1][c2 + c5]) + (c6));
///               }
/// #pragma endscop
/// }
///
/// legality=True
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
