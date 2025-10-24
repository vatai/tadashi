/// TRANSFORMATION: 0, 2, "SPLIT", 2
/// #include <stdlib.h>
/// 
/// #define N 10
/// void f(int n, double alpha, double beta, double A[N][N], double B[N][N], double tmp[N], double x[N], double y[N]) {
///   int i,j;
/// #pragma scop
///   {
///     for(int c0 = 0; c0 <= 9; c0 += 1)
///       {
///         tmp[c0] = 0.0;
///         y[c0] = 0.0;
///       }
///     for(int c0 = 0; c0 <= 9; c0 += 1)
///       {
///         for(int c1 = 0; c1 <= 9; c1 += 1)
///           {
///             tmp[c0] = ((A[c0][c1] * x[c1]) + tmp[c0]);
///             y[c0] = ((B[c0][c1] * x[c1]) + y[c0]);
///           }
///         y[c0] = ((alpha * tmp[c0]) + (beta * y[c0]));
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
