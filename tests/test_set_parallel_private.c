/// TRANSFORMATION: 0, 1, "SET_PARALLEL_PRIVATE", 0, 2
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   int _tadashi_0, _tadashi_1, _tadashi_2;
///   int lbp, ubp;
///   register int lbv, ubv;
/// #pragma omp parallel for private(lbv,ubv,_tadashi_1,_tadashi_2)
///   for(_tadashi_0 = 0; _tadashi_0 < N; _tadashi_0 += 1)
///     for(_tadashi_1 = 0; _tadashi_1 < N; _tadashi_1 += 1)
///       A[_tadashi_0][_tadashi_1] = 1.0;
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
