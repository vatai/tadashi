/// TRANSFORMATION: 0, 8, "FULL_FUSE"
/// TRANSFORMATION: 0, 8, "FULL_SHIFT_VAR",  2, 0
/// TRANSFORMATION: 0, 8, "PARTIAL_SHIFT_VAL",  0, 1
/// TRANSFORMATION: 0, 8, "SET_LOOP_OPT",  0, 3
/// #include <stdlib.h>
///
/// void f(int N, int T, double a[N], double b[N]) {
/// #pragma scop
///   double third;
///   {
///     third = (1. / 3.);
///     if (N >= 4)
///       for(int c0 = 0; c0 < T; c0 += 1)
///         {
///           b[2] = (third * ((a[1] + a[2]) + a[3]));
///           for(int c1 = 2 * c0 + 3; c1 < N + 2 * c0 - 1; c1 += 1)
///             {
///               b[-2 * c0 + c1] = (third * ((a[-2 * c0 + c1 - 1] + a[-2 * c0 + c1]) + a[-2 * c0 + c1 + 1]));
///               a[-2 * c0 + c1 - 1] = b[-2 * c0 + c1 - 1];
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
