/// TRANSFORMATION: 0, 1, "TILE_3D", 13, 17, 25
/// #include <stdlib.h>
///
/// void f(size_t N, double A[N][N]) {
/// #pragma scop
///   int _tadashi_0, _tadashi_1, _tadashi_2, _tadashi_3, _tadashi_4, _tadashi_5, _tadashi_6;
///   register int lbv, ubv;
///   #define min(x,y)    ((x) < (y) ? (x) : (y))
///   #define max(x,y)    ((x) > (y) ? (x) : (y))
///   #define floord(n,d) (((n)<0) ? -((-(n)+(d)-1)/(d)) : (n)/(d))
///   for(_tadashi_0 = 0; _tadashi_0 <= floord(N - 1, 13); _tadashi_0 += 1)
///     for(_tadashi_1 = 0; _tadashi_1 <= (N - 1) / 17; _tadashi_1 += 1)
///       for(_tadashi_2 = 0; _tadashi_2 <= (N - 1) / 25; _tadashi_2 += 1)
///         for(_tadashi_3 = 13 * _tadashi_0; _tadashi_3 <= min(N - 1, 13 * _tadashi_0 + 12); _tadashi_3 += 1)
///           for(_tadashi_4 = max(1, 17 * _tadashi_1); _tadashi_4 <= min(N - 1, 17 * _tadashi_1 + 16); _tadashi_4 += 1)
///             for(_tadashi_5 = 25 * _tadashi_2; _tadashi_5 <= min(N - 1, 25 * _tadashi_2 + 24); _tadashi_5 += 1)
///               {
///                 for(_tadashi_6 = 0; _tadashi_6 < N; _tadashi_6 += 1)
///                   A[_tadashi_4][_tadashi_5] = (A[_tadashi_4][_tadashi_5] + (A[_tadashi_4 - 1][_tadashi_5] * (_tadashi_6)));
///                 for(_tadashi_6 = 0; _tadashi_6 < N; _tadashi_6 += 1)
///                   A[_tadashi_4][_tadashi_5] = ((A[_tadashi_4][_tadashi_5] + A[_tadashi_4 - 1][_tadashi_5]) + (_tadashi_6));
///               }
/// #pragma endscop
/// }
///
/// legality=False
#include <stdlib.h>

void f(size_t N, double A[N][N]) {
#pragma scop
  for(size_t t = 0; t < N; t++)
    for (size_t i = 1; i < N; i++) {
      for (size_t j = 0; j < N; j++) {
        for (size_t k1 = 0; k1 < N; k1++)
          A[i][j] = A[i][j] + A[i - 1][j] * k1;
        for (size_t k2 = 0; k2 < N; k2++)
          A[i][j] = A[i][j] + A[i - 1][j] + k2;
      }
    }
#pragma endscop
}
