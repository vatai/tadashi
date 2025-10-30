/// TRANSFORMATION: 0, 2, "SPLIT", 2
/// #include <stdlib.h>
/// 
/// #define N 10
/// void f(int n, double alpha, double beta, double A[N][N], double B[N][N], double tmp[N], double x[N], double y[N]) {
///   int i,j;
/// #pragma scop
///   {
///     for(int _tadashi_0 = 0; _tadashi_0 <= 9; _tadashi_0 += 1)
///       {
///         tmp[_tadashi_0] = 0.0;
///         y[_tadashi_0] = 0.0;
///       }
///     for(int _tadashi_0 = 0; _tadashi_0 <= 9; _tadashi_0 += 1)
///       {
///         for(int _tadashi_1 = 0; _tadashi_1 <= 9; _tadashi_1 += 1)
///           {
///             tmp[_tadashi_0] = ((A[_tadashi_0][_tadashi_1] * x[_tadashi_1]) + tmp[_tadashi_0]);
///             y[_tadashi_0] = ((B[_tadashi_0][_tadashi_1] * x[_tadashi_1]) + y[_tadashi_0]);
///           }
///         y[_tadashi_0] = ((alpha * tmp[_tadashi_0]) + (beta * y[_tadashi_0]));
///       }
///   }
/// #pragma endscop
/// }
/// 
/// legality=True
#include <stdlib.h>

#define N 10
void f(int n, double alpha, double beta, double A[N][N], double B[N][N], double tmp[N], double x[N], double y[N]) {
  int i,j;
#pragma scop
  for (i = 0; i < N; i++)
    {
      tmp[i] = 0.0;
      y[i] = 0.0;
      for (j = 0; j < N; j++)
	{
	  tmp[i] = A[i][j] * x[j] + tmp[i];
	  y[i] = B[i][j] * x[j] + y[i];
	}
      y[i] = alpha * tmp[i] + beta * y[i];
    }
#pragma endscop
}
