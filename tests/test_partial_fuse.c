/// TRANSFORMATION: 0, 3, "FUSE", 0, 1
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   for(int _tadashi_0 = 1; _tadashi_0 < N; _tadashi_0 += 1)
///     for(int _tadashi_1 = 0; _tadashi_1 < N; _tadashi_1 += 1)
///       {
///         for(int _tadashi_2 = 0; _tadashi_2 < N; _tadashi_2 += 1)
///           {
///             A[_tadashi_0][_tadashi_1] = (A[_tadashi_0][_tadashi_1] + (A[_tadashi_0 - 1][_tadashi_1] * (_tadashi_2)));
///             A[_tadashi_0][_tadashi_1] = ((A[_tadashi_0][_tadashi_1] + A[_tadashi_0 - 1][_tadashi_1]) + (_tadashi_2));
///           }
///         for(int _tadashi_2 = 0; _tadashi_2 < N; _tadashi_2 += 1)
///           A[_tadashi_0][_tadashi_1] = (A[_tadashi_0][_tadashi_1] + (A[_tadashi_0 - 1][_tadashi_1] / (_tadashi_2)));
///       }
/// #pragma endscop
/// }
///
/// legality=False
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
