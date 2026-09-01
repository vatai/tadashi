/// TRANSFORMATION: 0, 1, "FULL_FUSE"
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N], double B[N]) {
/// #pragma scop
///   for(int p = 0; p < N; p += 1)
///     {
///       A[p] = (A[p] + 1.0);
///       B[p] = (B[p] * 2.0);
///     }
/// #pragma endscop
/// }
///
/// legality=True
#include <stdlib.h>

void f(size_t N, double A[N], double B[N]) {
#pragma scop
  for (size_t p = 0; p < N; p++)
    A[p] = A[p] + 1.0;
  for (size_t q = 0; q < N; q++)
    B[q] = B[q] * 2.0;
#pragma endscop
}
