/// TRANSFORMATION: 0, 6, "FULL_FUSE"
/// TRANSFORMATION: 0, 6, "FULL_SHIFT_VAR", 0, 2
/// TRANSFORMATION: 0, 6, "PARTIAL_SHIFT_VAL", 0, 1
/// TRANSFORMATION: 0, 6, "SET_LOOP_OPT", 0, 3
/// #include <stdlib.h>
///
/// void f(int N, int T, double a[N], double b[N]) {
/// #pragma scop
///   double third;
///   {
///     third = (1. / 3.);
///     if (N >= 4)
///       for(int _tadashi_0 = 0; _tadashi_0 < T; _tadashi_0 += 1)
///         {
///           b[2] = (third * ((a[1] + a[2]) + a[3]));
///           for(int _tadashi_1 = 2 * _tadashi_0 + 3; _tadashi_1 < N + 2 * _tadashi_0 - 1; _tadashi_1 += 1)
///             {
///               b[-2 * _tadashi_0 + _tadashi_1] = (third * ((a[-2 * _tadashi_0 + _tadashi_1 - 1] + a[-2 * _tadashi_0 + _tadashi_1]) + a[-2 * _tadashi_0 + _tadashi_1 + 1]));
///               a[-2 * _tadashi_0 + _tadashi_1 - 1] = b[-2 * _tadashi_0 + _tadashi_1 - 1];
///             }
///           a[N - 2] = b[N - 2];
///         }
///   }
/// #pragma endscop
/// }
///
/// legality=True
/// legality=True
/// legality=True
/// legality=True
#include <stdlib.h>

void f(int N, int T, double a[N], double b[N]) {
#pragma scop
  const double third = 1. / 3.;
  for (int t = 0; t < T; t++) {
    for (int i = 2; i < N - 1; i++)
      b[i] = third * (a[i - 1] + a[i] + a[i + 1]);
    for (int j = 2; j < N - 1; j++)
      a[j] = b[j];
  }
#pragma endscop
}
