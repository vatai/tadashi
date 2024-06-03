/// TRANSFORMATION: 0, 13, "PARTIAL_SHIFT_VAL", 0, 1
/// #include <stdlib.h>
///
/// void f(size_t N, size_t T, double a[N], double b[N]) {
/// #pragma scop
///   const double third = 1. / 3.;
///   for (size_t t = 0; t < T; t++) {
///     for (size_t i = 2; i < N - 1; i++)
///       b[i] = third * (a[i - 1] + a[i] + a[i + 1]);
///     for (size_t j = 2; j < N - 1; j++)
///       a[j] = b[j];
///   }
/// #pragma endscop
/// }
///
#include <stdlib.h>

void f(size_t N, size_t T, double a[N], double b[N]) {
#pragma scop
  const double third = 1. / 3.;
  for (size_t t = 0; t < T; t++) {
    for (size_t i = 2; i < N - 1; i++)
      b[i] = third * (a[i - 1] + a[i] + a[i + 1]);
    for (size_t j = 2; j < N - 1; j++)
      a[j] = b[j];
  }
#pragma endscop
}
