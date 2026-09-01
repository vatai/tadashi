/// TRANSFORMATION: 0, 3, "SET_PARALLEL", 1
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N], double B[N]) {
///   double i = 42.0;
/// #pragma scop
///   {
/// #pragma omp parallel for num_threads(1)
///     for(int i_1 = 0; i_1 < N; i_1 += 1)
///       A[i_1] = (A[i_1] + 1.0);
///     B[0] = i;
///   }
/// #pragma endscop
/// }
///
/// legality=True
#include <stdlib.h>

void f(size_t N, double A[N], double B[N]) {
  double i = 42.0;
#pragma scop
  for (size_t i = 0; i < N; i++)
    A[i] = A[i] + 1.0;
  B[0] = i;
#pragma endscop
}
