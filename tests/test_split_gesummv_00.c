/// TRANSFORMATION: 0, 2, "SPLIT", 2
/// TRANSFORMATION: 0, 18, "TILE1D", 64
/// #include <stdlib.h>
///
///
/// legality=False
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
