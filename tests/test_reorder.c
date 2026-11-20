/// TRANSFORMATION: 0, 1, "REORDER", [1, 0]
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N], double B[N]) {
/// #pragma scop
///   int _tadashi_0, _tadashi_1;
///   int lbp, ubp;
///   register int lbv, ubv;
///   {
///     for(_tadashi_1 = 0; _tadashi_1 < N; _tadashi_1 += 1)
///       B[_tadashi_1] = 2.0;
///     for(_tadashi_1 = 0; _tadashi_1 < N; _tadashi_1 += 1)
///       A[_tadashi_1] = 1.0;
///   }
/// #pragma endscop
/// }
///
/// legality=True
#include <stdlib.h>

void f(size_t N, double A[N], double B[N]) {
#pragma scop
  for (size_t i = 0; i < N; i++)
    A[i] = 1.0;
  for (size_t j = 0; j < N; j++)
    B[j] = 2.0;
#pragma endscop
}
