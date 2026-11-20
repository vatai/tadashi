/// TRANSFORMATION: 0, 1, "FULL_SHIFT_BAND", 1
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   int _tadashi_0, _tadashi_1;
///   int lbp, ubp;
///   register int lbv, ubv;
///   #define min(x,y)    ((x) < (y) ? (x) : (y))
///   #define max(x,y)    ((x) > (y) ? (x) : (y))
///   for(_tadashi_0 = 0; _tadashi_0 < 2 * N - 1; _tadashi_0 += 1)
///     for(_tadashi_1 = max(0, -N + _tadashi_0 + 1); _tadashi_1 <= min(_tadashi_0, N - 1); _tadashi_1 += 1)
///       A[_tadashi_0 - _tadashi_1][_tadashi_1] = 1.0;
/// #pragma endscop
/// }
///
/// legality=True
#include <stdlib.h>

void f(size_t N, double A[N][N]) {
#pragma scop
  for (size_t i = 0; i < N; i++)
    for (size_t j = 0; j < N; j++)
      A[i][j] = 1.0;
#pragma endscop
}
