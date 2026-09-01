/// TRANSFORMATION: 0, 2, "SCALE", 2
/// TRANSFORMATION: 0, 2, "PARTIAL_SHIFT_VAR", 0, 0, 5
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   #define min(x,y)    ((x) < (y) ? (x) : (y))
///   for(int i = 1; i < N; i += 1)
///     {
///       for(int j = 0; j < min(2 * N - 1, 5 * i); j += 2)
///         for(int k1 = 0; k1 < N; k1 += 1)
///           A[i][j / 2] = ((A[i][j / 2] + A[i - 1][j / 2]) + (k1));
///       for(int j = 5 * i; j < 2 * N + 5 * i - 1; j += 1)
///         {
///           if ((i + j) % 2 == 0)
///             for(int k1 = 0; k1 < N; k1 += 1)
///               A[i][(-5 * i + j) / 2] = (A[i][(-5 * i + j) / 2] + (A[i - 1][(-5 * i + j) / 2] * (k1)));
///           if (2 * N >= j + 2 && j % 2 == 0)
///             for(int k1 = 0; k1 < N; k1 += 1)
///               A[i][j / 2] = ((A[i][j / 2] + A[i - 1][j / 2]) + (k1));
///         }
///     }
/// #pragma endscop
/// }
///
/// legality=True
/// legality=False
#include <stdlib.h>

void f(size_t N, double A[N][N]) {
#pragma scop
  for (size_t i = 1; i < N; i++) {
    for (size_t j = 0; j < N; j++) {
      for (size_t k1 = 0; k1 < N; k1++)
        A[i][j] = A[i][j] + A[i - 1][j] * k1;
      for (size_t k1 = 0; k1 < N; k1++)
        A[i][j] = A[i][j] + A[i - 1][j] + k1;
    }
  }
#pragma endscop
}
