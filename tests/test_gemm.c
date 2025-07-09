/// TRANSFORMATION: 0, 2, "FULL_SPLIT"
/// TRANSFORMATION: 0, 3, "TILE2D", 13, 25
/// TRANSFORMATION: 0, 9, "TILE3D", 13, 25, 7
/// #include <stdlib.h>
///
/// void f(double alpha, double beta,
///        size_t Ni, size_t Nj, size_t Nk,
///        double A[Ni][Nk],
///        double B[Nk][Nj],
///        double C[Ni][Nj]) {
///   int i, j, k;
/// #pragma scop
///   #define min(x,y)    ((x) < (y) ? (x) : (y))
///   {
///     for(int c0 = 0; c0 < Ni; c0 += 13)
///       for(int c1 = 0; c1 < Nj; c1 += 25)
///         for(int c2 = 0; c2 <= min(12, Ni - c0 - 1); c2 += 1)
///           for(int c3 = 0; c3 <= min(24, Nj - c1 - 1); c3 += 1)
///             C[c0 + c2][c1 + c3] *= beta;
///     for(int c0 = 0; c0 < Ni; c0 += 13)
///       for(int c1 = 0; c1 < Nk; c1 += 25)
///         for(int c2 = 0; c2 < Nj; c2 += 7)
///           for(int c3 = 0; c3 <= min(12, Ni - c0 - 1); c3 += 1)
///             for(int c4 = 0; c4 <= min(24, Nk - c1 - 1); c4 += 1)
///               for(int c5 = 0; c5 <= min(6, Nj - c2 - 1); c5 += 1)
///                 C[c0 + c3][c2 + c5] += ((alpha * A[c0 + c3][c1 + c4]) * B[c1 + c4][c2 + c5]);
///   }
/// #pragma endscop
/// }
///
/// legality=True
/// legality=True
/// legality=True
#include <stdlib.h>

void f(double alpha, double beta,
       size_t Ni, size_t Nj, size_t Nk,
       double A[Ni][Nk],
       double B[Nk][Nj],
       double C[Ni][Nj]) {
  int i, j, k;
#pragma scop
  for (i = 0; i < Ni; i++) {
    for (j = 0; j < Nj; j++)
	C[i][j] *= beta;
    for (k = 0; k < Nk; k++) {
       for (j = 0; j < Nj; j++)
	  C[i][j] += alpha * A[i][k] * B[k][j];
    }
  }
#pragma endscop
}
