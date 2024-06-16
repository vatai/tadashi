/// TRANSFORMATION: 0, 2, "PARTIAL_SHIFT_VAR", 0, 0
/// TRANSFORMATION: 0, 2, "PARTIAL_SHIFT_VAR", 0, 0
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   #define max(x,y)    ((x) > (y) ? (x) : (y))
///   for(int c0 = 1; c0 < N; c0 += 1)
///     {
///       for(int c1 = 0; c1 < N; c1 += 1)
///         {
///           if (c1 >= 2 * c0)
///             for(int c2 = 0; c2 < N; c2 += 1)
///               A[c0][-2 * c0 + c1] = (A[c0][-2 * c0 + c1] + (A[c0 - 1][-2 * c0 + c1] * (c2)));
///           for(int c2 = 0; c2 < N; c2 += 1)
///             A[c0][c1] = ((A[c0][c1] + A[c0 - 1][c1]) + (c2));
///         }
///       for(int c1 = max(N, 2 * c0); c1 < N + 2 * c0; c1 += 1)
///         for(int c2 = 0; c2 < N; c2 += 1)
///           A[c0][-2 * c0 + c1] = (A[c0][-2 * c0 + c1] + (A[c0 - 1][-2 * c0 + c1] * (c2)));
///     }
/// #pragma endscop
/// }
///
/// legality=False
/// legality=False
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
