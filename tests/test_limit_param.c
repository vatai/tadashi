/// TRANSFORMATION: 0, 1, "LIMIT_PARAM", 0, 100
/// #include <stdlib.h>
///
/// void f(int n, double A[50][100]) {
/// #pragma scop
///   int _tadashi_0;
///   int lbp, ubp;
///   register int lbv, ubv;
///   for(_tadashi_0 = 0; _tadashi_0 < n; _tadashi_0 += 1)
///     A[0][_tadashi_0] = (_tadashi_0);
/// #pragma endscop
/// }
///
/// legality=True
#include <stdlib.h>

void f(int n, double A[50][100]) {
#pragma scop
  for (int i = 0; i < n; i++)
    A[0][i] = i;
#pragma endscop
}
