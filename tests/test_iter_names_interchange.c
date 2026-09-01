/// TRANSFORMATION: 0, 1, "INTERCHANGE"
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   for(int col = 0; col < N; col += 1)
///     for(int row = 0; row < N; row += 1)
///       A[row][col] = (A[row][col] + 1.0);
/// #pragma endscop
/// }
///
/// legality=True
#include <stdlib.h>

void f(size_t N, double A[N][N]) {
#pragma scop
  for (size_t row = 0; row < N; row++)
    for (size_t col = 0; col < N; col++)
      A[row][col] = A[row][col] + 1.0;
#pragma endscop
}
