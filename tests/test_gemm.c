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
///     for(int _tadashi_0 = 0; _tadashi_0 < Ni; _tadashi_0 += 13)
///       for(int _tadashi_1 = 0; _tadashi_1 < Nj; _tadashi_1 += 25)
///         for(int _tadashi_2 = 0; _tadashi_2 <= min(12, Ni - _tadashi_0 - 1); _tadashi_2 += 1)
///           for(int _tadashi_3 = 0; _tadashi_3 <= min(24, Nj - _tadashi_1 - 1); _tadashi_3 += 1)
///             C[_tadashi_0 + _tadashi_2][_tadashi_1 + _tadashi_3] *= beta;
///     for(int _tadashi_0 = 0; _tadashi_0 < Ni; _tadashi_0 += 13)
///       for(int _tadashi_1 = 0; _tadashi_1 < Nk; _tadashi_1 += 25)
///         for(int _tadashi_2 = 0; _tadashi_2 < Nj; _tadashi_2 += 7)
///           for(int _tadashi_3 = 0; _tadashi_3 <= min(12, Ni - _tadashi_0 - 1); _tadashi_3 += 1)
///             for(int _tadashi_4 = 0; _tadashi_4 <= min(24, Nk - _tadashi_1 - 1); _tadashi_4 += 1)
///               for(int _tadashi_5 = 0; _tadashi_5 <= min(6, Nj - _tadashi_2 - 1); _tadashi_5 += 1)
///                 C[_tadashi_0 + _tadashi_3][_tadashi_2 + _tadashi_5] += ((alpha * A[_tadashi_0 + _tadashi_3][_tadashi_1 + _tadashi_4]) * B[_tadashi_1 + _tadashi_4][_tadashi_2 + _tadashi_5]);
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
