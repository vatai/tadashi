/// TRANSFORMATION: 0, 2, "SCALE", 2
/// TRANSFORMATION: 0, 2, "PARTIAL_SHIFT_VAR", 0, 0, 5
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   #define min(x,y)    ((x) < (y) ? (x) : (y))
///   for(int _tadashi_0 = 1; _tadashi_0 < N; _tadashi_0 += 1)
///     {
///       for(int _tadashi_1 = 0; _tadashi_1 < min(2 * N - 1, 5 * _tadashi_0); _tadashi_1 += 2)
///         for(int _tadashi_2 = 0; _tadashi_2 < N; _tadashi_2 += 1)
///           A[_tadashi_0][_tadashi_1 / 2] = ((A[_tadashi_0][_tadashi_1 / 2] + A[_tadashi_0 - 1][_tadashi_1 / 2]) + (_tadashi_2));
///       for(int _tadashi_1 = 5 * _tadashi_0; _tadashi_1 < 2 * N + 5 * _tadashi_0 - 1; _tadashi_1 += 1)
///         {
///           if ((_tadashi_0 + _tadashi_1) % 2 == 0)
///             for(int _tadashi_2 = 0; _tadashi_2 < N; _tadashi_2 += 1)
///               A[_tadashi_0][(-5 * _tadashi_0 + _tadashi_1) / 2] = (A[_tadashi_0][(-5 * _tadashi_0 + _tadashi_1) / 2] + (A[_tadashi_0 - 1][(-5 * _tadashi_0 + _tadashi_1) / 2] * (_tadashi_2)));
///           if (2 * N >= _tadashi_1 + 2 && _tadashi_1 % 2 == 0)
///             for(int _tadashi_2 = 0; _tadashi_2 < N; _tadashi_2 += 1)
///               A[_tadashi_0][_tadashi_1 / 2] = ((A[_tadashi_0][_tadashi_1 / 2] + A[_tadashi_0 - 1][_tadashi_1 / 2]) + (_tadashi_2));
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
