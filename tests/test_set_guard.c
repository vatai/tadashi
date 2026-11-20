/// TRANSFORMATION: 0, 1, "SET_GUARD"
/// #include <stdlib.h>
///
/// void f(size_t N, size_t M, double A[N][M]) {
/// #pragma scop
///   int _tadashi_0, _tadashi_1;
///   int lbp, ubp;
///   register int lbv, ubv;
///   if (M >= 1 && N >= 1)
///     for(_tadashi_0 = 0; _tadashi_0 < N; _tadashi_0 += 1)
///       for(_tadashi_1 = 0; _tadashi_1 < M; _tadashi_1 += 1)
///         A[_tadashi_0][_tadashi_1] = 1.0;
/// #pragma endscop
/// }
///
/// legality=True
#include <stdlib.h>

void f(size_t N, size_t M, double A[N][M]) {
#pragma scop
  for (size_t i = 0; i < N; i++)
    for (size_t j = 0; j < M; j++)
      A[i][j] = 1.0;
#pragma endscop
}
