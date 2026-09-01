/// TRANSFORMATION: 0, 2, "FULL_SPLIT"
/// TRANSFORMATION: 0, 3, "TILE_2D", 13, 25
/// TRANSFORMATION: 0, 9, "TILE_3D", 13, 25, 7
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
///     for(int i = 0; i < Ni; i += 13)
///       for(int j = 0; j < Nj; j += 25)
///         for(int i_1 = 0; i_1 <= min(12, Ni - i - 1); i_1 += 1)
///           for(int j_1 = 0; j_1 <= min(24, Nj - j - 1); j_1 += 1)
///             C[i + i_1][j + j_1] *= beta;
///     for(int i = 0; i < Ni; i += 13)
///       for(int j = 0; j < Nk; j += 25)
///         for(int i_1 = 0; i_1 < Nj; i_1 += 7)
///           for(int j_1 = 0; j_1 <= min(12, Ni - i - 1); j_1 += 1)
///             for(int k = 0; k <= min(24, Nk - j - 1); k += 1)
///               for(int j_2 = 0; j_2 <= min(6, Nj - i_1 - 1); j_2 += 1)
///                 C[i + j_1][i_1 + j_2] += ((alpha * A[i + j_1][j + k]) * B[j + k][i_1 + j_2]);
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
