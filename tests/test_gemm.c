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
///   int _tadashi_0, _tadashi_1, _tadashi_2, _tadashi_3, _tadashi_4, _tadashi_5;
///   int lbp, ubp;
///   register int lbv, ubv;
///   #define min(x,y)    ((x) < (y) ? (x) : (y))
///   #define floord(n,d) (((n)<0) ? -((-(n)+(d)-1)/(d)) : (n)/(d))
///   {
///     for(_tadashi_0 = 0; _tadashi_0 <= floord(Ni - 1, 13); _tadashi_0 += 1)
///       for(_tadashi_1 = 0; _tadashi_1 <= floord(Nj - 1, 25); _tadashi_1 += 1)
///         for(_tadashi_2 = 13 * _tadashi_0; _tadashi_2 <= min(Ni - 1, 13 * _tadashi_0 + 12); _tadashi_2 += 1)
///           for(_tadashi_3 = 25 * _tadashi_1; _tadashi_3 <= min(Nj - 1, 25 * _tadashi_1 + 24); _tadashi_3 += 1)
///             C[_tadashi_2][_tadashi_3] *= beta;
///     for(_tadashi_0 = 0; _tadashi_0 <= floord(Ni - 1, 13); _tadashi_0 += 1)
///       for(_tadashi_1 = 0; _tadashi_1 <= floord(Nk - 1, 25); _tadashi_1 += 1)
///         for(_tadashi_2 = 0; _tadashi_2 <= floord(Nj - 1, 7); _tadashi_2 += 1)
///           for(_tadashi_3 = 13 * _tadashi_0; _tadashi_3 <= min(Ni - 1, 13 * _tadashi_0 + 12); _tadashi_3 += 1)
///             for(_tadashi_4 = 25 * _tadashi_1; _tadashi_4 <= min(Nk - 1, 25 * _tadashi_1 + 24); _tadashi_4 += 1)
///               for(_tadashi_5 = 7 * _tadashi_2; _tadashi_5 <= min(Nj - 1, 7 * _tadashi_2 + 6); _tadashi_5 += 1)
///                 C[_tadashi_3][_tadashi_5] += ((alpha * A[_tadashi_3][_tadashi_4]) * B[_tadashi_4][_tadashi_5]);
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
