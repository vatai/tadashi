/// TRANSFORMATION: 0, 13, "PARTIAL_SHIFT_VAL", 0, 1
/// #include <stdlib.h>
///
/// void f(size_t N, size_t T, double a[N], double b[N]) {
/// #pragma scop
///   double third;
///   #define floord(n,d) (((n)<0) ? -((-(n)+(d)-1)/(d)) : (n)/(d))
///   {
///     third = (1. / 3.);
///     for(int c0 = 0; c0 < T; c0 += 1)
///       {
///         for(int c1 = 2; c1 < N - 18446744073709551616 * floord(N - 1, 18446744073709551616) - 1; c1 += 1)
///           b[c1] = (third * ((a[c1 - 1] + a[c1]) + a[c1 + 1]));
///         for(int c1 = 3; c1 < N - 18446744073709551616 * floord(N - 1, 18446744073709551616); c1 += 1)
///           a[c1 - 1] = b[c1 - 1];
///       }
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
