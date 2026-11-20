/// TRANSFORMATION: 0, 1, "SET_VECTOR"
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N]) {
/// #pragma scop
///   int _tadashi_0;
///   int lbp, ubp;
///   register int lbv, ubv;
/// #pragma ivdep
/// #pragma vector always
///   for(_tadashi_0 = 0; _tadashi_0 < N; _tadashi_0 += 1)
///     A[_tadashi_0] = (2 * A[_tadashi_0]);
/// #pragma endscop
/// }
///
/// legality=True
#include <stdlib.h>

void f(size_t N, double A[N]) {
#pragma scop
  for (size_t i = 0; i < N; i++)
    A[i] = 2 * A[i];
#pragma endscop
}
