/// TRANSFORMATION: 0, 2, "TILE1D", 4
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   #define min(x,y)    ((x) < (y) ? (x) : (y))
///   for(int _tadashi_0 = 1; _tadashi_0 < N; _tadashi_0 += 1)
///     for(int _tadashi_1 = 0; _tadashi_1 < N; _tadashi_1 += 4)
///       for(int _tadashi_2 = 0; _tadashi_2 <= min(3, N - _tadashi_1 - 1); _tadashi_2 += 1)
///         {
///           for(int _tadashi_3 = 0; _tadashi_3 < N; _tadashi_3 += 1)
///             A[_tadashi_0][_tadashi_1 + _tadashi_2] = (A[_tadashi_0][_tadashi_1 + _tadashi_2] + (A[_tadashi_0 - 1][_tadashi_1 + _tadashi_2] * (_tadashi_3)));
///           for(int _tadashi_3 = 0; _tadashi_3 < N; _tadashi_3 += 1)
///             A[_tadashi_0][_tadashi_1 + _tadashi_2] = ((A[_tadashi_0][_tadashi_1 + _tadashi_2] + A[_tadashi_0 - 1][_tadashi_1 + _tadashi_2]) + (_tadashi_3));
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
